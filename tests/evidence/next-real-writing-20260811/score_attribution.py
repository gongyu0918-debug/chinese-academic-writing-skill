from __future__ import annotations

"""Aggregate blinded target labels into symmetric preregistered causal decisions."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from attribution_common import (
    DEFINITE_LABELS,
    PRIMARY_JUDGES,
    TARGETS_BY_GROUP,
    load_valid_map,
)
from run_attribution_judges import (
    MANIFEST_ROOT,
    labels_by_arm,
    load_valid_judge_results,
    primary_unresolved_tasks,
    task_ids,
)
from run_discovery import sha256_file


GROUP_NAMES = {"A1": "ollama-h4", "A2": "alibaba-h2", "A3": "minimax-h4"}


def causal_decision(scorable: int, candidate_only: int, baseline_only: int) -> str:
    if scorable < 4:
        return "INSUFFICIENT"
    if candidate_only >= 3 and baseline_only == 0:
        return "CAUSAL_HARM"
    if baseline_only >= 3 and candidate_only == 0:
        return "CAUSAL_BENEFIT"
    if candidate_only <= 1 and baseline_only <= 1:
        return "NO_DIRECTIONAL_SIGNAL"
    return "AMBIGUOUS"


def majority_label(votes: list[str]) -> str | None:
    counts = Counter(label for label in votes if label in DEFINITE_LABELS)
    for label in ("PRESENT", "ABSENT"):
        if counts[label] >= 2:
            return label
    return None


def build_score() -> dict[str, Any]:
    primary = {judge: load_valid_judge_results(judge) for judge in PRIMARY_JUDGES}
    unresolved = primary_unresolved_tasks()
    third: dict[str, dict[str, Any]] = {}
    if unresolved:
        third = load_valid_judge_results("judge-3")
        if list(third) != sorted(unresolved):
            raise RuntimeError("judge-3 results do not exactly cover primary unresolved tasks")
    outputs = {**primary, **({"judge-3": third} if third else {})}
    pairs: list[dict[str, Any]] = []
    unrelated: list[dict[str, Any]] = []
    for task_id in task_ids():
        group = task_id.split("-", 1)[0]
        judges = list(PRIMARY_JUDGES) + (["judge-3"] if task_id in unresolved else [])
        labels = {
            judge: labels_by_arm(judge, task_id, outputs[judge][task_id])
            for judge in judges
        }
        target_rows: list[dict[str, Any]] = []
        for target_id in TARGETS_BY_GROUP[group]:
            votes = {
                arm: [labels[judge][target_id][arm] for judge in judges]
                for arm in ("baseline", "candidate")
            }
            final_labels = {arm: majority_label(arm_votes) for arm, arm_votes in votes.items()}
            target_rows.append(
                {
                    "target_id": target_id,
                    "votes": votes,
                    "baseline": final_labels["baseline"],
                    "candidate": final_labels["candidate"],
                    "scorable": all(label in DEFINITE_LABELS for label in final_labels.values()),
                }
            )
        for judge in judges:
            mapping, _ = load_valid_map(judge)
            map_row = next(row for row in mapping["mappings"] if row["task_id"] == task_id)
            payload = outputs[judge][task_id]
            for side in ("left", "right"):
                arm = map_row[side]
                for error in payload["unrelated_errors"][side]:
                    unrelated.append(
                        {
                            "judge_id": judge,
                            "task_id": task_id,
                            "arm": arm,
                            "code": error["code"],
                            "quote": error["quote"],
                        }
                    )
        pairs.append(
            {
                "task_id": task_id,
                "group": group,
                "replicate": int(task_id.rsplit("R", 1)[1]),
                "judges_used": judges,
                "targets": target_rows,
            }
        )
    aggregates: list[dict[str, Any]] = []
    for group, targets in TARGETS_BY_GROUP.items():
        group_pairs = [pair for pair in pairs if pair["group"] == group]
        for target_id in targets:
            counts = Counter()
            for pair in group_pairs:
                target = next(item for item in pair["targets"] if item["target_id"] == target_id)
                baseline = target["baseline"]
                candidate = target["candidate"]
                if not target["scorable"]:
                    counts["unscorable"] += 1
                elif baseline == "ABSENT" and candidate == "PRESENT":
                    counts["candidate_only"] += 1
                elif baseline == "PRESENT" and candidate == "ABSENT":
                    counts["baseline_only"] += 1
                elif baseline == "PRESENT" and candidate == "PRESENT":
                    counts["both_present"] += 1
                else:
                    counts["neither_present"] += 1
            scorable = 4 - counts["unscorable"]
            row = {
                "schema_version": 1,
                "group_id": GROUP_NAMES[group],
                "target_id": target_id,
                "replicates_total": 4,
                "scorable": scorable,
                "candidate_only": counts["candidate_only"],
                "baseline_only": counts["baseline_only"],
                "both_present": counts["both_present"],
                "neither_present": counts["neither_present"],
                "unscorable": counts["unscorable"],
                "candidate_present": counts["candidate_only"] + counts["both_present"],
                "baseline_present": counts["baseline_only"] + counts["both_present"],
                "decision": causal_decision(
                    scorable,
                    counts["candidate_only"],
                    counts["baseline_only"],
                ),
            }
            if sum(row[key] for key in ("candidate_only", "baseline_only", "both_present", "neither_present")) != scorable:
                raise RuntimeError(f"aggregate count invariant failed: {group}/{target_id}")
            aggregates.append(row)
    decisions = [row["decision"] for row in aggregates]
    regression_gate = "FAIL" if "CAUSAL_HARM" in decisions else "PASS"
    benefit_gate = "PASS" if "CAUSAL_BENEFIT" in decisions else "FAIL"
    return {
        "schema_version": 1,
        "primary_judges": list(PRIMARY_JUDGES),
        "primary_unresolved_tasks": unresolved,
        "third_judge_used": bool(unresolved),
        "judge_manifest_sha256": {
            judge: sha256_file(MANIFEST_ROOT / f"{judge}.json")
            for judge in outputs
        },
        "pairs": pairs,
        "aggregates": aggregates,
        "unrelated_errors": unrelated,
        "regression_gate": regression_gate,
        "benefit_gate": benefit_gate,
        "attribution_gate": "PASS" if regression_gate == "PASS" and benefit_gate == "PASS" else "FAIL",
        "remaining_uncertainty": [
            {"group_id": row["group_id"], "target_id": row["target_id"], "decision": row["decision"]}
            for row in aggregates
            if row["decision"] in {"AMBIGUOUS", "INSUFFICIENT"}
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"attribution score already exists: {args.output}")
    payload = build_score()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "regression_gate": payload["regression_gate"],
                "benefit_gate": payload["benefit_gate"],
                "attribution_gate": payload["attribution_gate"],
                "third_judge_used": payload["third_judge_used"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["attribution_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
