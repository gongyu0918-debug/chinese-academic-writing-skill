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

    def test_blind_verifier_record_has_all_samples(self) -> None:
        self.assertTrue(self.verifier["blind"])
        self.assertEqual(6, len(self.verifier["results"]))


if __name__ == "__main__":
    unittest.main()
