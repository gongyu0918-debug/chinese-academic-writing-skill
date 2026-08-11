from __future__ import annotations

"""Run the frozen three-group paired attribution replay without single-call retries."""

import argparse
import concurrent.futures
import json
import tempfile
from pathlib import Path
from typing import Any

import run_ab
from run_discovery import final_shape_valid, sha256_bytes, sha256_file, visible_char_count


EVIDENCE_ROOT = Path(__file__).resolve().parent
SPECS_PATH = EVIDENCE_ROOT / "attribution_specs.json"
OUTPUT_ROOT = EVIDENCE_ROOT / "attribution"
ARMS = ("baseline", "candidate")
JUDGES = ("judge-1", "judge-2", "judge-3")
EXPECTED_CANDIDATE_COMMIT = "66ea04b18d066ac3f2ed075cb91b5a1659c1a131"
EXPECTED_ATTRIBUTION_SPECS_SHA256 = "bc67d484c28e414b4b68951e993a5053e7e6217a5a54dbfcc47b958ec5e6ebdf"
EXPECTED_SOURCE_AB_SPECS_SHA256 = "aad99c0b051187337cc1a6cc6dab5e7733dfcb65d539beaba6610fa14f12453a"
EXPECTED_RUNTIME_FINGERPRINTS = {
    "baseline": "0b649ff5a1fb0e3cfca3c25f8a1ecd5c8fc652ab4489cb63fc5531a5dec8e3d3",
    "candidate": "18ea87efe5a7fcf79803e4d5c1b235ec54be37431b0b71704119dec2810b0cc3",
}
EXPECTED_TASK_SHA256 = {
    "H2": "713066a338a1064941b59214de13026c56d9b7712c9b6fdd2722f14d5e054236",
    "H4": "49885dcccdf47ad5a2a0f5be73c6fa575a0cf2f6c7314259fef1665daf7bc166",
}
EXPECTED_PROMPT_SHA256 = {
    "H2": "aeb244e10585e23665ac43ddc7faf6ec505fe624033d6acf9abf9b862e2f1c91",
    "H4": "589e36edd5acdd70e5badcab8319ce5e4df96ba02c7266029765e906c55d6c60",
}
EXPECTED_MODELS = {
    "alibaba": "alibaba-token-plan/deepseek-v4-flash-0731",
    "ollama": "ollama-cloud/deepseek-v4-flash:0731",
    "minimax": "minimax-cn/MiniMax-M3",
}
EXPECTED_GROUPS = {
    "A1": ("H4", "ollama"),
    "A2": ("H2", "alibaba"),
    "A3": ("H4", "minimax"),
}


def load_specs_snapshot() -> tuple[dict[str, Any], str]:
    raw = SPECS_PATH.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "arms", "judges", "tasks"}:
        raise RuntimeError("attribution specs top-level schema mismatch")
    rows = payload.get("tasks")
    if payload.get("schema_version") != 1 or not isinstance(rows, list) or len(rows) != 12:
        raise RuntimeError("attribution_specs.json must contain twelve tasks")
    if payload.get("arms") != list(ARMS) or payload.get("judges") != list(JUDGES):
        raise RuntimeError("attribution arms or judges do not match preregistration")
    required_row_keys = {
        "task_id",
        "group",
        "replicate",
        "source_task",
        "provider",
        "min_visible",
        "max_visible",
        "body_only",
        "forbid_lists",
        "forbid_process_leak",
        "required_literals",
    }
    if any(not isinstance(row, dict) or set(row) != required_row_keys for row in rows):
        raise RuntimeError("attribution task row schema mismatch")
    task_ids = [row.get("task_id") for row in rows]
    if len(set(task_ids)) != 12 or not all(isinstance(item, str) and item for item in task_ids):
        raise RuntimeError("attribution task IDs must be unique and non-empty")
    observed = {
        (row.get("group"), row.get("replicate"), row.get("source_task"), row.get("provider"))
        for row in rows
    }
    expected = {
        (group, replicate, source_task, provider)
        for group, (source_task, provider) in EXPECTED_GROUPS.items()
        for replicate in (1, 2, 3, 4)
    }
    if observed != expected:
        raise RuntimeError("attribution matrix does not match the frozen three-group design")
    if any(
        not isinstance(row["min_visible"], int)
        or not isinstance(row["max_visible"], int)
        or row["min_visible"] >= row["max_visible"]
        or row["body_only"] is not True
        or row["forbid_lists"] is not True
        or row["forbid_process_leak"] is not True
        or not isinstance(row["required_literals"], list)
        or not row["required_literals"]
        or any(not isinstance(item, str) or not item for item in row["required_literals"])
        for row in rows
    ):
        raise RuntimeError("attribution task constraints are invalid")
    return payload, sha256_bytes(raw)


