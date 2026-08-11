from __future__ import annotations

"""Shared frozen bindings and validators for target-specific attribution judging."""

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from run_discovery import sha256_bytes, sha256_file


EVIDENCE_ROOT = Path(__file__).resolve().parent
ATTRIBUTION_ROOT = EVIDENCE_ROOT / "attribution"
SPECS_PATH = EVIDENCE_ROOT / "attribution_specs.json"
INSTRUCTIONS_PATH = EVIDENCE_ROOT / "attribution-judge-instructions.md"
SCHEMA_PATH = EVIDENCE_ROOT / "attribution-judge-schema.json"
MAPS_ROOT = EVIDENCE_ROOT / "attribution_maps"
PACKETS_ROOT = ATTRIBUTION_ROOT / "packets"
MAP_SEED = "academic-synthesis-attribution-20260811-v1"
EXPECTED_INSTRUCTIONS_SHA256 = "bb67d1093a29c200cf3decaaec3b02e20e4a6cb7c2a7366e34ea60c87d917115"
EXPECTED_SCHEMA_SHA256 = "c927da9cb5e50fb358f3515f05274906bbf1bd002dbf0b038d7a051bccef7c49"
JUDGES = ("judge-1", "judge-2", "judge-3")
PRIMARY_JUDGES = ("judge-1", "judge-2")
TARGETS_BY_GROUP = {
    "A1": ("FALSE_CROSS_SOURCE_LINK",),
    "A2": ("STABILITY_AMPLIFICATION", "LEGAL_SYNTHESIS_MISSING"),
    "A3": ("UNKNOWN_DIMENSION_EXPLANATION", "CITATION_LOCALITY_FAILURE"),
}
DEFINITE_LABELS = {"PRESENT", "ABSENT"}
ALL_LABELS = DEFINITE_LABELS | {"UNCERTAIN", "UNJUDGEABLE"}


def load_specs() -> dict[str, Any]:
    import run_attribution

    return run_attribution.load_specs_snapshot()[0]


