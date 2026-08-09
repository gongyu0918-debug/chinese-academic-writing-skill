from __future__ import annotations

"""Build blind T6 confirmatory packets: c1 vs b1 (judge-4), c2 vs b2 (judge-5)."""

import hashlib
from pathlib import Path

EV = Path(__file__).resolve().parent
SEED = "v0.0.8-confirm-2026-08-09"
PAIRS = (
    ("judge-4", "T6A", "c1", "b1"),
    ("judge-5", "T6B", "c2", "b2"),
)


def orientation(judge_id: str, pair_id: str) -> bool:
    digest = hashlib.sha256(f"{SEED}\0{judge_id}\0{pair_id}".encode("utf-8")).digest()
    return digest[0] % 2 == 0


def synthetic_mapping_hash(pair_id: str) -> str:
    return hashlib.sha256(f"{SEED}\0{pair_id}".encode("utf-8")).hexdigest()


def main() -> int:
    instructions = (EV / "judge-instructions.md").read_text(encoding="utf-8").strip()
    task = (EV / "tasks" / "T6.md").read_text(encoding="utf-8").strip()
    for judge_id, pair_id, cand_arm, base_arm in PAIRS:
        candidate = (EV / "raw-confirm" / cand_arm / "T6.md").read_text(encoding="utf-8").strip()
        baseline = (EV / "raw-confirm" / base_arm / "T6.md").read_text(encoding="utf-8").strip()
        candidate_left = orientation(judge_id, pair_id)
        left, right = (candidate, baseline) if candidate_left else (baseline, candidate)
        left_arm, right_arm = (cand_arm, base_arm) if candidate_left else (base_arm, cand_arm)
        mapping_hash = synthetic_mapping_hash(pair_id)
        packet = (
            f"{instructions}\n\n"
            "## 当前匿名对\n\n"
            f"- judge_id：`{judge_id}`\n"
            f"- task_id：`{pair_id}`\n"
            f"- pair_id：`{pair_id}`\n"
            f"- mapping_sha256：`{mapping_hash}`\n\n"
            f"## 用户任务\n\n{task}\n\n"
            f"## 左稿\n\n{left}\n\n"
            f"## 右稿\n\n{right}\n\n"
            "## 输出绑定\n\n"
            "返回一个符合 judge_schema.json 的对象，`results` 数组只含当前一项。"
            f"`judge_id` 写 `{judge_id}`，`mapping_sha256` 写 `{mapping_hash}`，"
            f"`task_id` 写 `{pair_id}`，`pair_id` 写 `{pair_id}`，`blind` 为 true。\n"
        )
        out = EV / "packets" / judge_id / f"{pair_id}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(packet, encoding="utf-8", newline="\n")
        print(f"PACKET={out} left={left_arm} right={right_arm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
