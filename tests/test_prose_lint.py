import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "chinese-academic-writing-assistant" / "scripts" / "prose_lint.py"
SPEC = importlib.util.spec_from_file_location("academic_prose_lint", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load prose_lint.py")
LINT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINT
SPEC.loader.exec_module(LINT)


def pattern_ids(findings: list) -> set[str]:
    return {finding.pattern_id for finding in findings}


class ProseLintTests(unittest.TestCase):
    def test_semantic_patterns_are_candidates_not_hard_failures(self) -> None:
        text = (
            "本研究不是为了否定既有研究，而是讨论样本中的空间选择。"
            "这一变化不仅影响座位选择，而且影响停留时间。"
            "分析一方面关注设施，另一方面关注交往。"
        )
        findings = LINT.scan("draft.md", text)
        self.assertTrue({"not-but", "not-only", "two-sides"}.issubset(pattern_ids(findings)))
        self.assertTrue(all(item.severity == "low" for item in findings))
        self.assertEqual(text, text[:])

    def test_quotes_formulas_citations_and_references_are_protected(self) -> None:
        text = (
            "受访者原话为：“这不是距离问题，而是时间问题。此外，此外，此外。”[1]\n"
            "关系式 $A不是B而是C$ 与 \\cite{zhang2024} 保持原样。\n"
            "参考文献\n"
            "[1] 张三. 此外此外此外的研究[J]. 2024.\n"
        )
        findings = LINT.scan("protected.md", text, include_format=True, include_structure=True)
        self.assertNotIn("not-but", pattern_ids(findings))
        self.assertNotIn("space-before-punctuation", pattern_ids(findings))
        self.assertFalse(any(item.pattern_id == "term-discourse-marker" for item in findings))
        self.assertFalse(any(item.severity == "high" for item in findings))

    def test_frequency_counts_visible_body_without_forcing_replacement(self) -> None:
        text = "此外，材料支持甲。\n此外，材料支持乙。\n此外，材料支持丙。"
        findings = LINT.scan("frequency.md", text)
        item = next(finding for finding in findings if finding.match == "此外")
        self.assertEqual(3, item.count)
        self.assertEqual("low", item.severity)
        self.assertIn("不按阈值自动换词", item.advice)

    def test_body_with_suggestions_excludes_suggestion_term_frequency(self) -> None:
        text = (
            "研究结果与材料一致。\n\n"
            "## 补充与修改建议\n"
            "此外可补访谈材料。此外可补来源。此外可补定义。此外可补限制。"
        )
        findings = LINT.scan("suggestions.md", text, delivery_mode="body-with-suggestions")
        self.assertFalse(any(item.match == "此外" for item in findings))
        self.assertFalse(any(item.severity == "high" for item in findings))

    def test_delivery_residues_have_three_independent_variants(self) -> None:
        variants = (
            "以下为修改后的正文：研究结果见表1。",
            "本稿为给领导看的修改版。",
            "当前文本已经通过内容门禁和内部校验。",
        )
        for text in variants:
            with self.subTest(text=text):
                findings = LINT.scan("delivery.md", text, delivery_mode="body-only")
                self.assertTrue(any(item.severity == "high" for item in findings))

    def test_legitimate_academic_terms_and_suggestion_heading_are_not_residues(self) -> None:
        text = "本研究讨论内部效度与外部效度。\n\n## 补充与修改建议\n可补充访谈记录。"
        findings = LINT.scan("clean.md", text, delivery_mode="body-with-suggestions")
        self.assertFalse(any(item.category == "production-residue" for item in findings))

    def test_protected_urls_and_paths_do_not_hide_following_prose_three_variants(self) -> None:
        variants = (
            ("来源见https://example.com。以下为修改后的正文。", "delivery-preface"),
            ("数据见https://example.com/a；当前文本已经通过内容门禁。", "internal-gate"),
            ("投入/产出比不是唯一指标，而是综合指标之一。", "not-but"),
        )
        for text, expected in variants:
            with self.subTest(text=text):
                self.assertIn(expected, pattern_ids(LINT.scan("protected-boundary.md", text)))

    def test_legitimate_academic_context_is_not_high_residue(self) -> None:
        variants = (
            "训练集与测试样本分别包含80条和20条记录。",
            "实验对象通过门禁进入观察区。",
            "实验文本由AI生成，再由两名编码员盲审。",
            "本研究采用焦虑量表中文版的修改版。",
            "附录提供访谈语料脱敏版。",
        )
        for text in variants:
            with self.subTest(text=text):
                findings = LINT.scan("academic-context.md", text, delivery_mode="body-only")
                self.assertFalse(any(item.severity == "high" for item in findings))

    def test_scanning_resumes_after_references_for_three_post_sections(self) -> None:
        variants = (
            ("附录A", "以下为修改后的正文。", "delivery-preface"),
            ("致谢", "当前文本已经通过内容门禁。", "internal-gate"),
            ("后记", "本稿为给领导看的修改版。", "version-audience-label"),
        )
        for heading, residue, expected in variants:
            with self.subTest(heading=heading):
                text = f"正文。\n参考文献\n[1] 张三. 论文题名。\n{heading}\n{residue}"
                self.assertIn(expected, pattern_ids(LINT.scan("post-reference.md", text)))

    def test_format_and_structure_candidates_are_reported(self) -> None:
        text = (
            "研究结果显示甲组变化稳定。。研究,结果仍需结合样本解释（\n\n"
            "研究结果显示第一组样本主要关注空间距离和到达时间。\n\n"
            "研究结果显示第二组样本主要关注空间距离和到达时间。\n\n"
            "研究结果显示第三组样本主要关注空间距离和到达时间。"
        )
        findings = LINT.scan("structure.md", text, include_format=True, include_structure=True)
        ids = pattern_ids(findings)
        self.assertIn("repeated-punctuation", ids)
        self.assertIn("halfwidth-cn-punctuation", ids)
        self.assertIn("unbalanced-pair", ids)
        self.assertIn("repeated-paragraph-start", ids)

    def test_review_only_does_not_treat_quoted_problem_text_as_own_style(self) -> None:
        text = "| 位置 | 问题 |\n| --- | --- |\n| 第1段 | “不是甲，而是乙”缺少对照依据 |"
        findings = LINT.scan("review.md", text, delivery_mode="review-only")
        self.assertNotIn("not-but", pattern_ids(findings))

    def test_docx_reads_only_main_body(self) -> None:
        header = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:p><w:r><w:t>以下为修改后的正文</w:t></w:r></w:p></w:hdr>'
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, body in enumerate(
                (
                    "以下为修改后的正文",
                    "本研究不是甲，而是乙",
                    "相关研究表明结论",
                ),
                start=1,
            ):
                with self.subTest(body=body):
                    document = (
                        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                        f'<w:body><w:p><w:r><w:t>{body}</w:t></w:r></w:p></w:body></w:document>'
                    )
                    path = Path(directory) / f"sample-{index}.docx"
                    with zipfile.ZipFile(path, "w") as archive:
                        archive.writestr("word/document.xml", document)
                        archive.writestr("word/header1.xml", header)
                    content = LINT.read_docx(path)
                    findings = LINT.scan(str(path), content)
                    self.assertIn(body, content)
                    self.assertNotIn("以下为修改后的正文", content if body != "以下为修改后的正文" else "")
                    self.assertTrue(findings)
                    self.assertEqual(1, findings[0].line)

    def test_cli_is_read_only_json_capable_and_strict_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("本研究不是为了否定原研究，而是限定材料范围。", encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            normal = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after_normal = hashlib.sha256(path.read_bytes()).hexdigest()
            low_strict = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--strict"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after_low_strict = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_text("以下为修改后的正文。", encoding="utf-8")
            high_before = hashlib.sha256(path.read_bytes()).hexdigest()
            high_strict = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--strict"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after_high_strict = hashlib.sha256(path.read_bytes()).hexdigest()

        self.assertEqual(0, normal.returncode, normal.stderr)
        self.assertIsInstance(json.loads(normal.stdout), list)
        self.assertEqual(0, low_strict.returncode)
        self.assertEqual(1, high_strict.returncode)
        self.assertEqual(before, after_normal)
        self.assertEqual(before, after_low_strict)
        self.assertEqual(high_before, after_high_strict)

    def test_missing_file_returns_controlled_error(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT_PATH), "definitely-missing-file.md"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("文件不存在", result.stderr)


if __name__ == "__main__":
    unittest.main()
