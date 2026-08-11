from __future__ import annotations

"""Run zero-retry blind target judges over frozen attribution packets."""

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import run_attribution
import run_judges
from attribution_common import (
    ATTRIBUTION_ROOT,
    DEFINITE_LABELS,
    EVIDENCE_ROOT,
    EXPECTED_INSTRUCTIONS_SHA256,
    EXPECTED_SCHEMA_SHA256,
    INSTRUCTIONS_PATH,
    JUDGES,
    MAPS_ROOT,
    PACKETS_ROOT,
    PRIMARY_JUDGES,
    SCHEMA_PATH,
    TARGETS_BY_GROUP,
    load_specs,
    load_valid_map,
    packet_text,
    validate_final,
)
from run_discovery import normalize_text, sha256_bytes, sha256_file


WRITER_MANIFEST_PATH = ATTRIBUTION_ROOT / "manifest.json"
OUTPUT_ROOT = ATTRIBUTION_ROOT / "judgments"
MANIFEST_ROOT = ATTRIBUTION_ROOT / "judge-manifests"
MANIFEST_WRITE_LOCK = ATTRIBUTION_ROOT / ".judge-manifests.write.lock"
MODEL = "gpt-5.6-sol"
TIMEOUT_SECONDS = 900


@contextmanager
def judge_manifest_write_lock():
    """Serialize every repository-managed attribution manifest writer."""

    ATTRIBUTION_ROOT.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    try:
        with MANIFEST_WRITE_LOCK.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(token + "\n")
    except FileExistsError as exc:
        raise RuntimeError(f"attribution judge manifest writer is already active: {MANIFEST_WRITE_LOCK}") from exc
    try:
        yield
    finally:
        if not MANIFEST_WRITE_LOCK.is_file() or MANIFEST_WRITE_LOCK.read_text(encoding="utf-8").strip() != token:
            raise RuntimeError("attribution judge manifest write lock changed while held")
        MANIFEST_WRITE_LOCK.unlink()


def writer_snapshot() -> dict[str, Any]:
    if not WRITER_MANIFEST_PATH.is_file():
        raise RuntimeError(f"attribution writer manifest missing: {WRITER_MANIFEST_PATH}")
    specs = load_specs()
    manifest = json.loads(WRITER_MANIFEST_PATH.read_text(encoding="utf-8"))
    current = run_attribution.preflight_payload(run_attribution.EXPECTED_CANDIDATE_COMMIT)
    if not isinstance(manifest, dict):
        raise RuntimeError("attribution writer manifest must be an object")
    if (
        manifest.get("valid_calls") != 24
        or manifest.get("calls_planned") != 24
        or manifest.get("binding_stable") is not True
        or manifest.get("record_closure_issues") != []
        or manifest.get("pair_launch") != "concurrent_arms_sequential_pairs"
        or run_attribution.input_identity(manifest) != run_attribution.input_identity(current)
        or not isinstance(manifest.get("postflight"), dict)
        or run_attribution.input_identity(manifest["postflight"])
        != run_attribution.input_identity(current)
    ):
        raise RuntimeError("attribution writer manifest is not a stable frozen 24/24 run")
    records = manifest.get("records")
    if not isinstance(records, list):
        raise RuntimeError("attribution writer records are missing")
    closure = run_attribution.record_closure_issues(records, specs, manifest, ATTRIBUTION_ROOT)
    if closure:
        raise RuntimeError(f"attribution writer closure failed: {closure}")
    for row in specs["tasks"]:
        snapshot = ATTRIBUTION_ROOT / "tasks" / f"{row['task_id']}.md"
        source = EVIDENCE_ROOT / "tasks" / f"{row['source_task']}.md"
        if not snapshot.is_file() or snapshot.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
            raise RuntimeError(f"attribution task snapshot mismatch: {row['task_id']}")
    return {
        "writer_manifest_sha256": sha256_file(WRITER_MANIFEST_PATH),
        "writer_input_identity": run_attribution.input_identity(manifest),
    }


