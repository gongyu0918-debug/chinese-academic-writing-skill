from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attribution_common
import make_attribution_maps
import make_attribution_packets
import revalidate_attribution_judges
import run_attribution_judges
import score_attribution


class AttributionJudgingTests(unittest.TestCase):
    def test_four_replicate_causal_threshold_is_symmetric(self) -> None:
        self.assertEqual("CAUSAL_HARM", score_attribution.causal_decision(4, 3, 0))
        self.assertEqual("CAUSAL_BENEFIT", score_attribution.causal_decision(4, 0, 3))
        self.assertEqual("NO_DIRECTIONAL_SIGNAL", score_attribution.causal_decision(4, 1, 1))
        self.assertEqual("AMBIGUOUS", score_attribution.causal_decision(4, 2, 0))
        self.assertEqual("INSUFFICIENT", score_attribution.causal_decision(3, 3, 0))

    def test_majority_ignores_uncertain_but_requires_two_definite_votes(self) -> None:
        self.assertEqual("PRESENT", score_attribution.majority_label(["PRESENT", "UNCERTAIN", "PRESENT"]))
        self.assertIsNone(score_attribution.majority_label(["PRESENT", "ABSENT", "UNCERTAIN"]))

    def test_final_validator_requires_exact_targets_and_verbatim_anchor(self) -> None:
        payload = {
            "schema_version": 1,
            "judge_id": "judge-1",
            "blind": True,
            "mapping_sha256": "a" * 64,
            "packet_sha256": "b" * 64,
            "task_id": "A1-R1",
            "pair_id": "J01-P001",
            "targets": [
                {
                    "target_id": "FALSE_CROSS_SOURCE_LINK",
                    "left": {
                        "label": "PRESENT",
                        "anchors": [{"quote": "一致信号", "reason": "把不显著结果写成一致"}],
                    },
                    "right": {"label": "ABSENT", "anchors": []},
                }
            ],
            "unrelated_errors": {"left": [], "right": []},
        }
        final = json.dumps(payload, ensure_ascii=False)
        issues = attribution_common.validate_final(
            final,
            "judge-1",
            "A1-R1",
            "J01-P001",
            "a" * 64,
            "b" * 64,
            "稿件声称形成一致信号。",
            "右稿克制。",
        )
        self.assertEqual([], issues)
        payload["targets"][0]["left"]["anchors"][0]["quote"] = "原稿中不存在"
        issues = attribution_common.validate_final(
            json.dumps(payload, ensure_ascii=False),
            "judge-1",
            "A1-R1",
            "J01-P001",
            "a" * 64,
            "b" * 64,
            "稿件声称形成一致信号。",
            "右稿克制。",
        )
        self.assertIn("FALSE_CROSS_SOURCE_LINK:left:anchor_not_verbatim", issues)

    def test_unrelated_error_quote_drift_does_not_invalidate_target_vote(self) -> None:
        payload = {
            "schema_version": 1,
            "judge_id": "judge-1",
            "blind": True,
            "mapping_sha256": "a" * 64,
            "packet_sha256": "b" * 64,
            "task_id": "A1-R1",
            "pair_id": "J01-P001",
            "targets": [
                {
                    "target_id": "FALSE_CROSS_SOURCE_LINK",
                    "left": {"label": "ABSENT", "anchors": []},
                    "right": {"label": "ABSENT", "anchors": []},
                }
            ],
            "unrelated_errors": {
                "left": [],
                "right": [{"code": "MARKDOWN_DRIFT", "quote": "省略了反引号的日志引用"}],
            },
        }
        issues = attribution_common.validate_final(
            json.dumps(payload, ensure_ascii=False),
            "judge-1",
            "A1-R1",
            "J01-P001",
            "a" * 64,
            "b" * 64,
            "左稿。",
            "右稿包含 `带反引号` 的原文。",
        )
        self.assertEqual([], issues)

    def test_judge_revalidation_refuses_to_overwrite_concurrent_change(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            manifest_root = Path(folder)
            judge_path = manifest_root / "judge-2.json"
            judge_path.write_bytes(b"concurrent-update")
            with mock.patch.object(
                revalidate_attribution_judges,
                "MANIFEST_ROOT",
                manifest_root,
            ):
                with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
                    revalidate_attribution_judges.rollback_changed_manifest(
                        b"original",
                        b"our-corrected-version",
                    )
            self.assertEqual(b"concurrent-update", judge_path.read_bytes())

    def test_judge_manifest_write_lock_rejects_competing_writer(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lock_path = root / ".judge-manifests.write.lock"
            with mock.patch.multiple(
                run_attribution_judges,
                ATTRIBUTION_ROOT=root,
                MANIFEST_WRITE_LOCK=lock_path,
            ):
                with run_attribution_judges.judge_manifest_write_lock():
                    with self.assertRaisesRegex(RuntimeError, "already active"):
                        with run_attribution_judges.judge_manifest_write_lock():
                            self.fail("a competing writer acquired the same lock")
                self.assertFalse(lock_path.exists())

    def test_fixed_orientations_are_balanced_and_independent(self) -> None:
        tasks = [f"A1-R{index}" for index in range(1, 5)] + [f"A2-R{index}" for index in range(1, 5)] + [f"A3-R{index}" for index in range(1, 5)]
        orientations = [
            tuple(attribution_common.expected_orientations(tasks, judge))
            for judge in attribution_common.JUDGES
        ]
        self.assertEqual(3, len(set(orientations)))
        self.assertTrue(all(sum(row) == 6 for row in orientations))

    def test_judge_protocol_hashes_are_preregistered(self) -> None:
        self.assertEqual(
            attribution_common.EXPECTED_INSTRUCTIONS_SHA256,
            attribution_common.sha256_file(attribution_common.INSTRUCTIONS_PATH),
        )
        self.assertEqual(
            attribution_common.EXPECTED_SCHEMA_SHA256,
            attribution_common.sha256_file(attribution_common.SCHEMA_PATH),
        )

    def test_map_builder_atomically_emits_all_three_maps(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "maps"
            self.assertEqual(0, make_attribution_maps.build(output))
            self.assertEqual(
                {"judge-1.json", "judge-2.json", "judge-3.json"},
                {path.name for path in output.glob("*.json")},
            )
            for path in output.glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(12, len(payload["mappings"]))
                self.assertEqual(6, sum(row["left"] == "candidate" for row in payload["mappings"]))

    def test_packet_builder_rejects_partial_judge_set_before_writing(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "all three"):
            make_attribution_packets.build(["judge-1"])

    def test_judge_record_closure_rejects_forged_success_flags(self) -> None:
        forged = {
            "judge_id": "wrong",
            "task_id": "A1-R1",
            "model": "wrong",
            "reasoning_effort": "low",
            "return_code": 17,
            "timeout": True,
            "retry_count": 9,
            "duration_seconds": -1,
            "valid": True,
            "issues": [],
        }
        issues = run_attribution_judges.judge_record_execution_issues(
            forged,
            "judge-1",
            "A1-R1",
        )
        self.assertIn("record_judge_id_mismatch", issues)
        self.assertIn("record_return_code_mismatch", issues)
        self.assertIn("record_timeout_mismatch", issues)
        self.assertIn("record_duration_invalid", issues)

    def test_third_judge_trigger_covers_disagreement_and_uncertainty(self) -> None:
        target = "FALSE_CROSS_SOURCE_LINK"
        agreed = {
            "judge-1": {target: {"baseline": "ABSENT", "candidate": "PRESENT"}},
            "judge-2": {target: {"baseline": "ABSENT", "candidate": "PRESENT"}},
        }
        self.assertFalse(run_attribution_judges.needs_third_judge(agreed, (target,)))
        disagreed = json.loads(json.dumps(agreed))
        disagreed["judge-2"][target]["candidate"] = "ABSENT"
        self.assertTrue(run_attribution_judges.needs_third_judge(disagreed, (target,)))
        uncertain = json.loads(json.dumps(agreed))
        uncertain["judge-1"][target]["baseline"] = "UNCERTAIN"
        self.assertTrue(run_attribution_judges.needs_third_judge(uncertain, (target,)))


if __name__ == "__main__":
    unittest.main()
