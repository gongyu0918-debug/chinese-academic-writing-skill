from __future__ import annotations

import json
import shutil

import run_discovery as discovery


BACKUP_PATH = discovery.OUTPUT_ROOT / "manifest.before-validation-correction.json"
MANIFEST_PATH = discovery.OUTPUT_ROOT / "manifest.json"


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(f"manifest missing: {MANIFEST_PATH}")
    if BACKUP_PATH.exists():
        raise RuntimeError(f"validation backup already exists: {BACKUP_PATH}")
    original_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(original_bytes)
    preflight = discovery.preflight_payload()
    if manifest["baseline_commit"] != preflight["baseline_commit"]:
        raise RuntimeError("baseline commit differs from the frozen discovery manifest")
    if manifest["runtime_fingerprint"] != preflight["runtime_fingerprint"]:
        raise RuntimeError("runtime fingerprint differs from the frozen discovery manifest")

    specs = discovery.load_specs()
    for record in manifest["records"]:
        spec = specs[record["task"]]
        final_name = record.get("final_file")
        trace_name = record.get("trace_file")
        before = {
            "trace_load_valid": record.get("trace_load_valid"),
            "trace_issues": record.get("trace_issues"),
            "valid": record.get("valid"),
        }
        if not final_name or not trace_name:
            record["validation_before_correction"] = before
            continue
        final_path = discovery.OUTPUT_ROOT / str(final_name)
        trace_path = discovery.OUTPUT_ROOT / str(trace_name)
        final = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
        load_ok, load_issues = discovery.trace_valid(
            trace_path,
            list(spec["required_reads"]),
        )
        shape_ok = discovery.final_shape_valid(final)
        record.update(
            {
                "validation_before_correction": before,
                "trace_load_valid": load_ok,
                "trace_issues": load_issues,
                "final_shape_valid": shape_ok,
                "mechanical_issues": discovery.mechanical_issues(final, spec)
                if final
                else ["missing_final"],
                "valid": record.get("return_code") == 0
                and not record.get("timeout")
                and load_ok
                and shape_ok,
            }
        )

    previous_valid_calls = int(manifest.get("valid_calls", 0))
    valid_calls = sum(bool(record.get("valid")) for record in manifest["records"])
    manifest.update(
        {
            "valid_calls": valid_calls,
            "mechanical_issue_calls": sum(
                bool(record.get("mechanical_issues")) for record in manifest["records"]
            ),
            "validation_correction": {
                "scope": "trace classification only; no model call or artifact replaced",
                "reason": (
                    "The original validator treated the current frozen baseline path under "
                    ".release/worktrees as another worktree. Exact allowed-root handling keeps "
                    "the current root valid and still rejects sibling worktrees."
                ),
                "previous_valid_calls": previous_valid_calls,
                "corrected_valid_calls": valid_calls,
                "original_manifest_file": BACKUP_PATH.name,
            },
        }
    )
    shutil.copyfile(MANIFEST_PATH, BACKUP_PATH)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "valid_calls": valid_calls,
                "expected_calls": manifest["calls_planned"],
                "backup": str(BACKUP_PATH),
            },
            ensure_ascii=False,
        )
    )
    return 0 if valid_calls == int(manifest["calls_planned"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
