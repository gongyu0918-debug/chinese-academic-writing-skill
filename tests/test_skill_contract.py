import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "chinese-academic-writing-assistant"
SKILL_PATH = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
REFERENCE_DIR = SKILL_DIR / "references"


def parse_frontmatter(text: str) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    _, frontmatter, _ = normalized.split("---\n", 2)
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line: {line!r}")
        fields[key.strip()] = value.strip()
    return fields


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.openai = OPENAI_YAML.read_text(encoding="utf-8")
        cls.references = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(REFERENCE_DIR.glob("*.md"))
        }

    def test_frontmatter_has_only_name_and_description(self) -> None:
        fields = parse_frontmatter(self.skill)
        self.assertEqual({"name", "description"}, set(fields))
        self.assertEqual("chinese-academic-writing-assistant", fields["name"])
        self.assertTrue(fields["description"].strip())

    def test_openai_metadata_uses_new_invocation_name(self) -> None:
        self.assertIn('display_name: "中文论文写作"', self.openai)
        self.assertIn("$chinese-academic-writing-assistant", self.openai)
        self.assertNotRegex(
            self.openai,
            r"\$chinese-academic-writing(?!-assistant)",
        )

    def test_runtime_has_no_legacy_invocation_identifier(self) -> None:
        runtime = self.skill + self.openai + "".join(self.references.values())
        self.assertIsNone(
            re.search(r"\$chinese-academic-writing(?!-assistant)", runtime)
        )


if __name__ == "__main__":
    unittest.main()
