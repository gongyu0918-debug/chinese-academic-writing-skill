from __future__ import annotations

"""Build a deterministic anonymous packet from the final R1 real-writing pairs."""

import hashlib
import json
import random
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN_ROOT = REPO / ".release/evidence-bound-inference-r1"
BLIND_ROOT = RUN_ROOT / "blind-final-r1"
SEED = 20260831
PROVIDERS = ("alibaba1", "alibaba2", "minimax", "ollama", "opencode")
LOGICAL_TASKS = ("P1_DISCUSSION", "P2_REWRITE", "P3_MIXED_REVIEW", "C1_CORRELATION", "C2_CLEAN_REVIEW")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cases() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for filename in ("cases.json", "supplemental-cases.json"):
        payload = json.loads((HERE / filename).read_text(encoding="utf-8"))
        for case in payload["cases"]:
            result[case["task_id"]] = case
    return result


def final_path(arm: str, provider: str, logical_task: str) -> tuple[str, Path]:
    if provider == "minimax":
        replacements = {
            "P1_DISCUSSION": (
                "S1_DISCUSSION",
                "supplemental-baseline/minimax-s1/minimax/S1_DISCUSSION/final.md",
                "supplemental-candidate/minimax/minimax/S1_DISCUSSION/final.md",
            ),
            "P2_REWRITE": (
                "S4_REWRITE",
                "supplemental-baseline-r2/minimax/minimax/S4_REWRITE/final.md",
                "supplemental-candidate/minimax/minimax/S4_REWRITE/final.md",
            ),
            "P3_MIXED_REVIEW": (
                "S5_MIXED_REVIEW",
                "supplemental-baseline-r3/minimax/minimax/S5_MIXED_REVIEW/final.md",
                "supplemental-candidate-final/minimax-s5/minimax/S5_MIXED_REVIEW/final.md",
            ),
            "C2_CLEAN_REVIEW": (
                "S3_CLEAN_REVIEW",
                "supplemental-baseline/minimax-s3/minimax/S3_CLEAN_REVIEW/final.md",
                "supplemental-candidate/minimax/minimax/S3_CLEAN_REVIEW/final.md",
            ),
        }
        if logical_task in replacements:
            actual_task, baseline, candidate = replacements[logical_task]
            return actual_task, RUN_ROOT / (baseline if arm == "baseline" else candidate)
    if provider == "ollama" and logical_task == "P3_MIXED_REVIEW":
        relative = (
            "supplemental-baseline/ollama-s2/ollama/S2_MIXED_REVIEW/final.md"
            if arm == "baseline"
            else "supplemental-candidate/ollama/ollama/S2_MIXED_REVIEW/final.md"
        )
        return "S2_MIXED_REVIEW", RUN_ROOT / relative
    return logical_task, RUN_ROOT / arm / provider / logical_task / "final.md"


def main() -> int:
    if BLIND_ROOT.exists():
        raise SystemExit(f"blind output already exists: {BLIND_ROOT}")
    cases = load_cases()
    specs = [(provider, task) for provider in PROVIDERS for task in LOGICAL_TASKS]
    rng = random.Random(SEED)
    rng.shuffle(specs)
    packet_parts = [
        "# 匿名真实写稿配对审稿包",
        "",
        "共25对。A/B身份、provider和版本均已隐藏。逐对先判事实、数据、研究状态、因果、范围与交付模式硬失败，再比较论证有效性、审稿准确性、直接可用性和修改负担。合理的作者归纳、候选解释或条件性意义，只要没有冒充来源结论、已测结果、确定因果或总体规律，不因材料未逐字写出同一句而判错。只审不改题不得为了凑项制造问题。",
        "",
        "每对只给一个结论：`A`、`B`、`TIE` 或 `INVALID`。`INVALID` 仅用于题面或稿件技术上无法判断，不用于质量差。最后按 `编号｜结论｜硬失败｜简要理由` 逐行输出，并汇总 A/B/TIE/INVALID 数量。",
        "",
    ]
    mapping: list[dict[str, Any]] = []
    for index, (provider, logical_task) in enumerate(specs, start=1):
        pair_id = f"Q{index:02d}"
        actual_task, baseline_path = final_path("baseline", provider, logical_task)
        candidate_task, candidate_path = final_path("candidate", provider, logical_task)
        if candidate_task != actual_task:
            raise RuntimeError(f"task mismatch for {provider}/{logical_task}")
        if not baseline_path.is_file() or not candidate_path.is_file():
            raise RuntimeError(f"missing pair file for {provider}/{logical_task}")
        baseline = baseline_path.read_text(encoding="utf-8").strip()
        candidate = candidate_path.read_text(encoding="utf-8").strip()
        if not baseline or not candidate or baseline == "ENV_INVALID" or candidate == "ENV_INVALID":
            raise RuntimeError(f"invalid final selected for {provider}/{logical_task}")
        candidate_label = "A" if rng.randrange(2) == 0 else "B"
        label_text = {
            candidate_label: candidate,
            "B" if candidate_label == "A" else "A": baseline,
        }
        case = cases[actual_task]
        packet_parts.extend(
            [
                f"## {pair_id}",
                "",
                "### 任务",
                "",
                case["request"].strip(),
                "",
                "### 硬失败",
                "",
                *[f"- {item}" for item in case["hard_failures"]],
                "",
                "### 质量观察",
                "",
                *[f"- {item}" for item in case["quality_observations"]],
                "",
                "### 稿件A",
                "",
                label_text["A"],
                "",
                "### 稿件B",
                "",
                label_text["B"],
                "",
            ]
        )
        mapping.append(
            {
                "pair_id": pair_id,
                "provider": provider,
                "logical_task": logical_task,
                "actual_task": actual_task,
                "candidate_label": candidate_label,
                "baseline_file": baseline_path.relative_to(REPO).as_posix(),
                "candidate_file": candidate_path.relative_to(REPO).as_posix(),
                "baseline_sha256": sha256_text(baseline),
                "candidate_sha256": sha256_text(candidate),
            }
        )
    packet = "\n".join(packet_parts).rstrip() + "\n"
    BLIND_ROOT.mkdir(parents=True)
    packet_path = BLIND_ROOT / "packet.md"
    mapping_path = BLIND_ROOT / "mapping.json"
    packet_path.write_text(packet, encoding="utf-8", newline="\n")
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "schema_version": 1,
        "seed": SEED,
        "pair_count": len(mapping),
        "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        "mapping_sha256": hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
    }
    (BLIND_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
