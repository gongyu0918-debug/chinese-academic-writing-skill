import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "sanitize_public_eval_logs.py"
SPEC = importlib.util.spec_from_file_location("public_log_sanitizer", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load sanitize_public_eval_logs.py")
SANITIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SANITIZER)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PublicLogSanitizerTests(unittest.TestCase):
    def test_redacts_internal_url_path_and_opaque_keys(self) -> None:
        source = (
            'request failed url (https://chatgpt.com/backend-api/catalog?limit=200&pageToken=opaque-token) '
            'endpoint_host="chatgpt.com" endpoint_path="/backend-api/run/query/leaf" '
            'session_id=opaque-session'
        )
        redacted, count = SANITIZER.redact_text(source)
        self.assertGreaterEqual(count, 3)
        self.assertNotIn("chatgpt.com", redacted)
        self.assertNotIn("opaque-token", redacted)
        self.assertNotIn("opaque-session", redacted)
        self.assertIn("<redacted", redacted)

    def test_unrelated_stderr_is_unchanged(self) -> None:
        source = "warning: model response ended without retry"
        self.assertEqual((source, 0), SANITIZER.redact_text(source))

    def test_check_covers_markdown_and_json_not_only_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "note.md").write_text("internal host chatgpt.com", encoding="utf-8")
            self.assertEqual(["note.md"], SANITIZER.check_public_tree(root))

    def test_apply_backs_up_and_propagates_nested_hash_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            public = base / "public"
            private = base / "private"
            public.mkdir()
            stderr = public / "call.stderr.txt"
            stderr.write_text(
                "failed https://chatgpt.com/backend-api/catalog?pageToken=secret-token\n",
                encoding="utf-8",
            )
            original_stderr_hash = sha256(stderr.read_bytes())
            manifest = public / "manifest.json"
            manifest.write_text(
                json.dumps({"stderr_file": stderr.name, "stderr_sha256": original_stderr_hash}) + "\n",
                encoding="utf-8",
            )
            original_manifest_hash = sha256(manifest.read_bytes())
            parent = public / "parent.json"
            parent.write_text(
                json.dumps({"manifest_sha256": original_manifest_hash}) + "\n",
                encoding="utf-8",
            )
            report_path = public / "PUBLIC-LOG-REDACTION.json"

            report = SANITIZER.apply_redaction(public, private, report_path)

            self.assertEqual(1, report["stderr_files_redacted"])
            self.assertEqual([], SANITIZER.check_public_tree(public))
            self.assertTrue((private / "call.stderr.txt").is_file())
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(sha256(stderr.read_bytes()), manifest_payload["stderr_sha256"])
            parent_payload = json.loads(parent.read_text(encoding="utf-8"))
            self.assertEqual(sha256(manifest.read_bytes()), parent_payload["manifest_sha256"])
            self.assertTrue(report_path.is_file())


if __name__ == "__main__":
    unittest.main()