def task_ids() -> list[str]:
    return [row["task_id"] for row in load_specs()["tasks"]]


def public_packet_bindings(packets: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        task_id: {key: value for key, value in packet.items() if not key.startswith("_")}
        for task_id, packet in packets.items()
    }


def judge_record_execution_issues(
    record: dict[str, Any],
    judge_id: str,
    task_id: str,
) -> list[str]:
    expected = {
        "judge_id": judge_id,
        "task_id": task_id,
        "model": MODEL,
        "reasoning_effort": "max",
        "return_code": 0,
        "timeout": False,
        "retry_count": 0,
        "valid": True,
        "issues": [],
    }
    issues = [f"record_{key}_mismatch" for key, value in expected.items() if record.get(key) != value]
    duration = record.get("duration_seconds")
    if not isinstance(duration, (int, float)) or duration < 0:
        issues.append("record_duration_invalid")
    return issues


def preflight(
    judges: list[str],
    selected_tasks: list[str] | None = None,
    *,
    require_empty_outputs: bool = True,
) -> dict[str, Any]:
    if not judges or len(judges) != len(set(judges)) or any(judge not in JUDGES for judge in judges):
        raise RuntimeError("judges must be unique preregistered IDs")
    if not SCHEMA_PATH.is_file() or not INSTRUCTIONS_PATH.is_file():
        raise RuntimeError("attribution judge schema or instructions missing")
    if sha256_file(SCHEMA_PATH) != EXPECTED_SCHEMA_SHA256:
        raise RuntimeError("attribution judge schema differs from preregistration")
    if sha256_file(INSTRUCTIONS_PATH) != EXPECTED_INSTRUCTIONS_SHA256:
        raise RuntimeError("attribution judge instructions differ from preregistration")
    all_tasks = task_ids()
    if judges == ["judge-3"]:
        unresolved = primary_unresolved_tasks()
        chosen = unresolved if selected_tasks is None else selected_tasks
        if chosen != unresolved or not chosen:
            raise RuntimeError("judge-3 tasks must exactly match non-empty primary unresolved list")
    else:
        if any(judge not in PRIMARY_JUDGES for judge in judges):
            raise RuntimeError("judge-3 must run alone after primary disagreement")
        chosen = all_tasks if selected_tasks is None else selected_tasks
        if chosen != all_tasks:
            raise RuntimeError("primary judges must score all frozen attribution tasks")
    writer = writer_snapshot()
    run_inputs: dict[str, Any] = {
        **writer,
        "specs_sha256": sha256_file(run_attribution.SPECS_PATH),
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "instructions_sha256": sha256_file(INSTRUCTIONS_PATH),
        "model": MODEL,
        "reasoning_effort": "max",
        "retry_count": 0,
    }
    judge_rows: dict[str, Any] = {}
    seen_orientations: set[tuple[bool, ...]] = set()
    for judge_id in judges:
        mapping, mapping_hash = load_valid_map(judge_id)
        orientation = tuple(row["left"] == "candidate" for row in mapping["mappings"])
        if orientation in seen_orientations:
            raise RuntimeError("requested judges have duplicate arm orientation")
        seen_orientations.add(orientation)
        packets: dict[str, dict[str, str]] = {}
        for task_id in chosen:
            expected, content_hash, row, left, right = packet_text(judge_id, task_id)
            path = PACKETS_ROOT / judge_id / f"{task_id}.md"
            if not path.is_file():
                raise RuntimeError(f"attribution packet missing: {judge_id}/{task_id}")
            actual_packet = path.read_text(encoding="utf-8")
            if actual_packet != expected:
                raise RuntimeError(f"attribution packet mismatch: {judge_id}/{task_id}")
            packets[task_id] = {
                "pair_id": row["pair_id"],
                "file_sha256": sha256_bytes(actual_packet.encode("utf-8")),
                "content_sha256": content_hash,
                "_prompt": actual_packet,
                "_left": left,
                "_right": right,
            }
        destination = OUTPUT_ROOT / judge_id
        manifest_path = MANIFEST_ROOT / f"{judge_id}.json"
        if require_empty_outputs and (destination.exists() or manifest_path.exists()):
            raise RuntimeError(f"attribution judge output already exists: {judge_id}")
        judge_rows[judge_id] = {
            "map_sha256": mapping_hash,
            "tasks": chosen,
            "packets": packets,
            "calls_planned": len(chosen),
        }
    return {
        "run_inputs": run_inputs,
        "judges": judge_rows,
        "calls_planned": sum(row["calls_planned"] for row in judge_rows.values()),
    }


