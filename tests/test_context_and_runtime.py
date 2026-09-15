import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "chinese-academic-writing-assistant"
CASES_PATH = ROOT / "tests" / "fixtures" / "academic-smoke.jsonl"


def load_cases() -> list[dict]:
    return [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class ContextAndRuntimeTests(unittest.TestCase):
    def test_runtime_directory_has_expected_files(self) -> None:
        actual = {
            path.relative_to(SKILL_DIR).as_posix()
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
        }
        expected = {
            "LICENSE.md",
            "SKILL.md",
            "agents/openai.yaml",
            "references/academic-writing.md",
            "references/academic-proposal.md",
            "references/academic-literature-review.md",
            "references/anti-ai-writing.md",
            "references/citation-research.md",
            "references/long-form-consistency.md",
            "scripts/citation_audit.py",
            "scripts/manuscript_audit.py",
            "scripts/prose_lint.py",
        }
        self.assertEqual(expected, actual)

    def test_fixture_has_twelve_unique_core_cases(self) -> None:
        cases = load_cases()
        ids = [case["id"] for case in cases]
        self.assertEqual(12, len(cases))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            {"A01", "A02", "A03", "P01", "P02", "L01", "L02", "R01", "X01", "X02", "X03", "X04"},
            set(ids),
        )

    def test_legacy_fixture_schema(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
