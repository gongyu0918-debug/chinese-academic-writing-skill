from __future__ import annotations

"""Apply the frozen primary-judge validation correction without rerunning models."""

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import run_attribution_judges
import run_judges
from attribution_common import PRIMARY_JUDGES, load_valid_map, validate_final
from run_discovery import sha256_bytes


EVIDENCE_ROOT = Path(__file__).resolve().parent
RUN_ROOT = EVIDENCE_ROOT / "attribution"
MANIFEST_ROOT = RUN_ROOT / "judge-manifests"
OUTPUT_ROOT = RUN_ROOT / "judgments"
EXPECTED_ORIGINAL_MANIFEST_SHA256 = {
    "judge-1": "653b5e9607391d0c853aaba0650bd72e30d82c6d2b94f6b32684fabafc448954",
    "judge-2": "1d852ed521176d33313e0447c12c5b37cc4e6d9d8dab6e95cbe8d8034a2c901d",
}
EXPECTED_CHANGED_RECORD = {
    "judge_id": "judge-2",
    "task_id": "A1-R3",
    "before": {
        "issues": ["unrelated_errors:right:quote_not_verbatim"],
        "valid": False,
    },
    "after": {"issues": [], "valid": True},
}
DERIVED_FIELDS = {"issues", "valid"}


