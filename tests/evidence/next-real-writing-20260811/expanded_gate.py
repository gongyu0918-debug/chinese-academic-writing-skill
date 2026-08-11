from __future__ import annotations

"""Apply provider balance and positive-control gates after the generic score."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_raw_binding(
    writer: dict[str, Any],
    writer_manifest_path: Path,
    raw_root: Path,
    specs: dict[str, Any],
) -> dict[tuple[str, str], str]:
    expected_root = (writer_manifest_path.resolve().parent / "raw").resolve()
    if raw_root.resolve() != expected_root:
        raise ValueError("raw root is not the writer manifest's sealed raw directory")
    task_ids = [row.get("task_id") for row in specs.get("tasks", []) if isinstance(row, dict)]
    expected_keys = {
        (arm, task_id)
        for arm in ("baseline", "candidate")
        for task_id in task_ids
    }
    records = writer.get("records")
    if len(task_ids) != 12 or len(set(task_ids)) != 12 or not isinstance(records, list):
        raise ValueError("writer/spec matrix is incomplete")
    records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    text_snapshot: dict[tuple[str, str], str] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("writer records must be objects")
        key = (record.get("arm"), record.get("pair_id"))
        if key not in expected_keys or key in records_by_key or record.get("valid") is not True:
            raise ValueError(f"invalid or duplicate writer record: {key}")
        expected_relative = f"raw/{key[0]}/{key[1]}.md"
        if record.get("final_file") != expected_relative:
            raise ValueError(f"writer final path mismatch: {key}")
        path = writer_manifest_path.resolve().parent / expected_relative
        try:
            final_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"writer final missing or unreadable: {key}: {exc}") from exc
        final_hash = hashlib.sha256(final_text.encode("utf-8")).hexdigest()
        if final_hash != record.get("final_sha256"):
            raise ValueError(f"writer final hash mismatch: {key}")
        records_by_key[key] = record
        text_snapshot[key] = final_text
    if set(records_by_key) != expected_keys:
        raise ValueError("writer records do not cover the full two-arm matrix")
    return text_snapshot


def joint_synthesis(text: str) -> bool:
    sentences = [sentence for sentence in re.split(r"[。！？；\n]+", text) if sentence.strip()]
    for index, sentence in enumerate(sentences):
        citation_context = " ".join(sentences[max(0, index - 2) : index + 1])
        if not re.search(r"(?<![A-Za-z0-9])\[?S1\]?(?![A-Za-z0-9])", citation_context):
            continue
        if not re.search(r"(?<![A-Za-z0-9])\[?S2\]?(?![A-Za-z0-9])", citation_context):
            continue
        if not re.search(r"两项|两项研究|二者", sentence):
            continue
        if re.search(
            r"不能联合|无法联合|拒绝联合|并无共同|没有共同|不能归纳|无法归纳|"
            r"结果相反|方向相反|不一致|有争议|存在争议|存在分歧|是否支持|"
            r"不显著|未显著|证据不足|证据不明确|互相矛盾|相互矛盾|结论矛盾",
            sentence,
        ):
            continue
        if not re.search(
            r"(?:均|二者都|共同)(?:观察到|显示|报告|发现|表明)|"
            r"(?:均|都|共同).{0,6}(?:观察到|显示|报告|发现|表明)",
            sentence,
        ):
            continue
        participation = re.search(
            r"(?:课程参与(?:度|水平)?|参与度).{0,12}(?:提升|提高|增加)|"
            r"(?:提升|提高|增加).{0,12}(?:课程参与(?:度|水平)?|参与度)",
            sentence,
        )
        if participation is None:
            continue
        prefix = sentence[max(0, participation.start() - 12) : participation.start()]
        if re.search(r"(?:未|没有|并未|不|无|不能|无法|尚未).{0,8}$", prefix):
            continue
        return True
    return False


def evaluate(
    score: dict[str, Any],
    specs: dict[str, Any],
    writer: dict[str, Any],
    raw_snapshot: dict[tuple[str, str], str],
) -> dict[str, Any]:
    metadata = {row["task_id"]: row for row in specs["tasks"]}
    blockers: list[str] = []
    if writer.get("valid_calls") != 24 or writer.get("calls_planned") != 24:
        blockers.append("writer calls are not 24/24 valid")
    if writer.get("binding_stable") is not True:
        blockers.append("writer runtime binding is not stable")
    if writer.get("runtime_changed_files") != ["references/academic-literature-review.md"]:
        blockers.append("runtime diff is not the preregistered single file")
    if int(writer.get("reference_char_delta", 1)) > 0:
        blockers.append("candidate reference grew")
    totals = score.get("totals", {})
    wins = int(totals.get("candidate_wins", 0))
    losses = int(totals.get("baseline_wins", 0))
    rate = float(totals.get("decided_win_rate", 0.0))
    if wins < 6:
        blockers.append(f"candidate wins {wins} below 6")
    if wins - losses < 2:
        blockers.append(f"candidate net wins {wins - losses} below 2")
    if rate <= 0.60:
        blockers.append(f"candidate decided win rate {rate:.1%} is not above 60%")
    if score.get("candidate_only_hard_fail") is not False:
        blockers.append("candidate has a candidate-only hard failure")
    provider_results: dict[str, Counter[str]] = {
        provider: Counter() for provider in {row["provider"] for row in specs["tasks"]}
    }
    h2 = Counter()
    for row in score.get("tasks", []):
        task_id = row["task_id"]
        winner = row.get("winner")
        provider = metadata[task_id]["provider"]
        if winner in {"candidate", "baseline"}:
            provider_results[provider][winner] += 1
            if metadata[task_id]["source_task"] == "H2":
                h2[winner] += 1
    provider_net = {
        provider: counts["candidate"] - counts["baseline"]
        for provider, counts in provider_results.items()
    }
    if sum(net > 0 for net in provider_net.values()) < 2:
        blockers.append("fewer than two providers are candidate net-positive")
    if any(net < 0 for net in provider_net.values()):
        blockers.append("at least one provider is candidate net-negative")
    if h2["candidate"] < h2["baseline"]:
        blockers.append("H2 positive control is candidate net-negative")
    h2_candidate_texts = [
        raw_snapshot[("candidate", task_id)]
        for task_id, row in metadata.items()
        if row["source_task"] == "H2"
    ]
    joint_count = sum(joint_synthesis(text) for text in h2_candidate_texts)
    if joint_count < 2:
        blockers.append(f"only {joint_count}/3 H2 candidate outputs jointly synthesize S1 and S2")
    if score.get("gate_pass") is not True:
        blockers.extend(f"generic score: {item}" for item in score.get("blockers", []))
    return {
        "schema_version": 1,
        "gate_pass": not blockers,
        "blockers": blockers,
        "candidate_wins": wins,
        "baseline_wins": losses,
        "candidate_decided_win_rate": rate,
        "provider_net": provider_net,
        "h2_wins": dict(h2),
        "h2_joint_synthesis_count": joint_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", required=True, type=Path)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--writer-manifest", required=True, type=Path)
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    writer = read_json(args.writer_manifest)
    specs_bytes = args.specs.read_bytes()
    specs = json.loads(specs_bytes.decode("utf-8"))
    specs_hash = hashlib.sha256(specs_bytes).hexdigest()
    if writer.get("specs_sha256") != specs_hash:
        print("EXPANDED_GATE=ERROR")
        print("BLOCKERS=specs hash does not match the frozen writer matrix")
        return 2
    try:
        raw_snapshot = validate_raw_binding(writer, args.writer_manifest, args.raw_root, specs)
    except ValueError as exc:
        print("EXPANDED_GATE=ERROR")
        print(f"BLOCKERS={exc}")
        return 2
    payload = evaluate(read_json(args.score), specs, writer, raw_snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EXPANDED_GATE={'PASS' if payload['gate_pass'] else 'FAIL'}")
    if payload["blockers"]:
        print("BLOCKERS=" + " | ".join(payload["blockers"]))
    return 0 if payload["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
