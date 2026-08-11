import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "tools" / "skillhub-package-policy.json"
LICENSE_PATH = ROOT / "LICENSE"
README_PATH = ROOT / "README.md"
HANDOFF_PATH = ROOT / "HANDOFF.md"
RELEASE_NOTES_PATH = ROOT / "tests" / "evidence" / "v0.0.9-release-gate" / "RELEASE-NOTES.md"
RELEASE_RECEIPT_PATH = ROOT / "tests" / "evidence" / "v0.0.9-release-gate" / "RELEASE-RECEIPT.json"


class ReleasePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.package = cls.policy["skillhub_package"]
        cls.package_root = ROOT / cls.package["root"]
        cls.readme = README_PATH.read_text(encoding="utf-8")
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")
        cls.release_notes = RELEASE_NOTES_PATH.read_text(encoding="utf-8")
        cls.release_receipt = json.loads(RELEASE_RECEIPT_PATH.read_text(encoding="utf-8"))

    def test_only_github_and_skillhub_are_future_publish_targets(self) -> None:
        self.assertEqual(["github", "skillhub.cn"], self.policy["publish_targets"])
        self.assertEqual(["clawhub"], self.policy["excluded_publish_targets"])
        self.assertNotIn("[![ClawHub]", self.readme)
        self.assertIn("不再向 ClawHub 发布或更新", self.readme)
        self.assertIn("不得构建、检查、上传或更新 ClawHub 包", self.handoff)

    def test_project_and_skillhub_metadata_use_mit(self) -> None:
        self.assertEqual("MIT", self.policy["license"])
        self.assertEqual("MIT", self.package["derived_frontmatter"]["license"])
        root_license = LICENSE_PATH.read_text(encoding="utf-8")
        package_license = (self.package_root / self.package["markdown_license"]).read_text(
            encoding="utf-8"
        )
        self.assertTrue(root_license.startswith("MIT License\n"))
        self.assertEqual(root_license, package_license.removeprefix("# "))
        self.assertNotIn("MIT-0", self.readme + self.handoff)

    def test_skillhub_frontmatter_is_minimal_and_has_no_homepage(self) -> None:
        metadata = self.package["derived_frontmatter"]
        self.assertEqual(
            ["name", "description", "slug", "version", "displayName", "tags", "license"],
            metadata["field_order"],
        )
        self.assertEqual("policy", metadata["description_source"])
        self.assertEqual(
            "依据作者材料、文献或授权来源，协助起草、改写和审阅中文论文、开题报告及文献综述，并核对论证、证据与引用。",
            metadata["description"],
        )
        self.assertEqual("chinese-academic-writing-assistant", metadata["slug"])
        self.assertEqual("中文论文写作", metadata["displayName"])
        self.assertEqual(["chinese", "academic"], metadata["tags"])
        self.assertEqual(["summary", "homepage"], metadata["omitted_optional_fields"])
        self.assertNotIn("homepage", metadata)
        self.assertNotIn("summary", metadata)

    def test_skillhub_package_is_eleven_runtime_files_plus_markdown_license(self) -> None:
        expected = set(self.package["files"])
        actual = {
            path.relative_to(self.package_root).as_posix()
            for path in self.package_root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertEqual(11, self.package["runtime_file_count"])
        self.assertEqual(12, self.package["file_count"])
        self.assertEqual(self.package["file_count"], len(expected))
        self.assertEqual(expected, actual)
        self.assertEqual(
            self.package["runtime_file_count"],
            len(expected - {self.package["markdown_license"]}),
        )

    def test_repository_and_local_surfaces_cannot_enter_skillhub_package(self) -> None:
        package_files = set(self.package["files"])
        for forbidden in (
            "LICENSE",
            "README.md",
            "HANDOFF.md",
            "tests/",
            "tools/",
            "evidence/",
            "receipts/",
            ".release/",
        ):
            if forbidden.endswith("/"):
                self.assertFalse(any(path.startswith(forbidden) for path in package_files))
            else:
                self.assertNotIn(forbidden, package_files)
        self.assertEqual("LICENSE.md", self.package["markdown_license"])
        self.assertIn("LICENSE.md", package_files)
        self.assertIn("assets/**", self.policy["github_only_surfaces"])
        self.assertIn("tests/**", self.policy["github_only_surfaces"])
        self.assertIn("tools/**", self.policy["github_only_surfaces"])
        self.assertEqual(
            "tests/evidence/{version}-release-gate/RELEASE-RECEIPT.json",
            self.policy["public_receipt_path_template"],
        )
        self.assertEqual([".release/**"], self.policy["local_only_surfaces"])

    def test_v008_clawhub_release_remains_a_historical_fact(self) -> None:
        historical = "0.0.8 已发布到 GitHub（tag v0.0.8）、ClawHub 与 skillhub.cn"
        self.assertIn(historical, self.readme)
        self.assertIn("版本 0.0.8 已发布至 GitHub（tag v0.0.8）、ClawHub 与 skillhub.cn", self.handoff)

    def test_v009_release_copy_matches_the_package_and_evidence_boundary(self) -> None:
        self.assertIn("version-0.0.9-blue", self.readme)
        self.assertIn("chinese-academic-writing-assistant@0.0.9", self.readme)
        combined = self.readme + self.release_notes
        for marker in (
            "11 个运行文件和独立 `LICENSE.md`",
            "统一采用 MIT",
            "不更新 ClawHub",
            "省去重复 `summary` 和 `homepage`",
            "已经撤回，不在 0.0.9 运行规则中",
            "不据此声称论文质量或去 AI 味效果获得提升",
            "公开评测 stderr 中的内部请求标识已替换为固定占位符",
        ):
            self.assertIn(marker, combined)

    def test_v009_public_receipt_binds_both_release_surfaces(self) -> None:
        receipt = self.release_receipt
        self.assertEqual("0.0.9", receipt["version"])
        self.assertEqual(
            "31d3beac65f6e33663463476f0110f65e08fd821",
            receipt["release_commit"],
        )
        self.assertEqual("MIT", receipt["package"]["license"])
        self.assertEqual("LICENSE.md", receipt["package"]["license_file"])
        self.assertEqual(12, receipt["package"]["file_count"])
        self.assertEqual(
            "e3873160e4806f1192df3a1afbf256d515b18523af679524fe161f5c2901fe5f",
            receipt["package"]["zip_sha256"],
        )
        self.assertEqual(368620368, receipt["github"]["release_id"])
        self.assertEqual(98987, receipt["skillhub"]["skill_id"])
        self.assertEqual(229892, receipt["skillhub"]["version_id"])
        self.assertEqual("pending", receipt["skillhub"]["review_status_at_upload"])
        self.assertEqual("0.0.9", receipt["skillhub"]["public_search_visible_version"])
        self.assertEqual("PASS", receipt["skillhub"]["signature_verify_status"])
        self.assertTrue(receipt["skillhub"]["signature"]["content_hash_match"])
        self.assertEqual(["clawhub"], receipt["excluded_publish_targets"])
        self.assertFalse(receipt["cover"]["included_in_package"])
        self.assertFalse(receipt["cover"]["uploaded_to_skillhub"])
        self.assertEqual(164, receipt["validation"]["full_unittest_count"])


if __name__ == "__main__":
    unittest.main()