def normalized_text(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def backup_path(judge_id: str) -> Path:
    return MANIFEST_ROOT / f"{judge_id}.before-unrelated-quote-correction.json"


def assert_artifacts_unchanged(artifact_hashes: dict[Path, str]) -> None:
    changed = [
        str(path.relative_to(RUN_ROOT))
        for path, expected_hash in artifact_hashes.items()
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected_hash
    ]
    if changed:
        raise RuntimeError(f"judge artifacts changed during revalidation: {changed}")


def assert_original_manifests_unchanged(original_bytes_by_judge: dict[str, bytes]) -> None:
    changed = [
        judge_id
        for judge_id, expected_bytes in original_bytes_by_judge.items()
        if not (MANIFEST_ROOT / f"{judge_id}.json").is_file()
        or (MANIFEST_ROOT / f"{judge_id}.json").read_bytes() != expected_bytes
    ]
    if changed:
        raise RuntimeError(f"judge manifests changed during revalidation: {changed}")


def corrected_manifests() -> tuple[dict[str, dict[str, Any]], dict[str, bytes], dict[Path, str], dict[str, Any]]:
    expected = run_attribution_judges.preflight(
        list(PRIMARY_JUDGES),
        require_empty_outputs=False,
    )
    corrected_by_judge: dict[str, dict[str, Any]] = {}
    original_bytes_by_judge: dict[str, bytes] = {}
    artifact_hashes: dict[Path, str] = {}
    changed: list[dict[str, Any]] = []
    valid_before: dict[str, int] = {}
    valid_after: dict[str, int] = {}

    for judge_id in PRIMARY_JUDGES:
        manifest_path = MANIFEST_ROOT / f"{judge_id}.json"
        if not manifest_path.is_file():
            raise RuntimeError(f"judge manifest missing: {judge_id}")
        original_bytes = manifest_path.read_bytes()
        original_hash = sha256_bytes(original_bytes)
        if original_hash != EXPECTED_ORIGINAL_MANIFEST_SHA256[judge_id]:
            raise RuntimeError(f"unexpected original manifest SHA-256 for {judge_id}: {original_hash}")
        original_bytes_by_judge[judge_id] = original_bytes
        original = json.loads(original_bytes.decode("utf-8"))
        judge_expected = expected["judges"][judge_id]
        public_packets = run_attribution_judges.public_packet_bindings(judge_expected["packets"])
        records = original.get("records") if isinstance(original, dict) else None
        expected_top_level = {
            "schema_version": 1,
            "judge_id": judge_id,
            "model": run_attribution_judges.MODEL,
            "reasoning_effort": "max",
            "retry_count": 0,
            "run_inputs": expected["run_inputs"],
            "map_sha256": judge_expected["map_sha256"],
            "tasks": judge_expected["tasks"],
            "packets": public_packets,
            "calls_planned": judge_expected["calls_planned"],
            "inputs_stable": True,
            "postflight_error": None,
        }
        mismatches = [
            key for key, value in expected_top_level.items() if original.get(key) != value
        ]
        if mismatches or not isinstance(records, list) or len(records) != len(judge_expected["tasks"]):
            raise RuntimeError(f"original judge manifest binding invalid for {judge_id}: {mismatches}")
        if [record.get("task_id") for record in records] != judge_expected["tasks"]:
            raise RuntimeError(f"judge record order or coverage invalid: {judge_id}")
        if original.get("valid_calls") != sum(bool(record.get("valid")) for record in records):
            raise RuntimeError(f"original valid_calls mismatch: {judge_id}")

        _, mapping_hash = load_valid_map(judge_id)
        corrected_records: list[dict[str, Any]] = []
        for original_record in records:
            record = copy.deepcopy(original_record)
            task_id = record["task_id"]
            expected_execution = {
                "judge_id": judge_id,
                "task_id": task_id,
                "model": run_attribution_judges.MODEL,
                "reasoning_effort": "max",
                "return_code": 0,
                "timeout": False,
                "retry_count": 0,
            }
            execution_mismatches = [
                key for key, value in expected_execution.items() if record.get(key) != value
            ]
            duration = record.get("duration_seconds")
            if execution_mismatches or not isinstance(duration, (int, float)) or duration < 0:
                raise RuntimeError(
                    f"judge execution binding invalid for {judge_id}/{task_id}: {execution_mismatches}"
                )
            packet = judge_expected["packets"][task_id]
            if record.get("prompt_sha256") != packet["file_sha256"]:
                raise RuntimeError(f"judge prompt hash invalid: {judge_id}/{task_id}")

            frozen_text: dict[str, str] = {}
            expected_paths = {
                "final": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.json",
                "trace": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.trace.jsonl",
                "stderr": OUTPUT_ROOT / judge_id / "per-task" / f"{task_id}.stderr.txt",
            }
            for kind, path in expected_paths.items():
                expected_relative = f"judgments/{judge_id}/per-task/{path.name}"
                if record.get(f"{kind}_file") != expected_relative or not path.is_file():
                    raise RuntimeError(f"judge {kind} path invalid: {judge_id}/{task_id}")
                raw_bytes = path.read_bytes()
                raw_hash = sha256_bytes(raw_bytes)
                if path in artifact_hashes or (not raw_bytes and kind == "final"):
                    raise RuntimeError(f"judge {kind} artifact invalid or duplicate: {judge_id}/{task_id}")
                artifact_hashes[path] = raw_hash
                text = normalized_text(raw_bytes)
                frozen_text[kind] = text
                observed_record_hash = sha256_bytes(text.encode("utf-8")) if kind == "final" else raw_hash
                if record.get(f"{kind}_sha256") != observed_record_hash:
                    raise RuntimeError(f"judge {kind} hash invalid: {judge_id}/{task_id}")

            trace_issues = run_judges.trace_issues_text(frozen_text["trace"], frozen_text["final"])
            if trace_issues:
                raise RuntimeError(
                    f"judge trace recomputation failed: {judge_id}/{task_id}: {trace_issues}"
                )
            new_issues = validate_final(
                frozen_text["final"],
                judge_id,
                task_id,
                packet["pair_id"],
                mapping_hash,
                packet["content_sha256"],
                packet["_left"],
                packet["_right"],
            )
            new_valid = not new_issues
            before_derived = {key: record.get(key) for key in sorted(DERIVED_FIELDS)}
            record["issues"] = new_issues
            record["valid"] = new_valid
            after_derived = {key: record.get(key) for key in sorted(DERIVED_FIELDS)}
            if before_derived != after_derived:
                changed.append(
                    {
                        "judge_id": judge_id,
                        "task_id": task_id,
                        "before": before_derived,
                        "after": after_derived,
                    }
                )
            if any(
                record.get(key) != original_record.get(key)
                for key in set(record) | set(original_record)
                if key not in DERIVED_FIELDS
            ):
                raise RuntimeError(f"immutable record field changed: {judge_id}/{task_id}")
            corrected_records.append(record)

        corrected = copy.deepcopy(original)
        corrected["records"] = corrected_records
        corrected["valid_calls"] = sum(bool(record["valid"]) for record in corrected_records)
        if judge_id == EXPECTED_CHANGED_RECORD["judge_id"]:
            corrected["validation_correction"] = {
                "original_manifest_sha256": original_hash,
                "rule": "unrelated_error_quote_is_non_directional_log_not_target_vote_gate",
                "target": {
                    "judge_id": EXPECTED_CHANGED_RECORD["judge_id"],
                    "task_id": EXPECTED_CHANGED_RECORD["task_id"],
                },
                "before": EXPECTED_CHANGED_RECORD["before"],
                "after": EXPECTED_CHANGED_RECORD["after"],
                "immutable_artifact_count": 72,
            }
        valid_before[judge_id] = original["valid_calls"]
        valid_after[judge_id] = corrected["valid_calls"]
        corrected_by_judge[judge_id] = corrected

    if changed != [EXPECTED_CHANGED_RECORD]:
        raise RuntimeError(f"unexpected judge validation changes: {changed}")
    if len(artifact_hashes) != 72 or any(value != 12 for value in valid_after.values()):
        raise RuntimeError(
            f"corrected primary judgments are incomplete: artifacts={len(artifact_hashes)} valid={valid_after}"
        )
    assert_artifacts_unchanged(artifact_hashes)
    report = {
        "original_manifest_sha256": EXPECTED_ORIGINAL_MANIFEST_SHA256,
        "valid_calls_before": valid_before,
        "valid_calls_after": valid_after,
        "changed": changed,
        "immutable_artifact_count": len(artifact_hashes),
    }
    return corrected_by_judge, original_bytes_by_judge, artifact_hashes, report


def rollback_changed_manifest(original_bytes: bytes, corrected_bytes: bytes) -> None:
    judge_id = EXPECTED_CHANGED_RECORD["judge_id"]
    manifest_path = MANIFEST_ROOT / f"{judge_id}.json"
    if not manifest_path.is_file() or manifest_path.read_bytes() != corrected_bytes:
        raise RuntimeError("judge-2 changed after replacement; refusing to overwrite it during rollback")
    rollback_path = MANIFEST_ROOT / f".{judge_id}.rollback.tmp"
    with rollback_path.open("xb") as handle:
        handle.write(original_bytes)
    if manifest_path.read_bytes() != corrected_bytes:
        raise RuntimeError("judge-2 changed while preparing rollback; refusing to overwrite it")
    rollback_path.replace(manifest_path)


def apply_correction() -> dict[str, Any]:
    with run_attribution_judges.judge_manifest_write_lock():
        return apply_correction_locked()


def apply_correction_locked() -> dict[str, Any]:
    corrected, original_bytes, artifact_hashes, report = corrected_manifests()
    judge_id = EXPECTED_CHANGED_RECORD["judge_id"]
    destination = backup_path(judge_id)
    if destination.exists():
        raise RuntimeError(f"backup manifest already exists: {destination}")
    with destination.open("xb") as handle:
        handle.write(original_bytes[judge_id])
    if sha256_bytes(destination.read_bytes()) != EXPECTED_ORIGINAL_MANIFEST_SHA256[judge_id]:
        raise RuntimeError(f"backup manifest hash mismatch: {judge_id}")

    temporary = MANIFEST_ROOT / f".{judge_id}.corrected.tmp"
    if temporary.exists():
        raise RuntimeError(f"temporary corrected manifest already exists: {temporary}")
    corrected_bytes = (
        json.dumps(corrected[judge_id], ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    with temporary.open("xb") as handle:
        handle.write(corrected_bytes)

    replaced = False
    try:
        assert_original_manifests_unchanged(original_bytes)
        assert_artifacts_unchanged(artifact_hashes)
        if temporary.read_bytes() != corrected_bytes:
            raise RuntimeError("temporary corrected judge-2 manifest changed before replacement")
        temporary.replace(MANIFEST_ROOT / f"{judge_id}.json")
        replaced = True
        assert_artifacts_unchanged(artifact_hashes)
        if (MANIFEST_ROOT / "judge-1.json").read_bytes() != original_bytes["judge-1"]:
            raise RuntimeError("judge-1 manifest changed during judge-2 revalidation")
        if sha256_bytes(destination.read_bytes()) != EXPECTED_ORIGINAL_MANIFEST_SHA256[judge_id]:
            raise RuntimeError("judge-2 backup manifest changed during revalidation")
        for primary_judge in PRIMARY_JUDGES:
            results = run_attribution_judges.load_valid_judge_results(primary_judge)
            if len(results) != 12:
                raise RuntimeError(f"corrected judge loader coverage mismatch: {primary_judge}")
    except Exception as exc:
        if replaced:
            try:
                rollback_changed_manifest(original_bytes[judge_id], corrected_bytes)
            except Exception as rollback_exc:
                raise RuntimeError(
                    f"judge-2 correction failed and safe rollback was refused: {rollback_exc}"
                ) from exc
        raise
    report["corrected_manifest_sha256"] = {
        primary_judge: sha256_bytes((MANIFEST_ROOT / f"{primary_judge}.json").read_bytes())
        for primary_judge in PRIMARY_JUDGES
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check:
        _, _, _, report = corrected_manifests()
    else:
        report = apply_correction()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