def input_identity(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime": {
            # This identity is persisted in judge JSON manifests. Use lists so a
            # JSON round trip does not change equality semantics.
            arm: [payload[arm]["commit"], payload[arm]["runtime_fingerprint"]]
            for arm in ARMS
        },
        "source_ab_specs_sha256": payload["source_ab_specs_sha256"],
        "attribution_specs_sha256": payload["attribution_specs_sha256"],
        "attribution_tasks": payload["attribution_tasks"],
        "task_sha256": payload["task_sha256"],
        "prompt_sha256": payload["prompt_sha256"],
        "providers": payload["providers"],
    }


def preflight_payload(candidate_commit: str, expected_specs_hash: str | None = None) -> dict[str, Any]:
    if candidate_commit != EXPECTED_CANDIDATE_COMMIT:
        raise RuntimeError(f"candidate commit must be {EXPECTED_CANDIDATE_COMMIT}")
    specs, specs_hash = load_specs_snapshot()
    if specs_hash != EXPECTED_ATTRIBUTION_SPECS_SHA256:
        raise RuntimeError("attribution specs do not match the preregistered SHA-256")
    if expected_specs_hash is not None and specs_hash != expected_specs_hash:
        raise RuntimeError("attribution specs changed after freeze")
    writer_preflight = run_ab.preflight_payload(candidate_commit, EXPECTED_SOURCE_AB_SPECS_SHA256)
    for arm, expected_fingerprint in EXPECTED_RUNTIME_FINGERPRINTS.items():
        if writer_preflight[arm]["runtime_fingerprint"] != expected_fingerprint:
            raise RuntimeError(f"{arm} runtime fingerprint differs from preregistration")
    task_hashes = {key: writer_preflight["task_sha256"][key] for key in EXPECTED_TASK_SHA256}
    prompt_hashes = {key: writer_preflight["prompt_sha256"][key] for key in EXPECTED_PROMPT_SHA256}
    if task_hashes != EXPECTED_TASK_SHA256 or prompt_hashes != EXPECTED_PROMPT_SHA256:
        raise RuntimeError("H2/H4 task or prompt hash differs from preregistration")
    providers = {item["name"]: item["model"] for item in writer_preflight["providers"]}
    if providers != EXPECTED_MODELS:
        raise RuntimeError("provider/model mapping differs from preregistration")
    return {
        "schema_version": 1,
        "baseline": writer_preflight["baseline"],
        "candidate": writer_preflight["candidate"],
        "runtime_changed_files": writer_preflight["runtime_changed_files"],
        "reference_char_delta": writer_preflight["reference_char_delta"],
        "source_ab_specs_sha256": writer_preflight["specs_sha256"],
        "attribution_specs_sha256": specs_hash,
        "attribution_tasks": [row["task_id"] for row in specs["tasks"]],
        "task_sha256": task_hashes,
        "prompt_sha256": prompt_hashes,
        "providers": [
            {"name": name, "model": EXPECTED_MODELS[name]}
            for name in ("alibaba", "ollama", "minimax")
        ],
        "reasoning_effort": "max",
        "calls_planned": len(specs["tasks"]) * len(ARMS),
        "retry_count": 0,
    }


