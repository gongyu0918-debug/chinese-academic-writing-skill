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
