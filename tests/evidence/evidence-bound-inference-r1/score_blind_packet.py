from __future__ import annotations

"""Unblind a fixed verdict file and verify an optional expected score."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_MAPPING = REPO / ".release/evidence-bound-inference-r1/blind-final-r1-audited/mapping.json"
DEFAULT_VERDICTS = HERE / "blind-verdicts.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--verdicts", type=Path, default=DEFAULT_VERDICTS)
    parser.add_argument("--expected", type=Path, help="compare the computed JSON object with this file")
    return parser.parse_args()


def score(mapping_path: Path, verdicts_path: Path) -> dict[str, Any]:
    mapping = load_json(mapping_path)
    verdict_payload = load_json(verdicts_path)
    decisions = verdict_payload.get("decisions")
    if not isinstance(mapping, list) or not isinstance(decisions, list):
        raise RuntimeError("mapping and decisions must be lists")
    mapping_by_id = {str(item.get("pair_id")): item for item in mapping}
    decisions_by_id = {str(item.get("pair_id")): item for item in decisions}
    if len(mapping_by_id) != len(mapping) or len(decisions_by_id) != len(decisions):
        raise RuntimeError("pair IDs must be unique")
    if set(mapping_by_id) != set(decisions_by_id):
        raise RuntimeError("mapping and verdict pair IDs differ")
    manifest_path = mapping_path.with_name("manifest.json")
    manifest = load_json(manifest_path)
    if verdict_payload.get("packet_sha256") != manifest.get("packet_sha256"):
        raise RuntimeError("verdict packet hash does not match the blind manifest")

    anonymous = {"A": 0, "B": 0, "TIE": 0, "INVALID": 0}
    candidate_wins = 0
    baseline_wins = 0
    for pair_id in sorted(mapping_by_id):
        decision = str(decisions_by_id[pair_id].get("decision"))
        if decision not in anonymous:
            raise RuntimeError(f"invalid decision for {pair_id}: {decision}")
        anonymous[decision] += 1
        if decision in {"TIE", "INVALID"}:
            continue
        if decision == mapping_by_id[pair_id].get("candidate_label"):
            candidate_wins += 1
        else:
            baseline_wins += 1
    decided = candidate_wins + baseline_wins
    return {
        "schema_version": 1,
        "packet_sha256": manifest["packet_sha256"],
        "mapping_sha256": sha256_file(mapping_path),
        "verdicts_sha256": sha256_file(verdicts_path),
        "pair_count": len(mapping),
        "anonymous_counts": anonymous,
        "candidate_wins": candidate_wins,
        "baseline_wins": baseline_wins,
        "ties": anonymous["TIE"],
        "invalid": anonymous["INVALID"],
        "decided_pairs": decided,
        "candidate_decided_win_rate_percent": round(100 * candidate_wins / decided, 1) if decided else None,
    }


def main() -> int:
    args = parse_args()
    result = score(args.mapping.resolve(), args.verdicts.resolve())
    if args.expected:
        expected = load_json(args.expected.resolve())
        if result != expected:
            raise SystemExit("computed blind score differs from expected result")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
