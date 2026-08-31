from __future__ import annotations

"""Build or verify the deterministic anonymous packet for final R1 pairs."""

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN_ROOT = REPO / ".release/evidence-bound-inference-r1"
DEFAULT_BLIND_ROOT = RUN_ROOT / "blind-final-r1-audited"
OVERRIDES_PATH = HERE / "selection-overrides.json"
SEED = 20260831
PROVIDERS = ("alibaba1", "alibaba2", "minimax", "ollama", "opencode")
LOGICAL_TASKS = ("P1_DISCUSSION", "P2_REWRITE", "P3_MIXED_REVIEW", "C1_CORRELATION", "C2_CLEAN_REVIEW")
REQUIRED_READS = ("references/academic-writing.md", "skill.md")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def relative_repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO.resolve()).as_posix()


def load_cases() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for filename in ("cases.json", "supplemental-cases.json"):
        payload = json.loads((HERE / filename).read_text(encoding="utf-8"))
        for case in payload["cases"]:
            result[case["task_id"]] = case
    return result


def load_overrides() -> tuple[dict[tuple[str, str, str], dict[str, Any]], set[str]]:
    payload = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    overrides = payload.get("overrides")
    if payload.get("schema_version") != 1 or not isinstance(overrides, list):
        raise RuntimeError("selection-overrides.json must use schema_version=1")
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    ids: set[str] = set()
    for item in overrides:
        override_id = str(item.get("id") or "")
        key = (
            str(item.get("manifest_file") or "").casefold(),
            str(item.get("provider") or ""),
            str(item.get("task_id") or ""),
        )
        if not override_id or override_id in ids or not all(key) or key in indexed:
            raise RuntimeError("selection override IDs and keys must be unique and non-empty")
        ids.add(override_id)
        indexed[key] = item
    return indexed, ids


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


def find_manifest(final: Path) -> Path:
    for parent in final.resolve().parents:
        candidate = parent / "manifest.json"
        if candidate.is_file():
            return candidate
        if parent == RUN_ROOT.resolve():
            break
    raise RuntimeError(f"no run manifest found for {final}")


def normalized_reads(record: dict[str, Any], final: Path) -> list[str]:
    copied_root = re.sub(r"[\\/]+", "/", str((final.parent / "skill").resolve())).casefold().rstrip("/")
    reads: set[str] = set()
    for observed in record.get("observed_reads") or []:
        normalized = re.sub(r"[\\/]+", "/", str(observed)).casefold()
        if normalized.startswith(f"{copied_root}/"):
            normalized = normalized[len(copied_root) + 1 :]
        else:
            normalized = normalized.removeprefix("./").removeprefix("skill/")
        reads.add(normalized)
    return sorted(reads)


def selection_proof(
    arm: str,
    provider: str,
    task_id: str,
    final: Path,
    overrides: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    if not final.is_file():
        raise RuntimeError(f"missing final for {arm}/{provider}/{task_id}")
    manifest_path = find_manifest(final)
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    records = [
        item
        for item in manifest.get("records") or []
        if item.get("provider") == provider and item.get("task_id") == task_id
    ]
    if len(records) != 1:
        raise RuntimeError(f"expected one manifest record for {arm}/{provider}/{task_id}")
    record = records[0]
    recorded_final = (manifest_path.parent / str(record.get("final_file") or "")).resolve()
    if recorded_final != final.resolve():
        raise RuntimeError(f"manifest final path mismatch for {arm}/{provider}/{task_id}")
    raw_final_sha = sha256_file(final)
    if raw_final_sha != record.get("final_sha256"):
        raise RuntimeError(f"manifest final hash mismatch for {arm}/{provider}/{task_id}")
    if manifest.get("arm") != arm or record.get("arm") != arm:
        raise RuntimeError(f"arm mismatch for {arm}/{provider}/{task_id}")
    if manifest.get("source_binding_stable") is not True or record.get("skill_binding_stable") is not True:
        raise RuntimeError(f"unstable Skill binding for {arm}/{provider}/{task_id}")
    if record.get("technical_valid") is not True or record.get("retry_count") != 0:
        raise RuntimeError(f"technically invalid or retried final for {arm}/{provider}/{task_id}")
    if record.get("forbidden_trace_markers"):
        raise RuntimeError(f"forbidden trace marker for {arm}/{provider}/{task_id}")

    manifest_file = relative_repo_path(manifest_path)
    manifest_sha = sha256_text(manifest_text)
    override_id: str | None = None
    if record.get("valid") is not True:
        key = (manifest_file.casefold(), provider, task_id)
        override = overrides.get(key)
        if override is None:
            raise RuntimeError(f"invalid selected record lacks an audited override: {arm}/{provider}/{task_id}")
        if override.get("manifest_sha256") != manifest_sha or override.get("final_sha256") != raw_final_sha:
            raise RuntimeError(f"selection override hash mismatch for {arm}/{provider}/{task_id}")
        if record.get("route_complete") is not False or normalized_reads(record, final) != list(REQUIRED_READS):
            raise RuntimeError(f"selection override is not a duplicate allowed-read normalization")
        override_id = str(override["id"])

    return {
        "manifest_file": manifest_file,
        "manifest_sha256": manifest_sha,
        "record_valid": bool(record.get("valid")),
        "validity_override": override_id,
        "raw_final_sha256": raw_final_sha,
    }


def build_artifacts() -> tuple[str, str, dict[str, Any]]:
    cases = load_cases()
    overrides, override_ids = load_overrides()
    used_overrides: set[str] = set()
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
        baseline_proof = selection_proof("baseline", provider, actual_task, baseline_path, overrides)
        candidate_proof = selection_proof("candidate", provider, actual_task, candidate_path, overrides)
        for proof in (baseline_proof, candidate_proof):
            if proof["validity_override"]:
                used_overrides.add(str(proof["validity_override"]))
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
                "baseline_file": relative_repo_path(baseline_path),
                "candidate_file": relative_repo_path(candidate_path),
                "baseline_sha256": sha256_text(baseline),
                "candidate_sha256": sha256_text(candidate),
                "baseline_selection": baseline_proof,
                "candidate_selection": candidate_proof,
            }
        )
    if used_overrides != override_ids:
        raise RuntimeError(f"unused or missing selection overrides: expected={sorted(override_ids)}, used={sorted(used_overrides)}")
    packet = "\n".join(packet_parts).rstrip() + "\n"
    mapping_json = json_text(mapping)
    manifest = {
        "schema_version": 2,
        "seed": SEED,
        "pair_count": len(mapping),
        "packet_sha256": sha256_text(packet),
        "mapping_sha256": sha256_text(mapping_json),
        "selection_overrides_sha256": sha256_file(OVERRIDES_PATH),
        "validity_override_count": len(used_overrides),
    }
    return packet, mapping_json, manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_BLIND_ROOT)
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="rebuild in memory and verify packet.md, mapping.json, and manifest.json without writing",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    packet, mapping_json, manifest = build_artifacts()
    manifest_json = json_text(manifest)
    artifacts = {
        "packet.md": packet,
        "mapping.json": mapping_json,
        "manifest.json": manifest_json,
    }
    if args.verify_existing:
        for filename, expected in artifacts.items():
            path = output_root / filename
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                raise SystemExit(f"blind artifact mismatch: {path}")
        print(json.dumps({"verified": True, **manifest}, ensure_ascii=False))
        return 0
    if output_root.exists():
        raise SystemExit(f"blind output already exists: {output_root}")
    output_root.mkdir(parents=True)
    for filename, content in artifacts.items():
        (output_root / filename).write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
