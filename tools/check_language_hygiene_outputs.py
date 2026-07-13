#!/usr/bin/env python3
"""Validate read-only evidence for the Prompt-driven academic language review.

The checker never rewrites a draft.  Candidate phrase matches are observations,
not errors; semantic decisions remain with blind verifiers.  The small Finding
model and quoted-span handling are adapted from the user-owned
``chinese-official-writing`` prose_lint design for academic-writing tests.  No
official-document vocabulary, replacement table, or runtime dependency is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_WRITERS = 2
EXPECTED_VERIFIERS = 2
PROTECTED_PATHS = (
    "chinese-academic-writing-assistant/SKILL.md",
    "chinese-academic-writing-assistant/agents/openai.yaml",
    "chinese-academic-writing-assistant/references/academic-writing.md",
    "chinese-academic-writing-assistant/references/academic-proposal.md",
    "chinese-academic-writing-assistant/references/academic-literature-review.md",
    "chinese-academic-writing-assistant/references/anti-ai-writing.md",
    "chinese-academic-writing-assistant/references/citation-research.md",
    "chinese-academic-writing-assistant/scripts/citation_audit.py",
    "chinese-academic-writing-assistant/scripts/prose_lint.py",
    "tests/fixtures/language-hygiene-smoke.jsonl",
    "tests/test_language_hygiene.py",
    "tools/check_language_hygiene_outputs.py",
)
CASES_PATH = "tests/fixtures/language-hygiene-smoke.jsonl"
FIX_THRESHOLD = {
    "minimum_outputs": 3,
    "minimum_cases": 2,
    "minimum_writers": 2,
}
ALLOWED_MODES = {"rewrite-only", "final-text-only", "review-only"}
ALLOWED_VERDICTS = {"PASS", "WARN", "FAIL", "BLOCK"}
REVIEW_FIELDS = ("位置", "严重度", "问题", "依据", "修改建议")
VERIFIER_DIMENSIONS = (
    "semantic_fidelity_verdict",
    "contextual_style_verdict",
    "output_hygiene_verdict",
    "mode_adherence_verdict",
    "overediting_verdict",
)
VERIFIER_CRITERIA = [
    "semantic_fidelity",
    "contextual_style",
    "output_hygiene",
    "mode_adherence",
    "overediting",
]


class EvidenceError(ValueError):
    """Raised for malformed or unreadable evidence."""


@dataclass(frozen=True)
class Finding:
    writer_id: str
    case_id: str
    line: int
    pattern_id: str
    label: str
    match: str
    quoted: bool


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"unable to hash file {path}: {exc}") from exc


def read_utf8(path: Path) -> tuple[bytes, str]:
    try:
        raw = path.read_bytes()
        return raw, raw.decode("utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceError(f"unable to read UTF-8 file {path}: {exc}") from exc


def read_json(path: Path) -> Any:
    _, text = read_utf8(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON in {path}: {exc}") from exc


def resolve_evidence_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise EvidenceError(f"{label} must be a non-empty relative path")
    relative_path = Path(relative)
    if relative_path.is_absolute():
        raise EvidenceError(f"{label} must be relative: {relative}")
    candidate = (root.resolve() / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceError(f"{label} escapes evidence root: {relative}") from exc
    if not candidate.is_file():
        raise EvidenceError(f"{label} is not a file: {relative}")
    return candidate


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _require_string_list(case: dict[str, Any], field: str, line_number: int) -> None:
    value = case.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise EvidenceError(f"case line {line_number}.{field} must be a string list")


def load_cases(path: Path) -> dict[str, dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceError(f"unable to read cases {path}: {exc}") from exc
    cases: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvidenceError(f"invalid JSON on case line {line_number}: {exc}") from exc
        if not isinstance(case, dict):
            raise EvidenceError(f"case line {line_number} must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"H\d{2}", case_id):
            raise EvidenceError(f"case line {line_number} has invalid id")
        if case_id in cases:
            raise EvidenceError(f"duplicate case id: {case_id}")
        if not isinstance(case.get("title"), str) or not case["title"].strip():
            raise EvidenceError(f"case {case_id} has invalid title")
        if not isinstance(case.get("prompt"), str) or len(case["prompt"].strip()) < 40:
            raise EvidenceError(f"case {case_id} has invalid prompt")
        if case.get("expected_mode") not in ALLOWED_MODES:
            raise EvidenceError(f"case {case_id} has invalid expected_mode")
        for field in (
            "semantic_focus",
            "immutable_literals",
            "required_literals",
            "forbidden_literals",
        ):
            _require_string_list(case, field, line_number)
        patterns = case.get("candidate_patterns")
        if not isinstance(patterns, list) or not patterns:
            raise EvidenceError(f"case {case_id}.candidate_patterns must be a non-empty list")
        seen_pattern_ids: set[str] = set()
        for pattern in patterns:
            if not isinstance(pattern, dict) or set(pattern) != {"id", "label", "regex"}:
                raise EvidenceError(f"case {case_id} has malformed candidate pattern")
            pattern_id = pattern.get("id")
            if not isinstance(pattern_id, str) or not re.fullmatch(
                r"[a-z][a-z0-9_-]{1,40}", pattern_id
            ):
                raise EvidenceError(f"case {case_id} has invalid pattern id")
            if pattern_id in seen_pattern_ids:
                raise EvidenceError(f"case {case_id} repeats pattern id {pattern_id}")
            seen_pattern_ids.add(pattern_id)
            if not isinstance(pattern.get("label"), str) or not pattern["label"].strip():
                raise EvidenceError(f"case {case_id}/{pattern_id} has invalid label")
            try:
                re.compile(pattern.get("regex"))
            except (re.error, TypeError) as exc:
                raise EvidenceError(
                    f"case {case_id}/{pattern_id} has invalid regex: {exc}"
                ) from exc
        cases[case_id] = case
    if not cases:
        raise EvidenceError("case fixture is empty")
    return cases


def quoted_spans_by_line(lines: list[str]) -> list[list[tuple[int, int]]]:
    """Return Chinese/ASCII quote spans, including spans crossing line breaks."""
    pairs = {"“": "”", "‘": "’", '"': '"'}
    result: list[list[tuple[int, int]]] = []
    active_close: str | None = None
    for line in lines:
        spans: list[tuple[int, int]] = []
        index = 0
        while index < len(line):
            if active_close is not None:
                right = line.find(active_close, index)
                if right == -1:
                    spans.append((index, len(line)))
                    index = len(line)
                else:
                    spans.append((index, right + 1))
                    index = right + 1
                    active_close = None
                continue
            positions = [(line.find(opener, index), opener) for opener in pairs]
            positions = [(position, opener) for position, opener in positions if position != -1]
            if not positions:
                break
            left, opener = min(positions)
            close = pairs[opener]
            right = line.find(close, left + 1)
            if right == -1:
                spans.append((left, len(line)))
                active_close = close
                index = len(line)
            else:
                spans.append((left, right + 1))
                index = right + 1
        result.append(spans)
    return result


def inside_spans(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(left <= start and end <= right for left, right in spans)


def scan_candidates(
    case: dict[str, Any], text: str, writer_id: str = "unassigned"
) -> list[Finding]:
    lines = text.splitlines() or [text]
    quote_spans = quoted_spans_by_line(lines)
    findings: list[Finding] = []
    for line_index, line in enumerate(lines):
        for pattern in case["candidate_patterns"]:
            regex = re.compile(pattern["regex"])
            for match in regex.finditer(line):
                findings.append(
                    Finding(
                        writer_id=writer_id,
                        case_id=case["id"],
                        line=line_index + 1,
                        pattern_id=pattern["id"],
                        label=pattern["label"],
                        match=match.group(0),
                        quoted=inside_spans(
                            quote_spans[line_index], match.start(), match.end()
                        ),
                    )
                )
    return findings


def check_output(case: dict[str, Any], text: str) -> list[str]:
    """Return hard-gate failures only; phrase frequency never fails here."""
    errors: list[str] = []
    if not text.strip():
        errors.append("output mode violation: output is empty")
        return errors
    for literal in case["immutable_literals"]:
        if literal not in text:
            errors.append(f"missing immutable literal: {literal!r}")
    for literal in case["required_literals"]:
        if literal not in text:
            errors.append(f"output mode missing required literal: {literal!r}")
    for literal in case["forbidden_literals"]:
        if literal in text:
            errors.append(f"explicit leakage or mode violation: {literal!r}")
    review_fields_present = [field for field in REVIEW_FIELDS if field in text]
    if case["expected_mode"] == "review-only":
        for field in REVIEW_FIELDS:
            if field not in text and field not in case["required_literals"]:
                errors.append(f"output mode missing review field: {field!r}")
    elif len(review_fields_present) == len(REVIEW_FIELDS):
        errors.append(
            "output mode violation: rewrite/final output contains a complete review table"
        )
    return errors


def normalize_packet(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def expected_packet(sample_id: str, prompt: str, output: str) -> str:
    return (
        f"# 匿名语言复核样本 {sample_id}\n\n"
        f"## 用户任务\n\n{prompt}\n\n"
        f"## 匿名输出\n\n{output}"
    )


def git_binding_errors(
    manifest: dict[str, Any], repo_root: Path | None, cases_path: Path | None
) -> list[str]:
    """Bind strict evidence to one committed, byte-identical protected surface."""
    if repo_root is None or cases_path is None:
        return ["strict evidence validation requires repo_root and cases_path"]
    errors: list[str] = []
    repo_root = repo_root.resolve()
    expected_cases = (repo_root / CASES_PATH).resolve()
    if cases_path.resolve() != expected_cases:
        errors.append("strict cases path must be the protected language-hygiene fixture")
    candidate = manifest.get("candidate_commit")
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
        return errors + [
            "manifest.candidate_commit must be a full 40-character lowercase SHA"
        ]
    commit_probe = subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_probe.returncode != 0:
        errors.append(
            f"candidate_commit does not exist in the local repository: {candidate}"
        )
        return errors
    tested_paths = manifest.get("tested_paths")
    if tested_paths != list(PROTECTED_PATHS):
        errors.append("manifest.tested_paths does not match the protected candidate surface")
    protected_hashes = manifest.get("protected_sha256")
    if not isinstance(protected_hashes, dict) or set(protected_hashes) != set(
        PROTECTED_PATHS
    ):
        errors.append("manifest.protected_sha256 must cover the exact protected surface")
    else:
        for relative in PROTECTED_PATHS:
            path = repo_root / relative
            try:
                actual = sha256_file(path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if protected_hashes.get(relative) != actual:
                errors.append(f"protected SHA-256 mismatch: {relative}")
    for relative in PROTECTED_PATHS:
        path_probe = subprocess.run(
            ["git", "cat-file", "-e", f"{candidate}:{relative}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if path_probe.returncode != 0:
            errors.append(f"candidate_commit does not contain protected file: {relative}")
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
        errors.append(
            f"unable to compare protected candidate files: {diff_probe.stderr.strip()}"
        )
    return errors


def summarize_prompt_fix_candidates(
    issue_samples: dict[str, set[str]], samples: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for issue_code, sample_ids in sorted(issue_samples.items()):
        valid_ids = sorted(sample_id for sample_id in sample_ids if sample_id in samples)
        case_ids = {samples[sample_id]["case_id"] for sample_id in valid_ids}
        writer_ids = {samples[sample_id]["writer_id"] for sample_id in valid_ids}
        if (
            len(valid_ids) >= FIX_THRESHOLD["minimum_outputs"]
            and len(case_ids) >= FIX_THRESHOLD["minimum_cases"]
            and len(writer_ids) >= FIX_THRESHOLD["minimum_writers"]
        ):
            recommendations.append(
                {
                    "issue_code": issue_code,
                    "outputs": len(valid_ids),
                    "cases": len(case_ids),
                    "writers": len(writer_ids),
                    "sample_ids": valid_ids,
                }
            )
    return recommendations


def consensus_issue_samples(
    issue_votes: dict[str, dict[str, set[str]]]
) -> dict[str, set[str]]:
    """Count an issue only when both blind verifiers agree on the same sample."""
    return {
        issue_code: {
            sample_id
            for sample_id, verifier_ids in sample_votes.items()
            if len(verifier_ids) >= EXPECTED_VERIFIERS
        }
        for issue_code, sample_votes in issue_votes.items()
    }


def validate_evidence(
    cases: dict[str, dict[str, Any]],
    evidence_root: Path,
    strict: bool = False,
    repo_root: Path | None = None,
    cases_path: Path | None = None,
) -> tuple[list[str], dict[str, int], list[Finding], list[dict[str, Any]]]:
    errors: list[str] = []
    counts = {
        "writers": 0,
        "input_packets": 0,
        "writer_outputs": 0,
        "blind_samples": 0,
        "verifiers": 0,
        "verdicts": 0,
        "candidate_hits": 0,
        "quoted_candidate_hits": 0,
    }
    findings: list[Finding] = []
    issue_votes: dict[str, dict[str, set[str]]] = {}
    try:
        manifest_path = resolve_evidence_path(evidence_root, "manifest.json", "manifest")
        manifest = read_json(manifest_path)
    except EvidenceError as exc:
        return [str(exc)], counts, findings, []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"], counts, findings, []
    if manifest.get("schema_version") != 1:
        errors.append("manifest.schema_version must equal 1")
    candidate_commit = manifest.get("candidate_commit")
    if not isinstance(candidate_commit, str) or not candidate_commit.strip():
        errors.append("manifest.candidate_commit must be recorded")
    if strict:
        errors.extend(git_binding_errors(manifest, repo_root, cases_path))
    if manifest.get("fix_threshold") != FIX_THRESHOLD:
        errors.append("manifest.fix_threshold must record 3 outputs, 2 cases, 2 writers")

    expected_case_ids = set(cases)
    writers = manifest.get("writers")
    if not isinstance(writers, list):
        errors.append("manifest.writers must be a list")
        writers = []
    if strict and len(writers) != EXPECTED_WRITERS:
        errors.append(f"strict evidence requires exactly {EXPECTED_WRITERS} writers")
    writer_ids: set[str] = set()
    context_ids: set[str] = set()
    input_paths: set[Path] = set()
    output_paths: set[Path] = set()
    outputs: dict[tuple[str, str], tuple[Path, bytes, str]] = {}
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
        output_map = writer.get("outputs")
        contexts = writer.get("contexts")
        inputs = writer.get("inputs")
        if (
            not isinstance(output_map, dict)
            or not isinstance(contexts, dict)
            or not isinstance(inputs, dict)
        ):
            errors.append(
                f"writer {writer_id} inputs, outputs and contexts must be objects"
            )
            continue
        if (
            set(output_map) != expected_case_ids
            or set(contexts) != expected_case_ids
            or set(inputs) != expected_case_ids
        ):
            errors.append(f"writer {writer_id} must cover every H case")
        for case_id, relative in output_map.items():
            if case_id not in cases:
                continue
            input_record = inputs.get(case_id)
            if not isinstance(input_record, dict) or set(input_record) != {
                "path",
                "sha256",
            }:
                errors.append(
                    f"writer {writer_id}/{case_id} input must record path and raw SHA-256"
                )
            else:
                try:
                    input_path = resolve_evidence_path(
                        evidence_root,
                        input_record.get("path"),
                        f"writer {writer_id}/{case_id} prompt-only input",
                    )
                    input_raw, input_text = read_utf8(input_path)
                except EvidenceError as exc:
                    errors.append(str(exc))
                else:
                    if input_path in input_paths:
                        errors.append(
                            f"writer prompt-only inputs reuse one path: "
                            f"{input_record.get('path')}"
                        )
                    input_paths.add(input_path)
                    if input_record.get("path") != relative_posix(
                        input_path, evidence_root
                    ):
                        errors.append(
                            f"writer {writer_id}/{case_id} input path is not normalized"
                        )
                    if input_record.get("sha256") != sha256_bytes(input_raw):
                        errors.append(
                            f"writer {writer_id}/{case_id} input raw SHA-256 mismatch"
                        )
                    if input_text != cases[case_id]["prompt"]:
                        errors.append(
                            f"writer {writer_id}/{case_id} input must contain only the exact prompt"
                        )
                    counts["input_packets"] += 1
            context_id = contexts.get(case_id)
            if not isinstance(context_id, str) or not context_id:
                errors.append(f"writer {writer_id}/{case_id} has invalid context id")
            elif context_id in context_ids:
                errors.append(f"writer context reused: {context_id}")
            else:
                context_ids.add(context_id)
            try:
                output_path = resolve_evidence_path(
                    evidence_root, relative, f"writer {writer_id}/{case_id} output"
                )
                raw, text = read_utf8(output_path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if output_path in output_paths:
                errors.append(f"writer outputs reuse one path: {relative}")
                continue
            output_paths.add(output_path)
            outputs[(writer_id, case_id)] = (output_path, raw, text)
            counts["writer_outputs"] += 1
            for problem in check_output(cases[case_id], text):
                errors.append(f"{writer_id}/{case_id}: {problem}")
            output_findings = scan_candidates(cases[case_id], text, writer_id)
            findings.extend(output_findings)
            counts["candidate_hits"] += len(output_findings)
            counts["quoted_candidate_hits"] += sum(
                1 for item in output_findings if item.quoted
            )
    counts["writers"] = len(writer_ids)
    if strict and counts["input_packets"] != EXPECTED_WRITERS * len(cases):
        errors.append("strict evidence prompt-only input count mismatch")

    samples: dict[str, dict[str, Any]] = {}
    packet_paths: set[Path] = set()
    try:
        blind_path = resolve_evidence_path(
            evidence_root, manifest.get("blind_map"), "blind_map"
        )
        blind_payload = read_json(blind_path)
        rows = blind_payload.get("samples") if isinstance(blind_payload, dict) else None
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
                errors.append(f"duplicate blind sample: {sample_id}")
                continue
            if not isinstance(writer_id, str) or not isinstance(case_id, str):
                errors.append(f"blind sample {sample_id} has invalid mapping")
                continue
            pair = (writer_id, case_id)
            if pair not in outputs:
                errors.append(f"blind sample {sample_id} maps to unknown output")
                continue
            output_path, output_raw, output_text = outputs[pair]
            if row.get("output") != relative_posix(output_path, evidence_root):
                errors.append(f"blind sample {sample_id} output path mismatch")
            if row.get("output_sha256") != sha256_bytes(output_raw):
                errors.append(f"blind sample {sample_id} output SHA-256 mismatch")
            prompt_sha = sha256_text(cases[case_id]["prompt"])
            if row.get("prompt_sha256") != prompt_sha:
                errors.append(f"blind sample {sample_id} prompt SHA-256 mismatch")
            try:
                packet_path = resolve_evidence_path(
                    evidence_root, row.get("packet"), f"blind sample {sample_id} packet"
                )
                packet_raw, packet_text = read_utf8(packet_path)
            except EvidenceError as exc:
                errors.append(str(exc))
                continue
            if packet_path in packet_paths:
                errors.append(f"blind packets reuse one path: {row.get('packet')}")
            packet_paths.add(packet_path)
            if row.get("packet_sha256") != sha256_bytes(packet_raw):
                errors.append(f"blind sample {sample_id} packet SHA-256 mismatch")
            expected = expected_packet(sample_id, cases[case_id]["prompt"], output_text)
            if normalize_packet(packet_text) != normalize_packet(expected):
                errors.append(f"blind packet {sample_id} must contain exact prompt and output")
            if any(writer_name in packet_text for writer_name in writer_ids):
                errors.append(f"blind packet {sample_id} leaks writer identity")
            samples[sample_id] = {
                "writer_id": writer_id,
                "case_id": case_id,
                "output": output_text,
                "output_sha256": sha256_bytes(output_raw),
                "prompt_sha256": prompt_sha,
                "packet_sha256": sha256_bytes(packet_raw),
            }
    except EvidenceError as exc:
        errors.append(str(exc))
    counts["blind_samples"] = len(samples)
    mapped_pairs = {
        (sample["writer_id"], sample["case_id"]) for sample in samples.values()
    }
    if mapped_pairs != set(outputs):
        errors.append("blind mapping must be a bijection over writer outputs")
    if strict and len(samples) != EXPECTED_WRITERS * len(cases):
        errors.append("strict evidence blind sample count mismatch")

    packet_set_sha = sha256_text(
        "\n".join(
            f"{sample_id}:{samples[sample_id]['packet_sha256']}"
            for sample_id in sorted(samples)
        )
    )
    verifiers = manifest.get("verifiers")
    if not isinstance(verifiers, list):
        errors.append("manifest.verifiers must be a list")
        verifiers = []
    if strict and len(verifiers) != EXPECTED_VERIFIERS:
        errors.append(f"strict evidence requires exactly {EXPECTED_VERIFIERS} verifiers")
    verifier_ids: set[str] = set()
    verifier_context_ids: set[str] = set()
    verifier_paths: dict[str, Path] = {}
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
        elif context_id in context_ids or context_id in verifier_context_ids:
            errors.append(f"verifier context is not independent: {context_id}")
        else:
            verifier_context_ids.add(context_id)
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
        verifier_paths[verifier_id] = result_path
        if not isinstance(payload, dict):
            errors.append(f"verifier {verifier_id} results must be an object")
            continue
        if payload.get("verifier_id") != verifier_id or payload.get("blind") is not True:
            errors.append(f"verifier {verifier_id} metadata mismatch")
        if payload.get("packet_set_sha256") != packet_set_sha:
            errors.append(f"verifier {verifier_id} packet set SHA-256 mismatch")
        if payload.get("criteria") != VERIFIER_CRITERIA:
            errors.append(f"verifier {verifier_id} criteria mismatch")
        rows = payload.get("results")
        if not isinstance(rows, list):
            errors.append(f"verifier {verifier_id}.results must be a list")
            continue
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"verifier {verifier_id} result must be an object")
                continue
            sample_id = row.get("sample_id")
            if not isinstance(sample_id, str) or sample_id not in samples:
                errors.append(f"verifier {verifier_id} references unknown sample")
                continue
            if sample_id in seen:
                errors.append(f"verifier {verifier_id} repeats sample {sample_id}")
            seen.add(sample_id)
            sample = samples[sample_id]
            if row.get("output_sha256") != sample["output_sha256"]:
                errors.append(f"verifier {verifier_id}/{sample_id} output hash mismatch")
            if row.get("prompt_sha256") != sample["prompt_sha256"]:
                errors.append(f"verifier {verifier_id}/{sample_id} prompt hash mismatch")
            verdict = row.get("verdict")
            if verdict not in ALLOWED_VERDICTS:
                errors.append(f"verifier {verifier_id}/{sample_id} invalid verdict")
            elif verdict in {"FAIL", "BLOCK"}:
                errors.append(f"verifier {verifier_id}/{sample_id} hard verdict {verdict}")
            hard_failures = row.get("hard_failures")
            if not isinstance(hard_failures, list) or not all(
                isinstance(item, str) for item in hard_failures
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} invalid hard_failures")
                hard_failures = []
            if hard_failures:
                errors.append(
                    f"verifier {verifier_id}/{sample_id} reports hard failures: {hard_failures}"
                )
            for dimension in VERIFIER_DIMENSIONS:
                dimension_verdict = row.get(dimension)
                if dimension_verdict not in ALLOWED_VERDICTS:
                    errors.append(
                        f"verifier {verifier_id}/{sample_id} invalid {dimension}"
                    )
                elif dimension_verdict in {"FAIL", "BLOCK"}:
                    errors.append(
                        f"verifier {verifier_id}/{sample_id} {dimension} is "
                        f"{dimension_verdict}"
                    )
            issue_codes = row.get("issue_codes")
            if not isinstance(issue_codes, list) or not all(
                isinstance(item, str) and item.strip() for item in issue_codes
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} invalid issue_codes")
                issue_codes = []
            for issue_code in set(issue_codes):
                issue_votes.setdefault(issue_code, {}).setdefault(sample_id, set()).add(
                    verifier_id
                )
            rationale = row.get("rationale")
            if not isinstance(rationale, str) or len(rationale.strip()) < 20:
                errors.append(f"verifier {verifier_id}/{sample_id} lacks rationale")
            anchors = row.get("anchors")
            if not isinstance(anchors, list) or not anchors or not all(
                isinstance(anchor, str) and len(anchor.strip()) >= 2 for anchor in anchors
            ):
                errors.append(f"verifier {verifier_id}/{sample_id} has invalid anchors")
            elif not any(anchor in sample["output"] for anchor in anchors):
                errors.append(f"verifier {verifier_id}/{sample_id} anchors do not match output")
            counts["verdicts"] += 1
        if seen != set(samples):
            errors.append(f"verifier {verifier_id} must assess every blind sample")
        serialized = json.dumps(payload, ensure_ascii=False)
        if any(writer_name in serialized for writer_name in writer_ids):
            errors.append(f"verifier {verifier_id} results leak writer identity")
    counts["verifiers"] = len(verifier_ids)
    if strict and counts["verdicts"] != EXPECTED_VERIFIERS * len(samples):
        errors.append("strict evidence verifier verdict count mismatch")

    try:
        hashes_path = resolve_evidence_path(
            evidence_root, manifest.get("verdict_hashes"), "verdict_hashes"
        )
        hashes = read_json(hashes_path)
        if not isinstance(hashes, dict):
            raise EvidenceError("verdict_hashes must be an object")
        if hashes.get("sealed_before_unblinding") is not True:
            errors.append("verdict hashes must be sealed before unblinding")
        if not isinstance(hashes.get("unblinded_at"), str) or not hashes.get(
            "unblinded_at"
        ):
            errors.append("verdict hashes must record unblinded_at")
        expected_hashes = hashes.get("sha256")
        if not isinstance(expected_hashes, dict):
            raise EvidenceError("verdict_hashes.sha256 must be an object")
        for verifier_id, result_path in verifier_paths.items():
            if expected_hashes.get(verifier_id) != sha256_file(result_path):
                errors.append(f"verifier {verifier_id} sealed hash mismatch")
    except EvidenceError as exc:
        errors.append(str(exc))

    recommendations = summarize_prompt_fix_candidates(
        consensus_issue_samples(issue_votes), samples
    )
    return errors, counts, findings, recommendations


def frequency_report(findings: list[Finding]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for finding in findings:
        key = (finding.pattern_id, finding.label)
        bucket = buckets.setdefault(
            key,
            {
                "pattern_id": finding.pattern_id,
                "label": finding.label,
                "hits": 0,
                "quoted_hits": 0,
                "outputs": set(),
            },
        )
        bucket["hits"] += 1
        bucket["quoted_hits"] += int(finding.quoted)
        bucket["outputs"].add(f"{finding.writer_id}/{finding.case_id}")
    report: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        report.append(
            {
                "pattern_id": bucket["pattern_id"],
                "label": bucket["label"],
                "hits": bucket["hits"],
                "quoted_hits": bucket["quoted_hits"],
                "outputs": len(bucket["outputs"]),
            }
        )
    return report


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
        cases_path = args.cases.resolve()
        try:
            repo_root = cases_path.parents[2]
        except IndexError:
            repo_root = Path.cwd().resolve()
        errors, counts, findings, recommendations = validate_evidence(
            cases,
            args.evidence,
            args.strict,
            repo_root=repo_root,
            cases_path=cases_path,
        )
    except (EvidenceError, OSError, TypeError, ValueError) as exc:
        print(f"CHECK=FAIL\nERROR={exc}")
        return 1
    print("CHECK=" + ("FAIL" if errors else "PASS"))
    for error in errors:
        print(f"ERROR={error}")
    print("COUNTS=" + ",".join(f"{key}:{value}" for key, value in counts.items()))
    print(
        "CANDIDATE_FREQUENCIES="
        + json.dumps(frequency_report(findings), ensure_ascii=False, sort_keys=True)
    )
    print(
        "PROMPT_FIX_RECOMMENDATIONS="
        + json.dumps(recommendations, ensure_ascii=False, sort_keys=True)
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
