import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "chinese-academic-writing-assistant"
SKILL_PATH = SKILL_DIR / "SKILL.md"
REFERENCE_DIR = SKILL_DIR / "references"
CASES_PATH = ROOT / "tests" / "fixtures" / "academic-smoke.jsonl"


def unicode_length(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").replace("\r\n", "\n"))


def load_cases() -> list[dict]:
    return [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class ContextAndRuntimeTests(unittest.TestCase):
    def test_runtime_directory_has_exactly_seven_files(self) -> None:
        actual = {
            path.relative_to(SKILL_DIR).as_posix()
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
        }
        expected = {
            "SKILL.md",
            "agents/openai.yaml",
            "references/academic-writing.md",
            "references/academic-proposal.md",
            "references/academic-literature-review.md",
            "references/anti-ai-writing.md",
            "scripts/prose_lint.py",
        }
        self.assertEqual(expected, actual)

    def test_entry_and_single_leaf_stay_within_character_budget(self) -> None:
        entry_length = unicode_length(SKILL_PATH)
        self.assertLessEqual(entry_length, 4_000)
        for leaf in REFERENCE_DIR.glob("*.md"):
            with self.subTest(leaf=leaf.name):
                self.assertLessEqual(entry_length + unicode_length(leaf), 8_000)

    def test_entry_task_leaf_and_anti_ai_layer_stay_within_runtime_budget(self) -> None:
        entry_length = unicode_length(SKILL_PATH)
        anti_ai_length = unicode_length(REFERENCE_DIR / "anti-ai-writing.md")
        for name in (
            "academic-writing.md",
            "academic-proposal.md",
            "academic-literature-review.md",
        ):
            with self.subTest(leaf=name):
                self.assertLessEqual(
                    entry_length + unicode_length(REFERENCE_DIR / name) + anti_ai_length,
                    8_000,
                )

    def test_leaf_bodies_do_not_embed_other_leaf_files(self) -> None:
        for leaf in REFERENCE_DIR.glob("*.md"):
            with self.subTest(leaf=leaf.name):
                self.assertNotIn("references/", leaf.read_text(encoding="utf-8"))

    def test_fixture_has_twelve_unique_core_cases(self) -> None:
        cases = load_cases()
        ids = [case["id"] for case in cases]
        self.assertEqual(12, len(cases))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            {"A01", "A02", "A03", "P01", "P02", "L01", "L02", "R01", "X01", "X02", "X03", "X04"},
            set(ids),
        )

    def test_short_review_minimum_does_not_reward_filler(self) -> None:
        cases = load_cases()
        l01 = next(case for case in cases if case["id"] == "L01")
        self.assertEqual("short-review", l01["scope"])
        self.assertEqual(150, l01["minimum_output_chars"])

    def test_fixture_schema_and_route_mapping(self) -> None:
        expected_reference = {
            "ordinary-paper": "references/academic-writing.md",
            "proposal": "references/academic-proposal.md",
            "independent-literature-review": "references/academic-literature-review.md",
            "out-of-scope": None,
        }
        required = {
            "id",
            "prompt",
            "artifact",
            "expected_route",
            "expected_reference",
            "expected_mode",
            "material_state",
            "research_stage",
            "output_protocol",
            "scope",
            "minimum_output_chars",
            "immutable_literals",
            "required_markers",
            "forbidden_claims",
            "allowed_degradation",
        }
        for case in load_cases():
            with self.subTest(case=case["id"]):
                self.assertTrue(required.issubset(case))
                self.assertEqual(
                    expected_reference[case["expected_route"]],
                    case["expected_reference"],
                )
                self.assertTrue(case["prompt"].strip())
                self.assertIsInstance(case["minimum_output_chars"], int)
                self.assertGreater(case["minimum_output_chars"], 0)
                for key in (
                    "immutable_literals",
                    "required_markers",
                    "forbidden_claims",
                    "allowed_degradation",
                ):
                    self.assertIsInstance(case[key], list)

    def test_fixture_covers_modes_material_states_and_protocols(self) -> None:
        cases = load_cases()
        modes = {case["expected_mode"] for case in cases}
        states = {case["material_state"] for case in cases}
        protocols = {case["output_protocol"] for case in cases}
        self.assertTrue({"outline", "draft", "revise", "review-only"}.issubset(modes))
        self.assertIn("title-only", states)
        self.assertIn("no-sources", states)
        self.assertIn("no-target-text", states)
        self.assertIn("no-data", states)
        self.assertIn("revised-text-only", protocols)
        self.assertIn("review-table-only", protocols)
        self.assertIn("safe-degradation", protocols)


if __name__ == "__main__":
    unittest.main()
