from __future__ import annotations

"""Build one blinded packet per judge and task from frozen maps and outputs."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class PacketError(ValueError):
    pass


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"cannot read {label} {path}: {exc}") from exc


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PacketError(f"cannot read {label} {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps-dir", required=True, type=Path)
    parser.add_argument("--tasks-dir", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--instructions", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        instructions = read_text(args.instructions, "judge instructions").strip()
        map_paths = sorted(args.maps_dir.glob("*.json"))
        if not map_paths:
            raise PacketError("no judge maps found")
        packet_count = 0
        for map_path in map_paths:
            mapping = read_json(map_path, "judge map")
            if not isinstance(mapping, dict) or mapping.get("schema_version") != 1:
                raise PacketError(f"invalid judge map: {map_path}")
            judge_id = mapping.get("judge_id")
            rows = mapping.get("mappings")
            if not isinstance(judge_id, str) or not judge_id or not isinstance(rows, list):
                raise PacketError(f"judge map lacks judge_id or mappings: {map_path}")
            mapping_hash = sha256_file(map_path)
            for row in rows:
                if not isinstance(row, dict):
                    raise PacketError(f"invalid map row: {map_path}")
                task_id = row.get("task_id")
                pair_id = row.get("pair_id")
                left_arm = row.get("left")
                right_arm = row.get("right")
                if not all(
                    isinstance(item, str) and item
                    for item in (task_id, pair_id, left_arm, right_arm)
                ):
                    raise PacketError(f"invalid map row identity: {row!r}")
                task = read_text(args.tasks_dir / f"{task_id}.md", "task").strip()
                left = read_text(args.raw_dir / left_arm / f"{task_id}.md", "left output").strip()
                right = read_text(args.raw_dir / right_arm / f"{task_id}.md", "right output").strip()
                packet = (
                    f"{instructions}\n\n"
                    f"## 当前匿名对\n\n"
                    f"- judge_id：`{judge_id}`\n"
                    f"- task_id：`{task_id}`\n"
                    f"- pair_id：`{pair_id}`\n"
                    f"- mapping_sha256：`{mapping_hash}`\n\n"
                    f"## 用户任务\n\n{task}\n\n"
                    f"## 左稿\n\n{left}\n\n"
                    f"## 右稿\n\n{right}\n\n"
                    "## 输出绑定\n\n"
                    "返回一个符合 judge_schema.json 的对象，`results` 数组只含当前一项。"
                    f"`judge_id` 写 `{judge_id}`，`mapping_sha256` 写 `{mapping_hash}`，"
                    f"`task_id` 写 `{task_id}`，`pair_id` 写 `{pair_id}`，`blind` 为 true。\n"
                )
                write_lf(args.output_dir / judge_id / f"{task_id}.md", packet)
                packet_count += 1
        print(f"PACKETS={packet_count}")
        return 0
    except PacketError as exc:
        print(f"PACKETS=ERROR\nERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
