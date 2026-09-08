import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "chinese-academic-writing-assistant" / "scripts"
SCRIPT_PATH = SCRIPT_DIR / "manuscript_audit.py"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("academic_manuscript_audit", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load manuscript_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def finding_codes(report: dict) -> set[str]:
    return {item["code"] for item in report["findings"]}


class ManuscriptAuditTests(unittest.TestCase):
    def test_cross_file_candidates_and_latex_errors_are_separated(self) -> None:
        repeated = "这一段用于核对跨章节完全重复内容。" * 8
        report = AUDIT.analyze(
            [
                ("chapter1.md", f"学习分析系统使用 LA 完成处理。\n\n{repeated}\n\\label{{fig:one}}"),
                ("chapter2.md", f"学习分析平台（LA）进入后续讨论。\n\n{repeated}\n\\ref{{fig:missing}}\n\\label{{fig:one}}"),
            ],
            term_groups=[("学习分析系统", "学习分析平台")],
            abbreviations=["LA"],
        )
        codes = finding_codes(report)
        self.assertIn("duplicate-paragraph-candidate", codes)
        self.assertIn("term-variant-group", codes)
        self.assertIn("abbreviation-before-definition-candidate", codes)
        self.assertIn("duplicate-latex-label", codes)
        self.assertIn("missing-latex-label", codes)
        severities = {item["code"]: item["severity"] for item in report["findings"]}
        self.assertEqual("medium", severities["duplicate-paragraph-candidate"])
        self.assertEqual("high", severities["missing-latex-label"])

    def test_term_and_abbreviation_checks_are_opt_in(self) -> None:
        report = AUDIT.analyze([("draft.md", "甲术语与乙术语同时出现，ABC 尚未定义。")])
        codes = finding_codes(report)
        self.assertNotIn("term-variant-group", codes)
        self.assertNotIn("undefined-abbreviation-candidate", codes)

    def test_same_line_abbreviation_before_definition_is_reported(self) -> None:
        report = AUDIT.analyze(
            [("draft.md", "LA 用于处理数据，后文称学习分析系统（LA）。")],
            abbreviations=["LA"],
        )
        self.assertIn("abbreviation-before-definition-candidate", finding_codes(report))

    def test_nested_term_variants_do_not_double_count_one_occurrence(self) -> None:
        report = AUDIT.analyze(
            [("draft.md", "学习分析系统用于记录。")],
            term_groups=[("学习分析系统", "分析系统")],
        )
        self.assertNotIn("term-variant-group", finding_codes(report))

    def test_latex_comments_and_code_are_ignored_but_reference_variants_are_checked(self) -> None:
        text = (
            "% \\ref{comment-only}\n"
            "```tex\n\\ref{fenced-only}\n```\n"
            "\\begin{verbatim}\\ref{verbatim-only}\\end{verbatim}\n"
            "正文见\\pageref{page:missing}、\\nameref{name:missing}和\\cref{fig:one,fig:two}。\n"
            "\\label{fig:one}\n\\label{fig:two}"
        )
        report = AUDIT.analyze([("draft.tex", text)])
        missing = {
            item["excerpt"]
            for item in report["findings"]
            if item["code"] == "missing-latex-label"
        }
        self.assertEqual({"page:missing", "name:missing"}, missing)

    def test_heading_without_blank_line_does_not_hide_duplicate_prose(self) -> None:
        repeated = "标题之后没有空行时，这一长段仍应进入完全重复候选检查。" * 6
        report = AUDIT.analyze(
            [("one.md", f"# 第一节\n{repeated}"), ("two.md", f"# 第二节\n{repeated}")]
        )
        self.assertIn("duplicate-paragraph-candidate", finding_codes(report))

    def test_longer_closing_fences_and_unclosed_blocks_hide_example_refs(self) -> None:
        for opening, closing in (("```tex", "````"), ("~~~tex", "~~~~"), ("```tex", "")):
            with self.subTest(opening=opening, closing=closing):
                text = f"正文见\\ref{{real-missing}}。\n{opening}\n\\ref{{example-only}}\n{closing}"
                findings = AUDIT.analyze([("draft.md", text)])["findings"]
                self.assertEqual(["real-missing"], [item["excerpt"] for item in findings])
                self.assertEqual(1, findings[0]["line"])

    def test_fence_marker_length_and_closing_suffix_preserve_boundaries(self) -> None:
        text = (
            "   ````tex\n\\ref{hidden-one}\n"
            "~~~\n```\n````not-a-close\n\\ref{hidden-two}\n"
            "  ````` \t\n正文见\\ref{real-missing}。\n"
        )
        findings = AUDIT.analyze([("draft.md", text)])["findings"]
        self.assertEqual(["real-missing"], [item["excerpt"] for item in findings])
        self.assertEqual(8, findings[0]["line"])

    def test_invalid_backtick_info_does_not_hide_following_prose(self) -> None:
        text = "```tex`invalid\n正文见\\ref{real-missing}。\n"
        findings = AUDIT.analyze([("draft.md", text)])["findings"]
        self.assertEqual(["real-missing"], [item["excerpt"] for item in findings])

    def test_fence_in_latex_literal_does_not_hide_following_real_reference(self) -> None:
        for environment, fence in (("verbatim", "```"), ("comment", "~~~"), ("minted", "```")):
            with self.subTest(environment=environment):
                text = f"\\begin{{{environment}}}\n{fence}\n\\end{{{environment}}}\n\\ref{{real}}"
                findings = AUDIT.analyze([("draft.md", text)])["findings"]
                self.assertEqual(["real"], [item["excerpt"] for item in findings])
                self.assertEqual(4, findings[0]["line"])

    def test_fake_latex_opener_in_fence_does_not_consume_following_literal(self) -> None:
        text = (
            "```tex\n\\begin{verbatim}\n```\n"
            "\\begin{verbatim}\n~~~\n\\end{verbatim}\n\\ref{real}"
        )
        findings = AUDIT.analyze([("draft.md", text)])["findings"]
        self.assertEqual(["real"], [item["excerpt"] for item in findings])
        self.assertEqual(7, findings[0]["line"])

    def test_commented_or_inline_latex_begin_does_not_disable_fence_protection(self) -> None:
        for prefix in ("% \\begin{verbatim}", "`\\begin{verbatim}`", "说明 `\\begin{comment}`"):
            with self.subTest(prefix=prefix):
                text = prefix + "\n~~~tex\n\\ref{example}\n~~~\n\\ref{real}"
                findings = AUDIT.analyze([("draft.md", text)])["findings"]
                self.assertEqual(["real"], [item["excerpt"] for item in findings])
                self.assertEqual(5, findings[0]["line"])

    def test_comment_character_in_literal_does_not_hide_next_environment(self) -> None:
        text = "\\begin{verbatim}%\\end{verbatim}\\begin{comment}\n~~~\n\\end{comment}\n\\ref{real}"
        findings = AUDIT.analyze([("draft.md", text)])["findings"]
        self.assertEqual(["real"], [item["excerpt"] for item in findings])
        self.assertEqual(4, findings[0]["line"])

    def test_fence_mask_preserves_offsets_for_lf_crlf_and_cr(self) -> None:
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=repr(newline)):
                text = newline.join(("~~~tex", "\\ref{hidden}", "~~~~", "正文\\ref{missing}"))
                masked = AUDIT.mask_fenced_code(text)
                self.assertEqual(len(text), len(masked))
                self.assertEqual(text.count(newline), masked.count(newline))
                self.assertNotIn("hidden", masked)
                self.assertIn("missing", masked)

    def test_strict_cli_ignores_fenced_examples_but_checks_following_prose(self) -> None:
        example = "~~~tex\n\\ref{example-only}\n~~~~\n"
        for text, expected in ((example, 0), (example + "\\ref{real-missing}", 1)):
            with self.subTest(expected=expected):
                result = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT_PATH), "-", "--json", "--strict"],
                    input=text, capture_output=True, text=True, encoding="utf-8", check=False,
                )
                self.assertEqual(expected, result.returncode, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(expected, report["summary"]["findings"])

    def test_strict_only_fails_high_structural_findings(self) -> None:
        repeated = "用于测试的完全重复长段。" * 10
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "one.md"
            second = root / "two.md"
            first.write_text(repeated, encoding="utf-8")
            second.write_text(repeated, encoding="utf-8")
            candidate = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(first), str(second), "--strict"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            second.write_text(repeated + "\n\\ref{missing}", encoding="utf-8")
            structural = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(first), str(second), "--strict"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(0, candidate.returncode, candidate.stderr)
        self.assertEqual(1, structural.returncode, structural.stderr)

    def test_cli_is_json_report_only_and_rejects_fix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "draft.md"
            draft.write_text("学习分析系统（LA）用于本节。", encoding="utf-8")
            before_hash = hashlib.sha256(draft.read_bytes()).hexdigest()
            before_listing = sorted(path.name for path in root.iterdir())
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(draft), "--abbreviation", "LA", "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            fix = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(draft), "--fix"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after_hash = hashlib.sha256(draft.read_bytes()).hexdigest()
            after_listing = sorted(path.name for path in root.iterdir())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIsInstance(json.loads(result.stdout), dict)
        self.assertNotEqual(0, fix.returncode)
        self.assertIn("unrecognized arguments", fix.stderr)
        self.assertEqual(before_hash, after_hash)
        self.assertEqual(before_listing, after_listing)


if __name__ == "__main__":
    unittest.main()
