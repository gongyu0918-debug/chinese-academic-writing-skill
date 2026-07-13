import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests" / "evidence" / "v0.0.3-citation-sanity"
FIXTURE = ROOT / "tests" / "fixtures" / "v0.0.3-citation-sanity.md"
SCRIPT_DIR = ROOT / "chinese-academic-writing-assistant" / "scripts"
SPEC = importlib.util.spec_from_file_location("v003_citation_audit", SCRIPT_DIR / "citation_audit.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load citation_audit.py")
sys.path.insert(0, str(SCRIPT_DIR))
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_text_sha(commit: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    text = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Version003CitationSanityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
        cls.verifiers = [
            json.loads((EVIDENCE / relative).read_text(encoding="utf-8"))
            for relative in cls.manifest["verifiers"]
        ]

    def test_fixture_and_twelve_raw_outputs_are_sealed_to_candidate(self) -> None:
        self.assertEqual(self.manifest["fixture"]["sha256_normalized_lf"], normalized_sha(FIXTURE))
        outputs = self.manifest["output_sha256_normalized_lf"]
        self.assertEqual(12, len(outputs))
        commit = self.manifest["candidate_commit"]
        for relative, expected in outputs.items():
            path = EVIDENCE / relative
            repo_relative = path.relative_to(ROOT).as_posix()
            with self.subTest(relative=relative):
                self.assertEqual(expected, normalized_sha(path))
                self.assertEqual(expected, git_text_sha(commit, repo_relative))

    def test_two_continuous_writers_report_only_the_authorized_web_turn(self) -> None:
        for writer_id in ("writer-a", "writer-b"):
            report = json.loads((EVIDENCE / "writers" / writer_id / "writer-report.json").read_text(encoding="utf-8"))
            self.assertEqual("unavailable", report["model_id"])
            if "web_used" in report:
                web_turns = {turn for turn, used in report["web_used"].items() if used}
            else:
                web_turns = {turn for turn, row in report["rounds"].items() if row["web_used"]}
            self.assertEqual({"M1-T2"}, web_turns)
            self.assertTrue(all(report["continuous_context"].values()))

    def test_outputs_follow_source_layers_modes_and_default_citation_style(self) -> None:
        dois = (
            "10.1111/j.1467-9280.2006.01693.x",
            "10.1126/science.1152408",
            "10.1037/a0037559",
        )
        for writer_id in ("writer-a", "writer-b"):
            root = EVIDENCE / "writers" / writer_id
            t1 = (root / "M1-T1.md").read_text(encoding="utf-8")
            t2 = (root / "M1-T2.md").read_text(encoding="utf-8")
            t3 = (root / "M1-T3.md").read_text(encoding="utf-8")
            review = (root / "M2-T1.md").read_text(encoding="utf-8")
            quota = (root / "M2-T2.md").read_text(encoding="utf-8")
            final = (root / "M2-T3.md").read_text(encoding="utf-8")

            self.assertRegex(t1, r"材料|来源")
            self.assertNotRegex(t1, r"https?://|10\.\d{4,9}/")
            for doi in dois:
                self.assertIn(doi, t2)
                self.assertIn(doi, t3)
            self.assertIn("未读取", t2)
            self.assertIn("不能支持", t2)
            self.assertTrue(review.startswith("| 位置 | 严重度 | 问题 | 依据 | 修改建议 |"))
            self.assertIn("30%", quota)
            self.assertRegex(quota, r"不能|无法")
            self.assertIn("<sup>[1]</sup>", t3)
            self.assertIn("参考文献", t3)
            self.assertIn("<sup>[1]</sup>", final)
            self.assertIn("<sup>[2]</sup>", final)
            self.assertIn("参考文献", final)
            self.assertNotRegex(final, r"材料\s*[BC](?![A-Za-z])")
            for residue in ("检索过程", "证据账本", "门禁", "脚本", "writer", "verifier"):
                self.assertNotIn(residue, final)

            for name, lower, upper in (("M1-T3.md", 250, 350), ("M2-T3.md", 180, 250)):
                content = (root / name).read_text(encoding="utf-8")
                body = re.split(r"(?:^|\n)#{0,6}\s*参考文献\s*\n", content, maxsplit=1)[0]
                visible = re.sub(r"<[^>]+>", "", body)
                self.assertLessEqual(lower, len(re.sub(r"\s+", "", visible)))
                self.assertGreaterEqual(upper, len(re.sub(r"\s+", "", visible)))

    def test_final_outputs_have_complete_reference_mapping_and_only_review_candidates(self) -> None:
        for writer_id in ("writer-a", "writer-b"):
            for name in ("M1-T3.md", "M2-T3.md"):
                content = (EVIDENCE / "writers" / writer_id / name).read_text(encoding="utf-8")
                report = AUDIT.analyze(content, mode="literature-review")
                with self.subTest(writer=writer_id, name=name):
                    self.assertEqual(1.0, report["summary"]["numeric_reference_utilization"])
                    self.assertGreater(report["summary"]["citation_marker_coverage"], 0)
                    self.assertFalse(any(item["severity"] == "high" for item in report["findings"]))
                    self.assertTrue(
                        all(item["code"] == "uncited-claim-candidate" for item in report["findings"])
                    )

    def test_two_cold_verifiers_have_no_hard_or_common_failure(self) -> None:
        self.assertEqual(2, len(self.verifiers))
        for verifier in self.verifiers:
            self.assertTrue(verifier["blind"])
            self.assertEqual("unavailable", verifier["model_id"])
            self.assertEqual({"PASS": 11, "WARN": 1, "FAIL": 0}, verifier["counts"])
            self.assertEqual([], verifier["hard_failures"])
            self.assertEqual([], verifier["common_issue_candidates"])
            warnings = [row for row in verifier["results"] if row["verdict"] == "WARN"]
            self.assertEqual(["A/M1-T3"], [row["sample"] for row in warnings])
            self.assertFalse(verifier["fix_threshold"]["reached"])


if __name__ == "__main__":
    unittest.main()
