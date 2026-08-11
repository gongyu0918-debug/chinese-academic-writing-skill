import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "chinese-academic-writing-assistant" / "scripts" / "prose_lint.py"
SPEC = importlib.util.spec_from_file_location("academic_prose_lint_final_body", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load prose_lint.py")
LINT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINT
SPEC.loader.exec_module(LINT)


def pattern_ids(findings: list) -> set[str]:
    return {finding.pattern_id for finding in findings}


def paragraph(seed: str, length: int = 52) -> str:
    base = f"围绕{seed}的调查表明，材料在对象、范围与方法上保持一致，并能够回查到原始记录。"
    while len(base.replace(" ", "")) < length:
        base += "该段落补充一项可核对的细节。"
    return base


class FinalBodyNegativeTailTests(unittest.TestCase):
    def test_unresolved_state_tail_flags_body_only_mode(self) -> None:
        text = "综上，现有解释尚未形成最终结论。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertIn("unresolved-state-tail", pattern_ids(findings))
        finding = next(item for item in findings if item.pattern_id == "unresolved-state-tail")
        self.assertEqual("medium", finding.severity)
        self.assertEqual("semantic-review", finding.category)

    def test_unresolved_state_tail_requires_sentence_final_position(self) -> None:
        text = "尚未形成定论的说法还有很多，需要继续核对材料。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertNotIn("unresolved-state-tail", pattern_ids(findings))

    def test_unresolved_state_tail_excludes_procedural_prefixes(self) -> None:
        text = "未对样本形成明确分组。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertNotIn("unresolved-state-tail", pattern_ids(findings))

    def test_protective_negative_inference_flags_generic_denial(self) -> None:
        text = "尚不能据此认定两者存在因果关系。现有数据无法作为判断依据。现有材料不足以作出判断。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        matches = [item for item in findings if item.pattern_id == "protective-negative-inference"]
        self.assertEqual(3, len(matches))

    def test_protective_negative_inference_locates_two_clauses_in_one_sentence(self) -> None:
        text = "该结果不能说明干预有效，也不能据此认定机制成立。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        match = next(item for item in findings if item.pattern_id == "protective-negative-inference")
        self.assertIn("不能说明", match.match)
        self.assertIn("不能据此认定", match.match)

    def test_protective_negative_inference_locates_adjacent_sentences(self) -> None:
        text = "该结果不能说明干预有效。现有材料也不能据此认定机制成立。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        matches = [item for item in findings if item.pattern_id == "protective-negative-inference"]
        self.assertEqual(2, len(matches))

    def test_necessary_negative_facts_are_not_protective_inference(self) -> None:
        text = "其余样本未发现同类现象，原始数据未发生缺失。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertNotIn("protective-negative-inference", pattern_ids(findings))

    def test_negative_boundary_tail_is_low_candidate(self) -> None:
        text = "两项指标存在相关，但这并不意味着存在因果关系。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        finding = next(item for item in findings if item.pattern_id == "negative-boundary-tail")
        self.assertEqual("low", finding.severity)
        self.assertIn("真实边界应保留", finding.advice)

    def test_negative_tails_do_not_load_outside_final_body_modes(self) -> None:
        text = (
            "综上，现有解释尚未形成最终结论。"
            "尚不能据此认定两者存在因果关系。"
            "两项指标存在相关，但这并不意味着存在因果关系。"
        )
        for mode in ("generic", "review-only"):
            findings = LINT.scan("draft.md", text, delivery_mode=mode)
            self.assertFalse(
                {"unresolved-state-tail", "protective-negative-inference", "negative-boundary-tail"}
                & pattern_ids(findings),
                f"mode {mode} must not load final-body patterns",
            )

    def test_body_with_suggestions_still_scans_body_area(self) -> None:
        text = "综上，现有解释尚未形成最终结论。\n\n## 补充与修改建议\n可补充变量说明。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-with-suggestions")
        self.assertIn("unresolved-state-tail", pattern_ids(findings))

    def test_quoted_material_is_not_scanned_as_final_body(self) -> None:
        text = "受访者记录写道：“目前还不能得出确定结果，尚未形成最终结论。”"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertNotIn("unresolved-state-tail", pattern_ids(findings))


