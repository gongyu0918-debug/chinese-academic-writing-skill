import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v0.0.2-writing-sanity.jsonl"
EVIDENCE = ROOT / "tests" / "evidence" / "v0.0.2-anti-ai-sanity"


def sha256_normalized_lf(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def sha256_git_text(commit: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    text = result.stdout.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class Version002SanityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = {
            row["id"]: row
            for row in (
                json.loads(line)
                for line in FIXTURE.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        cls.manifest = json.loads(
            (EVIDENCE / "manifest.json").read_text(encoding="utf-8")
        )
        cls.mapping = json.loads(
            (EVIDENCE / "blind" / "unblinded-map.json").read_text(
                encoding="utf-8"
            )
        )
        cls.verifier = json.loads(
            (EVIDENCE / "blind" / "verifier.json").read_text(encoding="utf-8")
        )

    def test_fixture_and_historical_runtime_hashes_are_sealed(self) -> None:
        self.assertEqual(3, len(self.cases))
        self.assertEqual(
            sha256_normalized_lf(FIXTURE),
            self.manifest["fixture"]["sha256_normalized_lf"],
        )
        protected = self.manifest["protected_sha256_normalized_lf"]
        self.assertEqual(
            {
                "chinese-academic-writing-assistant/SKILL.md",
                "chinese-academic-writing-assistant/references/anti-ai-writing.md",
                "chinese-academic-writing-assistant/scripts/prose_lint.py",
            },
            set(protected),
        )
        for relative, expected in protected.items():
            with self.subTest(relative=relative):
                self.assertRegex(expected, r"^[0-9a-f]{64}$")
                self.assertEqual(
                    expected,
                    sha256_git_text(self.manifest["candidate_commit"], relative),
                )
        self.assertRegex(self.manifest["candidate_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            "UTF-8 text with CRLF and CR normalized to LF",
            self.manifest["hash_mode"],
        )

    def test_two_fresh_writers_cover_all_cases(self) -> None:
        rows = self.mapping["samples"]
        self.assertTrue(self.mapping["verifier_completed_before_unblinding"])
        self.assertEqual(6, len(rows))
        self.assertEqual({"writer-a", "writer-b"}, {row["writer_id"] for row in rows})
        self.assertEqual({"S01", "S02", "S03"}, {row["case_id"] for row in rows})
        self.assertEqual(6, len({row["sample_id"] for row in rows}))

        for row in rows:
            case = self.cases[row["case_id"]]
            output = (EVIDENCE / row["output"]).read_text(encoding="utf-8")
            for literal in case["immutable_literals"] + case["required"]:
                self.assertIn(literal, output, f"{row['sample_id']}: {literal}")
            for forbidden in case["forbidden"]:
                self.assertNotIn(forbidden, output, f"{row['sample_id']}: {forbidden}")

    def test_review_only_outputs_use_the_five_column_contract(self) -> None:
        for writer_id in ("writer-a", "writer-b"):
            output = (EVIDENCE / "writers" / writer_id / "S03.md").read_text(
                encoding="utf-8"
            )
            self.assertTrue(
                output.startswith("| 位置 | 严重度 | 问题 | 依据 | 修改建议 |")
            )
            self.assertNotIn("改写后全文", output)

    def test_blind_verifier_passes_adherence_and_orchestration(self) -> None:
        self.assertTrue(self.verifier["blind"])
        self.assertEqual("PASS", self.verifier["overall"])
        self.assertEqual([], self.verifier["common_issue_candidates"])
        self.assertEqual(6, len(self.verifier["results"]))
        for result in self.verifier["results"]:
            for dimension in (
                "adherence",
                "orchestration",
                "semantic_fidelity",
                "output_hygiene",
            ):
                self.assertEqual("PASS", result[dimension])
            self.assertEqual([], result["hard_failures"])

        threshold = self.manifest["fix_threshold"]
        self.assertEqual(3, threshold["minimum_outputs"])
        self.assertEqual(2, threshold["minimum_cases"])
        self.assertEqual(2, threshold["minimum_writers"])
        self.assertFalse(threshold["prompt_changed_from_this_sanity"])


if __name__ == "__main__":
    unittest.main()
