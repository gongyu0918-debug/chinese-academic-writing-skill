import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "chinese-academic-writing-assistant" / "scripts"
SCRIPT_PATH = SCRIPT_DIR / "citation_audit.py"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("academic_citation_audit", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load citation_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def finding_codes(report: dict) -> set[str]:
    return {item["code"] for item in report["findings"]}


class CitationAuditTests(unittest.TestCase):
    def test_claim_coverage_reports_n_over_m_without_default_pass_quota(self) -> None:
        text = (
            "已有研究表明检索练习有助于延迟测验表现[1]。\n"
            "这种方法显著提高所有学习者的长期成绩。\n"
            "参考文献\n[1] 张三. 检索练习研究[J]. 2024."
        )
        report = AUDIT.analyze(text, mode="literature-review")
        self.assertEqual(2, report["summary"]["claim_candidates"])
        self.assertEqual(1, report["summary"]["cited_claim_candidates"])
        self.assertEqual(0.5, report["summary"]["claim_coverage"])
        self.assertIn("uncited-claim-candidate", finding_codes(report))
        self.assertNotIn("below-explicit-minimum", finding_codes(report))

    def test_explicit_minimum_only_affects_strict_when_user_supplies_it(self) -> None:
        text = "已有研究表明甲结论[1]。乙方法显著提高成绩。\n参考文献\n[1] 甲文献。"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text(text, encoding="utf-8")
            default = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--strict"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            explicit = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--strict", "--minimum-coverage", "0.8"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(0, default.returncode, default.stderr)
        self.assertEqual(1, explicit.returncode, explicit.stderr)
        self.assertIn("below-explicit-minimum", explicit.stdout)

    def test_numeric_mapping_duplicate_id_and_duplicate_doi_are_reported(self) -> None:
        text = (
            "研究表明甲结论[1,3]。\n参考文献\n"
            "[1] 甲. 题名. doi:10.1000/ABC.\n"
            "[1] 乙. 重复编号.\n"
            "[2] 丙. 另一题名. https://doi.org/10.1000/abc"
        )
        report = AUDIT.analyze(text)
        codes = finding_codes(report)
        self.assertIn("duplicate-reference-id", codes)
        self.assertIn("duplicate-doi", codes)
        self.assertIn("missing-reference-entry", codes)
        self.assertIn("unused-reference-entry", codes)

    def test_author_year_and_latex_count_as_coverage_without_fake_numeric_mapping(self) -> None:
        text = (
            "相关研究指出该效应受到任务难度影响（Li, 2022）。\n"
            "已有研究表明该结论仍有争议\\cite{wang2023}。"
        )
        report = AUDIT.analyze(text, mode="literature-review")
        self.assertEqual(["author-year", "latex"], report["summary"]["schemes"])
        self.assertEqual(2, report["summary"]["cited_claim_candidates"])
        self.assertIsNone(report["summary"]["numeric_reference_utilization"])
        self.assertNotIn("missing-reference-entry", finding_codes(report))

    def test_reference_section_and_markdown_links_are_not_body_citations(self) -> None:
        text = (
            "项目说明见[1](https://example.com)，尚未提出需要外部证据的结论。\n"
            "参考文献\n[1] 某研究表明该方法显著提高成绩。"
        )
        report = AUDIT.analyze(text)
        self.assertEqual(0, report["summary"]["citation_occurrences"])
        self.assertNotIn("numeric", report["summary"]["schemes"])
        self.assertIn("unused-reference-entry", finding_codes(report))
        self.assertNotIn("uncited-claim-candidate", finding_codes(report))

    def test_own_study_statements_are_not_forced_to_take_external_citations(self) -> None:
        variants = (
            "本研究采用访谈法分析十二份材料。",
            "本文发现样本中的修订次数为三次。",
            "我们通过编码比较两组材料。",
        )
        for text in variants:
            with self.subTest(text=text):
                report = AUDIT.analyze(text, mode="proposal")
                self.assertEqual(0, report["summary"]["claim_candidates"])

    def test_cli_is_read_only_for_markdown_docx_and_stdin_and_rejects_fix(self) -> None:
        document_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>已有研究表明甲结论[1]。</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>参考文献</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>[1] 甲文献。</w:t></w:r></w:p></w:body></w:document>'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markdown = root / "draft.md"
            markdown.write_text("已有研究表明甲结论[1]。\n参考文献\n[1] 甲文献。", encoding="utf-8")
            docx = root / "draft.docx"
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (markdown, docx)}
            before_listing = sorted(path.name for path in root.iterdir())
            for path in (markdown, docx):
                result = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIsInstance(json.loads(result.stdout), list)
            stdin_result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), "-", "--json"],
                input="已有研究表明甲结论[1]。\n参考文献\n[1] 甲文献。",
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            fix_result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(markdown), "--fix"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (markdown, docx)}
            after_listing = sorted(path.name for path in root.iterdir())
        self.assertEqual(0, stdin_result.returncode, stdin_result.stderr)
        self.assertNotEqual(0, fix_result.returncode)
        self.assertIn("unrecognized arguments", fix_result.stderr)
        self.assertEqual(before, after)
        self.assertEqual(before_listing, after_listing)

    def test_text_report_uses_plain_n_over_m_display(self) -> None:
        report = AUDIT.analyze("已有研究表明甲结论[1]。\n参考文献\n[1] 甲文献。")
        stream = io.StringIO()
        with redirect_stdout(stream):
            AUDIT.print_text_report(report)
        self.assertIn("(1/1)", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
