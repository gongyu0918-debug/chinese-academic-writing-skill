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
        self.assertGreater(len(fields["description"]), 40)

    def test_openai_metadata_uses_new_invocation_name(self) -> None:
        self.assertIn('display_name: "中文论文助手"', self.openai)
        self.assertIn("$chinese-academic-writing-assistant", self.openai)
        self.assertNotRegex(
            self.openai,
            r"\$chinese-academic-writing(?!-assistant)",
        )

    def test_four_dimensional_route_and_nested_routes_are_explicit(self) -> None:
        for marker in (
            "最终交付物 × 操作模式 × 材料状态 × 研究阶段",
            "普通论文或论文中的文献综述章节",
            "开题报告及其中的研究现状、研究述评",
            "最终交付物本身为独立文献综述",
            "每个原子任务只读取一个专项叶",
        ):
            self.assertIn(marker, self.skill)

    def test_material_gates_are_explicit(self) -> None:
        for marker in (
            "无目标文本不能执行底稿修改",
            "只有题目时，不形成完整论文或完整开题设计",
            "常识性判断都不是事实证据",
            "不预选统计检验、结果方向、显著性表达或因果模板",
            "独立综述没有可用来源且用户未授权检索时，不写综述正文",
            "未完整读取时明确已覆盖和未覆盖部分",
        ):
            self.assertIn(marker, self.skill)

    def test_evidence_and_citation_contract_is_explicit(self) -> None:
        for marker in (
            "材料 ID、来源层级",
            "已读原文",
            "已读摘要",
            "仅有元数据",
            "待核验来源",
            "来源是否存在、元数据是否一致、原文是否支持当前论断、著录格式是否符合要求",
            "DOI 存在不等于论点获得支持",
        ):
            self.assertIn(marker, self.skill)

    def test_integrity_standards_and_review_interface_are_explicit(self) -> None:
        for marker in (
            "不得代写整篇提交稿",
            "GB/T 7714-2025",
            "GB/T 7713.1-2025",
            "不得声称“完全符合”",
            "位置—严重度—问题—依据—修改建议",
        ):
            self.assertIn(marker, self.skill)

    def test_optional_post_text_suggestion_categories_are_complete(self) -> None:
        categories = {"可补充论点", "可补充论据", "可补充论述", "其他修改建议"}
        for category in categories:
            self.assertIn(category, self.skill)
            for content in self.references.values():
                self.assertIn(category, content)
        self.assertIn("按实际需要给出", self.skill)
        self.assertIn("没有实际建议的类别不输出", self.skill)

    def test_leaf_specific_contracts_exist_without_global_rule_copies(self) -> None:
        self.assertEqual(
            {
                "academic-writing.md",
                "academic-proposal.md",
                "academic-literature-review.md",
            },
            set(self.references),
        )
        writing = self.references["academic-writing.md"]
        proposal = self.references["academic-proposal.md"]
        review = self.references["academic-literature-review.md"]
        for marker in ("单段润色", "段落主导任务", "摘要与结论"):
            self.assertIn(marker, writing)
        for marker in ("已有基础", "拟开展工作", "预期结果", "三种模式"):
            self.assertIn(marker, proposal)
        for marker in ("不补行业趋势", "不先替后续材料分类"):
            self.assertIn(marker, proposal)
        for marker in ("来源覆盖表", "普通叙述性综述", "PRISMA", "三种模式"):
            self.assertIn(marker, review)
        for marker in ("实际使用来源", "提及但未用于观点", "静默遗漏"):
            self.assertIn(marker, review)
        for content in self.references.values():
            self.assertNotIn("默认不扩展检索", content)
            self.assertNotIn("位置—严重度—问题—依据—修改建议", content)
            self.assertNotIn("GB/T 7714", content)

    def test_runtime_prompt_has_no_version_or_legacy_invocation(self) -> None:
        runtime = self.skill + self.openai + "".join(self.references.values())
        self.assertNotIn("0.0.1", runtime)
        self.assertIsNone(
            re.search(r"\$chinese-academic-writing(?!-assistant)", runtime)
        )


if __name__ == "__main__":
    unittest.main()