class SignificanceTailClusterTests(unittest.TestCase):
    def clustered_text(self, hit_positions: tuple[int, ...]) -> str:
        blocks = []
        for index in range(5):
            body = paragraph(f"主题{index}")
            if index in hit_positions:
                body += "这为后续县域研究提供了理论支撑。"
            blocks.append(body)
        return "\n\n".join(blocks)

    def test_three_hits_within_window_trigger_cluster(self) -> None:
        text = self.clustered_text((0, 2, 4))
        findings = LINT.scan("draft.md", text, include_structure=True)
        finding = next(item for item in findings if item.pattern_id == "significance-tail-cluster")
        self.assertEqual("low", finding.severity)
        self.assertEqual(3, finding.count)

    def test_two_hits_do_not_trigger(self) -> None:
        text = self.clustered_text((1, 3))
        findings = LINT.scan("draft.md", text, include_structure=True)
        self.assertNotIn("significance-tail-cluster", pattern_ids(findings))

    def test_heading_between_hits_resets_window(self) -> None:
        text = (
            paragraph("主题甲") + "这为后续研究提供了理论支撑。"
            + "\n\n" + paragraph("主题乙") + "这为政策设计提供了参考。"
            + "\n\n## 新一节\n\n"
            + paragraph("主题丙") + "这为实践工作提供了基础。"
        )
        findings = LINT.scan("draft.md", text, include_structure=True)
        self.assertNotIn("significance-tail-cluster", pattern_ids(findings))

    def test_structure_flag_required(self) -> None:
        text = self.clustered_text((0, 2, 4))
        findings = LINT.scan("draft.md", text)
        self.assertNotIn("significance-tail-cluster", pattern_ids(findings))


class ExternalNoteHeadingTests(unittest.TestCase):
    def test_numbered_external_note_heading_flags_in_body_only(self) -> None:
        text = "正文第一段内容。\n\n一、待确认事项：\n需要作者确认样本范围。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        finding = next(item for item in findings if item.pattern_id == "unexpected-external-note")
        self.assertEqual("high", finding.severity)

    def test_markdown_and_chapter_numbered_variants_flag(self) -> None:
        for heading in ("## 需补充信息", "2. 风险提醒", "第3节 核验提示", "（一）写作说明"):
            text = f"正文内容。\n\n{heading}\n说明内容。"
            findings = LINT.scan("draft.md", text, delivery_mode="body-only")
            self.assertIn(
                "unexpected-external-note",
                pattern_ids(findings),
                f"heading variant not flagged: {heading}",
            )

    def test_longer_business_heading_is_kept(self) -> None:
        text = "正文内容。\n\n一、待确认事项办理情况\n本节记录已经办理的确认事项。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-only")
        self.assertNotIn("unexpected-external-note", pattern_ids(findings))

    def test_generic_and_review_modes_skip_external_note_scan(self) -> None:
        text = "正文内容。\n\n一、待确认事项：\n说明。"
        for mode in ("generic", "review-only"):
            findings = LINT.scan("draft.md", text, delivery_mode=mode)
            self.assertNotIn("unexpected-external-note", pattern_ids(findings))

    def test_suggestion_section_is_not_scanned(self) -> None:
        text = "正文内容。\n\n## 补充与修改建议\n可另列待确认事项：先补样本清单。"
        findings = LINT.scan("draft.md", text, delivery_mode="body-with-suggestions")
        self.assertNotIn("unexpected-external-note", pattern_ids(findings))


class FinalBodyReadOnlyAndOutputTests(unittest.TestCase):
    def test_input_file_is_never_modified(self) -> None:
        text = "综上，现有解释尚未形成最终结论。"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text(text, encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            exit_code = LINT.main([str(path), "--delivery-mode", "body-only", "--json"])
            self.assertEqual(0, exit_code)
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_json_output_carries_advice_and_pattern_fields(self) -> None:
        text = "综上，现有解释尚未形成最终结论。"
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text(text, encoding="utf-8")
            with redirect_stdout(buffer):
                LINT.main([str(path), "--delivery-mode", "body-only", "--json"])
        payload = json.loads(buffer.getvalue())
        self.assertTrue(any(item["pattern_id"] == "unresolved-state-tail" for item in payload))
        self.assertTrue(all("advice" in item and item["advice"] for item in payload))

    def test_cli_subprocess_smoke(self) -> None:
        text = "两项指标存在相关，但这并不意味着存在因果关系。"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT_PATH), str(path), "--delivery-mode", "body-only"],
                capture_output=True,
                text=True,
                timeout=120,
            )
        self.assertEqual(0, result.returncode)
        self.assertIn("negative-boundary-tail", result.stdout)


if __name__ == "__main__":
    unittest.main()
