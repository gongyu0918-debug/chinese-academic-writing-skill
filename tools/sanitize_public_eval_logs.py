#!/usr/bin/env python3
"""Redact internal request identifiers from public evaluation stderr evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path


TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".py", ".txt"}
HASH_REFERENCE_SUFFIXES = {".json"}
INTERNAL_URL = re.compile(r"https://chatgpt\.com/[^\s)\"']+", re.IGNORECASE)
ENDPOINT_PATH = re.compile(r'endpoint_path="[^"]*"', re.IGNORECASE)
OPAQUE_KEY = re.compile(
    r"\b(?P<key>pageToken|run_id|query_id|leaf_id|session_id)="
    r"(?P<value>\"[^\"]*\"|[^\s,;)}\]]+)",
    re.IGNORECASE,
)
FORBIDDEN_PUBLIC = re.compile(r"chatgpt\.com|pageToken", re.IGNORECASE)
URL_PLACEHOLDER = "<redacted-chatgpt-internal-url>"
HOST_PLACEHOLDER = "<redacted-chatgpt-internal-host>"
PATH_PLACEHOLDER = 'endpoint_path="<redacted-internal-path>"'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact_text(text: str) -> tuple[str, int]:
    substitutions = 0

    def replace_url(_: re.Match[str]) -> str:
        nonlocal substitutions
        substitutions += 1
        return URL_PLACEHOLDER

    def replace_key(match: re.Match[str]) -> str:
        nonlocal substitutions
        substitutions += 1
        return f"{match.group('key')}=<redacted>"

    redacted = INTERNAL_URL.sub(replace_url, text)
    redacted, path_count = ENDPOINT_PATH.subn(PATH_PLACEHOLDER, redacted)
    substitutions += path_count
    redacted = OPAQUE_KEY.sub(replace_key, redacted)
    redacted, host_count = re.subn(
        r"chatgpt\.com",
        HOST_PLACEHOLDER,
        redacted,
        flags=re.IGNORECASE,
    )
    substitutions += host_count
    return redacted, substitutions


def load_text_files(root: Path, report_path: Path | None = None) -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if report_path is not None and path.resolve() == report_path.resolve():
            continue
        data = path.read_bytes()
        data.decode("utf-8")
        files[path] = data
    return files


def build_public_tree(
    root: Path,
    report_path: Path | None = None,
) -> tuple[dict[Path, bytes], dict[Path, bytes], dict[Path, int]]:
    original = load_text_files(root, report_path)
    public = dict(original)
    redaction_counts: dict[Path, int] = {}
    pending_hashes: dict[str, str] = {}

    for path, data in original.items():
        if path.suffix.lower() != ".txt":
            continue
        text = data.decode("utf-8")
        if not FORBIDDEN_PUBLIC.search(text):
            continue
        redacted, count = redact_text(text)
        public_data = redacted.encode("utf-8")
        if public_data == data:
            continue
        public[path] = public_data
        redaction_counts[path] = count
        pending_hashes[sha256_bytes(data)] = sha256_bytes(public_data)

    seen_hashes: set[tuple[str, str]] = set()
    for _ in range(12):
        pending = {
            old: new
            for old, new in pending_hashes.items()
            if old != new and (old, new) not in seen_hashes
        }
        if not pending:
            break
        seen_hashes.update(pending.items())
        next_hashes: dict[str, str] = {}
        encoded = {old.encode("ascii"): new.encode("ascii") for old, new in pending.items()}
        for path, data in list(public.items()):
            if path.suffix.lower() not in HASH_REFERENCE_SUFFIXES:
                continue
            updated = data
            for old, new in encoded.items():
                updated = updated.replace(old, new)
            if updated == data:
                continue
            public[path] = updated
            next_hashes[sha256_bytes(data)] = sha256_bytes(updated)
        pending_hashes = next_hashes
    else:
        raise RuntimeError("hash-reference propagation did not converge")

    return original, public, redaction_counts


def check_public_tree(root: Path) -> list[str]:
    issues: list[str] = []
    for path, data in load_text_files(root).items():
        text = data.decode("utf-8")
        if FORBIDDEN_PUBLIC.search(text):
            issues.append(path.relative_to(root).as_posix())
    return issues


def atomic_write(path: Path, data: bytes) -> None:
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def apply_redaction(root: Path, backup_dir: Path, report_path: Path) -> dict[str, object]:
    root = root.resolve()
    backup_dir = backup_dir.resolve()
    report_path = report_path.resolve()
    if backup_dir.exists():
        raise FileExistsError(f"backup directory already exists: {backup_dir}")
    if report_path.exists():
        raise FileExistsError(f"public report already exists: {report_path}")
    try:
        backup_dir.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("private backup must be outside the public evidence root")

    original, public, redaction_counts = build_public_tree(root, report_path)
    changed = [path for path in sorted(original) if original[path] != public[path]]
    if not redaction_counts:
        raise ValueError("no internal request identifiers found")

    backup_dir.mkdir(parents=True)
    records: list[dict[str, object]] = []
    for path in changed:
        relative = path.relative_to(root)
        backup = backup_dir / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        records.append(
            {
                "path": relative.as_posix(),
                "original_sha256": sha256_bytes(original[path]),
                "public_sha256": sha256_bytes(public[path]),
                "redaction_count": redaction_counts.get(path, 0),
            }
        )

    for path in changed:
        atomic_write(path, public[path])

    issues = check_public_tree(root)
    if issues:
        raise RuntimeError(f"public redaction incomplete: {issues[:3]}")

    report = {
        "schema_version": 1,
        "redaction": "chatgpt_internal_request_identifiers",
        "public_placeholders": [URL_PLACEHOLDER, HOST_PLACEHOLDER, "<redacted>"],
        "hash_reference_suffixes": sorted(HASH_REFERENCE_SUFFIXES),
        "stderr_files_redacted": len(redaction_counts),
        "text_files_changed": len(changed),
        "private_backup": f".release/private-evidence/{backup_dir.name}",
        "records": records,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(
        report_path,
        (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    backup_manifest = backup_dir / "backup-manifest.json"
    backup_manifest.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Public evaluation evidence root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Fail if internal identifiers remain")
    mode.add_argument("--apply", action="store_true", help="Create a redacted public tree")
    parser.add_argument("--backup-dir", type=Path, help="Required local-only backup directory for --apply")
    parser.add_argument("--report", type=Path, help="Required public JSON report for --apply")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    if args.check:
        issues = check_public_tree(root)
        print(json.dumps({"status": "PASS" if not issues else "FAIL", "issues": issues}, ensure_ascii=False))
        return 0 if not issues else 1
    if args.backup_dir is None or args.report is None:
        raise SystemExit("--apply requires --backup-dir and --report")
    report = apply_redaction(root, args.backup_dir, args.report)
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
