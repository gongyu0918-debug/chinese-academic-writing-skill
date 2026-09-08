"""Offline integrity check for the frozen writing experiment, not a prose grader."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS = {
    "alibaba2": "alibaba-token-plan-2/deepseek-v4-flash-0731",
    "ollama": "ollama-cloud/deepseek-v4-flash:0731",
    "minimax": "minimax-cn/MiniMax-M3",
}
SNAPSHOTS = {
    "baseline": "baseline",
    "candidate": "candidate",
    "isolated-comparison": "isolated-comparison",
    "isolated-conclusion": "isolated-conclusion",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cases = {case["task_id"]: case for case in read_json(ROOT / "all-cases.json")["cases"]}
    records = {}
    summary = {}
    for arm, snapshot in SNAPSHOTS.items():
        counts = {"calls": 0, "completed_nonempty_responses": 0, "technical_invalid": 0}
        for record_path in sorted((ROOT / "calls" / arm).glob("*/*/record.json")):
            directory = record_path.parent
            record = read_json(record_path)
            request = read_json(directory / "request.json")
            provider, task = directory.parent.name, directory.name
            assert record["arm"] == arm and record["task_id"] == task
            assert record["requested_model"] == request["model"] == MODELS[provider]
            assert request["tools"] == [] and request["reasoning"] == {"effort": "max"}
            assert request["max_output_tokens"] == 14000 and not request["stream"]
            assert record["retry_count"] == 0
            assert digest(directory / "request.json") == record["request_sha256"]
            case = cases[task]
            assert request["input"][1] == {"role": "user", "content": case["request"]}
            files = ("SKILL.md", "references/" + case["leaf"])
            if "skill_files" in record:
                for file in files:
                    assert digest(ROOT / "frozen-inputs" / snapshot / file) == record["skill_files"][file]
            else:
                # The initial pilot predates per-file metadata. Its exact developer
                # message is still checked against the frozen files below.
                assert (arm, provider, task) == ("baseline", "alibaba2", "C1")
            rules = "\n\n".join(
                (ROOT / "frozen-inputs" / snapshot / file).read_text(encoding="utf-8")
                for file in files
            )
            assert request["input"][0] == {"role": "developer", "content": rules}
            if "final_sha256" in record:
                # The pilot recorded saved bytes; the transport records model text.
                # Windows write_text converts LF to CRLF. The manifest binds bytes.
                final = directory / "final.md"
                actual = digest(final) if (arm, provider, task) == ("baseline", "alibaba2", "C1") else hashlib.sha256(
                    final.read_text(encoding="utf-8").encode("utf-8")
                ).hexdigest()
                assert actual == record["final_sha256"], (arm, provider, task)
            if record["valid"]:
                assert record["status"] == "completed"
                assert (directory / "final.md").read_text(encoding="utf-8").strip()
            counts["calls"] += 1
            counts["completed_nonempty_responses"] += int(record["valid"])
            counts["technical_invalid"] += int(not record["valid"])
            records[(arm, provider, task)] = record
        expected = {"baseline": 39, "candidate": 36, "isolated-comparison": 9,
                    "isolated-conclusion": 6}[arm]
        assert counts["calls"] == expected, (arm, counts)
        summary[arm] = counts

    packet_cases = {}
    for path in ROOT.glob("review-*.json"):
        for case in read_json(path).get("cases", []):
            packet_cases[case["task_id"]] = case
    pair_count = 0
    for mapping_path in ROOT.glob("mapping-*.json"):
        packet_id = mapping_path.stem.removeprefix("mapping-")
        packet = packet_cases[packet_id]["request"]
        pairs = json.loads(packet.split("\n", 1)[1])
        by_id = {pair["pair_id"]: pair for pair in pairs}
        mapping = read_json(mapping_path)
        assert len(by_id) == len(mapping)
        for item in mapping:
            pair = by_id[item["pair_id"]]
            assert pair["request"] == cases[item["task_id"]]["request"]
            for side in ("A", "B"):
                key = (item[side], item["provider"], item["task_id"])
                assert records[key]["valid"]
                original = ROOT / "calls" / key[0] / key[1] / key[2] / "final.md"
                assert pair[side] == original.read_text(encoding="utf-8")
            pair_count += 1

    manifest = read_json(ROOT / "manifest.json")
    actual_files = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
                    if path.is_file() and path.name != "manifest.json"}
    assert set(manifest) == actual_files
    for relative, expected in manifest.items():
        assert digest(ROOT / relative) == expected, relative

    decision = read_json(ROOT / "decision.json")
    assert len(cases) == decision["distinct_tasks"] == 13
    assert pair_count == decision["bound_pairs"] == 45
    completed = sum(item["completed_nonempty_responses"] for item in summary.values())
    assert completed == decision["completed_nonempty_responses"] == 84
    failures = decision["adjudicated_delivery_failures"]
    assert len(failures) == 1
    for failure in failures:
        key = tuple(failure[field] for field in ("arm", "provider", "task_id"))
        assert records[key]["valid"]
        final = ROOT / "calls" / key[0] / key[1] / key[2] / "final.md"
        assert failure["evidence_quote"] in final.read_text(encoding="utf-8")
    assert completed - len(failures) == decision["actual_manuscripts"] == 83
    for path in (ROOT / "reviews").glob("luna-*.json"):
        for verdict in read_json(path)["verdicts"]:
            assert verdict["preferred"] in ("A", "B", "TIE")
            assert {"pair_id", "preferred", "reason", "hard_errors_A", "hard_errors_B"} <= verdict.keys()
    print(json.dumps({"result": "PASS", "arms": summary, "bound_pairs": pair_count,
                      "actual_manuscripts": completed - len(failures),
                      "manifest_files": len(manifest)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