def invoke_one(
    judge_id: str,
    task_id: str,
    row: dict[str, str],
    mapping_hash: str,
    frozen_schema: Path,
    staging: Path,
) -> dict[str, Any]:
    prompt = row["_prompt"]
    result_path = staging / judge_id / "per-task" / f"{task_id}.json"
    trace_path = staging / judge_id / "per-task" / f"{task_id}.trace.jsonl"
    stderr_path = staging / judge_id / "per-task" / f"{task_id}.stderr.txt"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryDirectory(prefix=f"attribution-blind-{judge_id}-{task_id}-") as empty_root:
        command = [
            shutil.which("codex") or "codex",
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-C",
            empty_root,
            "-m",
            MODEL,
            "-c",
            'model_reasoning_effort="max"',
            "-s",
            "read-only",
            "--ephemeral",
            "--output-schema",
            str(frozen_schema),
            "--json",
            "-o",
            str(result_path),
            "-",
        ]
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
            return_code: int | None = completed.returncode
            stdout, stderr = completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            return_code = None
            stdout, stderr = normalize_text(exc.stdout), normalize_text(exc.stderr)
    trace_path.write_text(normalize_text(stdout), encoding="utf-8", newline="\n")
    stderr_path.write_text(normalize_text(stderr), encoding="utf-8", newline="\n")
    final = result_path.read_text(encoding="utf-8") if result_path.is_file() else ""
    issues = run_judges.trace_issues(trace_path, final)
    prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    if prompt_hash != row["file_sha256"]:
        issues.append("packet_changed_after_preflight")
    issues.extend(
        validate_final(
            final,
            judge_id,
            task_id,
            row["pair_id"],
            mapping_hash,
            row["content_sha256"],
            row["_left"],
            row["_right"],
        )
        if final
        else ["missing_final"]
    )
    issues = sorted(set(issues))
    return {
        "judge_id": judge_id,
        "task_id": task_id,
        "model": MODEL,
        "reasoning_effort": "max",
        "return_code": return_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "retry_count": 0,
        "prompt_sha256": prompt_hash,
        "final_file": f"judgments/{judge_id}/per-task/{task_id}.json",
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "trace_file": f"judgments/{judge_id}/per-task/{task_id}.trace.jsonl",
        "trace_sha256": sha256_file(trace_path),
        "stderr_file": f"judgments/{judge_id}/per-task/{task_id}.stderr.txt",
        "stderr_sha256": sha256_file(stderr_path),
        "issues": issues,
        "valid": return_code == 0 and not timed_out and not issues,
    }


