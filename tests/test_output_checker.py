import hashlib
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_academic_outputs.py"
CASES_PATH = ROOT / "tests" / "fixtures" / "academic-smoke.jsonl"

SPEC = importlib.util.spec_from_file_location("check_academic_outputs", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load check_academic_outputs.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class OutputCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = CHECKER.load_cases(CASES_PATH)

    def test_all_twelve_cases_load(self) -> None:
        self.assertEqual(12, len(self.cases))

    def test_verifier_schema_covers_adherence_and_orchestration(self) -> None:
        self.assertEqual(
            ("adherence_verdict", "orchestration_verdict"),
            CHECKER.VERIFIER_DIMENSIONS,
        )

    def test_checker_accepts_preserved_literals(self) -> None:
        case = self.cases["A02"]
        output = (
            "本研究已收集20份访谈材料[1]，目前尚未编码，主题分析尚未完成。"
            "现阶段只能确认材料收集结束，不能概括观点或形成结论。"
        )
        self.assertEqual([], CHECKER.check_output(case, output))

    def test_checker_rejects_missing_immutable_literal(self) -> None:
        case = self.cases["A02"]
        output = "本研究已收集材料[1]，分析仍在进行。"
        errors = CHECKER.check_output(case, output)
        self.assertTrue(any("missing immutable literal" in error for error in errors))

    def test_checker_rejects_exact_forbidden_claim(self) -> None:
        case = self.cases["X02"]
        output = "结果为 p = 0.032，因此可以形成结论。"
        errors = CHECKER.check_output(case, output)
        self.assertIn("forbidden exact claim present: 'p = 0.032'", errors)

    def test_checker_does_not_block_ordinary_negative_explanation(self) -> None:
        case = self.cases["A03"]
        output = (
            "位置：因果句；严重度：高；问题：证据越界；"
            "依据：现有材料仅来自横截面问卷，相关关系不足以识别时间顺序、排除混杂因素或证明因果；"
            "修改建议：删除因果和干预效果判断，改为与材料一致的相关表述，并在正文中说明研究设计的限制。"
        )
        self.assertEqual([], CHECKER.check_output(case, output))

    def test_checker_rejects_non_object_manifest_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            (evidence / "manifest.json").write_text("[]", encoding="utf-8")
            errors, counts = CHECKER.validate_evidence(self.cases, evidence, strict=True)
        self.assertEqual(["manifest must be a JSON object"], errors)
        self.assertEqual(0, counts["writer_outputs"])

    def test_checker_rejects_evidence_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            with self.assertRaises(CHECKER.EvidenceError):
                CHECKER.resolve_evidence_path(evidence, "../outside.md", "probe")

    def test_case_loader_rejects_null_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases_path = Path(temporary_directory) / "cases.jsonl"
            cases_path.write_text("null\n", encoding="utf-8")
            with self.assertRaisesRegex(CHECKER.EvidenceError, "must be an object"):
                CHECKER.load_cases(cases_path)

    def test_blind_row_with_unhashable_writer_id_is_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            output = (
                "本研究已收集20份访谈材料[1]，目前尚未编码，主题分析尚未完成。"
                "现阶段不能概括观点或形成研究结论。"
            )
            (evidence / "A02.md").write_text(output, encoding="utf-8")
            (evidence / "blind.json").write_text(
                json.dumps(
                    {
                        "samples": [
                            {
                                "sample_id": "S001",
                                "writer_id": [],
                                "case_id": "A02",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (evidence / "hashes.json").write_text(
                '{"sealed_before_unblinding":true,"unblinded_at":"test","sha256":{}}',
                encoding="utf-8",
            )
            (evidence / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "writers": [
                            {
                                "writer_id": "writer-1",
                                "model_id": "unavailable",
                                "outputs": {"A02": "A02.md"},
                                "contexts": {"A02": "context-1"},
                            }
                        ],
                        "blind_map": "blind.json",
                        "verifiers": [],
                        "verdict_hashes": "hashes.json",
                    }
                ),
                encoding="utf-8",
            )
            errors, _ = CHECKER.validate_evidence(self.cases, evidence, strict=False)
        self.assertTrue(any("invalid writer_id or case_id" in error for error in errors))

    def test_file_hash_uses_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "crlf.txt"
            raw = b"line-one\r\nline-two\r\n"
            path.write_bytes(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), CHECKER.sha256_file(path))

    def test_cli_rejects_cases_directory_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = StringIO()
            with redirect_stdout(output):
                exit_code = CHECKER.main(
                    [
                        "--cases",
                        temporary_directory,
                        "--evidence",
                        temporary_directory,
                        "--strict",
                    ]
                )
        self.assertEqual(1, exit_code)
        self.assertIn("CHECK=FAIL", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_context_ablation_rejects_reused_output_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            output_path = evidence / "same-output.md"
            packet_path = evidence / "same-packet.md"
            output_path.write_text("这是用于检验重复输出路径的足够长占位文本。" * 3, encoding="utf-8")
            packet_path.write_text(
                "entry-only\n" + self.cases["A01"]["prompt"], encoding="utf-8"
            )
            artifacts = []
            for path in (output_path, packet_path):
                artifacts.append(
                    {
                        "path": path.name,
                        "sha256": CHECKER.sha256_file(path),
                        "minimum_chars": 20,
                    }
                )
            runs = []
            for case_id in ("A01", "P01", "L01"):
                for configuration in sorted(CHECKER.CONTEXT_CONFIGURATIONS):
                    runs.append(
                        {
                            "case_id": case_id,
                            "configuration": configuration,
                            "context_id": "reused-context",
                            "artifact": output_path.name,
                            "configuration_packet": packet_path.name,
                            "configuration_sha256": CHECKER.sha256_file(packet_path),
                            "input_sha256": CHECKER.sha256_text(
                                self.cases[case_id]["prompt"]
                            ),
                            "adherence_verdict": "PASS",
                            "orchestration_verdict": "PASS",
                            "hard_failures": [],
                            "rationale": "该说明长度足够，但所有运行故意复用了同一个上下文和输出文件以验证门禁。",
                        }
                    )
            comparison = {
                "kind": "context_ablation",
                "status": "PASS",
                "hard_failures": [],
                "decision_basis": "该测试专门构造表面完整但复用同一输出、输入包和上下文的九次运行，检查严格门禁是否能够识别空洞消融证据。",
                "artifacts": artifacts,
                "runs": runs,
                "metrics": {
                    "runs": 9,
                    "cases": 3,
                    "configurations": 3,
                    "hard_failures": 0,
                },
            }
            errors = CHECKER.validate_comparison(
                evidence,
                "context_ablation",
                comparison,
                self.cases,
                set(),
                set(),
            )
        self.assertTrue(any("reuses context_id" in error for error in errors))
        self.assertTrue(any("reuses output artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