def expected_orientations(task_ids: list[str], judge_id: str) -> list[bool]:
    digest = hashlib.sha256(f"{MAP_SEED}\0{judge_id}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    orientations = [False, True] * ((len(task_ids) + 1) // 2)
    orientations = orientations[: len(task_ids)]
    rng.shuffle(orientations)
    return orientations


def load_valid_map(judge_id: str) -> tuple[dict[str, Any], str]:
    if judge_id not in JUDGES:
        raise RuntimeError(f"unknown attribution judge: {judge_id}")
    specs = load_specs()
    task_ids = [row["task_id"] for row in specs["tasks"]]
    path = MAPS_ROOT / f"{judge_id}.json"
    if not path.is_file():
        raise RuntimeError(f"missing attribution map: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_top = {"schema_version", "judge_id", "task_specs_sha256", "seed_sha256", "mappings"}
    if not isinstance(payload, dict) or set(payload) != expected_top:
        raise RuntimeError(f"invalid map schema: {judge_id}")
    if (
        payload.get("schema_version") != 1
        or payload.get("judge_id") != judge_id
        or payload.get("task_specs_sha256") != sha256_file(SPECS_PATH)
        or payload.get("seed_sha256") != sha256_bytes(MAP_SEED.encode("utf-8"))
    ):
        raise RuntimeError(f"invalid map binding: {judge_id}")
    rows = payload.get("mappings")
    if not isinstance(rows, list) or len(rows) != len(task_ids):
        raise RuntimeError(f"invalid map row count: {judge_id}")
    expected_orientation = expected_orientations(task_ids, judge_id)
    for index, (row, task_id, candidate_left) in enumerate(
        zip(rows, task_ids, expected_orientation, strict=True),
        start=1,
    ):
        expected_row = {
            "task_id": task_id,
            "pair_id": f"J{JUDGES.index(judge_id) + 1:02d}-P{index:03d}",
            "left": "candidate" if candidate_left else "baseline",
            "right": "baseline" if candidate_left else "candidate",
        }
        if row != expected_row:
            raise RuntimeError(f"map row differs from fixed seed: {judge_id}/{task_id}")
    return payload, sha256_file(path)


def packet_text(
    judge_id: str,
    task_id: str,
) -> tuple[str, str, dict[str, Any], str, str]:
    mapping, mapping_hash = load_valid_map(judge_id)
    rows = {row["task_id"]: row for row in mapping["mappings"]}
    if task_id not in rows:
        raise RuntimeError(f"task missing from map: {judge_id}/{task_id}")
    row = rows[task_id]
    group = task_id.split("-", 1)[0]
    targets = TARGETS_BY_GROUP[group]
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()
    task = (ATTRIBUTION_ROOT / "tasks" / f"{task_id}.md").read_text(encoding="utf-8").strip()
    left = (
        ATTRIBUTION_ROOT / "raw" / row["left"] / f"{task_id}.md"
    ).read_text(encoding="utf-8").strip()
    right = (
        ATTRIBUTION_ROOT / "raw" / row["right"] / f"{task_id}.md"
    ).read_text(encoding="utf-8").strip()
    body = (
        f"{instructions}\n\n"
        "## 当前匿名对\n\n"
        f"- judge_id：`{judge_id}`\n"
        f"- task_id：`{task_id}`\n"
        f"- pair_id：`{row['pair_id']}`\n"
        f"- mapping_sha256：`{mapping_hash}`\n"
        f"- 本题 targets：`{', '.join(targets)}`\n\n"
        f"## 用户任务\n\n{task}\n\n"
        f"## 左稿\n\n{left}\n\n"
        f"## 右稿\n\n{right}\n"
    )
    content_hash = sha256_bytes(body.encode("utf-8"))
    packet = (
        f"{body}\n"
        "## 输出绑定\n\n"
        "返回一个符合 attribution-judge-schema.json 的对象。"
        f"`judge_id` 写 `{judge_id}`，`mapping_sha256` 写 `{mapping_hash}`，"
        f"`packet_sha256` 写 `{content_hash}`，`task_id` 写 `{task_id}`，"
        f"`pair_id` 写 `{row['pair_id']}`，`blind` 为 true。"
        f"targets 必须按顺序且恰好为 `{', '.join(targets)}`。\n"
    )
    return packet, content_hash, row, left, right


def validate_final(
    final: str,
    judge_id: str,
    task_id: str,
    pair_id: str,
    mapping_hash: str,
    packet_hash: str,
    left_text: str,
    right_text: str,
) -> list[str]:
    try:
        payload = json.loads(final)
    except json.JSONDecodeError as exc:
        return [f"invalid_json:{exc.msg}"]
    top_keys = {
        "schema_version",
        "judge_id",
        "blind",
        "mapping_sha256",
        "packet_sha256",
        "task_id",
        "pair_id",
        "targets",
        "unrelated_errors",
    }
    if not isinstance(payload, dict) or set(payload) != top_keys:
        return ["top_level_schema_mismatch"]
    issues: list[str] = []
    bindings = {
        "schema_version": 1,
        "judge_id": judge_id,
        "blind": True,
        "mapping_sha256": mapping_hash,
        "packet_sha256": packet_hash,
        "task_id": task_id,
        "pair_id": pair_id,
    }
    for key, expected in bindings.items():
        if payload.get(key) != expected:
            issues.append(f"{key}_mismatch")
    expected_targets = TARGETS_BY_GROUP.get(task_id.split("-", 1)[0], ())
    targets = payload.get("targets")
    if not isinstance(targets, list):
        issues.append("targets_not_array")
        return issues
    target_ids = [target.get("target_id") if isinstance(target, dict) else None for target in targets]
    if target_ids != list(expected_targets):
        issues.append("target_set_or_order_mismatch")
    side_texts = {"left": left_text, "right": right_text}
    for target in targets:
        if not isinstance(target, dict) or set(target) != {"target_id", "left", "right"}:
            issues.append("target_schema_mismatch")
            continue
        target_id = str(target.get("target_id") or "unknown")
        for side_name, side_text in side_texts.items():
            side = target.get(side_name)
            if not isinstance(side, dict) or set(side) != {"label", "anchors"}:
                issues.append(f"{target_id}:{side_name}:side_schema_mismatch")
                continue
            label = side.get("label")
            anchors = side.get("anchors")
            if label not in ALL_LABELS:
                issues.append(f"{target_id}:{side_name}:label_invalid")
            if not isinstance(anchors, list):
                issues.append(f"{target_id}:{side_name}:anchors_not_array")
                continue
            if label == "PRESENT" and not anchors:
                issues.append(f"{target_id}:{side_name}:present_without_anchor")
            if label == "ABSENT" and anchors:
                issues.append(f"{target_id}:{side_name}:absent_with_anchor")
            for anchor in anchors:
                if (
                    not isinstance(anchor, dict)
                    or set(anchor) != {"quote", "reason"}
                    or not isinstance(anchor.get("quote"), str)
                    or not anchor["quote"]
                    or not isinstance(anchor.get("reason"), str)
                    or not anchor["reason"]
                ):
                    issues.append(f"{target_id}:{side_name}:anchor_schema_mismatch")
                    continue
                if anchor["quote"] not in side_text:
                    issues.append(f"{target_id}:{side_name}:anchor_not_verbatim")
    unrelated = payload.get("unrelated_errors")
    if not isinstance(unrelated, dict) or set(unrelated) != {"left", "right"}:
        issues.append("unrelated_errors_schema_mismatch")
    else:
        for side_name, side_text in side_texts.items():
            errors = unrelated.get(side_name)
            if not isinstance(errors, list):
                issues.append(f"unrelated_errors:{side_name}:not_array")
                continue
            for error in errors:
                if (
                    not isinstance(error, dict)
                    or set(error) != {"code", "quote"}
                    or not isinstance(error.get("code"), str)
                    or not error["code"]
                    or not isinstance(error.get("quote"), str)
                    or not error["quote"]
                ):
                    issues.append(f"unrelated_errors:{side_name}:schema_mismatch")
                    continue
                # Unrelated errors are non-directional audit notes and never enter
                # the causal score. Keep their schema strict, but do not invalidate
                # an otherwise bound target judgment for Markdown-only quote drift.
    return sorted(set(issues))
