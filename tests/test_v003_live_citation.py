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
        self.assertEqual(MANIFEST["verdict"], "FAIL")

    def test_default_offline_and_metadata_only_boundaries_hold(self):
        noauth = (EVIDENCE / "noauth-output.md").read_text(encoding="utf-8")
        metadata = (EVIDENCE / "metadata-only-output.md").read_text(encoding="utf-8")
        self.assertIn("WEB_USED=false", noauth)
        self.assertIn("现有材料未包含相关文献", noauth)
        self.assertIn("现有材料仅包含书目信息", metadata)
        self.assertIn("不足以支持", metadata)
        self.assertIn("WEB_USED=false", metadata)

    def test_retrieval_and_numeric_mapping_cover_four_real_dois(self):
        retrieval = (EVIDENCE / "retrieval-output.md").read_text(encoding="utf-8")
        writer = (EVIDENCE / "writer-output.md").read_text(encoding="utf-8")
        for index, doi in enumerate(MANIFEST["source_dois"], start=1):
            self.assertIn(doi, retrieval)
            self.assertIn(doi, writer)
            self.assertIn(f"[{index}]", writer)
        self.assertIn("参考文献", writer)
        self.assertIn("TEST_WEB_USED=false", writer)

    def test_cold_review_preserves_semantic_failures(self):
        review = (EVIDENCE / "cold-verifier.md").read_text(encoding="utf-8")
        self.assertIn("总体：**FAIL**", review)
        self.assertIn("预测关系升级为“引发”", review)
        self.assertIn("可能错误归到解释性评论", review)
        self.assertIn("仅能对第 2、4 篇复现", review)


if __name__ == "__main__":
    unittest.main()
