from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_attribution


class AttributionRunnerTests(unittest.TestCase):
    def test_matrix_has_three_groups_four_replicates_and_two_arms(self) -> None:
        payload, digest = run_attribution.load_specs_snapshot()
        self.assertEqual(64, len(digest))
        self.assertEqual(12, len(payload["tasks"]))
        observed = {
            (row["group"], row["replicate"], row["source_task"], row["provider"])
            for row in payload["tasks"]
        }
        expected = {
            (group, replicate, source_task, provider)
            for group, (source_task, provider) in run_attribution.EXPECTED_GROUPS.items()
            for replicate in (1, 2, 3, 4)
        }
        self.assertEqual(expected, observed)
        self.assertEqual(("baseline", "candidate"), run_attribution.ARMS)

    def test_preflight_identity_includes_attribution_freeze(self) -> None:
        payload = {
            "baseline": {"commit": "b", "runtime_fingerprint": "bf"},
            "candidate": {"commit": "c", "runtime_fingerprint": "cf"},
            "source_ab_specs_sha256": "main-specs",
            "task_sha256": {"H2": "task"},
            "prompt_sha256": {"H2": "prompt"},
            "attribution_specs_sha256": "attribution-specs",
            "attribution_tasks": ["A2-R1"],
            "providers": [{"name": "alibaba", "model": "model"}],
        }
        identity = run_attribution.input_identity(payload)
        self.assertEqual("attribution-specs", identity["attribution_specs_sha256"])
        self.assertEqual(["A2-R1"], identity["attribution_tasks"])
        self.assertEqual(identity, json.loads(json.dumps(identity)))

    def test_preflight_rejects_unregistered_candidate_before_dependency(self) -> None:
        with mock.patch.object(run_attribution, "load_specs_snapshot") as load_specs:
            with self.assertRaisesRegex(RuntimeError, "candidate commit must be"):
                run_attribution.preflight_payload("unexpected")
        load_specs.assert_not_called()

    def test_specs_reject_wrong_arms_or_judges(self) -> None:
        original = run_attribution.SPECS_PATH
        payload = original.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            temp_path = Path(tmp) / "specs.json"
            temp_path.write_text(payload.replace('"baseline", "candidate"', '"wrong"'), encoding="utf-8")
            with mock.patch.object(run_attribution, "SPECS_PATH", temp_path):
                with self.assertRaisesRegex(RuntimeError, "arms or judges"):
                    run_attribution.load_specs_snapshot()

    def test_record_closure_rejects_missing_records(self) -> None:
        specs, _ = run_attribution.load_specs_snapshot()
        preflight = {
            "providers": [{"name": name, "model": model} for name, model in run_attribution.EXPECTED_MODELS.items()],
        }
        issues = run_attribution.record_closure_issues([], specs, preflight, Path("unused"))
        self.assertIn("record_count:0:24", issues)
        self.assertIn("record_coverage_mismatch", issues)

    def test_record_closure_recomputes_final_shape_and_trace(self) -> None:
        row = {
            "task_id": "A2-R1",
            "group": "A2",
            "replicate": 1,
            "source_task": "H2",
            "provider": "alibaba",
        }
        specs = {"tasks": [row]}
        preflight = {
            "providers": [
                {
                    "name": "alibaba",
                    "model": run_attribution.EXPECTED_MODELS["alibaba"],
                }
            ],
            "prompt_sha256": {"H2": "prompt"},
            "baseline": {"commit": "b", "runtime_fingerprint": "bf"},
            "candidate": {"commit": "c", "runtime_fingerprint": "cf"},
        }
        with tempfile.TemporaryDirectory() as folder:
            staging = Path(folder)
            records = []
            for arm in run_attribution.ARMS:
                final_path = staging / "raw" / arm / "A2-R1.md"
                trace_path = staging / "traces" / arm / "A2-R1.jsonl"
                stderr_path = staging / "stderr" / arm / "A2-R1.txt"
                for path in (final_path, trace_path, stderr_path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                final_path.write_text("ENV_INVALID", encoding="utf-8")
                trace_path.write_text("{}\n", encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                records.append(
                    {
                        "pair_id": "A2-R1",
                        "source_task": "H2",
                        "group": "A2",
                        "replicate": 1,
                        "arm": arm,
                        "provider": "alibaba",
                        "model": run_attribution.EXPECTED_MODELS["alibaba"],
                        "reasoning_effort": "max",
                        "retry_count": 0,
                        "commit": preflight[arm]["commit"],
                        "runtime_fingerprint": preflight[arm]["runtime_fingerprint"],
                        "prompt_sha256": "prompt",
                        "prompt_bound": True,
                        "return_code": 0,
                        "timeout": False,
                        "final_shape_valid": True,
                        "valid": True,
                        "trace_issues": [],
                        "pre_read_preamble_count": 0,
                        "final_chars_no_whitespace": len("ENV_INVALID"),
                        "final_file": f"raw/{arm}/A2-R1.md",
                        "final_sha256": run_attribution.sha256_bytes(b"ENV_INVALID"),
                        "trace_file": f"traces/{arm}/A2-R1.jsonl",
                        "trace_sha256": run_attribution.sha256_file(trace_path),
                        "stderr_file": f"stderr/{arm}/A2-R1.txt",
                        "stderr_sha256": run_attribution.sha256_file(stderr_path),
                    }
                )
            issues = run_attribution.record_closure_issues(records, specs, preflight, staging)
        self.assertIn("record_final_shape_recomputed_invalid:A2-R1:baseline", issues)
        self.assertIn("record_trace_recomputed_invalid:A2-R1:candidate", issues)


if __name__ == "__main__":
    unittest.main()
