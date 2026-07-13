#!/usr/bin/env python3
"""Read-only validation for academic-writing writer/verifier evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_CASE_KEYS = {
    "id",
    "prompt",
    "expected_route",
    "expected_reference",
    "expected_mode",
    "material_state",
    "research_stage",
    "output_protocol",
    "scope",
    "minimum_output_chars",
    "immutable_literals",
    "required_markers",
    "forbidden_claims",
    "allowed_degradation",
}
PROTECTED_PATHS = (
    "chinese-academic-writing-assistant",
    "tests/fixtures/academic-smoke.jsonl",
    "tests/test_context_and_runtime.py",
    "tests/test_output_checker.py",
    "tests/test_skill_contract.py",
    "tools/check_academic_outputs.py",
)
RUNTIME_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/academic-writing.md",
    "references/academic-proposal.md",
    "references/academic-literature-review.md",
)
STRICT_COMPARISONS: set[str] = set()
CONTEXT_CONFIGURATIONS = {"entry-only", "entry-correct-leaf", "entry-all-leaves"}
MATERIAL_ABLATIONS = {
    "remove-sources",
    "weaken-causal-evidence",
    "tamper-metadata",
    "remove-school-template",
}
ALLOWED_VERDICTS = {"PASS", "WARN", "FAIL", "BLOCK"}
VERIFIER_DIMENSIONS = ("adherence_verdict", "orchestration_verdict")
VERIFIER_PAYLOAD_KEYS = {
    "verifier_id",
    "model_id",
    "blind",
    "sealed_at",
    "packet_set_sha256",
    "criteria",
    "results",
}
VERIFIER_RESULT_KEYS = {
    "sample_id",
    "prompt_sha256",
    "output_sha256",
    "verdict",
    "adherence_verdict",
    "orchestration_verdict",
    "adherence_evidence",
    "orchestration_evidence",
    "anchors",
    "hard_failures",
    "style_warnings",
}


class EvidenceError(ValueError):
    """Raised for malformed deterministic evidence."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON in {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise EvidenceError(f"invalid UTF-8 in {path}: {exc}") from exc


def read_utf8_bytes(path: Path) -> tuple[bytes, str]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise EvidenceError(f"missing file: {path}") from exc
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError(f"invalid UTF-8 in {path}: {exc}") from exc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise EvidenceError(f"missing file: {path}") from exc


def load_cases(path: Path) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise EvidenceError(f"missing cases file: {path}") from exc
    except UnicodeDecodeError as exc:
        raise EvidenceError(f"invalid UTF-8 in {path}: {exc}") from exc
    except OSError as exc:
        raise EvidenceError(f"unable to read cases file {path}: {exc}") from exc

    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            case = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EvidenceError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(case, dict):
            raise EvidenceError(f"case at {path}:{line_number} must be an object")
        missing = REQUIRED_CASE_KEYS - set(case)
        if missing:
            raise EvidenceError(
                f"case at {path}:{line_number} missing keys: {sorted(missing)}"
            )
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id:
            raise EvidenceError(f"invalid case id at {path}:{line_number}")
        if case_id in cases:
            raise EvidenceError(f"duplicate case id: {case_id}")
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise EvidenceError(f"empty prompt for case {case_id}")
        for key in (
            "expected_route",
            "expected_mode",
            "material_state",
            "research_stage",
            "output_protocol",
            "scope",
        ):
            if not isinstance(case[key], str) or not case[key]:
                raise EvidenceError(f"{case_id}.{key} must be a non-empty string")
        if case["expected_reference"] is not None and not isinstance(
            case["expected_reference"], str
        ):
            raise EvidenceError(f"{case_id}.expected_reference must be a string or null")
        minimum = case["minimum_output_chars"]
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
            raise EvidenceError(f"{case_id}.minimum_output_chars must be a positive integer")
        for key in (
            "immutable_literals",
            "required_markers",
            "forbidden_claims",
            "allowed_degradation",
        ):
            value = case[key]
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise EvidenceError(f"{case_id}.{key} must be a string list")
        cases[case_id] = case
    if not cases:
        raise EvidenceError(f"no cases found in {path}")
    return cases


