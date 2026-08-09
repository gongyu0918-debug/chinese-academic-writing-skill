from __future__ import annotations

"""Create an independent, balanced left/right map for every judge and task."""

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path
from typing import Any


class MapError(ValueError):
    pass


def read_specs(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MapError(f"cannot read task specs: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise MapError("task specs must be an object with schema_version=1")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise MapError("task specs tasks must be a non-empty list")
    task_ids = [task.get("task_id") if isinstance(task, dict) else None for task in tasks]
    if not all(isinstance(task_id, str) and task_id for task_id in task_ids):
        raise MapError("every task must have a non-empty task_id")
    if len(set(task_ids)) != len(task_ids):
        raise MapError("task_id values must be unique")
    return payload


def stable_seed(master: str, judge_id: str) -> int:
    digest = hashlib.sha256(f"{master}\0{judge_id}".encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--judges", nargs="+")
    parser.add_argument("--baseline", default="baseline")
    parser.add_argument("--candidate", default="candidate")
    parser.add_argument("--seed", help="reproducible private seed; omit for a random seed")
    args = parser.parse_args()
    try:
        specs = read_specs(args.specs)
        judges = args.judges or specs.get("judges", ["judge-1", "judge-2"])
        if (
            not isinstance(judges, list)
            or not judges
            or len(set(judges)) != len(judges)
            or not all(isinstance(item, str) and item for item in judges)
        ):
            raise MapError("at least one unique non-empty judge ID is required")
        if args.baseline == args.candidate:
            raise MapError("baseline and candidate arm names must differ")
        task_ids = [task["task_id"] for task in specs["tasks"]]
        master = args.seed if args.seed is not None else secrets.token_hex(32)
        seed_hash = hashlib.sha256(master.encode("utf-8")).hexdigest()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for judge_index, judge_id in enumerate(judges, start=1):
            rng = random.Random(stable_seed(master, judge_id))
            orientations = [False, True] * ((len(task_ids) + 1) // 2)
            orientations = orientations[: len(task_ids)]
            rng.shuffle(orientations)
            rows = []
            for task_index, (task_id, candidate_left) in enumerate(
                zip(task_ids, orientations, strict=True),
                start=1,
            ):
                rows.append(
                    {
                        "task_id": task_id,
                        "pair_id": f"J{judge_index:02d}-P{task_index:03d}",
                        "left": args.candidate if candidate_left else args.baseline,
                        "right": args.baseline if candidate_left else args.candidate,
                    }
                )
            payload = {
                "schema_version": 1,
                "judge_id": judge_id,
                "task_specs_sha256": sha256_file(args.specs),
                "seed_sha256": seed_hash,
                "mappings": rows,
            }
            path = args.output_dir / f"{judge_id}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"MAP={path}")
        return 0
    except MapError as exc:
        print(f"MAPS=ERROR\nERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
