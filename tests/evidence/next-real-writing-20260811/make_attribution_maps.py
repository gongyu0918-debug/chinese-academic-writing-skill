from __future__ import annotations

"""Create the three preregistered fixed-seed attribution judge maps."""

import argparse
import json
import tempfile
from pathlib import Path

from attribution_common import (
    JUDGES,
    MAPS_ROOT,
    MAP_SEED,
    SPECS_PATH,
    expected_orientations,
    load_specs,
)
from run_discovery import sha256_bytes, sha256_file


def build(output_dir: Path = MAPS_ROOT) -> int:
    if output_dir.exists():
        raise RuntimeError(f"attribution maps already exist: {output_dir}")
    task_ids = [row["task_id"] for row in load_specs()["tasks"]]
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="attribution-maps.incomplete-", dir=output_dir.parent))
    staged_maps = staging / "maps"
    staged_maps.mkdir()
    for judge_index, judge_id in enumerate(JUDGES, start=1):
        rows = []
        for task_index, (task_id, candidate_left) in enumerate(
            zip(task_ids, expected_orientations(task_ids, judge_id), strict=True),
            start=1,
        ):
            rows.append(
                {
                    "task_id": task_id,
                    "pair_id": f"J{judge_index:02d}-P{task_index:03d}",
                    "left": "candidate" if candidate_left else "baseline",
                    "right": "baseline" if candidate_left else "candidate",
                }
            )
        payload = {
            "schema_version": 1,
            "judge_id": judge_id,
            "task_specs_sha256": sha256_file(SPECS_PATH),
            "seed_sha256": sha256_bytes(MAP_SEED.encode("utf-8")),
            "mappings": rows,
        }
        path = staged_maps / f"{judge_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    expected_files = {f"{judge}.json" for judge in JUDGES}
    actual_files = {path.name for path in staged_maps.glob("*.json")}
    if actual_files != expected_files:
        raise RuntimeError("staged attribution map set is incomplete")
    staged_maps.replace(output_dir)
    staging.rmdir()
    for judge_id in JUDGES:
        print(f"ATTRIBUTION_MAP={output_dir / (judge_id + '.json')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=MAPS_ROOT)
    args = parser.parse_args()
    return build(args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
