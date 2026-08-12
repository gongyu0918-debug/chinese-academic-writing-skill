import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).parent
    / "evidence"
    / "prompt-gates-20260812"
    / "run_provider_matrix.py"
)
SPEC = importlib.util.spec_from_file_location("prompt_gate_provider_matrix", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PromptGateProviderMatrixTests(unittest.TestCase):
    def test_schedule_is_three_provider_twenty_one_call_matrix(self):
        rows = MODULE.schedule()
        self.assertEqual(21, len(rows))
        self.assertEqual(3, len({row["provider"] for row in rows}))
        self.assertEqual(3, sum(row["task_id"] == "PERSIST_AUTHORIZED" for row in rows))
        self.assertEqual(6, sum(row["task_id"] == "PERSIST_UNAUTHORIZED" for row in rows))
        self.assertEqual(6, sum(row["task_id"] == "CUMULATIVE_DRAFT" for row in rows))
        self.assertEqual(6, sum(row["task_id"] == "CITATION_STOP" for row in rows))

    def test_pair_order_is_balanced_across_providers(self):
        rows = MODULE.schedule()
        by_provider = {provider.name: [] for provider in MODULE.PROVIDERS}
        for row in rows:
            if row["task_id"] == "PERSIST_UNAUTHORIZED":
                by_provider[row["provider"]].append(row["arm"])
        self.assertEqual(["maple", "river"], by_provider["alibaba"])
        self.assertEqual(["river", "maple"], by_provider["ollama"])
        self.assertEqual(["maple", "river"], by_provider["minimax"])

    def test_skill_fingerprint_binds_relative_paths_and_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "SKILL.md").write_text("one", encoding="utf-8")
            (root / "nested" / "leaf.md").write_text("two", encoding="utf-8")
            before = MODULE.skill_fingerprint(root)
            (root / "nested" / "leaf.md").write_text("changed", encoding="utf-8")
            self.assertNotEqual(before, MODULE.skill_fingerprint(root))

    def test_observed_reads_reports_each_exact_skill_relative_path(self):
        skill_files = ("SKILL.md", "references/academic-writing.md", "references/other.md")
        trace = "\n".join(
            [
                '{"item":{"type":"command_execution","command":"Get-Content -Raw -LiteralPath \'skill\\\\SKILL.md\'"}}',
                '{"item":{"type":"command_execution","command":"Get-Content -Raw -LiteralPath \'skill\\\\references\\\\academic-writing.md\'"}}',
            ]
        )
        self.assertEqual(
            ["SKILL.md", "references/academic-writing.md"],
            MODULE.observed_reads(trace, skill_files),
        )

    def test_build_prompt_does_not_expose_arm_or_expected_behavior(self):
        prompt = MODULE.build_prompt("用户请求")
        self.assertNotIn("maple", prompt.casefold())
        self.assertNotIn("river", prompt.casefold())
        self.assertNotIn("candidate", prompt.casefold())
        self.assertNotIn("baseline", prompt.casefold())
        self.assertNotIn("academic-writing.md", prompt)
        self.assertNotIn("long-form-consistency.md", prompt)


if __name__ == "__main__":
    unittest.main()
