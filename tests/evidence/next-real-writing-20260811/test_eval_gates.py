from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import expanded_gate
import run_judges


class EvalGateTests(unittest.TestCase):
    def test_joint_synthesis_requires_both_ids_and_joint_language(self) -> None:
        self.assertTrue(expanded_gate.joint_synthesis("两项研究均观察到课程参与度提升[S1][S2]。"))
        self.assertFalse(expanded_gate.joint_synthesis("研究一观察到提升[S1]。研究二也观察到提升[S2]。"))
        self.assertFalse(expanded_gate.joint_synthesis("两项研究均观察到课程参与度提升[S1]。"))
        self.assertFalse(
            expanded_gate.joint_synthesis(
                "两项研究[S1][S2]并无共同结论，不能联合归纳课程参与度提升。"
            )
        )
        for false_positive in (
            "两项研究关于课程参与度提升的结果相反[S1][S2]。",
            "两项研究关于课程参与度提升的证据不一致[S1][S2]。",
            "两项研究是否支持课程参与度提升仍有争议[S1][S2]。",
            "两项研究均显示课程参与度提升并不显著[S1][S2]。",
            "两项研究均显示课程参与度提升的证据不足[S1][S2]。",
            "两项研究均显示课程参与度提升，但两者结论互相矛盾[S1][S2]。",
        ):
            self.assertFalse(expanded_gate.joint_synthesis(false_positive))
        self.assertTrue(
            expanded_gate.joint_synthesis(
                "两项研究的具体结果见[S1][S2]。两项研究均显示课程参与度提升。"
            )
        )
        self.assertTrue(
            expanded_gate.joint_synthesis(
                "S1 和 S2 的设计具有可比性。两项研究均观察到课程参与度提升。"
            )
        )
        self.assertTrue(
            expanded_gate.joint_synthesis(
                "第一项结果见[S1]。第二项结果见[S2]。两项研究均观察到课程参与度提升。"
            )
        )

    def test_judge_trace_rejects_tools_and_multiple_finals(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started"},
                {"type": "item.completed", "item": {"type": "command_execution"}},
                {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
                {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
                {"type": "turn.completed"},
            ]
            trace.write_text("".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
            issues = run_judges.trace_issues(trace, "{}")
            self.assertIn("forbidden_judge_tool:command_execution", issues)

            trace.write_text(
                "\n".join(
                    json.dumps(event, ensure_ascii=False)
                    for event in (
                        {"type": "thread.started"},
                        {"type": "item.completed", "item": {"type": "file_change", "status": "failed"}},
                        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
                        {"type": "turn.completed"},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertIn("forbidden_judge_tool:file_change", run_judges.trace_issues(trace, "{}"))
            self.assertIn("trace_count:agent_message:2", issues)

    def test_validate_final_checks_binding_fields(self) -> None:
        mapping_hash = "a" * 64
        payload = {
            "schema_version": 1,
            "judge_id": "judge-1",
            "blind": True,
            "mapping_sha256": mapping_hash,
            "results": [
                {
                    "task_id": "H1-Q1",
                    "pair_id": "P001",
                    "left": {"verdict": "PASS", "hard_failures": [], "notes": ""},
                    "right": {"verdict": "WARN", "hard_failures": [], "notes": "局部问题"},
                    "winner": "left",
                    "rationale": "左稿更准确。",
                    "anchors": ["来源边界"],
                }
            ],
        }
        final = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(
            [],
            run_judges.validate_final(final, "judge-1", "H1-Q1", "P001", mapping_hash),
        )
        self.assertIn(
            "task_id_mismatch",
            run_judges.validate_final(final, "judge-1", "H2-Q1", "P001", mapping_hash),
        )
        incomplete = json.dumps(
            {"judge_id": "judge-1", "blind": True, "results": [{"task_id": "H1-Q1"}]}
        )
        self.assertIn(
            "top_level_schema_mismatch",
            run_judges.validate_final(incomplete, "judge-1", "H1-Q1", "P001", mapping_hash),
        )

    def test_expanded_gate_rejects_alternate_or_tampered_raw_root(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            ab_root = Path(folder) / "ab"
            raw_root = ab_root / "raw"
            manifest_path = ab_root / "manifest.json"
            task_ids = [f"T{index:02d}" for index in range(12)]
            specs = {"tasks": [{"task_id": task_id} for task_id in task_ids]}
            records = []
            for arm in ("baseline", "candidate"):
                for task_id in task_ids:
                    path = raw_root / arm / f"{task_id}.md"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    text = f"{arm}-{task_id}\n"
                    path.write_text(text, encoding="utf-8")
                    records.append(
                        {
                            "arm": arm,
                            "pair_id": task_id,
                            "valid": True,
                            "final_file": f"raw/{arm}/{task_id}.md",
                            "final_sha256": run_judges.sha256_bytes(text.encode("utf-8")),
                        }
                    )
            writer = {"records": records}
            manifest_path.write_text(json.dumps(writer), encoding="utf-8")
            snapshot = expanded_gate.validate_raw_binding(writer, manifest_path, raw_root, specs)
            alternate = Path(folder) / "fake-raw"
            alternate.mkdir()
            with self.assertRaisesRegex(ValueError, "sealed raw directory"):
                expanded_gate.validate_raw_binding(writer, manifest_path, alternate, specs)
            original_snapshot = snapshot[("candidate", task_ids[0])]
            (raw_root / "candidate" / f"{task_ids[0]}.md").write_text("tampered", encoding="utf-8")
            self.assertEqual(original_snapshot, snapshot[("candidate", task_ids[0])])
            with self.assertRaisesRegex(ValueError, "final hash mismatch"):
                expanded_gate.validate_raw_binding(writer, manifest_path, raw_root, specs)

    def test_judge_preflight_binds_unique_map_and_exact_packets(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            evidence = Path(folder) / "evidence"
            ab_root = evidence / "ab"
            maps_root = evidence / "ab_maps"
            packets_root = ab_root / "packets"
            output_root = ab_root / "judgments"
            manifest_root = ab_root / "judge-manifests"
            for path in (evidence / "tasks", ab_root / "tasks", maps_root, packets_root / "judge-1"):
                path.mkdir(parents=True, exist_ok=True)
            task_ids = [f"H1-Q{index:02d}" for index in range(1, 13)]
            specs = {
                "schema_version": 1,
                "tasks": [
                    {"task_id": task_id, "source_task": "H1", "provider": "alibaba"}
                    for task_id in task_ids
                ],
            }
            specs_path = evidence / "ab_specs.json"
            specs_path.write_text(json.dumps(specs), encoding="utf-8")
            instructions_path = evidence / "instructions.md"
            instructions_path.write_text("judge instructions\n", encoding="utf-8")
            schema_path = evidence / "schema.json"
            schema_path.write_text("{}\n", encoding="utf-8")
            (evidence / "tasks" / "H1.md").write_text("task body\n", encoding="utf-8")
            task_hash = run_judges.sha256_bytes("task body\n".encode("utf-8"))
            prompt_hash = run_judges.sha256_bytes(
                run_judges.build_prompt("task body\n").encode("utf-8")
            )
            records = []
            for task_id in task_ids:
                (ab_root / "tasks" / f"{task_id}.md").write_text("task body\n", encoding="utf-8")
                for arm in ("baseline", "candidate"):
                    raw_path = ab_root / "raw" / arm / f"{task_id}.md"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_text = f"{arm} output for {task_id}\n"
                    raw_path.write_text(raw_text, encoding="utf-8")
                    records.append(
                        {
                            "arm": arm,
                            "pair_id": task_id,
                            "source_task": "H1",
                            "provider": "alibaba",
                            "model": next(
                                provider.model
                                for provider in run_judges.PROVIDERS
                                if provider.name == "alibaba"
                            ),
                            "reasoning_effort": "max",
                            "retry_count": 0,
                            "commit": f"{arm}-commit",
                            "runtime_fingerprint": f"{arm}-fingerprint",
                            "valid": True,
                            "final_file": f"raw/{arm}/{task_id}.md",
                            "final_sha256": run_judges.sha256_bytes(raw_text.encode("utf-8")),
                            "prompt_sha256": prompt_hash,
                            "prompt_bound": True,
                        }
                    )
            writer_manifest = {
                "valid_calls": 24,
                "calls_planned": 24,
                "binding_stable": True,
                "baseline": {
                    "commit": "baseline-commit",
                    "runtime_fingerprint": "baseline-fingerprint",
                },
                "candidate": {
                    "commit": "candidate-commit",
                    "runtime_fingerprint": "candidate-fingerprint",
                },
                "specs_sha256": run_judges.sha256_file(specs_path),
                "task_sha256": {"H1": task_hash},
                "prompt_sha256": {"H1": prompt_hash},
                "records": records,
            }
            writer_manifest_path = ab_root / "manifest.json"
            writer_manifest_path.write_text(json.dumps(writer_manifest), encoding="utf-8")
            map_path = maps_root / "judge-1.json"
            orientations = run_judges.expected_orientations(task_ids, "judge-1")
            mapping = {
                "schema_version": 1,
                "judge_id": "judge-1",
                "task_specs_sha256": run_judges.sha256_file(specs_path),
                "seed_sha256": run_judges.sha256_bytes(run_judges.MAP_SEED.encode("utf-8")),
                "mappings": [
                    {
                        "task_id": task_id,
                        "pair_id": f"P{index:03d}",
                        "left": "candidate" if candidate_left else "baseline",
                        "right": "baseline" if candidate_left else "candidate",
                    }
                    for index, (task_id, candidate_left) in enumerate(
                        zip(task_ids, orientations, strict=True), start=1
                    )
                ],
            }
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            patched = {
                "EVIDENCE_ROOT": evidence,
                "AB_ROOT": ab_root,
                "SPECS_PATH": specs_path,
                "INSTRUCTIONS_PATH": instructions_path,
                "WRITER_MANIFEST_PATH": writer_manifest_path,
                "PACKETS_ROOT": packets_root,
                "MAPS_ROOT": maps_root,
                "OUTPUT_ROOT": output_root,
                "MANIFEST_ROOT": manifest_root,
                "SCHEMA_PATH": schema_path,
            }
            with mock.patch.multiple(run_judges, **patched):
                mapping_hash = run_judges.sha256_file(map_path)
                for row in mapping["mappings"]:
                    packet = run_judges.expected_packet_text(
                        "judge-1",
                        row["task_id"],
                        row["pair_id"],
                        row["left"],
                        row["right"],
                        mapping_hash,
                    )
                    (packets_root / "judge-1" / f"{row['task_id']}.md").write_text(packet, encoding="utf-8")
                self.assertEqual(12, run_judges.preflight(["judge-1"])["calls_planned"])
                saved_prompt_hash = records[0].pop("prompt_sha256")
                writer_manifest_path.write_text(json.dumps(writer_manifest), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "writer prompt record mismatch"):
                    run_judges.preflight(["judge-1"])
                records[0]["prompt_sha256"] = saved_prompt_hash
                writer_manifest_path.write_text(json.dumps(writer_manifest), encoding="utf-8")
                saved_provider = records[0].pop("provider")
                writer_manifest_path.write_text(json.dumps(writer_manifest), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "writer record binding mismatch"):
                    run_judges.preflight(["judge-1"])
                records[0]["provider"] = saved_provider
                writer_manifest_path.write_text(json.dumps(writer_manifest), encoding="utf-8")
                saved_mapping = json.loads(json.dumps(mapping))
                for row in mapping["mappings"]:
                    row["left"], row["right"] = "baseline", "candidate"
                map_path.write_text(json.dumps(mapping), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "fixed seed"):
                    run_judges.preflight(["judge-1"])
                mapping = saved_mapping
                map_path.write_text(json.dumps(mapping), encoding="utf-8")
                packet_path = packets_root / "judge-1" / f"{task_ids[0]}.md"
                packet_path.write_text(packet_path.read_text(encoding="utf-8") + "Candidate identity", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "packet content mismatch"):
                    run_judges.preflight(["judge-1"])
                mapping["mappings"][1]["task_id"] = task_ids[0]
                map_path.write_text(json.dumps(mapping), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "task IDs"):
                    run_judges.preflight(["judge-1"])


if __name__ == "__main__":
    unittest.main()
