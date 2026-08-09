from __future__ import annotations

"""Run task-spec-driven mechanical checks over paired writing outputs.

Expected task_specs.json shape:

{
  "schema_version": 1,
  "arms": ["baseline", "candidate"],
  "tasks": [{
    "task_id": "T01",
    "min_han": 1000,
    "max_han": 1300,
    "min_visible": 1200,
    "max_visible": 1800,
    "required_headings": ["3.1 结果", "4.1 讨论"],
    "heading_level": 2,
    "expected_part_count": 2,
    "body_only": true,
    "forbid_lists": true,
    "forbid_revision_notes": true,
    "forbid_process_leak": true,
    "required_literals": ["96份"],
    "forbidden_literals": ["120份"],
    "forbidden_patterns": ["自定义正则"]
  }]
}

Outputs are read from RAW_DIR/ARM/TASK_ID.md. All failures are mechanical
hard failures; semantic quality remains the blind judges' responsibility.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any


HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
HEADING_NUMBER_PREFIX = re.compile(
    r"^(?:[一二三四五六七八九十]+、|\d+[.、．]|[（(][一二三四五六七八九十\d]+[)）]|"
    r"第[一二三四五六七八九十百\d]+[章节部分])[ \t]*"
)
LIST_RE = re.compile(
    r"^[ \t]*(?:"
    r"[-+*][ \t]+|"
    r"\d+[、）)][ \t]*\S|"
    r"\d+\.(?!\d)[ \t]*\S|"
    r"[一二三四五六七八九十]+[、）)][ \t]*\S"
    r")",
)
REVISION_NOTE_PATTERNS = (
    re.compile(
        r"(^|\n)[ \t]*(?:(?:[-+*]|\d+[.)、])[ \t]+)?"
        r"(?:修订|修改|改写|核验|写作)(?:说明|记录|过程|要点)[：:\s]",
        re.MULTILINE,
    ),
    re.compile(
        r"(^|\n)[ \t]*(?:(?:[-+*]|\d+[.)、])[ \t]+)?"
        r"(?:说明|备注|注)[：:][ \t]*(?:本次|本文已|修改|改写|修订)",
        re.MULTILINE,
    ),
)
PROCESS_LEAK_PATTERNS = (
    re.compile(r"(^|\n)[ \t]*(?:以下|下面)(?:是|为).{0,20}(?:正文|改写|修订|内容)[：:]", re.MULTILINE),
    re.compile(r"\bSKILL\.md\b", re.IGNORECASE),
    re.compile(r"\breferences?[/\\]", re.IGNORECASE),
    re.compile(r"\bworktree\b", re.IGNORECASE),
    re.compile(r"(?:候选|基线)(?:版本|分支|样稿|输出)"),
    re.compile(r"(?:本模型|本助手|我)(?:已|将|需要)?(?:读取|加载|调用|遵循|生成|改写)"),
    re.compile(r"(?:按|根据)(?:上述|所给|该)(?:规则|门禁|Skill|reference)"),
    re.compile(r"(?:评测|盲评|打分)(?:结果|过程|标准|门槛)|判定门槛"),
)


class GateError(ValueError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON {path}: {exc}") from exc


def resolve_under(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise GateError(f"path escapes raw directory: {relative}") from exc
    return candidate


def load_specs(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise GateError("task specs must be an object with schema_version=1")
    arms = payload.get("arms", ["baseline", "candidate"])
    tasks = payload.get("tasks")
    if (
        not isinstance(arms, list)
        or len(arms) < 2
        or len(set(arms)) != len(arms)
        or not all(isinstance(arm, str) and arm for arm in arms)
    ):
        raise GateError("task specs arms must contain at least two unique non-empty strings")
    if not isinstance(tasks, list) or not tasks:
        raise GateError("task specs tasks must be a non-empty list")
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise GateError(f"task {index} must be an object")
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise GateError(f"task {index} has invalid task_id")
        if task_id in seen:
            raise GateError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        for key in (
            "required_headings",
            "optional_headings",
            "required_literals",
            "forbidden_literals",
            "forbidden_patterns",
        ):
            value = task.get(key, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise GateError(f"{task_id}.{key} must be a list of strings")
        outputs = task.get("outputs", {})
        if not isinstance(outputs, dict) or not all(
            isinstance(key, str)
            and isinstance(value, str)
            and value
            for key, value in outputs.items()
        ):
            raise GateError(f"{task_id}.outputs must map arm names to non-empty paths")
        for key in (
            "min_han",
            "max_han",
            "min_visible",
            "max_visible",
            "expected_part_count",
            "heading_level",
        ):
            value = task.get(key)
            if value is not None and (not isinstance(value, int) or value < 0):
                raise GateError(f"{task_id}.{key} must be a non-negative integer")
        if (
            task.get("min_han") is not None
            and task.get("max_han") is not None
            and task["min_han"] > task["max_han"]
        ):
            raise GateError(f"{task_id} has min_han greater than max_han")
        if (
            task.get("min_visible") is not None
            and task.get("max_visible") is not None
            and task["min_visible"] > task["max_visible"]
        ):
            raise GateError(f"{task_id} has min_visible greater than max_visible")
    return arms, tasks


def normalize_heading(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip().lstrip("#").strip())
    return HEADING_NUMBER_PREFIX.sub("", text).strip()


def ordered_subsequence(required: list[str], actual: list[str]) -> bool:
    position = 0
    for heading in actual:
        if position < len(required) and heading == required[position]:
            position += 1
    return position == len(required)


def check_output(task: dict[str, Any], text: str) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    han_count = len(HAN_RE.findall(text))
    visible_count = len(re.sub(r"\s+", "", text))
    min_han = task.get("min_han")
    max_han = task.get("max_han")
    min_visible = task.get("min_visible")
    max_visible = task.get("max_visible")
    if min_han is not None and han_count < min_han:
        failures.append(f"han_count {han_count} below minimum {min_han}")
    if max_han is not None and han_count > max_han:
        failures.append(f"han_count {han_count} above maximum {max_han}")
    if min_visible is not None and visible_count < min_visible:
        failures.append(f"visible_count {visible_count} below minimum {min_visible}")
    if max_visible is not None and visible_count > max_visible:
        failures.append(f"visible_count {visible_count} above maximum {max_visible}")

    required = [normalize_heading(item) for item in task.get("required_headings", [])]
    optional = [normalize_heading(item) for item in task.get("optional_headings", [])]
    configured_heading_level = task.get("heading_level")
    plain_heading_level = configured_heading_level if configured_heading_level is not None else 2
    headings: list[dict[str, Any]] = []
    heading_lines: set[int] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", line)
        if match:
            headings.append(
                {
                    "level": len(match.group(1)),
                    "text": normalize_heading(match.group(2)),
                    "plain": False,
                    "line": line_number,
                }
            )
            heading_lines.add(line_number)
            continue
        normalized = normalize_heading(line)
        if normalized and normalized in required:
            headings.append(
                {
                    "level": plain_heading_level,
                    "text": normalized,
                    "plain": True,
                    "line": line_number,
                }
            )
            heading_lines.add(line_number)
    actual_texts = [item["text"] for item in headings]
    missing = [item for item in required if item not in actual_texts]
    if missing:
        failures.append("missing required headings: " + ", ".join(missing))
    if required and not ordered_subsequence(required, actual_texts):
        failures.append("required headings are out of order")

    if configured_heading_level is not None:
        heading_level = configured_heading_level
    else:
        matching_levels = [
            item["level"]
            for item in headings
            if item["text"] in required and not item["plain"]
        ]
        heading_level = min(matching_levels) if matching_levels else plain_heading_level
    part_headings = [
        item
        for item in headings
        if item["level"] == heading_level and item["text"] not in optional
    ]
    expected_parts = task.get("expected_part_count")
    actual_parts = len(part_headings) if part_headings else (1 if text.strip() else 0)
    if expected_parts is not None and actual_parts != expected_parts:
        failures.append(f"output part count {actual_parts} does not equal {expected_parts}")

    if task.get("body_only", False):
        allowed = set(required + optional)
        extra = [item["text"] for item in headings if item["text"] not in allowed]
        if extra:
            failures.append("body-only output has extra headings: " + ", ".join(extra))
        if "```" in text:
            failures.append("body-only output contains a fenced code block")
        if re.search(r"^[ \t]*---+[ \t]*$", text, re.MULTILINE):
            failures.append("body-only output contains a horizontal separator")

    if task.get("forbid_lists", False):
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line_number in heading_lines:
                continue
            if LIST_RE.match(line):
                failures.append(f"output contains a forbidden list at line {line_number}")
                break
    if task.get("forbid_revision_notes", task.get("body_only", False)):
        if any(pattern.search(text) for pattern in REVISION_NOTE_PATTERNS):
            failures.append("output contains a revision or writing note")
    if task.get("forbid_process_leak", task.get("body_only", False)):
        if any(pattern.search(text) for pattern in PROCESS_LEAK_PATTERNS):
            failures.append("output leaks writing, evaluation, or Skill process")

    for literal in task.get("required_literals", []):
        if literal not in text:
            failures.append(f"missing required literal: {literal!r}")
    for literal in task.get("forbidden_literals", []):
        if literal in text:
            failures.append(f"forbidden literal present: {literal!r}")
    for pattern_text in task.get("forbidden_patterns", []):
        try:
            pattern = re.compile(pattern_text, re.MULTILINE)
        except re.error as exc:
            raise GateError(f"{task['task_id']} has invalid forbidden pattern {pattern_text!r}: {exc}") from exc
        if pattern.search(text):
            failures.append(f"forbidden pattern matched: {pattern_text!r}")

    return failures, {
        "han_count": han_count,
        "visible_count": visible_count,
        "heading_count": len(headings),
        "part_count": actual_parts,
        "required_heading_count": len(required),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        arms, tasks = load_specs(args.specs)
        rows: list[dict[str, Any]] = []
        for task in tasks:
            task_id = task["task_id"]
            for arm in arms:
                relative = task.get("outputs", {}).get(arm, f"{arm}/{task_id}.md")
                if not isinstance(relative, str) or not relative:
                    raise GateError(f"{task_id}.outputs.{arm} must be a non-empty string")
                path = resolve_under(args.raw_dir, relative)
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    failures = [f"cannot read output: {exc}"]
                    metrics = {"han_count": 0, "heading_count": 0, "part_count": 0}
                else:
                    failures, metrics = check_output(task, text)
                rows.append(
                    {
                        "task_id": task_id,
                        "arm": arm,
                        "output": path.relative_to(args.raw_dir.resolve()).as_posix(),
                        "passed": not failures,
                        "hard_failures": failures,
                        "metrics": metrics,
                    }
                )
        payload = {
            "schema_version": 1,
            "specs": args.specs.as_posix(),
            "arms": arms,
            "results": rows,
            "passed": all(row["passed"] for row in rows),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"MECHANICAL_GATE={'PASS' if payload['passed'] else 'FAIL'}")
        print(f"RESULTS={len(rows)}")
        return 0 if payload["passed"] else 1
    except GateError as exc:
        print(f"MECHANICAL_GATE=ERROR\nERROR={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
