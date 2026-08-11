from __future__ import annotations

"""Run isolated zero-retry blind judges over prebuilt one-pair packets."""

import argparse
import concurrent.futures
import hashlib
import json
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from run_ab import build_prompt
from run_discovery import PROVIDERS, normalize_text, sha256_bytes, sha256_file


EVIDENCE_ROOT = Path(__file__).resolve().parent
AB_ROOT = EVIDENCE_ROOT / "ab"
SPECS_PATH = EVIDENCE_ROOT / "ab_specs.json"
INSTRUCTIONS_PATH = EVIDENCE_ROOT / "ab-judge-instructions.md"
WRITER_MANIFEST_PATH = AB_ROOT / "manifest.json"
PACKETS_ROOT = AB_ROOT / "packets"
MAPS_ROOT = EVIDENCE_ROOT / "ab_maps"
OUTPUT_ROOT = AB_ROOT / "judgments"
MANIFEST_ROOT = AB_ROOT / "judge-manifests"
SCHEMA_PATH = EVIDENCE_ROOT.parent / "v0.0.8-release-gate" / "judge_schema.json"
MODEL = "gpt-5.6-sol"
TIMEOUT_SECONDS = 900
MAP_SEED = "academic-synthesis-holdout-20260811-v1"


def expected_orientations(task_ids: list[str], judge_id: str) -> list[bool]:
    digest = hashlib.sha256(f"{MAP_SEED}\0{judge_id}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    orientations = [False, True] * ((len(task_ids) + 1) // 2)
    orientations = orientations[: len(task_ids)]
    rng.shuffle(orientations)
    return orientations


def expected_packet_text(
    judge_id: str,
    task_id: str,
    pair_id: str,
    left_arm: str,
    right_arm: str,
    mapping_hash: str,
) -> str:
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()
    task = (AB_ROOT / "tasks" / f"{task_id}.md").read_text(encoding="utf-8").strip()
    left = (AB_ROOT / "raw" / left_arm / f"{task_id}.md").read_text(encoding="utf-8").strip()
    right = (AB_ROOT / "raw" / right_arm / f"{task_id}.md").read_text(encoding="utf-8").strip()
    return (
        f"{instructions}\n\n"
        "## 当前匿名对\n\n"
        f"- judge_id：`{judge_id}`\n"
        f"- task_id：`{task_id}`\n"
        f"- pair_id：`{pair_id}`\n"
        f"- mapping_sha256：`{mapping_hash}`\n\n"
        f"## 用户任务\n\n{task}\n\n"
        f"## 左稿\n\n{left}\n\n"
        f"## 右稿\n\n{right}\n\n"
        "## 输出绑定\n\n"
        "返回一个符合 judge_schema.json 的对象，`results` 数组只含当前一项。"
        f"`judge_id` 写 `{judge_id}`，`mapping_sha256` 写 `{mapping_hash}`，"
        f"`task_id` 写 `{task_id}`，`pair_id` 写 `{pair_id}`，`blind` 为 true。\n"
    )


def trace_issues_text(trace_text: str, final: str) -> list[str]:
    counts = {"thread.started": 0, "turn.completed": 0}
    messages: list[str] = []
    issues: list[str] = []
    for line in trace_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            issues.append("malformed_trace_json")
            continue
        event_type = event.get("type")
        if event_type in counts:
            counts[event_type] += 1
        item = event.get("item") or {}
        item_type = str(item.get("type") or "")
        if event_type == "item.completed" and item_type == "agent_message":
            messages.append(str(item.get("text") or ""))
        if item and item_type != "agent_message":
            issues.append(f"forbidden_judge_tool:{item_type}")
    for event_type, count in counts.items():
        if count != 1:
            issues.append(f"trace_count:{event_type}:{count}")
    if len(messages) != 1:
        issues.append(f"trace_count:agent_message:{len(messages)}")
    elif messages[0].strip() != final.strip():
        issues.append("trace_final_mismatch")
    return sorted(set(issues))


def trace_issues(trace_path: Path, final: str) -> list[str]:
    return trace_issues_text(
        trace_path.read_text(encoding="utf-8", errors="replace"),
        final,
    )


def validate_final(
    final: str,
    judge_id: str,
    task_id: str,
    pair_id: str,
    mapping_hash: str,
) -> list[str]:
    try:
        payload = json.loads(final)
    except json.JSONDecodeError as exc:
        return [f"invalid_json:{exc.msg}"]
    issues: list[str] = []
    expected_top_keys = {"schema_version", "judge_id", "blind", "mapping_sha256", "results"}
    if not isinstance(payload, dict) or set(payload) != expected_top_keys:
        return ["top_level_schema_mismatch"]
    if payload.get("schema_version") != 1:
        issues.append("schema_version_mismatch")
    if payload.get("judge_id") != judge_id:
        issues.append("judge_id_mismatch")
    if payload.get("blind") is not True:
        issues.append("blind_not_true")
    if payload.get("mapping_sha256") != mapping_hash:
        issues.append("mapping_sha256_mismatch")
    results = payload.get("results")
    if not isinstance(results, list) or len(results) != 1:
        issues.append("result_count_not_one")
        return issues
    result = results[0]
    expected_result_keys = {"task_id", "pair_id", "left", "right", "winner", "rationale", "anchors"}
    if not isinstance(result, dict) or set(result) != expected_result_keys:
        issues.append("result_schema_mismatch")
        return issues
    if result.get("task_id") != task_id:
        issues.append("task_id_mismatch")
    if result.get("pair_id") != pair_id:
        issues.append("pair_id_mismatch")
    if result.get("winner") not in {"left", "right", "tie"}:
        issues.append("winner_invalid")
    if not isinstance(result.get("rationale"), str) or not result["rationale"].strip():
        issues.append("rationale_invalid")
    anchors = result.get("anchors")
    if not isinstance(anchors, list) or any(not isinstance(item, str) or not item for item in anchors):
        issues.append("anchors_invalid")
    for side_name in ("left", "right"):
        side = result.get(side_name)
        if not isinstance(side, dict) or set(side) != {"verdict", "hard_failures", "notes"}:
            issues.append(f"{side_name}_schema_mismatch")
            continue
        verdict = side.get("verdict")
        failures = side.get("hard_failures")
        if verdict not in {"PASS", "WARN", "FAIL"}:
            issues.append(f"{side_name}_verdict_invalid")
        if not isinstance(failures, list) or any(not isinstance(item, str) or not item for item in failures):
            issues.append(f"{side_name}_hard_failures_invalid")
        elif (verdict == "FAIL") != bool(failures):
            issues.append(f"{side_name}_verdict_failure_mismatch")
        if not isinstance(side.get("notes"), str):
            issues.append(f"{side_name}_notes_invalid")
    return issues


def preflight(judges: list[str]) -> dict[str, Any]:
    for required_path in (SCHEMA_PATH, SPECS_PATH, INSTRUCTIONS_PATH, WRITER_MANIFEST_PATH):
        if not required_path.is_file():
            raise RuntimeError(f"judge input missing: {required_path}")
    if len(judges) != len(set(judges)):
        raise RuntimeError("judge IDs must be unique")
    if not judges:
        raise RuntimeError("at least one judge ID is required")
    specs = json.loads(SPECS_PATH.read_text(encoding="utf-8"))
    spec_rows = specs.get("tasks") if isinstance(specs, dict) else None
    if not isinstance(spec_rows, list) or len(spec_rows) != 12:
        raise RuntimeError("judge specs must contain 12 tasks")
    expected_task_ids = [row.get("task_id") for row in spec_rows]
    if not all(isinstance(task_id, str) and task_id for task_id in expected_task_ids):
        raise RuntimeError("judge specs contain an invalid task ID")
    if len(set(expected_task_ids)) != 12:
        raise RuntimeError("judge specs task IDs must be unique")
    spec_by_id = {row["task_id"]: row for row in spec_rows}
    writer = json.loads(WRITER_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(writer, dict):
        raise RuntimeError("writer manifest must be an object")
    writer_records = writer.get("records")
    if (
        writer.get("valid_calls") != 24
        or writer.get("calls_planned") != 24
        or writer.get("binding_stable") is not True
        or writer.get("specs_sha256") != sha256_file(SPECS_PATH)
        or not isinstance(writer_records, list)
        or len(writer_records) != 24
    ):
        raise RuntimeError("writer manifest is not a stable 24/24 run")
    writer_task_hashes = writer.get("task_sha256")
    writer_prompt_hashes = writer.get("prompt_sha256")
    if not isinstance(writer_task_hashes, dict) or not isinstance(writer_prompt_hashes, dict):
        raise RuntimeError("writer manifest lacks task or prompt hashes")
    arm_bindings: dict[str, tuple[str, str]] = {}
    for arm in ("baseline", "candidate"):
        binding = writer.get(arm)
        if not isinstance(binding, dict):
            raise RuntimeError(f"writer manifest lacks {arm} binding")
        commit = binding.get("commit")
        fingerprint = binding.get("runtime_fingerprint")
        if not isinstance(commit, str) or not isinstance(fingerprint, str):
            raise RuntimeError(f"writer manifest has invalid {arm} binding")
        arm_bindings[arm] = (commit, fingerprint)
    provider_models = {provider.name: provider.model for provider in PROVIDERS}
    records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for record in writer_records:
        if not isinstance(record, dict):
            raise RuntimeError("writer manifest records must be objects")
        key = (record.get("arm"), record.get("pair_id"))
        if key in records_by_key or key[0] not in {"baseline", "candidate"} or key[1] not in spec_by_id:
            raise RuntimeError(f"writer manifest has an invalid or duplicate record: {key}")
        if record.get("valid") is not True:
            raise RuntimeError(f"writer record is not valid: {key}")
        expected_spec = spec_by_id[key[1]]
        expected_provider = expected_spec["provider"]
        expected_commit, expected_fingerprint = arm_bindings[key[0]]
        if (
            record.get("source_task") != expected_spec["source_task"]
            or record.get("provider") != expected_provider
            or record.get("model") != provider_models[expected_provider]
            or record.get("reasoning_effort") != "max"
            or record.get("retry_count") != 0
            or record.get("commit") != expected_commit
            or record.get("runtime_fingerprint") != expected_fingerprint
        ):
            raise RuntimeError(f"writer record binding mismatch: {key}")
        expected_relative = f"raw/{key[0]}/{key[1]}.md"
        if record.get("final_file") != expected_relative:
            raise RuntimeError(f"writer final path mismatch: {key}")
        raw_path = AB_ROOT / expected_relative
        if (
            not raw_path.is_file()
            or sha256_bytes(raw_path.read_text(encoding="utf-8").encode("utf-8"))
            != record.get("final_sha256")
        ):
            raise RuntimeError(f"writer raw hash mismatch: {key}")
        records_by_key[key] = record
    prompt_hash_by_task: dict[str, str] = {}
    for task_id, row in spec_by_id.items():
        task_path = AB_ROOT / "tasks" / f"{task_id}.md"
        source_path = EVIDENCE_ROOT / "tasks" / f"{row['source_task']}.md"
        if not task_path.is_file() or not source_path.is_file():
            raise RuntimeError(f"task snapshot missing: {task_id}")
        task_text = task_path.read_text(encoding="utf-8")
        source_text = source_path.read_text(encoding="utf-8")
        if task_text != source_text:
            raise RuntimeError(f"task snapshot mismatch: {task_id}")
        source_hash = sha256_bytes(source_text.encode("utf-8"))
        if writer_task_hashes.get(row["source_task"]) != source_hash:
            raise RuntimeError(f"writer task hash mismatch: {task_id}")
        prompt_hash = sha256_bytes(build_prompt(task_text).encode("utf-8"))
        prompt_hash_by_task[task_id] = prompt_hash
        if writer_prompt_hashes.get(row["source_task"]) != prompt_hash:
            raise RuntimeError(f"writer prompt template hash mismatch: {task_id}")
    for (arm, task_id), record in records_by_key.items():
        if record.get("prompt_sha256") != prompt_hash_by_task[task_id] or record.get("prompt_bound") is not True:
            raise RuntimeError(f"writer prompt record mismatch: {(arm, task_id)}")
    payload: dict[str, Any] = {
        "model": MODEL,
        "reasoning_effort": "max",
        "retry_count": 0,
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "specs_sha256": sha256_file(SPECS_PATH),
        "instructions_sha256": sha256_file(INSTRUCTIONS_PATH),
        "writer_manifest_sha256": sha256_file(WRITER_MANIFEST_PATH),
        "judges": {},
    }
    seen_orientations: set[tuple[bool, ...]] = set()
    for judge_id in judges:
        map_path = MAPS_ROOT / f"{judge_id}.json"
        packet_dir = PACKETS_ROOT / judge_id
        if not map_path.is_file() or not packet_dir.is_dir():
            raise RuntimeError(f"map or packets missing for {judge_id}")
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
        if (
            not isinstance(mapping, dict)
            or mapping.get("schema_version") != 1
            or mapping.get("judge_id") != judge_id
            or mapping.get("task_specs_sha256") != sha256_file(SPECS_PATH)
            or mapping.get("seed_sha256") != sha256_bytes(MAP_SEED.encode("utf-8"))
        ):
            raise RuntimeError(f"invalid map binding for {judge_id}")
        rows = mapping.get("mappings")
        if not isinstance(rows, list) or len(rows) != 12:
            raise RuntimeError(f"{judge_id} must have 12 map rows")
        task_ids = [row.get("task_id") for row in rows]
        pair_ids = [row.get("pair_id") for row in rows]
        if task_ids != expected_task_ids or len(set(task_ids)) != 12:
            raise RuntimeError(f"{judge_id} task IDs do not exactly match frozen specs")
        if not all(isinstance(pair_id, str) and pair_id for pair_id in pair_ids) or len(set(pair_ids)) != 12:
            raise RuntimeError(f"{judge_id} pair IDs must be unique and non-empty")
        expected_orientation = expected_orientations(expected_task_ids, judge_id)
        actual_orientation = tuple(row.get("left") == "candidate" for row in rows)
        if actual_orientation != tuple(expected_orientation):
            raise RuntimeError(f"{judge_id} arm orientation does not match the fixed seed")
        if actual_orientation in seen_orientations:
            raise RuntimeError(f"{judge_id} duplicates another judge's orientation")
        seen_orientations.add(actual_orientation)
        mapping_hash = sha256_file(map_path)
        packet_hashes: dict[str, str] = {}
        pairs: dict[str, str] = {}
        for row in rows:
            task_id = row["task_id"]
            pair_id = row["pair_id"]
            left_arm, right_arm = row.get("left"), row.get("right")
            if {left_arm, right_arm} != {"baseline", "candidate"}:
                raise RuntimeError(f"{judge_id}/{task_id} has invalid arms")
            packet_path = packet_dir / f"{task_id}.md"
            if not packet_path.is_file():
                raise RuntimeError(f"missing packet: {judge_id}/{task_id}")
            expected_packet = expected_packet_text(
                judge_id,
                task_id,
                pair_id,
                left_arm,
                right_arm,
                mapping_hash,
            )
            actual_packet = packet_path.read_text(encoding="utf-8")
            if actual_packet != expected_packet:
                raise RuntimeError(f"packet content mismatch: {judge_id}/{task_id}")
            packet_hashes[task_id] = sha256_bytes(actual_packet.encode("utf-8"))
            pairs[task_id] = pair_id
        destination = OUTPUT_ROOT / judge_id
        if destination.exists() or (MANIFEST_ROOT / f"{judge_id}.json").exists():
            raise RuntimeError(f"judgment output already exists: {destination}")
        payload["judges"][judge_id] = {
            "map_sha256": mapping_hash,
            "tasks": task_ids,
            "pairs": pairs,
            "packet_sha256": packet_hashes,
            "calls_planned": len(task_ids),
        }
    payload["calls_planned"] = sum(row["calls_planned"] for row in payload["judges"].values())
    return payload


def run_one(
    judge_id: str,
    task_id: str,
    pair_id: str,
    mapping_hash: str,
    expected_prompt_hash: str,
    staging_root: Path,
) -> dict[str, Any]:
    packet_path = PACKETS_ROOT / judge_id / f"{task_id}.md"
    prompt = packet_path.read_text(encoding="utf-8")
    result_path = staging_root / judge_id / "per-task" / f"{task_id}.json"
    trace_path = staging_root / judge_id / "per-task" / f"{task_id}.trace.jsonl"
    stderr_path = staging_root / judge_id / "per-task" / f"{task_id}.stderr.txt"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryDirectory(prefix=f"blind-{judge_id}-{task_id}-") as empty_root:
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
            str(SCHEMA_PATH),
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
    issues = trace_issues(trace_path, final)
    prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    if prompt_hash != expected_prompt_hash:
        issues.append("packet_changed_after_preflight")
    issues.extend(
        validate_final(final, judge_id, task_id, pair_id, mapping_hash)
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
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "trace_sha256": sha256_file(trace_path),
        "stderr_sha256": sha256_file(stderr_path),
        "issues": issues,
        "valid": return_code == 0 and not timed_out and not issues,
    }


def execute(judges: list[str]) -> int:
    before = preflight(judges)
    staging_root = Path(tempfile.mkdtemp(prefix="judges.incomplete-", dir=AB_ROOT))
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(
                run_one,
                judge_id,
                task_id,
                row["pairs"][task_id],
                row["map_sha256"],
                row["packet_sha256"][task_id],
                staging_root,
            ): (judge_id, task_id)
            for judge_id, row in before["judges"].items()
            for task_id in row["tasks"]
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
                    "return_code": None,
                    "timeout": False,
                    "duration_seconds": None,
                    "retry_count": 0,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "valid": False,
                }
            records.append(record)
            print(json.dumps({key: record.get(key) for key in ("judge_id", "task_id", "valid", "duration_seconds")}, ensure_ascii=False), flush=True)
    postflight_error: str | None = None
    try:
        after = preflight(judges)
    except Exception as exc:
        after = None
        postflight_error = f"{type(exc).__name__}: {exc}"
    inputs_stable = after == before
    for judge_id in judges:
        judge_records = sorted(
            (row for row in records if row["judge_id"] == judge_id),
            key=lambda row: row["task_id"],
        )
        manifest = {
            **before["judges"][judge_id],
            "judge_id": judge_id,
            "model": MODEL,
            "reasoning_effort": "max",
            "retry_count": 0,
            "inputs_stable": inputs_stable,
            "postflight_error": postflight_error,
            "records": judge_records,
            "valid_calls": sum(bool(row.get("valid")) for row in judge_records),
        }
        manifest_path = staging_root / "manifests" / f"{judge_id}.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    for judge_id in judges:
        (staging_root / judge_id).replace(OUTPUT_ROOT / judge_id)
        (staging_root / "manifests" / f"{judge_id}.json").replace(
            MANIFEST_ROOT / f"{judge_id}.json"
        )
    (staging_root / "manifests").rmdir()
    staging_root.rmdir()
    valid = sum(bool(row.get("valid")) for row in records)
    expected = int(before["calls_planned"])
    print(json.dumps({"valid_calls": valid, "expected_calls": expected, "retry_count": 0}))
    return 0 if valid == expected and inputs_stable else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judges", nargs="+", required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.judges), ensure_ascii=False, indent=2))
        return 0
    return execute(args.judges)


if __name__ == "__main__":
    raise SystemExit(main())
