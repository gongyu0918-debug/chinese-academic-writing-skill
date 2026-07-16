from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests" / "evidence" / "v0.0.4-paragraph-ablation"


class ParagraphAblationEvidenceTests(unittest.TestCase):
    def test_anonymous_maps_cover_each_arm_once_per_task(self) -> None:
        mapping = json.loads((EVIDENCE / "blind" / "anonymous-map.json").read_text(encoding="utf-8"))
        expected = {"baseline", "candidate", "no-skill"}
        for judge in ("judge-1", "judge-2"):
            for task in ("T1", "T2", "T3"):
                with self.subTest(judge=judge, task=task):
                    self.assertEqual(expected, set(mapping[judge][task].values()))

    def test_frozen_tasks_packets_and_verdicts_are_complete(self) -> None:
        tasks = (EVIDENCE / "tasks.md").read_text(encoding="utf-8")
        packet = (EVIDENCE / "blind" / "judge-1-packet.md").read_text(encoding="utf-8")
        for task in ("T1", "T2", "T3"):
            self.assertIn(f"## {task}", tasks)
            for label in ("A", "B", "C"):
                self.assertIn(f"## {task}-{label}", packet)
        for judge in ("judge-1", "judge-2"):
            verdict = (EVIDENCE / "blind" / f"{judge}-verdict.md").read_text(encoding="utf-8")
            self.assertIn("PASS", verdict)
            self.assertIn("FAIL", verdict)
            self.assertIn("篇幅", verdict)

    def test_repair_is_pre_registered_as_one_shot(self) -> None:
        plan = (EVIDENCE / "repair-plan.md").read_text(encoding="utf-8")
        for marker in ("只生成一份新的候选 T1", "不重复采样", "唯一复测失败"):
            self.assertIn(marker, plan)

    def test_repair_blind_map_and_verdicts_are_complete(self) -> None:
        mapping = json.loads((EVIDENCE / "blind" / "repair-map.json").read_text(encoding="utf-8"))
        expected = {"baseline", "candidate-repair", "no-skill"}
        for judge in ("repair-judge-3", "repair-judge-4"):
            self.assertEqual(expected, set(mapping[judge].values()))
            verdict = (EVIDENCE / "blind" / f"{judge}-verdict.md").read_text(encoding="utf-8")
            self.assertIn("PASS", verdict)
            self.assertIn("FAIL", verdict)


if __name__ == "__main__":
    unittest.main()
