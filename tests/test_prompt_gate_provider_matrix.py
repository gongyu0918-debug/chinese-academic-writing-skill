import importlib.util
import json
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

    def test_replication_and_route_schedules_are_explicit(self):
        replication = MODULE.schedule(("CUMULATIVE_DRAFT_R2", "CITATION_STOP_R2"))
        routes = MODULE.schedule(
            (
                "LONGFORM_OUTLINE",
                "LONGFORM_CROSS_TURN",
                "ANTI_AI_OUTLINE",
                "ANTI_AI_REVIEW",
            )
        )
        self.assertEqual(12, len(replication))
        self.assertEqual(12, len(routes))
        self.assertEqual({"river"}, {row["arm"] for row in routes})

    def test_pair_order_is_balanced_across_providers(self):
        rows = MODULE.schedule()
        by_provider = {provider.name: [] for provider in MODULE.PROVIDERS}
        for row in rows:
            if row["task_id"] == "PERSIST_UNAUTHORIZED":
                by_provider[row["provider"]].append(row["arm"])
        self.assertEqual(["maple", "river"], by_provider["alibaba"])
        self.assertEqual(["river", "maple"], by_provider["ollama"])
        self.assertEqual(["maple", "river"], by_provider["minimax"])

    def test_filtered_persistence_schedule_has_nine_calls(self):
        rows = MODULE.schedule(("PERSIST_UNAUTHORIZED", "PERSIST_AUTHORIZED"))
        self.assertEqual(9, len(rows))
        self.assertEqual(
            {"PERSIST_UNAUTHORIZED", "PERSIST_AUTHORIZED"},
            {row["task_id"] for row in rows},
        )

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
            json.dumps(
                {
                    "item": {
                        "type": "command_execution",
                        "command": command,
                        "exit_code": 0,
                        "status": "completed",
                    }
                }
            )
            for command in (
                "pwsh -Command \"Get-Content -Raw -LiteralPath 'skill\\SKILL.md'\"",
                "pwsh -Command \"Get-Content -Raw -LiteralPath 'skill\\references\\academic-writing.md'\"",
            )
        )
        self.assertEqual(
            ["SKILL.md", "references/academic-writing.md"],
            MODULE.observed_reads(trace, skill_files),
        )

    def test_observed_reads_supports_absolute_windows_path_and_rejects_failed_read(self):
        skill_files = ("SKILL.md", "references/academic-writing.md")
        trace = "\n".join(
            json.dumps(
                {
                    "item": {
                        "type": "command_execution",
                        "command": command,
                        "exit_code": exit_code,
                        "status": "completed",
                    }
                }
            )
            for command, exit_code in (
                (
                    "pwsh -Command \"Get-Content -LiteralPath 'F:\\run\\skill\\SKILL.md' -Raw\"",
                    0,
                ),
                (
                    "pwsh -Command \"Get-Content -LiteralPath 'skill/references/academic-writing.md' -Raw\"",
                    1,
                ),
            )
        )
        self.assertEqual(["SKILL.md"], MODULE.observed_reads(trace, skill_files))

    def test_observed_reads_supports_cat_and_direct_get_content(self):
        skill_files = ("SKILL.md", "references/citation-research.md")
        trace = "\n".join(
            [
                '{"item":{"type":"command_execution","command":"pwsh -Command \'cat skill/SKILL.md\'","exit_code":0,"status":"completed"}}',
                '{"item":{"type":"command_execution","command":"pwsh -Command \'Get-Content skill/references/citation-research.md -Raw\'","exit_code":0,"status":"completed"}}',
            ]
        )
        self.assertEqual(list(skill_files), MODULE.observed_reads(trace, skill_files))

    def test_observed_reads_rejects_echo_and_compound_commands(self):
        skill_files = ("SKILL.md",)
        trace = "\n".join(
            [
                '{"item":{"type":"command_execution","command":"pwsh -Command \'Write-Output skill/SKILL.md\'","exit_code":0,"status":"completed"}}',
                '{"item":{"type":"command_execution","command":"pwsh -Command \'Get-Content skill/SKILL.md; Write-Output done\'","exit_code":0,"status":"completed"}}',
            ]
        )
        self.assertEqual([], MODULE.observed_reads(trace, skill_files))

    def test_bypass_scope_rejects_non_persistence_task(self):
        MODULE.ISOLATED_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODULE.ISOLATED_ROOT) as directory:
            root = Path(directory)
            maple = root / "maple"
            river = root / "river"
            maple.mkdir()
            river.mkdir()
            with self.assertRaises(SystemExit):
                MODULE.validate_bypass_scope(
                    True,
                    root / "out",
                    {"maple": maple, "river": river},
                    ("CUMULATIVE_DRAFT",),
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
