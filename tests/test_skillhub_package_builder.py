import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_skillhub_package.py"
POLICY_PATH = ROOT / "tools" / "skillhub-package-policy.json"
CANONICAL_SKILL = ROOT / "chinese-academic-writing-assistant" / "SKILL.md"
ICON_PATH = ROOT / "assets" / "skillhub-icon.png"
SPEC = importlib.util.spec_from_file_location("skillhub_package_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load build_skillhub_package.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def parse_simple_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    _, raw, _ = text.split("---\n", 2)
    fields: dict[str, object] = {}
    for line in raw.splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("["):
            fields[key] = json.loads(value)
        else:
            fields[key] = json.loads(value)
    return fields


class SkillHubPackageBuilderTests(unittest.TestCase):
    def test_build_is_minimal_metadata_valid_and_deterministic(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        expected_files = sorted(policy["skillhub_package"]["files"])
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out1 = tmp_path / "package-1"
            out2 = tmp_path / "package-2"
            zip1 = tmp_path / "package-1.zip"
            zip2 = tmp_path / "package-2.zip"
            first = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "0.0.9",
                    "--output-dir",
                    str(out1),
                    "--zip",
                    str(zip1),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            second = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "0.0.9",
                    "--output-dir",
                    str(out2),
                    "--zip",
                    str(zip2),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual("0.0.9", json.loads(first.stdout)["version"])

            actual = sorted(path.relative_to(out1).as_posix() for path in out1.rglob("*") if path.is_file())
            self.assertEqual(expected_files, actual)
            self.assertEqual(12, len(actual))
            self.assertLess(zip1.stat().st_size, 10 * 1024 * 1024)
            self.assertEqual(hashlib.sha256(zip1.read_bytes()).digest(), hashlib.sha256(zip2.read_bytes()).digest())
            with zipfile.ZipFile(zip1) as archive:
                self.assertEqual(expected_files, sorted(archive.namelist()))

            metadata = parse_simple_frontmatter(out1 / "SKILL.md")
            self.assertEqual(
                {"name", "description", "slug", "version", "displayName", "tags", "license"},
                set(metadata),
            )
            self.assertEqual("chinese-academic-writing-assistant", metadata["slug"])
            self.assertEqual("中文论文写作", metadata["displayName"])
            self.assertEqual(["chinese", "academic"], metadata["tags"])
            self.assertEqual("MIT", metadata["license"])
            self.assertIn("依据作者材料、文献或授权来源", metadata["description"])
            self.assertNotIn("材料不足时降级交付", metadata["description"])
            self.assertNotIn("不处理统计有效性", metadata["description"])
            self.assertNotIn("github.com", (out1 / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])

            canonical_body = BUILDER.split_frontmatter(CANONICAL_SKILL.read_text(encoding="utf-8"))[1]
            built_body = BUILDER.split_frontmatter((out1 / "SKILL.md").read_text(encoding="utf-8"))[1]
            self.assertEqual(canonical_body, built_body)

    def test_invalid_version_and_existing_destination_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            invalid = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "next",
                    "--output-dir",
                    str(tmp_path / "invalid-version"),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            destination = tmp_path / "existing"
            destination.mkdir()
            existing = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "0.0.9",
                    "--output-dir",
                    str(destination),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
        self.assertEqual(2, invalid.returncode)
        self.assertIn("version is not valid SemVer", invalid.stderr)
        self.assertEqual(2, existing.returncode)
        self.assertIn("output directory already exists", existing.stderr)

    def test_policy_rejects_traversal_absolute_and_reserved_paths(self) -> None:
        base = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.json"
            for unsafe in ("../secret.md", "/absolute.md", "C:\\secret.md", "CON.txt"):
                policy = json.loads(json.dumps(base))
                policy["skillhub_package"]["files"][0] = unsafe
                policy_path.write_text(json.dumps(policy), encoding="utf-8")
                with self.subTest(unsafe=unsafe):
                    with self.assertRaisesRegex(ValueError, "unsafe package path"):
                        BUILDER.read_policy(policy_path)

            for key in ("root", "license_source", "markdown_license"):
                policy = json.loads(json.dumps(base))
                policy["skillhub_package"][key] = "../external"
                policy_path.write_text(json.dumps(policy), encoding="utf-8")
                with self.subTest(key=key):
                    with self.assertRaisesRegex(ValueError, "unsafe package path"):
                        BUILDER.read_policy(policy_path)

            direct_policy = json.loads(json.dumps(base))
            direct_policy["skillhub_package"]["root"] = "../external"
            with self.assertRaisesRegex(ValueError, "package root escapes"):
                BUILDER.materialize_package("0.0.9", Path(tmp) / "output", direct_policy)

    def test_zip_inside_package_is_rejected_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "package"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "0.0.9",
                    "--output-dir",
                    str(output),
                    "--zip",
                    str(output / "nested.zip"),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("zip output must be outside", result.stderr)
            self.assertFalse(output.exists())

    def test_existing_or_failed_zip_never_leaves_a_package_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            existing_zip = tmp_path / "existing.zip"
            existing_zip.write_bytes(b"already here")
            output = tmp_path / "preflight-output"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BUILDER_PATH),
                    "--version",
                    "0.0.9",
                    "--output-dir",
                    str(output),
                    "--zip",
                    str(existing_zip),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("zip output already exists", result.stderr)
            self.assertFalse(output.exists())

            failed_output = tmp_path / "failed-output"
            failed_zip = tmp_path / "failed.zip"
            with mock.patch.object(BUILDER, "create_deterministic_zip", side_effect=OSError("simulated")):
                with self.assertRaisesRegex(OSError, "simulated"):
                    BUILDER.build("0.0.9", failed_output, failed_zip)
            self.assertFalse(failed_output.exists())
            self.assertFalse(failed_zip.exists())

    def test_generated_icon_is_github_only_square_png(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertIn("assets/**", policy["github_only_surfaces"])
        self.assertNotIn("assets/skillhub-icon.png", policy["skillhub_package"]["files"])
        data = ICON_PATH.read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual(width, height)
        self.assertGreaterEqual(width, 512)
        self.assertLess(len(data), 5 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
