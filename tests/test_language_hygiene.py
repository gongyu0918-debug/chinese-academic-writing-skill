import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_language_hygiene_outputs.py"
CASES_PATH = ROOT / "tests" / "fixtures" / "language-hygiene-smoke.jsonl"
SKILL_PATH = ROOT / "chinese-academic-writing-assistant" / "SKILL.md"

SPEC = importlib.util.spec_from_file_location(
    "check_language_hygiene_outputs", CHECKER_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load check_language_hygiene_outputs.py")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


VALID_OUTPUTS = {
    "H01": "访谈共涉及18名学生[1]，多名受访者提到插座位置会影响选座。现有材料可据此描述受访者的选座考虑。",
    "H02": "2025年4月，连续三个工作日晚间观察到二层靠窗座位紧张。开放时间、插座配置和座位布局可作为后续研究议题。",
    "H03": "问卷数据仅显示平台使用时长与成绩存在相关关系[2]。横截面相关不能证明因果关系，不得据此声称平台使用导致成绩下降。",
    "H04": "甲方案样本均值为80，乙方案样本均值为120[3]。作者将证据边界表述为‘这是一项相关分析，而不是因果识别’。",
    "H05": "2025年3月完成样本A的初步整理[4]。",
    "H06": "本研究仅分析已完成编码的12份访谈[5]，未编码材料不进入本次分析，结论适用范围限于这些材料。",
    "H07": "位置：第二句至第三句；严重度：高；问题：存在无依据否定、虚设对比和递进越界；依据：材料[6]只支持变量相关关系，未提供机制检验或外部效度证据；修改建议：删除理论突破、机制解释和普遍规律判断，保留与相关证据一致的有限表述。",
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_evidence(
    root: Path,
    cases: dict[str, dict],
    repo_root: Path | None = None,
    candidate_commit: str = "test-candidate",
) -> None:
    writers = []
    pairs = []
    for writer_index, writer_id in enumerate(("writer-a", "writer-b"), start=1):
        outputs = {}
        contexts = {}
        inputs = {}
        for case_id in sorted(cases):
            input_path = root / "inputs" / writer_id / f"{case_id}.md"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(cases[case_id]["prompt"], encoding="utf-8")
            inputs[case_id] = {
                "path": input_path.relative_to(root).as_posix(),
                "sha256": CHECKER.sha256_file(input_path),
            }
            output_path = root / "writers" / writer_id / f"{case_id}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(VALID_OUTPUTS[case_id], encoding="utf-8")
            outputs[case_id] = output_path.relative_to(root).as_posix()
            contexts[case_id] = f"fresh-w{writer_index}-{case_id.lower()}"
            pairs.append((writer_id, case_id, output_path))
        writers.append(
            {
                "writer_id": writer_id,
                "model_id": "unavailable",
                "inputs": inputs,
                "outputs": outputs,
                "contexts": contexts,
            }
        )

    samples = []
    sample_records = {}
    for number, (writer_id, case_id, output_path) in enumerate(pairs, start=1):
        sample_id = f"S{number:03d}"
        output_raw = output_path.read_bytes()
        output_text = output_raw.decode("utf-8")
        packet_path = root / "blind" / "packets" / f"{sample_id}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(
            CHECKER.expected_packet(
                sample_id, cases[case_id]["prompt"], output_text
            ),
            encoding="utf-8",
        )
        row = {
            "sample_id": sample_id,
            "writer_id": writer_id,
            "case_id": case_id,
            "output": output_path.relative_to(root).as_posix(),
            "output_sha256": hashlib.sha256(output_raw).hexdigest(),
            "prompt_sha256": CHECKER.sha256_text(cases[case_id]["prompt"]),
            "packet": packet_path.relative_to(root).as_posix(),
            "packet_sha256": CHECKER.sha256_file(packet_path),
        }
        samples.append(row)
        sample_records[sample_id] = (row, output_text)
    blind_map_path = root / "blind" / "anonymous-map.json"
    write_json(blind_map_path, {"samples": samples})
    packet_set_sha = CHECKER.sha256_text(
        "\n".join(
            f"{sample_id}:{sample_records[sample_id][0]['packet_sha256']}"
            for sample_id in sorted(sample_records)
        )
    )

    verifiers = []
    verifier_hashes = {}
    for number in (1, 2):
        verifier_id = f"verifier-{number}"
        results = []
        for sample_id in sorted(sample_records):
            row, output_text = sample_records[sample_id]
            result = {
                    "sample_id": sample_id,
                    "output_sha256": row["output_sha256"],
                    "prompt_sha256": row["prompt_sha256"],
                    "verdict": "PASS",
                    "hard_failures": [],
                    "issue_codes": [],
                    "rationale": "该匿名输出遵守字面不变量和交付模式，未发现需要阻断交付的语义问题。",
                    "anchors": [output_text[:8]],
                }
            result.update({dimension: "PASS" for dimension in CHECKER.VERIFIER_DIMENSIONS})
            results.append(result)
        result_path = root / "verifiers" / f"{verifier_id}.json"
        write_json(
            result_path,
            {
                "verifier_id": verifier_id,
                "blind": True,
                "packet_set_sha256": packet_set_sha,
                "criteria": CHECKER.VERIFIER_CRITERIA,
                "results": results,
            },
        )
        verifier_hashes[verifier_id] = CHECKER.sha256_file(result_path)
        verifiers.append(
            {
                "verifier_id": verifier_id,
                "model_id": "unavailable",
                "context_id": f"fresh-verifier-{number}",
                "results": result_path.relative_to(root).as_posix(),
            }
        )
    hashes_path = root / "verifiers" / "verdict-hashes.json"
    write_json(
        hashes_path,
        {
            "sealed_before_unblinding": True,
            "unblinded_at": "2026-07-13T17:00:00+08:00",
            "sha256": verifier_hashes,
        },
    )
    manifest = {
            "schema_version": 1,
            "candidate_commit": candidate_commit,
            "fix_threshold": CHECKER.FIX_THRESHOLD,
            "writers": writers,
            "blind_map": blind_map_path.relative_to(root).as_posix(),
            "verifiers": verifiers,
            "verdict_hashes": hashes_path.relative_to(root).as_posix(),
        }
    if repo_root is not None:
        manifest["tested_paths"] = list(CHECKER.PROTECTED_PATHS)
        manifest["protected_sha256"] = {
            relative: CHECKER.sha256_file(repo_root / relative)
            for relative in CHECKER.PROTECTED_PATHS
        }
    write_json(root / "manifest.json", manifest)


def make_git_candidate(root: Path) -> tuple[str, Path, dict[str, dict]]:
    for relative in CHECKER.PROTECTED_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT / relative
        target.write_bytes(source.read_bytes())
    commands = (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Language Hygiene Test"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "add", *CHECKER.PROTECTED_PATHS],
        ["git", "commit", "-q", "-m", "test candidate"],
    )
    for command in commands:
        subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    candidate = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    cases_path = root / "tests" / "fixtures" / "language-hygiene-smoke.jsonl"
    return candidate, cases_path, CHECKER.load_cases(cases_path)


class LanguageHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = CHECKER.load_cases(CASES_PATH)

    def test_fixture_has_seven_complementary_cases(self) -> None:
        self.assertEqual({f"H{number:02d}" for number in range(1, 8)}, set(self.cases))
        focuses = {
            focus for case in self.cases.values() for focus in case["semantic_focus"]
        }
        for expected in (
            "false-contrast",
            "mechanical-repetition",
            "necessary-negation",
            "genuine-comparison",
            "direct-quotation",
            "production-label-leak",
            "repeated-boundary",
            "tail-note",
            "review-only",
        ):
            self.assertIn(expected, focuses)
        self.assertIn("未编码材料", self.cases["H06"]["immutable_literals"])
        self.assertNotIn(
            "未编码材料不进入本次分析",
            self.cases["H06"]["immutable_literals"],
        )

    def test_runtime_prompt_defines_contextual_local_rewrite_layer(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        for marker in (
            "先按段落和全文统计高频词组",
            "词频和命中只提供复核线索",
            "否定对象未由前文、用户材料或真实争议提出",
            "只对确认有问题的局部",
            "不逐词替换或随机换词",
            "研究状态、否定范围和论断强度",
            "无法安全改写时保留原句",
            "本层不改变交付模式",
            "默认不输出词频、命中项、阈值、检查过程",
        ):
            self.assertIn(marker, skill)

    def test_candidate_frequency_is_observation_not_failure(self) -> None:
        text = (
            "2025年4月，连续三个工作日晚间观察到二层靠窗座位紧张。"
            "进一步讨论开放时间，进一步讨论插座配置，进一步讨论座位布局。"
        )
        self.assertEqual([], CHECKER.check_output(self.cases["H02"], text))
        findings = CHECKER.scan_candidates(self.cases["H02"], text, "writer-a")
        self.assertEqual(3, sum(item.pattern_id == "further" for item in findings))

    def test_quote_match_is_reported_as_quoted_and_preserved(self) -> None:
        text = VALID_OUTPUTS["H04"]
        self.assertEqual([], CHECKER.check_output(self.cases["H04"], text))
        findings = CHECKER.scan_candidates(self.cases["H04"], text, "writer-a")
        rather_than = [item for item in findings if item.pattern_id == "rather_than"]
        self.assertEqual(1, len(rather_than))
        self.assertTrue(rather_than[0].quoted)

    def test_hard_gate_blocks_missing_invariant_and_explicit_leak(self) -> None:
        errors = CHECKER.check_output(
            self.cases["H05"], "给领导看的脱敏修改版：样本A整理完成。"
        )
        self.assertTrue(any("missing immutable literal" in item for item in errors))
        self.assertTrue(any("explicit leakage" in item for item in errors))

    def test_review_only_mode_requires_review_fields(self) -> None:
        case = dict(self.cases["H07"])
        case["required_literals"] = []
        errors = CHECKER.check_output(case, "这段文字需要修改。")
        self.assertEqual(5, sum("output mode" in item for item in errors))

    def test_rewrite_mode_rejects_complete_review_table(self) -> None:
        text = (
            VALID_OUTPUTS["H01"]
            + "\n位置：第二句；严重度：中；问题：句式重复；依据：上下文；"
            "修改建议：压缩。"
        )
        errors = CHECKER.check_output(self.cases["H01"], text)
        self.assertTrue(any("complete review table" in item for item in errors))

    def test_prompt_fix_requires_three_outputs_two_cases_two_writers(self) -> None:
        samples = {
            "S001": {"writer_id": "writer-a", "case_id": "H01"},
            "S002": {"writer_id": "writer-a", "case_id": "H02"},
            "S003": {"writer_id": "writer-b", "case_id": "H01"},
        }
        one_sided_votes = {
            "false-contrast": {
                sample_id: {"verifier-1"} for sample_id in samples
            }
        }
        below = CHECKER.summarize_prompt_fix_candidates(
            CHECKER.consensus_issue_samples(one_sided_votes),
            samples,
        )
        self.assertEqual([], below)
        consensus_votes = {
            "false-contrast": {
                sample_id: {"verifier-1", "verifier-2"}
                for sample_id in samples
            }
        }
        eligible = CHECKER.summarize_prompt_fix_candidates(
            CHECKER.consensus_issue_samples(consensus_votes), samples
        )
        self.assertEqual(
            (3, 2, 2),
            (
                eligible[0]["outputs"],
                eligible[0]["cases"],
                eligible[0]["writers"],
            ),
        )

    def test_strict_evidence_accepts_two_writers_and_two_blind_verifiers_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory)
            candidate, cases_path, cases = make_git_candidate(repo)
            evidence = repo / "tests" / "evidence" / "language-hygiene"
            build_evidence(
                evidence,
                cases,
                repo_root=repo,
                candidate_commit=candidate,
            )
            before = {
                path.relative_to(evidence).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in evidence.rglob("*")
                if path.is_file()
            }
            errors, counts, findings, recommendations = CHECKER.validate_evidence(
                cases,
                evidence,
                strict=True,
                repo_root=repo,
                cases_path=cases_path,
            )
            cli_output = StringIO()
            with redirect_stdout(cli_output):
                cli_exit = CHECKER.main(
                    [
                        "--cases",
                        str(cases_path),
                        "--evidence",
                        str(evidence),
                        "--strict",
                    ]
                )
            after = {
                path.relative_to(evidence).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in evidence.rglob("*")
                if path.is_file()
            }
        self.assertEqual([], errors)
        self.assertEqual(0, cli_exit, cli_output.getvalue())
        self.assertEqual(14, counts["writer_outputs"])
        self.assertEqual(14, counts["input_packets"])
        self.assertEqual(14, counts["blind_samples"])
        self.assertEqual(28, counts["verdicts"])
        self.assertTrue(findings)
        self.assertEqual([], recommendations)
        self.assertEqual(before, after)

    def test_verifier_hard_failure_blocks_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            build_evidence(evidence, self.cases)
            verifier_path = evidence / "verifiers" / "verifier-1.json"
            payload = json.loads(verifier_path.read_text(encoding="utf-8"))
            payload["results"][0]["verdict"] = "FAIL"
            payload["results"][0]["hard_failures"] = ["事实不变量被改动"]
            write_json(verifier_path, payload)
            errors, _, _, _ = CHECKER.validate_evidence(
                self.cases, evidence, strict=False
            )
        self.assertTrue(any("hard verdict FAIL" in item for item in errors))
        self.assertTrue(any("reports hard failures" in item for item in errors))

    def test_any_five_dimension_failure_blocks_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            build_evidence(evidence, self.cases)
            verifier_path = evidence / "verifiers" / "verifier-1.json"
            payload = json.loads(verifier_path.read_text(encoding="utf-8"))
            payload["results"][0]["overediting_verdict"] = "FAIL"
            write_json(verifier_path, payload)
            errors, _, _, _ = CHECKER.validate_evidence(
                self.cases, evidence, strict=False
            )
        self.assertTrue(any("overediting_verdict is FAIL" in item for item in errors))

    def test_prompt_only_inputs_are_exact_unique_and_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            build_evidence(evidence, self.cases)
            manifest_path = evidence / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            h01 = manifest["writers"][0]["inputs"]["H01"]
            input_path = evidence / h01["path"]
            input_path.write_text(
                self.cases["H01"]["prompt"] + "\nexpected_mode: rewrite-only",
                encoding="utf-8",
            )
            h01["sha256"] = CHECKER.sha256_file(input_path)
            manifest["writers"][0]["inputs"]["H02"] = dict(h01)
            write_json(manifest_path, manifest)
            errors, _, _, _ = CHECKER.validate_evidence(
                self.cases, evidence, strict=False
            )
            with self.assertRaisesRegex(CHECKER.EvidenceError, "must be relative"):
                CHECKER.resolve_evidence_path(
                    evidence, str(input_path.resolve()), "absolute input"
                )
        self.assertTrue(any("only the exact prompt" in item for item in errors))
        self.assertTrue(any("reuse one path" in item for item in errors))

    def test_strict_git_binding_rejects_dirty_protected_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory)
            candidate, cases_path, cases = make_git_candidate(repo)
            evidence = repo / "tests" / "evidence" / "language-hygiene"
            build_evidence(
                evidence,
                cases,
                repo_root=repo,
                candidate_commit=candidate,
            )
            protected = repo / "chinese-academic-writing-assistant" / "agents" / "openai.yaml"
            protected.write_text(
                protected.read_text(encoding="utf-8") + "\ndirty: true\n",
                encoding="utf-8",
            )
            errors, _, _, _ = CHECKER.validate_evidence(
                cases,
                evidence,
                strict=True,
                repo_root=repo,
                cases_path=cases_path,
            )
        self.assertTrue(any("protected SHA-256 mismatch" in item for item in errors))
        self.assertTrue(any("differ from manifest.candidate_commit" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
