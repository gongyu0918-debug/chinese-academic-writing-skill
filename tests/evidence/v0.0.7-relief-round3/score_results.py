from __future__ import annotations

"""Aggregate mechanical gates and blinded judgments under a strict merge gate."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_VERDICTS = {"PASS", "WARN", "FAIL"}
ALLOWED_WINNERS = {"left", "right", "tie"}


class ScoreError(ValueError):
    pass


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScoreError(f"cannot read {label} {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_ids_from_specs(path: Path) -> list[str]:
    payload = read_json(path, "task specs")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ScoreError("task specs must have schema_version=1")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ScoreError("task specs tasks must be a non-empty list")
    ids = [task.get("task_id") if isinstance(task, dict) else None for task in tasks]
    if not all(isinstance(item, str) and item for item in ids):
        raise ScoreError("every task must have a non-empty task_id")
    if len(set(ids)) != len(ids):
        raise ScoreError("task_id values must be unique")
    return ids


def load_mechanical(path: Path, task_ids: set[str]) -> dict[tuple[str, str], list[str]]:
    payload = read_json(path, "mechanical results")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ScoreError("mechanical results must have schema_version=1")
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise ScoreError("mechanical results.results must be a list")
    output: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ScoreError("mechanical result rows must be objects")
        task_id, arm = row.get("task_id"), row.get("arm")
        failures = row.get("hard_failures")
        if task_id not in task_ids or not isinstance(arm, str) or not arm:
            raise ScoreError(f"invalid mechanical row identity: {row!r}")
        if not isinstance(failures, list) or not all(isinstance(item, str) for item in failures):
            raise ScoreError(f"invalid mechanical hard_failures for {task_id}/{arm}")
        key = (task_id, arm)
        if key in output:
            raise ScoreError(f"duplicate mechanical row: {task_id}/{arm}")
        output[key] = failures
    return output


def validate_side(side: Any, label: str) -> tuple[str, list[str]]:
    if not isinstance(side, dict):
        raise ScoreError(f"{label} must be an object")
    verdict, failures = side.get("verdict"), side.get("hard_failures")
    if verdict not in ALLOWED_VERDICTS:
        raise ScoreError(f"{label} has invalid verdict {verdict!r}")
    if not isinstance(failures, list) or not all(isinstance(item, str) and item for item in failures):
        raise ScoreError(f"{label}.hard_failures must be a list of non-empty strings")
    if (verdict == "FAIL") != bool(failures):
        raise ScoreError(f"{label} verdict and hard_failures disagree")
    return verdict, failures


def load_judge(
    map_path: Path,
    result_path: Path,
    task_ids: set[str],
    valid_arms: set[str],
) -> tuple[str, dict[str, dict[str, Any]]]:
    mapping = read_json(map_path, "judge map")
    result = read_json(result_path, "judge result")
    if not isinstance(mapping, dict) or mapping.get("schema_version") != 1:
        raise ScoreError(f"invalid map: {map_path}")
    if not isinstance(result, dict) or result.get("schema_version") != 1:
        raise ScoreError(f"invalid judge result: {result_path}")
    judge_id = mapping.get("judge_id")
    if result.get("judge_id") != judge_id or result.get("blind") is not True:
        raise ScoreError(f"judge identity or blind flag mismatch: {judge_id}")
    if result.get("mapping_sha256") != sha256_file(map_path):
        raise ScoreError(f"judge result is not bound to map: {judge_id}")

    map_rows = mapping.get("mappings")
    result_rows = result.get("results")
    if not isinstance(map_rows, list) or not isinstance(result_rows, list):
        raise ScoreError(f"map/results rows must be lists: {judge_id}")
    by_task: dict[str, dict[str, Any]] = {}
    for row in map_rows:
        if not isinstance(row, dict):
            raise ScoreError(f"map row must be an object: {judge_id}")
        task_id, pair_id = row.get("task_id"), row.get("pair_id")
        left, right = row.get("left"), row.get("right")
        if task_id not in task_ids or {left, right} != valid_arms or not isinstance(pair_id, str):
            raise ScoreError(f"invalid map row for {judge_id}: {row!r}")
        if task_id in by_task:
            raise ScoreError(f"duplicate task in map {judge_id}: {task_id}")
        by_task[task_id] = {"pair_id": pair_id, "left": left, "right": right}
    if set(by_task) != task_ids:
        raise ScoreError(f"map task set mismatch: {judge_id}")

    judged: dict[str, dict[str, Any]] = {}
    for row in result_rows:
        if not isinstance(row, dict):
            raise ScoreError(f"judge result row must be an object: {judge_id}")
        task_id, pair_id = row.get("task_id"), row.get("pair_id")
        if task_id not in by_task or pair_id != by_task[task_id]["pair_id"]:
            raise ScoreError(f"unknown task/pair in judge result {judge_id}: {task_id}/{pair_id}")
        if task_id in judged:
            raise ScoreError(f"duplicate judged task {judge_id}: {task_id}")
        left_verdict, left_failures = validate_side(row.get("left"), f"{judge_id}/{task_id}/left")
        right_verdict, right_failures = validate_side(row.get("right"), f"{judge_id}/{task_id}/right")
        winner = row.get("winner")
        if winner not in ALLOWED_WINNERS:
            raise ScoreError(f"{judge_id}/{task_id} has invalid winner {winner!r}")
        if winner == "left" and left_verdict == "FAIL":
            raise ScoreError(f"{judge_id}/{task_id} selects a FAIL left side")
        if winner == "right" and right_verdict == "FAIL":
            raise ScoreError(f"{judge_id}/{task_id} selects a FAIL right side")
        if left_verdict == "FAIL" and right_verdict != "FAIL" and winner != "right":
            raise ScoreError(f"{judge_id}/{task_id} fails to select the non-FAIL right side")
        if right_verdict == "FAIL" and left_verdict != "FAIL" and winner != "left":
            raise ScoreError(f"{judge_id}/{task_id} fails to select the non-FAIL left side")
        arm_for_side = {"left": by_task[task_id]["left"], "right": by_task[task_id]["right"]}
        vote = "tie" if winner == "tie" else arm_for_side[winner]
        verdicts = {
            arm_for_side["left"]: {"verdict": left_verdict, "hard_failures": left_failures},
            arm_for_side["right"]: {"verdict": right_verdict, "hard_failures": right_failures},
        }
        judged[task_id] = {"vote": vote, "verdicts": verdicts}
    if set(judged) != task_ids:
        raise ScoreError(f"judge result task set mismatch: {judge_id}")
    return judge_id, judged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--mechanical", required=True, type=Path)
    parser.add_argument("--maps-dir", required=True, type=Path)
    parser.add_argument("--judgments-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate", default="candidate")
    parser.add_argument("--baseline", default="baseline")
    parser.add_argument("--minimum-decided", type=int, default=3)
    parser.add_argument("--minimum-wins", type=int, default=2)
    args = parser.parse_args()
    try:
        if args.candidate == args.baseline:
            raise ScoreError("candidate and baseline arm names must differ")
        if args.minimum_decided < 3:
            raise ScoreError("minimum-decided cannot be lower than 3")
        if args.minimum_wins < 2:
            raise ScoreError("minimum-wins cannot be lower than 2")
        task_ids = task_ids_from_specs(args.specs)
        task_set = set(task_ids)
        arms = {args.candidate, args.baseline}
        mechanical = load_mechanical(args.mechanical, task_set)
        for task_id in task_ids:
            for arm in arms:
                if (task_id, arm) not in mechanical:
                    raise ScoreError(f"missing mechanical result: {task_id}/{arm}")

        map_paths = sorted(args.maps_dir.glob("*.json"))
        if len(map_paths) < 2:
            raise ScoreError("at least two judge maps are required")
        judges: dict[str, dict[str, dict[str, Any]]] = {}
        for map_path in map_paths:
            result_path = args.judgments_dir / map_path.name
            judge_id, rows = load_judge(map_path, result_path, task_set, arms)
            if judge_id in judges:
                raise ScoreError(f"duplicate judge_id: {judge_id}")
            judges[judge_id] = rows

        per_task: list[dict[str, Any]] = []
        candidate_only_hard_fail = False
        for task_id in task_ids:
            candidate_mechanical = mechanical[(task_id, args.candidate)]
            baseline_mechanical = mechanical[(task_id, args.baseline)]
            votes: list[str] = []
            candidate_fail_judges: list[str] = []
            baseline_fail_judges: list[str] = []
            for judge_id, rows in judges.items():
                row = rows[task_id]
                votes.append(row["vote"])
                if row["verdicts"][args.candidate]["verdict"] == "FAIL":
                    candidate_fail_judges.append(judge_id)
                if row["verdicts"][args.baseline]["verdict"] == "FAIL":
                    baseline_fail_judges.append(judge_id)

            candidate_only = (
                bool(candidate_mechanical) and not baseline_mechanical
            ) or any(
                judge_id not in baseline_fail_judges for judge_id in candidate_fail_judges
            )
            candidate_only_hard_fail = candidate_only_hard_fail or candidate_only

            if candidate_mechanical and not baseline_mechanical:
                status, winner = "DECIDED", args.baseline
            elif baseline_mechanical and not candidate_mechanical:
                status, winner = "DECIDED", args.candidate
            elif candidate_mechanical and baseline_mechanical:
                status, winner = "BOTH_HARD_FAIL", None
            else:
                counts = Counter(vote for vote in votes if vote in arms)
                if counts[args.candidate] >= 2:
                    status, winner = "DECIDED", args.candidate
                elif counts[args.baseline] >= 2:
                    status, winner = "DECIDED", args.baseline
                elif Counter(votes)["tie"] >= 2:
                    status, winner = "TIE", None
                else:
                    status, winner = "NEED_THIRD", None
            per_task.append(
                {
                    "task_id": task_id,
                    "status": status,
                    "winner": winner,
                    "votes": votes,
                    "mechanical_hard_failures": {
                        args.candidate: candidate_mechanical,
                        args.baseline: baseline_mechanical,
                    },
                    "judge_failures": {
                        args.candidate: candidate_fail_judges,
                        args.baseline: baseline_fail_judges,
                    },
                    "candidate_only_hard_fail": candidate_only,
                }
            )

        wins = sum(row["winner"] == args.candidate for row in per_task)
        losses = sum(row["winner"] == args.baseline for row in per_task)
        decided = wins + losses
        need_third = sum(row["status"] == "NEED_THIRD" for row in per_task)
        ties = sum(row["status"] == "TIE" for row in per_task)
        rate = wins / decided if decided else 0.0
        blockers = []
        if decided < args.minimum_decided:
            blockers.append(f"decided {decided} below minimum {args.minimum_decided}")
        if wins < args.minimum_wins:
            blockers.append(f"candidate wins {wins} below minimum {args.minimum_wins}")
        if wins <= losses:
            blockers.append(f"candidate wins {wins} are not strictly greater than baseline wins {losses}")
        if rate <= 0.5:
            blockers.append(f"decided win rate {rate:.1%} is not strictly above 50%")
        if candidate_only_hard_fail:
            blockers.append("candidate has at least one candidate-only hard FAIL")
        if need_third:
            blockers.append(f"{need_third} task(s) still require a third judge")

        payload = {
            "schema_version": 1,
            "candidate": args.candidate,
            "baseline": args.baseline,
            "judges": sorted(judges),
            "totals": {
                "tasks": len(task_ids),
                "decided": decided,
                "candidate_wins": wins,
                "baseline_wins": losses,
                "ties": ties,
                "need_third": need_third,
                "decided_win_rate": rate,
            },
            "candidate_only_hard_fail": candidate_only_hard_fail,
            "gate_pass": not blockers,
            "blockers": blockers,
            "tasks": per_task,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"MERGE_GATE={'PASS' if payload['gate_pass'] else 'FAIL'}")
        print(
            f"DECIDED={decided} CANDIDATE_WINS={wins} "
            f"BASELINE_WINS={losses} NEED_THIRD={need_third} RATE={rate:.1%}"
        )
        return 0 if payload["gate_pass"] else 1
    except ScoreError as exc:
        print(f"MERGE_GATE=ERROR\nERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