def execute(judges: list[str], selected_tasks: list[str] | None = None) -> int:
    before = preflight(judges, selected_tasks)
    staging = Path(tempfile.mkdtemp(prefix="attribution-judges.incomplete-", dir=ATTRIBUTION_ROOT))
    frozen_schema = staging / "attribution-judge-schema.json"
    frozen_schema.write_bytes(SCHEMA_PATH.read_bytes())
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(
                invoke_one,
                judge_id,
                task_id,
                packet,
                judge_row["map_sha256"],
                frozen_schema,
                staging,
            ): (judge_id, task_id)
            for judge_id, judge_row in before["judges"].items()
            for task_id, packet in judge_row["packets"].items()
        }
        for future in concurrent.futures.as_completed(futures):
            judge_id, task_id = futures[future]
            try:
                record = future.result()
            except Exception as exc:
                record = {
                    "judge_id": judge_id,
                    "task_id": task_id,
                    "model": MODEL,
                    "reasoning_effort": "max",
                    "retry_count": 0,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "valid": False,
                }
            records.append(record)
            print(
                json.dumps(
                    {key: record.get(key) for key in ("judge_id", "task_id", "valid", "duration_seconds")},
                    ensure_ascii=False,
                ),
                flush=True,
            )
    try:
        after = preflight(judges, selected_tasks, require_empty_outputs=False)
        inputs_stable = after == before and sha256_file(frozen_schema) == before["run_inputs"]["schema_sha256"]
        postflight_error = None
    except Exception as exc:
        inputs_stable = False
        postflight_error = f"{type(exc).__name__}: {exc}"
    for judge_id, judge_row in before["judges"].items():
        judge_records = sorted(
            (record for record in records if record["judge_id"] == judge_id),
            key=lambda record: record["task_id"],
        )
        manifest = {
            "schema_version": 1,
            "judge_id": judge_id,
            "model": MODEL,
            "reasoning_effort": "max",
            "retry_count": 0,
            "run_inputs": before["run_inputs"],
            "map_sha256": judge_row["map_sha256"],
            "tasks": judge_row["tasks"],
            "packets": public_packet_bindings(judge_row["packets"]),
            "calls_planned": judge_row["calls_planned"],
            "inputs_stable": inputs_stable,
            "postflight_error": postflight_error,
            "records": judge_records,
            "valid_calls": sum(bool(record.get("valid")) for record in judge_records),
        }
        manifest_path = staging / "manifests" / f"{judge_id}.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    frozen_schema.unlink()
    with judge_manifest_write_lock():
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
        conflicts = [
            judge_id
            for judge_id in judges
            if (OUTPUT_ROOT / judge_id).exists()
            or (MANIFEST_ROOT / f"{judge_id}.json").exists()
        ]
        if conflicts:
            raise RuntimeError(f"attribution judge output appeared before commit: {conflicts}")
        for judge_id in judges:
            (staging / judge_id).replace(OUTPUT_ROOT / judge_id)
            (staging / "manifests" / f"{judge_id}.json").replace(MANIFEST_ROOT / f"{judge_id}.json")
    (staging / "manifests").rmdir()
    staging.rmdir()
    valid = sum(bool(record.get("valid")) for record in records)
    expected = before["calls_planned"]
    print(json.dumps({"valid_calls": valid, "expected_calls": expected, "inputs_stable": inputs_stable}))
    return 0 if valid == expected and inputs_stable else 2


