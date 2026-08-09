from __future__ import annotations

"""Combine one-task blind judge JSON files into one complete file per judge."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class CombineError(ValueError):
    pass


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CombineError(f"cannot read {label} {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_map(path: Path) -> tuple[str, list[dict[str, Any]]]:
    payload = read_json(path, "judge map")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise CombineError(f"invalid judge map: {path}")
    judge_id = payload.get("judge_id")
    rows = payload.get("mappings")
    if not isinstance(judge_id, str) or not judge_id or not isinstance(rows, list):
        raise CombineError(f"judge map lacks judge_id or mappings: {path}")
    seen_tasks: set[str] = set()
    seen_pairs: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise CombineError(f"map rows must be objects: {path}")
        task_id, pair_id = row.get("task_id"), row.get("pair_id")
        if not isinstance(task_id, str) or not task_id or not isinstance(pair_id, str) or not pair_id:
            raise CombineError(f"invalid task/pair in map: {path}")
        if task_id in seen_tasks or pair_id in seen_pairs:
            raise CombineError(f"duplicate task or pair in map: {path}")
        seen_tasks.add(task_id)
        seen_pairs.add(pair_id)
    return judge_id, rows


def extract_single_result(payload: Any, path: Path) -> tuple[str, str, dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise CombineError(f"invalid per-task judgment: {path}")
    judge_id = payload.get("judge_id")
    mapping_sha256 = payload.get("mapping_sha256")
    if not isinstance(judge_id, str) or not judge_id:
        raise CombineError(f"missing judge_id: {path}")
    if not isinstance(mapping_sha256, str) or len(mapping_sha256) != 64:
        raise CombineError(f"invalid mapping_sha256: {path}")
    if payload.get("blind") is not True:
        raise CombineError(f"blind must be true: {path}")
    if "result" in payload:
        result = payload["result"]
    else:
        results = payload.get("results")
        if not isinstance(results, list) or len(results) != 1:
            raise CombineError(f"per-task judgment must contain one result: {path}")
        result = results[0]
    if not isinstance(result, dict):
        raise CombineError(f"result must be an object: {path}")
    validate_result(result, path)
    return judge_id, mapping_sha256, result


def validate_result(result: dict[str, Any], path: Path) -> None:
    for side_name in ("left", "right"):
        side = result.get(side_name)
        if not isinstance(side, dict):
            raise CombineError(f"{side_name} must be an object: {path}")
        verdict = side.get("verdict")
        hard_failures = side.get("hard_failures")
        if verdict not in {"PASS", "WARN", "FAIL"}:
            raise CombineError(f"invalid {side_name} verdict: {path}")
        if not isinstance(hard_failures, list) or any(
            not isinstance(item, str) or not item
            for item in hard_failures
        ):
            raise CombineError(f"invalid {side_name} hard_failures: {path}")
        if len(hard_failures) != len(set(hard_failures)):
            raise CombineError(f"duplicate {side_name} hard_failures: {path}")
        if verdict == "FAIL" and not hard_failures:
            raise CombineError(f"{side_name} FAIL requires a hard failure: {path}")
        if verdict != "FAIL" and hard_failures:
            raise CombineError(
                f"{side_name} {verdict} cannot contain hard failures: {path}"
            )
    anchors = result.get("anchors", [])
    if not isinstance(anchors, list) or any(
        not isinstance(item, str) or not item
        for item in anchors
    ):
        raise CombineError(f"invalid anchors: {path}")
    if len(anchors) != len(set(anchors)):
        raise CombineError(f"duplicate anchors: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps-dir", required=True, type=Path)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        maps: dict[str, tuple[Path, list[dict[str, Any]]]] = {}
        for map_path in sorted(args.maps_dir.glob("*.json")):
            judge_id, rows = load_map(map_path)
            if judge_id in maps:
                raise CombineError(f"duplicate judge map: {judge_id}")
            maps[judge_id] = (map_path, rows)
        if not maps:
            raise CombineError("at least one judge map is required")

        collected: dict[str, dict[str, dict[str, Any]]] = {judge_id: {} for judge_id in maps}
        seen_pairs: dict[str, set[str]] = {judge_id: set() for judge_id in maps}
        input_paths = sorted(args.input_dir.rglob("*.json"))
        if not input_paths:
            raise CombineError("no per-task judgment JSON files found")
        for path in input_paths:
            payload = read_json(path, "per-task judgment")
            judge_id, mapping_hash, result = extract_single_result(payload, path)
            if judge_id not in maps:
                raise CombineError(f"judgment has no matching map: {judge_id}")
            map_path, map_rows = maps[judge_id]
            if mapping_hash != sha256_file(map_path):
                raise CombineError(f"mapping_sha256 mismatch: {path}")
            task_id, pair_id = result.get("task_id"), result.get("pair_id")
            expected = {
                row["task_id"]: row["pair_id"]
                for row in map_rows
            }
            if task_id not in expected or pair_id != expected[task_id]:
                raise CombineError(f"task/pair does not match map: {path}")
            if task_id in collected[judge_id] or pair_id in seen_pairs[judge_id]:
                raise CombineError(f"duplicate task or pair judgment: {judge_id}/{task_id}/{pair_id}")
            collected[judge_id][task_id] = result
            seen_pairs[judge_id].add(pair_id)

        args.output_dir.mkdir(parents=True, exist_ok=True)
        for judge_id, (map_path, map_rows) in maps.items():
            expected_tasks = [row["task_id"] for row in map_rows]
            missing = [task_id for task_id in expected_tasks if task_id not in collected[judge_id]]
            if missing:
                raise CombineError(f"{judge_id} is missing tasks: {', '.join(missing)}")
            payload = {
                "schema_version": 1,
                "judge_id": judge_id,
                "blind": True,
                "mapping_sha256": sha256_file(map_path),
                "results": [collected[judge_id][task_id] for task_id in expected_tasks],
            }
            output_path = args.output_dir / f"{judge_id}.json"
            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"COMBINED={output_path}")
        return 0
    except CombineError as exc:
        print(f"COMBINE=ERROR\nERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
