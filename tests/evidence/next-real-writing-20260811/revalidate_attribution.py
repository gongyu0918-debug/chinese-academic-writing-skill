from __future__ import annotations

"""Apply the frozen run-2 trace-classifier correction without changing artifacts."""

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import run_ab
import run_attribution
from run_discovery import final_shape_valid, sha256_bytes, sha256_file, visible_char_count


EVIDENCE_ROOT = Path(__file__).resolve().parent
RUN_ROOT = EVIDENCE_ROOT / "attribution"
MANIFEST_PATH = RUN_ROOT / "manifest.json"
BACKUP_PATH = RUN_ROOT / "manifest.before-validation-correction.json"
EXPECTED_ORIGINAL_MANIFEST_SHA256 = "23d62b2fb7a5563d2d9a69d255af13a8008a25029c27aa4cc4c4c66472ce72cf"
EXPECTED_CHANGED_RECORD = ("A1-R4", "candidate")
DERIVED_FIELDS = {
    "trace_issues",
    "pre_read_preamble_count",
    "final_shape_valid",
    "final_chars_no_whitespace",
    "valid",
}


def artifact_hash(path: Path, kind: str) -> str:
    if kind == "final":
        return sha256_bytes(path.read_text(encoding="utf-8").encode("utf-8"))
    return sha256_file(path)


def corrected_manifest() -> tuple[dict[str, Any], dict[str, Any]]:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(f"attribution manifest missing: {MANIFEST_PATH}")
    original_bytes = MANIFEST_PATH.read_bytes()
    original_hash = sha256_bytes(original_bytes)
    if original_hash != EXPECTED_ORIGINAL_MANIFEST_SHA256:
        raise RuntimeError(f"unexpected original manifest SHA-256: {original_hash}")
    original = json.loads(original_bytes.decode("utf-8"))
    specs, _ = run_attribution.load_specs_snapshot()
    current = run_attribution.preflight_payload(run_attribution.EXPECTED_CANDIDATE_COMMIT)
    if (
        original.get("binding_stable") is not True
        or original.get("calls_planned") != 24
        or len(original.get("records") or []) != 24
        or run_attribution.input_identity(original) != run_attribution.input_identity(current)
        or not isinstance(original.get("postflight"), dict)
        or run_attribution.input_identity(original["postflight"])
        != run_attribution.input_identity(current)
    ):
        raise RuntimeError("original attribution manifest binding is invalid")
    rows = {row["task_id"]: row for row in specs["tasks"]}
    corrected_records: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    artifact_hashes_before: dict[str, str] = {}
    for original_record in original["records"]:
        record = copy.deepcopy(original_record)
        task_id = record.get("pair_id")
        arm = record.get("arm")
        if task_id not in rows or arm not in run_attribution.ARMS:
            raise RuntimeError(f"invalid record key: {(task_id, arm)}")
        expected_paths = {
            "final": f"raw/{arm}/{task_id}.md",
            "trace": f"traces/{arm}/{task_id}.jsonl",
            "stderr": f"stderr/{arm}/{task_id}.txt",
        }
        paths: dict[str, Path] = {}
        for kind, relative in expected_paths.items():
            if record.get(f"{kind}_file") != relative:
                raise RuntimeError(f"record {kind} path mismatch: {(task_id, arm)}")
            path = RUN_ROOT / relative
            if not path.is_file() or record.get(f"{kind}_sha256") != artifact_hash(path, kind):
                raise RuntimeError(f"record {kind} hash mismatch: {(task_id, arm)}")
            paths[kind] = path
            artifact_hashes_before[relative] = sha256_file(path)
        final = paths["final"].read_text(encoding="utf-8")
        trace_issues = run_ab.trace_issues(
            paths["trace"],
            run_ab.BASELINE_ROOT if arm == "baseline" else run_ab.CANDIDATE_ROOT,
            final,
        )
        updates = {
            "trace_issues": trace_issues,
            "pre_read_preamble_count": run_ab.pre_read_preamble_count(paths["trace"]),
            "final_shape_valid": final_shape_valid(final),
            "final_chars_no_whitespace": visible_char_count(final),
        }
        updates["valid"] = (
            record.get("return_code") == 0
            and record.get("timeout") is False
            and not trace_issues
            and updates["final_shape_valid"]
            and record.get("prompt_bound") is True
        )
        before_derived = {key: record.get(key) for key in DERIVED_FIELDS}
        record.update(updates)
        after_derived = {key: record.get(key) for key in DERIVED_FIELDS}
        if before_derived != after_derived:
            changed.append(
                {
                    "pair_id": task_id,
                    "arm": arm,
                    "before": before_derived,
                    "after": after_derived,
                }
            )
        if any(
            record.get(key) != original_record.get(key)
            for key in set(record) | set(original_record)
            if key not in DERIVED_FIELDS
        ):
            raise RuntimeError(f"immutable record field changed: {(task_id, arm)}")
        corrected_records.append(record)
    changed_keys = [(item["pair_id"], item["arm"]) for item in changed]
    if changed_keys != [EXPECTED_CHANGED_RECORD]:
        raise RuntimeError(f"unexpected validation changes: {changed_keys}")
    corrected = copy.deepcopy(original)
    corrected["records"] = corrected_records
    corrected["valid_calls"] = sum(bool(record.get("valid")) for record in corrected_records)
    closure = run_attribution.record_closure_issues(corrected_records, specs, current, RUN_ROOT)
    corrected["record_closure_issues"] = closure
    corrected["validation_correction"] = {
        "original_manifest_sha256": original_hash,
        "rule": "allow_at_most_one_nonfinal_progress_message_before_last_required_read_completion",
        "changed_records": changed_keys,
        "immutable_artifact_count": len(artifact_hashes_before),
    }
    if corrected["valid_calls"] != 24 or closure:
        raise RuntimeError(
            f"corrected attribution run is not 24/24: valid={corrected['valid_calls']} closure={closure}"
        )
    artifact_hashes_after = {
        relative: sha256_file(RUN_ROOT / relative) for relative in artifact_hashes_before
    }
    if artifact_hashes_after != artifact_hashes_before:
        raise RuntimeError("an immutable final/trace/stderr artifact changed during revalidation")
    report = {
        "original_manifest_sha256": original_hash,
        "valid_calls_before": original.get("valid_calls"),
        "valid_calls_after": corrected["valid_calls"],
        "changed": changed,
        "record_closure_issues": closure,
        "immutable_artifact_count": len(artifact_hashes_before),
    }
    return corrected, report


def apply_correction() -> dict[str, Any]:
    corrected, report = corrected_manifest()
    if BACKUP_PATH.exists():
        raise RuntimeError(f"backup manifest already exists: {BACKUP_PATH}")
    original_bytes = MANIFEST_PATH.read_bytes()
    BACKUP_PATH.write_bytes(original_bytes)
    if sha256_file(BACKUP_PATH) != EXPECTED_ORIGINAL_MANIFEST_SHA256:
        raise RuntimeError("backup manifest hash mismatch")
    temporary = MANIFEST_PATH.with_suffix(".json.corrected.tmp")
    if temporary.exists():
        raise RuntimeError(f"temporary corrected manifest already exists: {temporary}")
    temporary.write_text(
        json.dumps(corrected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(MANIFEST_PATH)
    report["corrected_manifest_sha256"] = sha256_file(MANIFEST_PATH)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    _, report = corrected_manifest() if args.check else (None, apply_correction())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