def load_valid_judge_results(judge_id: str) -> dict[str, dict[str, Any]]:
    manifest_path = MANIFEST_ROOT / f"{judge_id}.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"judge manifest missing: {judge_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = manifest.get("tasks") if isinstance(manifest, dict) else None
    if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
        raise RuntimeError(f"judge manifest task list invalid: {judge_id}")
    expected = preflight([judge_id], selected, require_empty_outputs=False)
    judge_expected = expected["judges"][judge_id]
    records = manifest.get("records")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("judge_id") != judge_id
        or manifest.get("model") != MODEL
        or manifest.get("reasoning_effort") != "max"
        or manifest.get("retry_count") != 0
        or manifest.get("run_inputs") != expected["run_inputs"]
        or manifest.get("map_sha256") != judge_expected["map_sha256"]
        or manifest.get("packets") != public_packet_bindings(judge_expected["packets"])
        or manifest.get("calls_planned") != len(selected)
        or manifest.get("valid_calls") != len(selected)
        or manifest.get("inputs_stable") is not True
        or not isinstance(records, list)
        or len(records) != len(selected)
    ):
        raise RuntimeError(f"judge manifest binding invalid: {judge_id}")
    by_task: dict[str, dict[str, Any]] = {}
    _, mapping_hash = load_valid_map(judge_id)
    for record in records:
        task_id = record.get("task_id")
        if task_id in by_task or task_id not in selected:
            raise RuntimeError(f"judge record invalid or duplicate: {judge_id}/{task_id}")
        execution_issues = judge_record_execution_issues(record, judge_id, task_id)
        if execution_issues:
            raise RuntimeError(
                f"judge record execution binding invalid: {judge_id}/{task_id}: {execution_issues}"
            )
        packet = judge_expected["packets"][task_id]
        expected_paths = {
            "final": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.json",
            "trace": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.trace.jsonl",
            "stderr": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.stderr.txt",
        }
        frozen_text: dict[str, str] = {}
        for kind, path in expected_paths.items():
            expected_relative = f"judgments/{judge_id}/per-task/{path.name}"
            if record.get(f"{kind}_file") != expected_relative or not path.is_file():
                raise RuntimeError(f"judge {kind} path invalid: {judge_id}/{task_id}")
            raw_bytes = path.read_bytes()
            decoded = raw_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            frozen_text[kind] = decoded
            observed_hash = (
                sha256_bytes(decoded.encode("utf-8"))
                if kind == "final"
                else sha256_bytes(raw_bytes)
            )
            if record.get(f"{kind}_sha256") != observed_hash:
                raise RuntimeError(f"judge {kind} hash invalid: {judge_id}/{task_id}")
        if record.get("prompt_sha256") != packet["file_sha256"]:
            raise RuntimeError(f"judge prompt hash invalid: {judge_id}/{task_id}")
        final_text = frozen_text["final"]
        trace_issues = run_judges.trace_issues_text(frozen_text["trace"], final_text)
        if trace_issues:
            raise RuntimeError(f"judge trace recomputation failed: {judge_id}/{task_id}: {trace_issues}")
        issues = validate_final(
            final_text,
            judge_id,
            task_id,
            packet["pair_id"],
            mapping_hash,
            packet["content_sha256"],
            packet["_left"],
            packet["_right"],
        )
        if issues:
            raise RuntimeError(f"judge final invalid: {judge_id}/{task_id}: {issues}")
        by_task[task_id] = json.loads(final_text)
    if set(by_task) != set(selected):
        raise RuntimeError(f"judge result coverage mismatch: {judge_id}")
    return by_task


def labels_by_arm(judge_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    mapping, _ = load_valid_map(judge_id)
    row = next(item for item in mapping["mappings"] if item["task_id"] == task_id)
    result: dict[str, dict[str, str]] = {}
    for target in payload["targets"]:
        result[target["target_id"]] = {
            row["left"]: target["left"]["label"],
            row["right"]: target["right"]["label"],
        }
    return result


def needs_third_judge(
    primary_labels: dict[str, dict[str, dict[str, str]]],
    targets: tuple[str, ...],
) -> bool:
    return any(
        primary_labels["judge-1"][target][arm] not in DEFINITE_LABELS
        or primary_labels["judge-2"][target][arm] not in DEFINITE_LABELS
        or primary_labels["judge-1"][target][arm]
        != primary_labels["judge-2"][target][arm]
        for target in targets
        for arm in ("baseline", "candidate")
    )


def primary_unresolved_tasks() -> list[str]:
    outputs = {judge: load_valid_judge_results(judge) for judge in PRIMARY_JUDGES}
    unresolved: list[str] = []
    for task_id in task_ids():
        group = task_id.split("-", 1)[0]
        by_judge = {
            judge: labels_by_arm(judge, task_id, outputs[judge][task_id])
            for judge in PRIMARY_JUDGES
        }
        if needs_third_judge(by_judge, TARGETS_BY_GROUP[group]):
            unresolved.append(task_id)
    return unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judges", nargs="+", required=True)
    parser.add_argument("--tasks", nargs="+")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.judges, args.tasks), ensure_ascii=False, indent=2))
        return 0
    return execute(args.judges, args.tasks)


if __name__ == "__main__":
    raise SystemExit(main())
