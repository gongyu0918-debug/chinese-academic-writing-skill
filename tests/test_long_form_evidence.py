import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests" / "evidence" / "v0.0.5-long-form"
FORWARD = EVIDENCE / "forward"


class LongFormEvidenceTests(unittest.TestCase):
    def test_research_records_borrowed_and_rejected_patterns(self) -> None:
        research = (EVIDENCE / "RESEARCH.md").read_text(encoding="utf-8")
        for marker in (
            "SNL-UCSB paper-writing-skill",
            "RE-paper-writing",
            "Hermes research-paper-writing",
            "vibe-paper-writing",
            "academic-writing-agents",
            "不采用固定句长",
            "不调整段落生成规则",
        ):
            self.assertIn(marker, research)

    def test_full_review_finds_seeded_hard_and_global_conflicts(self) -> None:
        review = (FORWARD / "review-output.md").read_text(encoding="utf-8")
        for marker in (
            "研究问题与证据不闭合",
            "30个座位",
            "50名学生",
            "学习分析平台",
            "LA",
            "显著提升了学生的学习效率",
            "直接决定学生的选座行为",
            "所有学生",
            "相互矛盾",
            "整段复制绪论内容",
            "第一人称复数“我们”",
        ):
            self.assertIn(marker, review)

    def test_continuation_preserves_state_and_prompt_range(self) -> None:
        output = (FORWARD / "continuation-output.md").read_text(encoding="utf-8")
        visible_length = len(re.sub(r"\s+", "", output))
        self.assertGreaterEqual(visible_length, 450)
        self.assertLessEqual(visible_length, 600)
        for marker in (
            "2025年3月连续三个工作日晚间",
            "48名",
            "31个座位",
            "24个座位",
            "18人",
            "11人",
            "8人",
            "回答可以重叠",
            "学习分析系统",
            "尚不能说明",
        ):
            self.assertIn(marker, output)
        for forbidden in (
            "50名",
            "30个座位",
            "学习分析平台",
            "LA",
            "显著提升",
            "直接决定",
            "优先改造",
            "扩大系统应用",
            "我们证明",
            "# ",
        ):
            self.assertNotIn(forbidden, output)

    def test_baseline_comparison_does_not_claim_candidate_superiority(self) -> None:
        baseline = (FORWARD / "baseline-review-output.md").read_text(encoding="utf-8")
        report = (EVIDENCE / "REPORT.md").read_text(encoding="utf-8")
        for marker in (
            "核心问题与证据不闭合",
            "30个座位",
            "50名",
            "学习分析平台（LA）",
            "显著提升学习效率",
            "虽是否定句，仍预设已经存在区域差异",
        ):
            self.assertIn(marker, baseline)
        for marker in (
            "不能声称一次性全文审查优于旧基线",
            "仍需真正跨会话、跨学科的配对消融",
            "本轮不发布",
        ):
            self.assertIn(marker, report)


if __name__ == "__main__":
    unittest.main()