def record_closure_issues(
    records: list[dict[str, Any]],
    specs: dict[str, Any],
    preflight: dict[str, Any],
    staging: Path,
) -> list[str]:
    issues: list[str] = []
    rows = {row["task_id"]: row for row in specs["tasks"]}
    expected_keys = {(task_id, arm) for task_id in rows for arm in ARMS}
    observed_keys: list[tuple[Any, Any]] = [
        (record.get("pair_id"), record.get("arm")) for record in records
    ]
    if len(records) != len(expected_keys):
        issues.append(f"record_count:{len(records)}:{len(expected_keys)}")
    if len(set(observed_keys)) != len(observed_keys):
        issues.append("duplicate_record_key")
    if set(observed_keys) != expected_keys:
        issues.append("record_coverage_mismatch")
    provider_models = {item["name"]: item["model"] for item in preflight["providers"]}
    for record in records:
        task_id = record.get("pair_id")
        arm = record.get("arm")
        row = rows.get(task_id)
        if row is None or arm not in ARMS:
            continue
        binding = preflight[arm]
        expected_fields = {
            "source_task": row["source_task"],
            "group": row["group"],
            "replicate": row["replicate"],
            "provider": row["provider"],
            "model": provider_models[row["provider"]],
            "reasoning_effort": "max",
            "retry_count": 0,
            "commit": binding["commit"],
            "runtime_fingerprint": binding["runtime_fingerprint"],
            "prompt_sha256": preflight["prompt_sha256"][row["source_task"]],
            "prompt_bound": True,
            "return_code": 0,
            "timeout": False,
            "final_shape_valid": True,
            "valid": True,
        }
        if any(record.get(key) != value for key, value in expected_fields.items()):
            issues.append(f"record_binding_mismatch:{task_id}:{arm}")
        if record.get("trace_issues") != []:
            issues.append(f"record_trace_issues:{task_id}:{arm}")
        expected_paths = {
            "final": f"raw/{arm}/{task_id}.md",
            "trace": f"traces/{arm}/{task_id}.jsonl",
            "stderr": f"stderr/{arm}/{task_id}.txt",
        }
        for kind, relative in expected_paths.items():
            if record.get(f"{kind}_file") != relative:
                issues.append(f"record_{kind}_path_mismatch:{task_id}:{arm}")
                continue
            path = staging / relative
            if not path.is_file():
                issues.append(f"record_{kind}_missing:{task_id}:{arm}")
                continue
            observed_hash = (
                sha256_bytes(path.read_text(encoding="utf-8").encode("utf-8"))
                if kind == "final"
                else sha256_file(path)
            )
            if record.get(f"{kind}_sha256") != observed_hash:
                issues.append(f"record_{kind}_hash_mismatch:{task_id}:{arm}")
        final_path = staging / expected_paths["final"]
        trace_path = staging / expected_paths["trace"]
        if final_path.is_file():
            final_text = final_path.read_text(encoding="utf-8")
            if not final_shape_valid(final_text):
                issues.append(f"record_final_shape_recomputed_invalid:{task_id}:{arm}")
            if record.get("final_chars_no_whitespace") != visible_char_count(final_text):
                issues.append(f"record_final_char_count_mismatch:{task_id}:{arm}")
        else:
            final_text = ""
        if trace_path.is_file():
            recomputed_trace_issues = run_ab.trace_issues(
                trace_path,
                run_ab.BASELINE_ROOT if arm == "baseline" else run_ab.CANDIDATE_ROOT,
                final_text,
            )
            if recomputed_trace_issues:
                issues.append(f"record_trace_recomputed_invalid:{task_id}:{arm}")
            if record.get("trace_issues") != recomputed_trace_issues:
                issues.append(f"record_trace_recomputed_mismatch:{task_id}:{arm}")
            if record.get("pre_read_preamble_count") != run_ab.pre_read_preamble_count(trace_path):
                issues.append(f"record_preamble_count_mismatch:{task_id}:{arm}")
    return sorted(set(issues))


