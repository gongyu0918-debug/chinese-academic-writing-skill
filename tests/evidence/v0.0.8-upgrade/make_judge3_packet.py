from __future__ import annotations

"""Build the judge-3 T1 packet from the frozen map and raw outputs."""

import hashlib
from pathlib import Path

EV = Path(__file__).resolve().parent


def main() -> int:
    mapping = EV / "maps" / "judge-3.json"
    mapping_hash = hashlib.sha256(mapping.read_bytes()).hexdigest()
    instructions = (EV / "judge-instructions.md").read_text(encoding="utf-8").strip()
    task = (EV / "tasks" / "T1.md").read_text(encoding="utf-8").strip()
    left = (EV / "raw" / "baseline" / "T1.md").read_text(encoding="utf-8").strip()
    right = (EV / "raw" / "candidate" / "T1.md").read_text(encoding="utf-8").strip()
    packet = (
        f"{instructions}\n\n"
        "## 当前匿名对\n\n"
        "- judge_id：`judge-3`\n"
        "- task_id：`T1`\n"
        "- pair_id：`J03-P001`\n"
        f"- mapping_sha256：`{mapping_hash}`\n\n"
        f"## 用户任务\n\n{task}\n\n"
        f"## 左稿\n\n{left}\n\n"
        f"## 右稿\n\n{right}\n\n"
        "## 输出绑定\n\n"
        "返回一个符合 judge_schema.json 的对象，`results` 数组只含当前一项。"
        f"`judge_id` 写 `judge-3`，`mapping_sha256` 写 `{mapping_hash}`，"
        "`task_id` 写 `T1`，`pair_id` 写 `J03-P001`，`blind` 为 true。\n"
    )
    out = EV / "packets" / "judge-3" / "T1.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(packet, encoding="utf-8", newline="\n")
    print(f"PACKET={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
