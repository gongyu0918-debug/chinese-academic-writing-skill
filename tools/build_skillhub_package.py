#!/usr/bin/env python3
"""Build the minimal SkillHub package without publishing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "tools" / "skillhub-package-policy.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def validate_package_path(relative: str) -> None:
    if not relative or "\\" in relative or "\0" in relative:
        raise ValueError(f"unsafe package path: {relative!r}")
    path = PurePosixPath(relative)
    if path.is_absolute() or path.as_posix() != relative:
        raise ValueError(f"unsafe package path: {relative!r}")
    for part in path.parts:
        if part in {"", ".", ".."} or part.rstrip(" .") != part or ":" in part:
            raise ValueError(f"unsafe package path: {relative!r}")
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            raise ValueError(f"unsafe package path: {relative!r}")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def read_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    package = policy.get("skillhub_package")
    if not isinstance(package, dict):
        raise ValueError("policy is missing skillhub_package")
    files = package.get("files")
    if not isinstance(files, list) or not files or any(not isinstance(item, str) for item in files):
        raise ValueError("skillhub_package.files must be a non-empty string list")
    if len(files) != len(set(files)):
        raise ValueError("skillhub_package.files contains duplicates")
    if len(files) != package.get("file_count"):
        raise ValueError("skillhub package file_count does not match whitelist")
    for key in ("root", "license_source", "markdown_license"):
        value = package.get(key)
        if not isinstance(value, str):
            raise ValueError(f"skillhub_package.{key} must be a string")
        validate_package_path(value)
    for relative in files:
        validate_package_path(relative)
    return policy


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("canonical SKILL.md must start with YAML frontmatter")
    try:
        _, raw_frontmatter, body = normalized.split("---\n", 2)
    except ValueError as exc:
        raise ValueError("canonical SKILL.md frontmatter is not closed") from exc
    fields: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            raise ValueError(f"unsupported canonical frontmatter line: {line!r}")
        fields[key.strip()] = value.strip().strip("\"'")
    return fields, body


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_skill_md(canonical_text: str, version: str, derived: dict[str, Any]) -> str:
    if not SEMVER.fullmatch(version):
        raise ValueError(f"version is not valid SemVer: {version}")
    canonical, body = split_frontmatter(canonical_text)
    if set(canonical) != {"name", "description"}:
        raise ValueError("canonical SKILL.md frontmatter must contain only name and description")
    if derived.get("description_source") != "policy":
        raise ValueError("derived description must come from the SkillHub policy")
    if derived.get("name") != canonical["name"]:
        raise ValueError("derived name must match canonical name")

    values: dict[str, Any] = {
        "name": canonical["name"],
        "description": derived.get("description"),
        "slug": derived.get("slug"),
        "version": version,
        "displayName": derived.get("displayName"),
        "tags": derived.get("tags"),
        "license": derived.get("license"),
    }
    order = derived.get("field_order")
    if order != list(values):
        raise ValueError("derived frontmatter field_order does not match the builder contract")
    if any(not isinstance(values[key], str) or not values[key] for key in values if key != "tags"):
        raise ValueError("derived frontmatter contains an empty string field")
    if not isinstance(values["tags"], list) or not values["tags"]:
        raise ValueError("derived frontmatter tags must be a non-empty list")

    lines = ["---"]
    for key in order:
        value = values[key]
        if key == "tags":
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_license(policy: dict[str, Any], source_root: Path) -> None:
    package = policy["skillhub_package"]
    root_license_path = ROOT / package["license_source"]
    markdown_license_path = source_root / package["markdown_license"]
    if not is_within(root_license_path, ROOT):
        raise ValueError("license_source escapes the repository root")
    if not is_within(markdown_license_path, source_root):
        raise ValueError("markdown_license escapes the package root")
    root_license = root_license_path.read_text(encoding="utf-8")
    markdown_license = markdown_license_path.read_text(encoding="utf-8")
    if markdown_license.removeprefix("# ") != root_license:
        raise ValueError("package LICENSE.md must equal the root MIT license with a Markdown heading")
    if package["derived_frontmatter"].get("license") != policy.get("license"):
        raise ValueError("derived and repository licenses must match")


def materialize_package(version: str, output_dir: Path, policy: dict[str, Any]) -> list[str]:
    package = policy["skillhub_package"]
    source_root = ROOT / package["root"]
    if not is_within(source_root, ROOT):
        raise ValueError("skillhub package root escapes the repository root")
    if not source_root.is_dir():
        raise FileNotFoundError(f"skillhub package root is missing: {source_root}")
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    validate_license(policy, source_root)

    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        for relative in package["files"]:
            source = source_root / relative
            if not is_within(source, source_root):
                raise ValueError(f"whitelisted source escapes package root: {relative}")
            if not source.is_file():
                raise FileNotFoundError(f"whitelisted package file is missing: {source}")
            destination = staging / relative
            if not is_within(destination, staging):
                raise ValueError(f"whitelisted destination escapes staging root: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if relative == "SKILL.md":
                rendered = render_skill_md(
                    source.read_text(encoding="utf-8"),
                    version,
                    package["derived_frontmatter"],
                )
                destination.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(source, destination)
        actual = sorted(
            path.relative_to(staging).as_posix()
            for path in staging.rglob("*")
            if path.is_file()
        )
        expected = sorted(package["files"])
        if actual != expected:
            raise ValueError("materialized package does not match the file whitelist")
        os.replace(staging, output_dir)
        return actual
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def create_deterministic_zip(package_dir: Path, zip_path: Path, files: list[str]) -> None:
    if zip_path.exists():
        raise FileExistsError(f"zip output already exists: {zip_path}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{zip_path.stem}-", suffix=".zip", dir=zip_path.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in sorted(files):
                info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, (package_dir / relative).read_bytes())
        os.replace(temporary, zip_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def build(version: str, output_dir: Path, zip_path: Path | None = None) -> dict[str, Any]:
    policy = read_policy()
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if zip_path is not None:
        if zip_path.exists():
            raise FileExistsError(f"zip output already exists: {zip_path}")
        if is_within(zip_path, output_dir):
            raise ValueError("zip output must be outside the package directory")

    materialized = False
    try:
        files = materialize_package(version, output_dir, policy)
        materialized = True
        if zip_path is not None:
            create_deterministic_zip(output_dir, zip_path, files)
        return {
            "version": version,
            "output_dir": str(output_dir),
            "files": files,
            "file_sha256": {relative: sha256_file(output_dir / relative) for relative in files},
            "zip": str(zip_path) if zip_path else None,
            "zip_sha256": sha256_file(zip_path) if zip_path else None,
        }
    except Exception:
        if materialized:
            shutil.rmtree(output_dir, ignore_errors=True)
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="SkillHub SemVer, for example 0.0.9")
    parser.add_argument("--output-dir", required=True, type=Path, help="New directory for the 12-file package")
    parser.add_argument("--zip", dest="zip_path", type=Path, help="Optional deterministic zip output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build(args.version, args.output_dir.resolve(), args.zip_path.resolve() if args.zip_path else None)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