def check_output(case: dict[str, Any], output: str) -> list[str]:
    """Return deterministic errors; semantic quality remains with blind verifiers."""
    errors: list[str] = []
    stripped = output.strip()
    if not stripped:
        return ["output is empty"]
    if len(stripped) < case["minimum_output_chars"]:
        errors.append(
            f"output too short: {len(stripped)} < {case['minimum_output_chars']} characters"
        )
    for literal in case["immutable_literals"]:
        if literal not in output:
            errors.append(f"missing immutable literal: {literal!r}")
    for marker in case["required_markers"]:
        if marker not in output:
            errors.append(f"missing required marker: {marker!r}")
    for claim in case["forbidden_claims"]:
        if claim in output:
            errors.append(f"forbidden exact claim present: {claim!r}")
    return errors


def resolve_evidence_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise EvidenceError(f"{label} must be a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise EvidenceError(f"{label} must be relative: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise EvidenceError(f"{label} escapes evidence root: {relative}")
    return resolved


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def normalize_packet_text(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip("\n")


def git_binding_errors(
    manifest: dict[str, Any], repo_root: Path | None, cases_path: Path | None
) -> list[str]:
    errors: list[str] = []
    if repo_root is None or cases_path is None:
        return ["strict evidence validation requires repo_root and cases_path"]
    repo_root = repo_root.resolve()
    candidate = manifest.get("candidate_commit", "")
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
        return ["manifest.candidate_commit must be a full 40-character lowercase SHA"]

    commit_probe = subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_probe.returncode != 0:
        errors.append(f"candidate_commit does not exist in the local repository: {candidate}")
        return errors

    tested_paths = manifest.get("tested_paths")
    if tested_paths != list(PROTECTED_PATHS):
        errors.append("manifest.tested_paths does not match the protected candidate surface")
    diff_probe = subprocess.run(
        ["git", "diff", "--quiet", candidate, "--", *PROTECTED_PATHS],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_probe.returncode == 1:
        errors.append("protected candidate files differ from manifest.candidate_commit")
    elif diff_probe.returncode != 0:
        errors.append(f"unable to compare protected candidate files: {diff_probe.stderr.strip()}")

    try:
        actual_fixture_hash = sha256_file(cases_path.resolve())
    except EvidenceError as exc:
        errors.append(str(exc))
    else:
        if manifest.get("fixture_sha256") != actual_fixture_hash:
            errors.append("manifest.fixture_sha256 does not match the cases file")

    runtime_hashes = manifest.get("runtime_sha256")
    if not isinstance(runtime_hashes, dict) or set(runtime_hashes) != set(RUNTIME_FILES):
        errors.append("manifest.runtime_sha256 must cover the exact five runtime files")
    else:
        for relative in RUNTIME_FILES:
            try:
                actual = sha256_file(
                    repo_root / "chinese-academic-writing-assistant" / relative
                )
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if runtime_hashes.get(relative) != actual:
                errors.append(f"runtime SHA-256 mismatch: {relative}")
    return errors


def validate_artifacts(
    evidence_root: Path, label: str, rows: Any
) -> tuple[list[str], dict[str, tuple[Path, str]]]:
    errors: list[str] = []
    artifacts: dict[str, tuple[Path, str]] = {}
    if not isinstance(rows, list) or not rows:
        return [f"comparison {label} must contain artifact records"], artifacts
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"comparison {label} artifact {index} must be an object")
            continue
        relative = row.get("path")
        try:
            path = resolve_evidence_path(
                evidence_root, relative, f"comparison {label} artifact {index}"
            )
            raw, text = read_utf8_bytes(path)
        except EvidenceError as exc:
            errors.append(str(exc))
            continue
        normalized_relative = relative_posix(path, evidence_root)
        if relative != normalized_relative:
            errors.append(
                f"comparison {label} artifact path must be normalized: {relative!r}"
            )
        if normalized_relative in artifacts:
            errors.append(f"comparison {label} repeats artifact {normalized_relative}")
            continue
        if row.get("sha256") != sha256_bytes(raw):
            errors.append(f"comparison {label} artifact SHA-256 mismatch: {relative}")
        minimum = row.get("minimum_chars", 40)
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
            errors.append(f"comparison {label} artifact has invalid minimum_chars: {relative}")
        elif len(text.strip()) < minimum:
            errors.append(
                f"comparison {label} artifact too short: {relative} "
                f"({len(text.strip())} < {minimum})"
            )
        artifacts[normalized_relative] = (path, text)
    return errors, artifacts


def validate_dimension_record(
    label: str, record: dict[str, Any], artifacts: dict[str, tuple[Path, str]]
) -> list[str]:
    errors: list[str] = []
    artifact = record.get("artifact")
    if artifact not in artifacts:
        errors.append(f"{label} references an unregistered artifact: {artifact!r}")
    for dimension in VERIFIER_DIMENSIONS:
        verdict = record.get(dimension)
        if verdict not in {"PASS", "WARN"}:
            errors.append(f"{label} {dimension} must be PASS or WARN, found {verdict!r}")
    if record.get("hard_failures") != []:
        errors.append(f"{label} hard_failures must be empty")
    rationale = record.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < 40:
        errors.append(f"{label} must include a substantive rationale")
    return errors


def validate_comparison(
    evidence_root: Path,
    label: str,
    comparison: Any,
    cases: dict[str, dict[str, Any]],
    writer_output_paths: set[str],
    reserved_context_ids: set[str],
) -> list[str]:
    if not isinstance(comparison, dict):
        return [f"comparison {label} must be a JSON object"]
    errors: list[str] = []
    if comparison.get("kind") != label:
        errors.append(f"comparison {label} kind mismatch")
    if comparison.get("status") != "PASS":
        errors.append(f"comparison {label} status is not PASS")
    if comparison.get("hard_failures") != []:
        errors.append(f"comparison {label} hard_failures must be empty")
    basis = comparison.get("decision_basis")
    if not isinstance(basis, str) or len(basis.strip()) < 80:
        errors.append(f"comparison {label} must include an 80-character decision basis")
    artifact_errors, artifacts = validate_artifacts(
        evidence_root, label, comparison.get("artifacts")
    )
    errors.extend(artifact_errors)

    def register_context(record: dict[str, Any], record_label: str) -> None:
        context_id = record.get("context_id")
        if not isinstance(context_id, str) or not context_id:
            errors.append(f"{record_label} has invalid context_id")
        elif context_id in reserved_context_ids:
            errors.append(f"{record_label} reuses context_id {context_id}")
        else:
            reserved_context_ids.add(context_id)

    if label == "baseline":
        pairs = comparison.get("pairs")
        if not isinstance(pairs, list) or len(pairs) < 3:
            errors.append("baseline comparison requires at least 3 paired cases")
            pairs = []
        seen_cases: set[str] = set()
        baseline_outputs: set[str] = set()
        candidate_outputs: set[str] = set()
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                errors.append(f"baseline pair {index} must be an object")
                continue
            case_id = pair.get("case_id")
            if case_id not in cases or case_id in seen_cases:
                errors.append(f"baseline pair {index} has invalid or duplicate case_id")
            seen_cases.add(case_id)
            register_context(pair, f"baseline pair {case_id}")
            candidate_output = pair.get("candidate_output")
            baseline_output = pair.get("baseline_output")
            if baseline_output in baseline_outputs:
                errors.append(f"baseline pair {case_id} reuses a baseline output")
            baseline_outputs.add(str(baseline_output))
            if candidate_output in candidate_outputs:
                errors.append(f"baseline pair {case_id} reuses a candidate output")
            candidate_outputs.add(str(candidate_output))
            if candidate_output not in writer_output_paths:
                errors.append(
                    f"baseline pair {case_id} candidate_output is not a writer artifact"
                )
            if baseline_output == candidate_output:
                errors.append(f"baseline pair {case_id} reuses the candidate output")
            record = dict(pair)
            record["artifact"] = baseline_output
            errors.extend(
                validate_dimension_record(f"baseline pair {case_id}", record, artifacts)
            )
            if candidate_output not in artifacts:
                errors.append(
                    f"baseline pair {case_id} candidate output lacks an artifact hash"
                )
        metrics = comparison.get("metrics")
        expected_metrics = {"pairs": len(pairs), "hard_failures": 0}
        if metrics != expected_metrics:
            errors.append(f"baseline metrics mismatch: expected {expected_metrics!r}")

    elif label == "context_ablation":
        runs = comparison.get("runs")
        if not isinstance(runs, list) or len(runs) != 9:
            errors.append("context ablation requires exactly 9 runs")
            runs = []
        by_case: dict[str, set[str]] = {}
        run_artifacts: set[str] = set()
        configuration_packets: set[str] = set()
        for index, run in enumerate(runs):
            if not isinstance(run, dict):
                errors.append(f"context run {index} must be an object")
                continue
            case_id = run.get("case_id")
            configuration = run.get("configuration")
            if case_id not in cases:
                errors.append(f"context run {index} has unknown case_id")
            if configuration not in CONTEXT_CONFIGURATIONS:
                errors.append(f"context run {index} has invalid configuration")
            by_case.setdefault(str(case_id), set()).add(str(configuration))
            register_context(run, f"context run {index}")
            artifact = run.get("artifact")
            if artifact in run_artifacts:
                errors.append(f"context run {index} reuses output artifact {artifact!r}")
            run_artifacts.add(str(artifact))
            configuration_packet = run.get("configuration_packet")
            if configuration_packet == artifact:
                errors.append(f"context run {index} reuses output as configuration packet")
            if configuration_packet not in artifacts:
                errors.append(
                    f"context run {index} references unknown configuration packet"
                )
            elif configuration_packet in configuration_packets:
                errors.append(f"context run {index} reuses a configuration packet")
            else:
                configuration_packets.add(configuration_packet)
                packet_path, packet_text = artifacts[configuration_packet]
                if run.get("configuration_sha256") != sha256_file(packet_path):
                    errors.append(f"context run {index} configuration SHA-256 mismatch")
                if cases.get(case_id, {}).get("prompt", "") not in packet_text:
                    errors.append(f"context run {index} packet lacks the case prompt")
                if str(configuration) not in packet_text:
                    errors.append(f"context run {index} packet lacks its configuration label")
            if case_id in cases and run.get("input_sha256") != sha256_text(
                cases[case_id]["prompt"]
            ):
                errors.append(f"context run {index} input SHA-256 mismatch")
            errors.extend(
                validate_dimension_record(f"context run {index}", run, artifacts)
            )
        if len(by_case) != 3 or any(
            configurations != CONTEXT_CONFIGURATIONS
            for configurations in by_case.values()
        ):
            errors.append("context ablation must cover 3 cases under all 3 configurations")
        metrics = comparison.get("metrics")
        expected_metrics = {
            "runs": len(runs),
            "cases": len(by_case),
            "configurations": len(CONTEXT_CONFIGURATIONS),
            "hard_failures": 0,
        }
        if metrics != expected_metrics:
            errors.append(f"context ablation metrics mismatch: expected {expected_metrics!r}")

    elif label == "material_ablation":
        runs = comparison.get("runs")
        if not isinstance(runs, list) or len(runs) < 4:
            errors.append("material ablation requires at least 4 runs")
            runs = []
        groups: set[str] = set()
        run_artifacts: set[str] = set()
        ablation_packets: set[str] = set()
        for index, run in enumerate(runs):
            if not isinstance(run, dict):
                errors.append(f"material run {index} must be an object")
                continue
            ablation = run.get("ablation")
            if ablation not in MATERIAL_ABLATIONS:
                errors.append(f"material run {index} has invalid ablation")
            groups.add(str(ablation))
            case_id = run.get("case_id")
            if case_id not in cases:
                errors.append(f"material run {index} has unknown case_id")
            register_context(run, f"material run {index}")
            artifact = run.get("artifact")
            if artifact in run_artifacts:
                errors.append(f"material run {index} reuses output artifact {artifact!r}")
            run_artifacts.add(str(artifact))
            ablation_packet = run.get("ablation_packet")
            if ablation_packet == artifact:
                errors.append(f"material run {index} reuses output as ablation packet")
            if ablation_packet not in artifacts:
                errors.append(f"material run {index} references unknown ablation packet")
            elif ablation_packet in ablation_packets:
                errors.append(f"material run {index} reuses an ablation packet")
            else:
                ablation_packets.add(ablation_packet)
                packet_path, _ = artifacts[ablation_packet]
                try:
                    packet = read_json(packet_path)
                except EvidenceError as exc:
                    errors.append(str(exc))
                    packet = None
                if not isinstance(packet, dict):
                    errors.append(f"material run {index} ablation packet must be an object")
                else:
                    original = packet.get("original_material")
                    ablated = packet.get("ablated_material")
                    if packet.get("ablation") != ablation or packet.get("case_id") != case_id:
                        errors.append(f"material run {index} ablation packet metadata mismatch")
                    if not isinstance(original, str) or not original.strip():
                        errors.append(f"material run {index} lacks original material")
                    if not isinstance(ablated, str) or not ablated.strip():
                        errors.append(f"material run {index} lacks ablated material")
                    if isinstance(original, str) and isinstance(ablated, str):
                        if original == ablated:
                            errors.append(f"material run {index} did not change the material")
                        if run.get("original_sha256") != sha256_text(original):
                            errors.append(f"material run {index} original SHA-256 mismatch")
                        if run.get("ablated_sha256") != sha256_text(ablated):
                            errors.append(f"material run {index} ablated SHA-256 mismatch")
            errors.extend(
                validate_dimension_record(f"material run {index}", run, artifacts)
            )
        if groups != MATERIAL_ABLATIONS:
            errors.append(
                f"material ablation group mismatch: expected {sorted(MATERIAL_ABLATIONS)}"
            )
        metrics = comparison.get("metrics")
        expected_metrics = {
            "runs": len(runs),
            "groups": len(groups),
            "hard_failures": 0,
        }
        if metrics != expected_metrics:
            errors.append(f"material ablation metrics mismatch: expected {expected_metrics!r}")
    return errors


def validate_evidence(
    cases: dict[str, dict[str, Any]],
    evidence_root: Path,
    strict: bool,
    repo_root: Path | None = None,
    cases_path: Path | None = None,
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {
        "cases": len(cases),
        "writer_outputs": 0,
        "samples": 0,
        "verdicts": 0,
        "style_warnings": 0,
        "adherence_failures": 0,
        "orchestration_failures": 0,
    }
    try:
        manifest = read_json(evidence_root / "manifest.json")
    except EvidenceError as exc:
        return [str(exc)], counts
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"], counts
    if manifest.get("schema_version") != 2:
        errors.append("manifest.schema_version must equal 2")
    if strict:
        errors.extend(git_binding_errors(manifest, repo_root, cases_path))

    writers = manifest.get("writers")
    if not isinstance(writers, list):
        errors.append("manifest.writers must be a list")
        writers = []
    if strict and len(writers) != 2:
        errors.append(f"strict evidence requires exactly 2 writer cohorts, found {len(writers)}")
    expected_case_ids = set(cases)
    writer_ids: set[str] = set()
    context_ids: set[str] = set()
    output_paths: set[Path] = set()
    output_pairs: dict[tuple[str, str], tuple[Path, bytes, str]] = {}
    for index, writer in enumerate(writers):
        if not isinstance(writer, dict):
            errors.append(f"writer entry {index} must be an object")
            continue
        writer_id = writer.get("writer_id")
        if not isinstance(writer_id, str) or not writer_id:
            errors.append(f"writer entry {index} has invalid writer_id")
            continue
        if writer_id in writer_ids:
            errors.append(f"duplicate writer_id: {writer_id}")
        writer_ids.add(writer_id)
        if not isinstance(writer.get("model_id"), str) or not writer.get("model_id"):
            errors.append(f"writer {writer_id} must record model_id or 'unavailable'")
        outputs = writer.get("outputs")
        contexts = writer.get("contexts")
        if not isinstance(outputs, dict):
            errors.append(f"writer {writer_id}.outputs must be an object")
            continue
        if not isinstance(contexts, dict):
            errors.append(f"writer {writer_id}.contexts must be an object")
            contexts = {}
        if set(outputs) != expected_case_ids or set(contexts) != expected_case_ids:
            errors.append(f"writer {writer_id} must cover every case in outputs and contexts")
        for case_id, relative in outputs.items():
            if case_id not in cases:
                continue
            context_id = contexts.get(case_id)
            if not isinstance(context_id, str) or not context_id:
                errors.append(f"writer {writer_id}/{case_id} has invalid context id")
            elif context_id in context_ids:
                errors.append(f"writer context reused: {context_id}")
            else:
                context_ids.add(context_id)
            try:
                output_path = resolve_evidence_path(
                    evidence_root, relative, f"writer {writer_id} output {case_id}"
                )
                raw, output = read_utf8_bytes(output_path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if output_path in output_paths:
                errors.append(f"writer outputs reuse one path: {relative}")
                continue
            output_paths.add(output_path)
            output_pairs[(writer_id, case_id)] = (output_path, raw, output)
            counts["writer_outputs"] += 1
            for problem in check_output(cases[case_id], output):
                errors.append(f"{writer_id}/{case_id}: {problem}")

    samples: dict[str, dict[str, Any]] = {}
    packet_paths: set[Path] = set()
    try:
        blind_map_path = resolve_evidence_path(
            evidence_root, manifest.get("blind_map"), "blind_map"
        )
        blind_map = read_json(blind_map_path)
        rows = blind_map.get("samples") if isinstance(blind_map, dict) else None
        if not isinstance(rows, list):
            raise EvidenceError("blind map must contain a samples list")
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"blind sample {index} must be an object")
                continue
            sample_id = row.get("sample_id")
            writer_id = row.get("writer_id")
            case_id = row.get("case_id")
            if not isinstance(sample_id, str) or not sample_id:
                errors.append(f"blind sample {index} has invalid sample_id")
                continue
            if sample_id in samples:
                errors.append(f"duplicate sample_id: {sample_id}")
                continue
            if not isinstance(writer_id, str) or not isinstance(case_id, str):
                errors.append(f"blind sample {sample_id} has invalid writer_id or case_id")
                continue
            pair = (writer_id, case_id)
            if pair not in output_pairs:
                errors.append(f"blind sample {sample_id} maps to unknown pair {pair}")
                continue
            output_path, output_raw, output = output_pairs[pair]
            expected_output = relative_posix(output_path, evidence_root)
            if row.get("output") != expected_output:
                errors.append(f"blind sample {sample_id} output path mismatch")
            output_digest = sha256_bytes(output_raw)
            if row.get("output_sha256") != output_digest:
                errors.append(f"blind sample {sample_id} output SHA-256 mismatch")
            prompt_digest = sha256_text(cases[case_id]["prompt"])
            if row.get("prompt_sha256") != prompt_digest:
                errors.append(f"blind sample {sample_id} prompt SHA-256 mismatch")
            try:
                packet_path = resolve_evidence_path(
                    evidence_root, row.get("packet"), f"blind sample {sample_id} packet"
                )
                packet_raw, packet = read_utf8_bytes(packet_path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if packet_path in packet_paths:
                errors.append(f"blind packets reuse one path: {row.get('packet')}")
            packet_paths.add(packet_path)
            if writer_id in relative_posix(packet_path, evidence_root):
                errors.append(f"blind packet path {sample_id} leaks a writer id")
            if row.get("packet_sha256") != sha256_bytes(packet_raw):
                errors.append(f"blind sample {sample_id} packet SHA-256 mismatch")
            expected_packet = (
                f"# 匿名写作样本 {sample_id}\n\n"
                f"## 用户任务\n\n{cases[case_id]['prompt']}\n\n"
                f"## 匿名输出\n\n{output}"
            )
            if normalize_packet_text(packet) != normalize_packet_text(expected_packet):
                errors.append(
                    f"blind packet {sample_id} must contain only the exact prompt and output"
                )
            if any(writer_name in packet for writer_name in writer_ids):
                errors.append(f"blind packet {sample_id} leaks a writer id")
            samples[sample_id] = {
                **row,
                "output_text": output,
                "output_digest": output_digest,
                "prompt_digest": prompt_digest,
            }
    except EvidenceError as exc:
        errors.append(str(exc))

    counts["samples"] = len(samples)
    mapped_pairs = {
        (row.get("writer_id"), row.get("case_id")) for row in samples.values()
    }
    if mapped_pairs != set(output_pairs):
        errors.append("blind mapping is not a bijection over writer outputs")
    if strict and len(samples) != 24:
        errors.append(f"strict evidence requires exactly 24 blind samples, found {len(samples)}")
    packet_set_digest = sha256_text(
        "\n".join(
            f"{sample_id}:{samples[sample_id].get('packet_sha256', '')}"
            for sample_id in sorted(samples)
        )
    )

    verifiers = manifest.get("verifiers")
    if not isinstance(verifiers, list):
        errors.append("manifest.verifiers must be a list")
        verifiers = []
    if strict and len(verifiers) != 2:
        errors.append(f"strict evidence requires exactly 2 verifiers, found {len(verifiers)}")
    verifier_ids: set[str] = set()
    verifier_contexts: set[str] = set()
    verifier_result_paths: dict[str, Path] = {}
    for index, verifier in enumerate(verifiers):
        if not isinstance(verifier, dict):
            errors.append(f"verifier entry {index} must be an object")
            continue
        verifier_id = verifier.get("verifier_id")
        context_id = verifier.get("context_id")
        if not isinstance(verifier_id, str) or not verifier_id:
            errors.append(f"verifier entry {index} has invalid verifier_id")
            continue
        if verifier_id in verifier_ids:
            errors.append(f"duplicate verifier_id: {verifier_id}")
        verifier_ids.add(verifier_id)
        if not isinstance(context_id, str) or not context_id:
            errors.append(f"verifier {verifier_id} has invalid context_id")
        elif context_id in context_ids or context_id in verifier_contexts:
            errors.append(f"verifier context is not independent: {context_id}")
        else:
            verifier_contexts.add(context_id)
        if not isinstance(verifier.get("model_id"), str) or not verifier.get("model_id"):
            errors.append(f"verifier {verifier_id} must record model_id or 'unavailable'")
        try:
            result_path = resolve_evidence_path(
                evidence_root, verifier.get("results"), f"verifier {verifier_id} results"
            )
            payload = read_json(result_path)
        except EvidenceError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict):
            errors.append(f"verifier results must be an object: {result_path}")
            continue
        if set(payload) != VERIFIER_PAYLOAD_KEYS:
            errors.append(f"verifier {verifier_id} payload keys do not match the blind schema")
        verifier_result_paths[verifier_id] = result_path
        if payload.get("verifier_id") != verifier_id or payload.get("blind") is not True:
            errors.append(f"verifier metadata mismatch: {verifier_id}")
        if payload.get("packet_set_sha256") != packet_set_digest:
            errors.append(f"verifier {verifier_id} packet set SHA-256 mismatch")
        if payload.get("criteria") != ["hard_failures", "adherence", "orchestration", "style"]:
            errors.append(f"verifier {verifier_id} criteria mismatch")
        results = payload.get("results")
        if not isinstance(results, list):
            errors.append(f"verifier {verifier_id}.results must be a list")
            continue
        seen_samples: set[str] = set()
        for result in results:
            if not isinstance(result, dict):
                errors.append(f"verifier {verifier_id} result must be an object")
                continue
            if set(result) != VERIFIER_RESULT_KEYS:
                errors.append(
                    f"verifier {verifier_id} result keys do not match the blind schema"
                )
            sample_id = result.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id:
                errors.append(f"verifier {verifier_id} result has invalid sample_id")
                continue
            if sample_id in seen_samples:
                errors.append(f"verifier {verifier_id} repeats sample {sample_id}")
            seen_samples.add(sample_id)
            sample = samples.get(sample_id)
            if sample is None:
                errors.append(f"verifier {verifier_id} references unknown sample {sample_id}")
                continue
            if result.get("output_sha256") != sample["output_digest"]:
                errors.append(f"verifier {verifier_id}/{sample_id} output SHA-256 mismatch")
            if result.get("prompt_sha256") != sample["prompt_digest"]:
                errors.append(f"verifier {verifier_id}/{sample_id} prompt SHA-256 mismatch")
            verdict = result.get("verdict")
            if verdict not in ALLOWED_VERDICTS:
                errors.append(f"verifier {verifier_id}/{sample_id} invalid verdict {verdict!r}")
            elif verdict in {"FAIL", "BLOCK"}:
                errors.append(f"verifier {verifier_id}/{sample_id} verdict is {verdict}")
            for dimension in VERIFIER_DIMENSIONS:
                dimension_verdict = result.get(dimension)
                if dimension_verdict not in ALLOWED_VERDICTS:
                    errors.append(
                        f"verifier {verifier_id}/{sample_id} invalid {dimension}"
                    )
                elif dimension_verdict in {"FAIL", "BLOCK"}:
                    counts[dimension.replace("_verdict", "_failures")] += 1
                    errors.append(
                        f"verifier {verifier_id}/{sample_id} {dimension} is {dimension_verdict}"
                    )
            for evidence_key in ("adherence_evidence", "orchestration_evidence"):
                evidence = result.get(evidence_key)
                if not isinstance(evidence, str) or len(evidence.strip()) < 20:
                    errors.append(
                        f"verifier {verifier_id}/{sample_id} lacks substantive {evidence_key}"
                    )
            anchors = result.get("anchors")
            if not isinstance(anchors, list) or not anchors or not all(
                isinstance(anchor, str) and len(anchor.strip()) >= 4 for anchor in anchors
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} has invalid anchors")
            elif not any(anchor in sample["output_text"] for anchor in anchors):
                errors.append(f"verifier {verifier_id}/{sample_id} anchors do not match output")
            hard_failures = result.get("hard_failures")
            style_warnings = result.get("style_warnings")
            if not isinstance(hard_failures, list) or not all(
                isinstance(item, str) for item in hard_failures
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} invalid hard_failures")
                hard_failures = []
            if not isinstance(style_warnings, list) or not all(
                isinstance(item, str) for item in style_warnings
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} invalid style_warnings")
                style_warnings = []
            counts["style_warnings"] += len(style_warnings)
            if hard_failures:
                errors.append(
                    f"verifier {verifier_id}/{sample_id} reports hard failures: {hard_failures}"
                )
            counts["verdicts"] += 1
        if seen_samples != set(samples):
            errors.append(f"verifier {verifier_id} sample set does not match blind packets")
        serialized = json.dumps(payload, ensure_ascii=False)
        if any(writer_id in serialized for writer_id in writer_ids):
            errors.append(f"verifier {verifier_id} results leak a writer id")

    if strict and counts["verdicts"] != 48:
        errors.append(f"strict evidence requires exactly 48 verdicts, found {counts['verdicts']}")
    try:
        hashes_path = resolve_evidence_path(
            evidence_root, manifest.get("verdict_hashes"), "verdict_hashes"
        )
        hashes_payload = read_json(hashes_path)
        if not isinstance(hashes_payload, dict):
            raise EvidenceError("verdict_hashes must be an object")
        if hashes_payload.get("sealed_before_unblinding") is not True:
            errors.append("verdict hashes must record sealed_before_unblinding=true")
        if not isinstance(hashes_payload.get("unblinded_at"), str) or not hashes_payload.get(
            "unblinded_at"
        ):
            errors.append("verdict hashes must record unblinded_at")
        expected_hashes = hashes_payload.get("sha256")
        if not isinstance(expected_hashes, dict):
            raise EvidenceError("verdict_hashes.sha256 must be an object")
        for verifier_id, result_path in verifier_result_paths.items():
            if expected_hashes.get(verifier_id) != sha256_file(result_path):
                errors.append(f"verifier {verifier_id} sealed SHA-256 mismatch")
    except EvidenceError as exc:
        errors.append(str(exc))

    comparison_statuses: dict[str, str] = {}
    if strict:
        comparisons = manifest.get("comparisons")
        if not isinstance(comparisons, dict):
            errors.append("strict evidence requires manifest.comparisons")
            comparisons = {}
        if set(comparisons) != STRICT_COMPARISONS:
            errors.append("comparison set mismatch")
        writer_output_relatives = {
            relative_posix(path, evidence_root) for path in output_paths
        }
        comparison_context_ids = set(context_ids) | set(verifier_contexts)
        for label, relative in comparisons.items():
            try:
                path = resolve_evidence_path(
                    evidence_root, relative, f"comparison {label}"
                )
                comparison = read_json(path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            errors.extend(
                validate_comparison(
                    evidence_root,
                    label,
                    comparison,
                    cases,
                    writer_output_relatives,
                    comparison_context_ids,
                )
            )
            comparison_statuses[label] = (
                comparison.get("status") if isinstance(comparison, dict) else "INVALID"
            )

        try:
            summary_path = resolve_evidence_path(
                evidence_root, manifest.get("summary"), "summary"
            )
            summary = read_json(summary_path)
        except EvidenceError as exc:
            errors.append(str(exc))
            summary = None
        if isinstance(summary, dict):
            expected_summary = {
                "status": "PASS",
                "candidate_commit": manifest.get("candidate_commit"),
                "cases": len(cases),
                "writer_outputs": counts["writer_outputs"],
                "blind_samples": counts["samples"],
                "verdicts": counts["verdicts"],
                "hard_failures": 0,
                "adherence_failures": counts["adherence_failures"],
                "orchestration_failures": counts["orchestration_failures"],
                "style_warnings": counts["style_warnings"],
                "comparisons": comparison_statuses,
            }
            if summary != expected_summary:
                errors.append("machine summary does not match recomputed evidence counts")
        elif summary is not None:
            errors.append("summary must be a JSON object")
        try:
            report_path = resolve_evidence_path(
                evidence_root, manifest.get("report"), "report"
            )
            _, report = read_utf8_bytes(report_path)
            if len(report.strip()) < 200:
                errors.append("human-readable evidence report is too short")
        except EvidenceError as exc:
            errors.append(str(exc))
    return errors, counts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        cases = load_cases(args.cases)
    except EvidenceError as exc:
        print(f"CHECK=FAIL\nERROR={exc}")
        return 1
    cases_path = args.cases.resolve()
    try:
        repo_root = cases_path.parents[2]
    except IndexError:
        repo_root = Path.cwd().resolve()
    try:
        errors, counts = validate_evidence(
            cases,
            args.evidence,
            args.strict,
            repo_root=repo_root,
            cases_path=cases_path,
        )
    except (EvidenceError, OSError, TypeError, ValueError) as exc:
        print(f"CHECK=FAIL\nERROR=unexpected malformed evidence: {exc}")
        return 1
    if errors:
        print("CHECK=FAIL")
        for error in errors:
            print(f"ERROR={error}")
        print("COUNTS=" + ",".join(f"{key}:{value}" for key, value in counts.items()))
        return 1
    print("CHECK=PASS")
    print("COUNTS=" + ",".join(f"{key}:{value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