def execute(candidate_commit: str) -> int:
    specs, specs_hash = load_specs_snapshot()
    preflight = preflight_payload(candidate_commit, specs_hash)
    if OUTPUT_ROOT.exists():
        raise RuntimeError(f"attribution output already exists: {OUTPUT_ROOT}")
    staging = Path(tempfile.mkdtemp(prefix="attribution.incomplete-", dir=EVIDENCE_ROOT))
    records: list[dict[str, Any]] = []
    for row in specs["tasks"]:
        source_text = (EVIDENCE_ROOT / "tasks" / f"{row['source_task']}.md").read_text(encoding="utf-8")
        snapshot = staging / "tasks" / f"{row['task_id']}.md"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(source_text, encoding="utf-8", newline="\n")
        if sha256_bytes(snapshot.read_text(encoding="utf-8").encode("utf-8")) != preflight["task_sha256"][row["source_task"]]:
            raise RuntimeError(f"task changed while freezing snapshot: {row['task_id']}")
    for row in specs["tasks"]:
        current = preflight_payload(candidate_commit, specs_hash)
        if input_identity(current) != input_identity(preflight):
            raise RuntimeError(f"runtime inputs changed before pair {row['task_id']}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = {}
            for arm, root in (("baseline", run_ab.BASELINE_ROOT), ("candidate", run_ab.CANDIDATE_ROOT)):
                future = pool.submit(
                    run_ab.run_one,
                    row,
                    arm,
                    root,
                    preflight[arm],
                    preflight["prompt_sha256"][row["source_task"]],
                    staging,
                )
                futures[future] = arm
            for future in concurrent.futures.as_completed(futures):
                arm = futures[future]
                try:
                    record = future.result()
                except Exception as exc:
                    record = {
                        "pair_id": row["task_id"],
                        "source_task": row["source_task"],
                        "group": row["group"],
                        "replicate": row["replicate"],
                        "arm": arm,
                        "provider": row["provider"],
                        "reasoning_effort": "max",
                        "retry_count": 0,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "valid": False,
                    }
                record["group"] = row["group"]
                record["replicate"] = row["replicate"]
                records.append(record)
                print(
                    json.dumps(
                        {key: record.get(key) for key in ("pair_id", "arm", "provider", "valid", "duration_seconds")},
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
    order = {row["task_id"]: index for index, row in enumerate(specs["tasks"])}
    records.sort(key=lambda row: (order[row["pair_id"]], ARMS.index(row["arm"])))
    closure_issues = record_closure_issues(records, specs, preflight, staging)
    postflight_error: str | None = None
    try:
        postflight = preflight_payload(candidate_commit, specs_hash)
    except Exception as exc:
        postflight = None
        postflight_error = f"{type(exc).__name__}: {exc}"
    inputs_stable = bool(postflight and input_identity(postflight) == input_identity(preflight))
    manifest = {
        **preflight,
        "postflight": postflight,
        "postflight_error": postflight_error,
        "binding_stable": inputs_stable,
        "pair_launch": "concurrent_arms_sequential_pairs",
        "record_closure_issues": closure_issues,
        "records": records,
        "valid_calls": sum(bool(row.get("valid")) for row in records),
    }
    (staging / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    staging.replace(OUTPUT_ROOT)
    expected = int(preflight["calls_planned"])
    print(
        json.dumps(
            {
                "manifest": str(OUTPUT_ROOT / "manifest.json"),
                "valid_calls": manifest["valid_calls"],
                "expected_calls": expected,
                "binding_stable": inputs_stable,
                "retry_count": 0,
                "record_closure_issues": closure_issues,
            },
            ensure_ascii=False,
        )
    )
    return 0 if manifest["valid_calls"] == expected and inputs_stable and not closure_issues else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--candidate-commit", required=True)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight_payload(args.candidate_commit), ensure_ascii=False, indent=2))
        return 0
    return execute(args.candidate_commit)


if __name__ == "__main__":
    raise SystemExit(main())
