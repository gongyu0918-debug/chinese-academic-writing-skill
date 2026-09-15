import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests" / "evidence" / "v0.0.3-live-citation"
MANIFEST = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))


class Version003LiveCitationTests(unittest.TestCase):
    def test_raw_live_outputs_and_cold_verdict_are_sealed(self):
        for relative, expected in MANIFEST["files"].items():
            actual = hashlib.sha256((EVIDENCE / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

if __name__ == "__main__":
    unittest.main()
