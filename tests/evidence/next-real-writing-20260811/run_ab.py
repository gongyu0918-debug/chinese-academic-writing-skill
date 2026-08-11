from __future__ import annotations

"""Run the frozen three-provider, two-arm academic-writing holdout matrix."""

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from run_discovery import (
    PROVIDERS,
    Provider,
    catalog_models,
    extracted_read_path,
    final_shape_valid,
    normalize_text,
    runtime_fingerprint,
    runtime_manifest,
    sha256_bytes,
    sha256_file,
    visible_char_count,
)


EVIDENCE_ROOT = Path(__file__).resolve().parent
SPECS_PATH = EVIDENCE_ROOT / "ab_specs.json"
OUTPUT_ROOT = EVIDENCE_ROOT / "ab"
BASELINE_ROOT = Path(
    r"F:\Workspaces\chinese-academic-writing-skill\.release\worktrees\matrix-baseline-v008"
)
CANDIDATE_ROOT = Path(
    r"F:\Workspaces\chinese-academic-writing-skill\.release\worktrees\matrix-candidate-synthesis-20260811"
)
BASELINE_COMMIT = "09b89a6f49f0d97f5bdd983fe29354636a0f5008"
SKILL_SUBDIR = Path("chinese-academic-writing-assistant")
TARGET_DIFF = "references/academic-literature-review.md"
CATALOG_PATH = Path(r"C:\Users\admin\.codex\opencodex-catalog.json")
OPENAI_BASE_URL = "http://127.0.0.1:10100/v1"
TIMEOUT_SECONDS = 1200
ARMS = ("baseline", "candidate")
REQUIRED_READS = (
    "chinese-academic-writing-assistant/SKILL.md",
    "chinese-academic-writing-assistant/references/academic-literature-review.md",
    "chinese-academic-writing-assistant/references/anti-ai-writing.md",
)
FORBIDDEN_TRACE_MARKERS = (
    "tests/evidence",
    "git diff",
    "git log",
    "git show",
    "c:/users/admin/.agents",
    "c:/users/admin/.codex/skills",
)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def load_specs_snapshot() -> tuple[dict[str, Any], str]:
    raw = SPECS_PATH.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if payload.get("schema_version") != 1 or not isinstance(tasks, list) or not tasks:
        raise RuntimeError("ab_specs.json must contain schema_version=1 and tasks")
    task_ids = [row.get("task_id") for row in tasks if isinstance(row, dict)]
    if len(task_ids) != 12 or len(set(task_ids)) != 12:
        raise RuntimeError("ab_specs.json must contain 12 unique pair task IDs")
    provider_names = {provider.name for provider in PROVIDERS}
    if any(row.get("provider") not in provider_names for row in tasks):
        raise RuntimeError("ab_specs.json contains an unknown provider")
    if any(row.get("source_task") not in {"H1", "H2", "H3", "H4"} for row in tasks):
        raise RuntimeError("ab_specs.json contains an unknown source task")
    combinations = {(row["source_task"], row["provider"]) for row in tasks}
    expected_combinations = {
        (source_task, provider.name)
        for source_task in ("H1", "H2", "H3", "H4")
        for provider in PROVIDERS
    }
    if combinations != expected_combinations:
        raise RuntimeError("ab_specs.json must contain each task/provider combination exactly once")
    return payload, sha256_bytes(raw)


def load_specs() -> dict[str, Any]:
    return load_specs_snapshot()[0]


def root_binding(root: Path, expected_commit: str) -> dict[str, Any]:
    if not root.is_dir():
        raise RuntimeError(f"run root missing: {root}")
    actual_commit = run_git(root, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        raise RuntimeError(f"commit mismatch for {root}: {actual_commit}")
    status = run_git(root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError(f"run root is dirty: {root}\n{status}")
    manifest = runtime_manifest(root / SKILL_SUBDIR)
    return {
        "root": str(root),
        "commit": actual_commit,
        "runtime_file_count": len(manifest),
        "runtime_fingerprint": runtime_fingerprint(manifest),
        "runtime_manifest": manifest,
    }


def preflight_payload(
    candidate_commit: str,
    expected_specs_sha256: str | None = None,
) -> dict[str, Any]:
    specs, specs_sha256 = load_specs_snapshot()
    if expected_specs_sha256 is not None and specs_sha256 != expected_specs_sha256:
        raise RuntimeError("ab_specs.json changed after the matrix was frozen")
    if not CATALOG_PATH.is_file():
        raise RuntimeError(f"model catalog missing: {CATALOG_PATH}")
    available_models = catalog_models()
    missing_models = [provider.model for provider in PROVIDERS if provider.model not in available_models]
    if missing_models:
        raise RuntimeError(f"models missing from catalog: {missing_models}")
    baseline = root_binding(BASELINE_ROOT, BASELINE_COMMIT)
    candidate = root_binding(CANDIDATE_ROOT, candidate_commit)
    baseline_manifest = baseline["runtime_manifest"]
    candidate_manifest = candidate["runtime_manifest"]
    if set(baseline_manifest) != set(candidate_manifest):
        raise RuntimeError("runtime file sets differ between arms")
    changed = sorted(
        path
        for path in baseline_manifest
        if baseline_manifest[path] != candidate_manifest[path]
    )
    if changed != [TARGET_DIFF]:
        raise RuntimeError(f"unexpected runtime differences: {changed}")
    baseline_reference = (BASELINE_ROOT / SKILL_SUBDIR / TARGET_DIFF).read_text(encoding="utf-8")
    candidate_reference = (CANDIDATE_ROOT / SKILL_SUBDIR / TARGET_DIFF).read_text(encoding="utf-8")
    char_delta = len(candidate_reference) - len(baseline_reference)
    if char_delta > 0:
        raise RuntimeError(f"candidate reference grew by {char_delta} characters")
    for source_task in ("H1", "H2", "H3", "H4"):
        if not (EVIDENCE_ROOT / "tasks" / f"{source_task}.md").is_file():
            raise RuntimeError(f"missing holdout task: {source_task}")
    task_texts = {
        source_task: (EVIDENCE_ROOT / "tasks" / f"{source_task}.md").read_text(encoding="utf-8")
        for source_task in ("H1", "H2", "H3", "H4")
    }
    return {
        "schema_version": 1,
        "baseline": baseline,
        "candidate": candidate,
        "runtime_changed_files": changed,
        "reference_char_delta": char_delta,
        "specs_sha256": specs_sha256,
        "task_sha256": {
            source_task: sha256_bytes(text.encode("utf-8"))
            for source_task, text in task_texts.items()
        },
        "prompt_sha256": {
            source_task: sha256_bytes(build_prompt(text).encode("utf-8"))
            for source_task, text in task_texts.items()
        },
        "tasks": [row["task_id"] for row in specs["tasks"]],
        "providers": [{"name": item.name, "model": item.model} for item in PROVIDERS],
        "reasoning_effort": "max",
        "calls_planned": len(specs["tasks"]) * len(ARMS),
        "retry_count": 0,
    }


def build_prompt(task_text: str) -> str:
    read_commands = "\n".join(
        f"Get-Content -Raw -LiteralPath '{relative_path.replace('/', chr(92))}'"
        for relative_path in REQUIRED_READS
    )
    return (
        "这是中文论文写作 Skill 的隔离真实任务。只使用当前工作目录中的 "
        "chinese-academic-writing-assistant，不得读取用户目录中的 Skill、其他仓库、"
        "tests/evidence、Git 历史、其他 worktree 或历史结果；不得联网，不得修改文件。\n"
        "第一步必须分别调用 shell_command，逐个完整读取以下文件；一个文件一次命令：\n"
        f"{read_commands}\n"
        "全部读取成功后再完成任务。若任一文件无法读取，最终只输出 ENV_INVALID。"
        "完成三次必读后不得再调用任何工具或命令，也不要用命令统计字数。"
        "最终不得回显命令、规则、读取过程、模型身份、自评或写作过程。\n\n"
        f"{task_text.strip()}\n"
    )


def trace_shape_issues(trace_path: Path, final: str) -> list[str]:
    counts = {"thread.started": 0, "turn.started": 0, "turn.completed": 0}
    messages: list[tuple[int, str]] = []
    command_positions: list[int] = []
    command_completion_positions: list[int] = []
    valid_events: list[tuple[int, dict[str, Any]]] = []
    issues: list[str] = []
    for position, line in enumerate(
        trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            issues.append("malformed_trace_json")
            continue
        valid_events.append((position, event))
        event_type = event.get("type")
        if event_type in counts:
            counts[event_type] += 1
        item = event.get("item") or {}
        if item.get("type") == "command_execution":
            command_positions.append(position)
            if event_type == "item.completed":
                command_completion_positions.append(position)
        if event_type == "item.completed" and item.get("type") == "agent_message":
            messages.append((position, str(item.get("text") or "")))
    for event_type, count in counts.items():
        if count != 1:
            issues.append(f"trace_count:{event_type}:{count}")
    if valid_events:
        if valid_events[0][1].get("type") != "thread.started":
            issues.append("thread_started_not_first")
        if valid_events[-1][1].get("type") != "turn.completed":
            issues.append("turn_completed_not_last")
    turn_started_positions = [
        position
        for position, event in valid_events
        if event.get("type") == "turn.started"
    ]
    if turn_started_positions:
        turn_started = turn_started_positions[0]
        activity_positions = command_positions + [position for position, _ in messages]
        if any(position <= turn_started for position in activity_positions):
            issues.append("activity_not_inside_turn")
    if len(messages) not in {1, 2}:
        issues.append(f"trace_count:agent_message:{len(messages)}")
    if messages:
        final_position, final_message = messages[-1]
        if final_message.strip() != final.strip():
            issues.append("trace_final_mismatch")
        if command_positions:
            if final_position <= max(command_positions):
                issues.append("final_message_not_after_reads")
            progress_positions = [position for position, _ in messages[:-1]]
            if any(message.strip() == final.strip() for _, message in messages[:-1]):
                issues.append("premature_final_message")
            last_read_completion = (
                max(command_completion_positions)
                if command_completion_positions
                else max(command_positions)
            )
            if any(position >= last_read_completion for position in progress_positions):
                issues.append("intermediate_agent_message")
        turn_completed_positions = [
            position
            for position, event in valid_events
            if event.get("type") == "turn.completed"
        ]
        if turn_completed_positions and final_position >= turn_completed_positions[0]:
            issues.append("final_message_not_before_turn_completed")
    return issues


def pre_read_preamble_count(trace_path: Path) -> int:
    first_command: int | None = None
    message_positions: list[int] = []
    for position, line in enumerate(
        trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "command_execution" and first_command is None:
            first_command = position
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            message_positions.append(position)
    if first_command is None:
        return 0
    return sum(position < first_command for position in message_positions)


def trace_issues(trace_path: Path, root: Path, final: str) -> list[str]:
    command_events: list[tuple[int, str, dict[str, Any]]] = []
    for position, line in enumerate(
        trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "command_execution" and event.get("type") in {
            "item.started",
            "item.completed",
        }:
            command_events.append((position, str(event["type"]), item))
    started_events = [
        (position, item)
        for position, event_type, item in command_events
        if event_type == "item.started"
    ]
    completed_events = [
        (position, item)
        for position, event_type, item in command_events
        if event_type == "item.completed"
    ]
    started_items = [item for _, item in started_events]
    command_items = [item for _, item in completed_events]
    commands = [str(item.get("command") or "") for _, _, item in command_events]
    issues = trace_shape_issues(trace_path, final)
    required_targets = {relative_path.casefold() for relative_path in REQUIRED_READS}
    if len(started_items) != len(REQUIRED_READS) or len(command_items) != len(REQUIRED_READS):
        issues.append(
            f"unexpected_command_event_count:{len(started_items)}:{len(command_items)}"
        )
    started_ids = [str(item.get("id") or "") for item in started_items]
    completed_ids = [str(item.get("id") or "") for item in command_items]
    if (
        any(not item_id for item_id in started_ids + completed_ids)
        or len(set(started_ids)) != len(started_ids)
        or len(set(completed_ids)) != len(completed_ids)
        or set(started_ids) != set(completed_ids)
    ):
        issues.append("command_event_pairing_mismatch")
    started_by_id = {str(item.get("id")): item for item in started_items}
    started_position_by_id = {
        str(item.get("id")): position for position, item in started_events
    }
    for item in command_items:
        started = started_by_id.get(str(item.get("id")))
        if started is not None and str(started.get("command") or "") != str(item.get("command") or ""):
            issues.append("command_changed_between_events")
    for completed_position, item in completed_events:
        started_position = started_position_by_id.get(str(item.get("id")))
        if started_position is not None and started_position >= completed_position:
            issues.append("command_completed_before_start")
    for _, _, item in command_events:
        if extracted_read_path(str(item.get("command") or "")) not in required_targets:
            issues.append("unexpected_command")
    for relative_path in REQUIRED_READS:
        target = relative_path.casefold()
        successful_reads = [
            item
            for item in command_items
            if extracted_read_path(str(item.get("command") or "")) == target
            and item.get("status") == "completed"
            and item.get("exit_code") == 0
        ]
        if len(successful_reads) != 1:
            issues.append(f"missing_successful_independent_read:{relative_path}")
            continue
        observed = str(successful_reads[0].get("aggregated_output") or "")
        expected = (root / relative_path).read_text(encoding="utf-8")
        observed = observed.replace("\r\n", "\n").replace("\r", "\n")
        expected = expected.replace("\r\n", "\n").replace("\r", "\n")
        if observed != expected and not (observed.endswith("\n") and observed[:-1] == expected):
            issues.append(f"read_content_mismatch:{relative_path}")
    blob = "\n".join(commands).replace("\\\\", "/").replace("\\", "/").casefold()
    for marker in FORBIDDEN_TRACE_MARKERS:
        if marker in blob:
            issues.append(f"forbidden_trace:{marker}")
    worktree_parent = str(root.parent).replace("\\", "/").casefold()
    allowed_root = str(root).replace("\\", "/").casefold()
    for command in commands:
        normalized = command.replace("\\\\", "/").replace("\\", "/").casefold()
        if worktree_parent in normalized.replace(allowed_root, ""):
            issues.append("forbidden_trace:other_worktree")
    allowed_item_types = {"agent_message", "command_execution"}
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line).get("item")
        except json.JSONDecodeError:
            continue
        item_type = str((item or {}).get("type") or "")
        if item is not None and item_type not in allowed_item_types:
            issues.append(f"forbidden_tool_type:{item_type}")
    return sorted(set(issues))


def provider_by_name(name: str) -> Provider:
    return next(provider for provider in PROVIDERS if provider.name == name)


def run_one(
    pair_spec: dict[str, Any],
    arm: str,
    root: Path,
    binding: dict[str, Any],
    expected_prompt_hash: str,
    staging_root: Path,
) -> dict[str, Any]:
    pair_id = pair_spec["task_id"]
    source_task = pair_spec["source_task"]
    provider = provider_by_name(pair_spec["provider"])
    task_text = (staging_root / "tasks" / f"{pair_id}.md").read_text(encoding="utf-8")
    prompt = build_prompt(task_text)
    prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    prompt_bound = prompt_hash == expected_prompt_hash
    final_path = staging_root / "raw" / arm / f"{pair_id}.md"
    trace_path = staging_root / "traces" / arm / f"{pair_id}.jsonl"
    stderr_path = staging_root / "stderr" / arm / f"{pair_id}.txt"
    for path in (final_path, trace_path, stderr_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(root),
        "-m",
        provider.model,
        "-c",
        f'openai_base_url="{OPENAI_BASE_URL}"',
        "-c",
        f'model_catalog_json="{CATALOG_PATH}"',
        "-c",
        'model_reasoning_effort="max"',
        "-s",
        "read-only",
        "--ephemeral",
        "--json",
        "-o",
        str(final_path),
        "-",
    ]
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        return_code: int | None = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout, stderr = normalize_text(exc.stdout), normalize_text(exc.stderr)
    trace_path.write_text(normalize_text(stdout), encoding="utf-8", newline="\n")
    stderr_path.write_text(normalize_text(stderr), encoding="utf-8", newline="\n")
    final = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    issues = trace_issues(trace_path, root, final)
    shape_ok = final_shape_valid(final)
    return {
        "pair_id": pair_id,
        "source_task": source_task,
        "arm": arm,
        "provider": provider.name,
        "model": provider.model,
        "reasoning_effort": "max",
        "commit": binding["commit"],
        "runtime_fingerprint": binding["runtime_fingerprint"],
        "return_code": return_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "retry_count": 0,
        "prompt_sha256": prompt_hash,
        "prompt_bound": prompt_bound,
        "final_file": final_path.relative_to(staging_root).as_posix(),
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "final_chars_no_whitespace": visible_char_count(final),
        "trace_file": trace_path.relative_to(staging_root).as_posix(),
        "trace_sha256": sha256_file(trace_path),
        "stderr_file": stderr_path.relative_to(staging_root).as_posix(),
        "stderr_sha256": sha256_file(stderr_path),
        "trace_issues": issues,
        "pre_read_preamble_count": pre_read_preamble_count(trace_path),
        "final_shape_valid": shape_ok,
        "valid": return_code == 0 and not timed_out and not issues and shape_ok and prompt_bound,
    }


def binding_identity(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime": {
            arm: (payload[arm]["commit"], payload[arm]["runtime_fingerprint"])
            for arm in ARMS
        },
        "specs_sha256": payload["specs_sha256"],
        "task_sha256": payload["task_sha256"],
        "prompt_sha256": payload["prompt_sha256"],
    }


def execute(candidate_commit: str) -> int:
    specs, frozen_specs_sha256 = load_specs_snapshot()
    preflight = preflight_payload(candidate_commit, frozen_specs_sha256)
    if OUTPUT_ROOT.exists():
        raise RuntimeError(f"A/B output already exists: {OUTPUT_ROOT}")
    staging_root = Path(tempfile.mkdtemp(prefix="ab.incomplete-", dir=EVIDENCE_ROOT))
    records: list[dict[str, Any]] = []
    try:
        for pair_spec in specs["tasks"]:
            task_copy = staging_root / "tasks" / f"{pair_spec['task_id']}.md"
            task_copy.parent.mkdir(parents=True, exist_ok=True)
            source = EVIDENCE_ROOT / "tasks" / f"{pair_spec['source_task']}.md"
            source_text = source.read_text(encoding="utf-8")
            task_copy.write_text(source_text, encoding="utf-8", newline="\n")
            snapshot_hash = sha256_bytes(task_copy.read_text(encoding="utf-8").encode("utf-8"))
            if snapshot_hash != preflight["task_sha256"][pair_spec["source_task"]]:
                raise RuntimeError(f"task changed while freezing snapshot: {pair_spec['task_id']}")
        for source_task in ("H1", "H2", "H3", "H4"):
            current = preflight_payload(candidate_commit, frozen_specs_sha256)
            if binding_identity(current) != binding_identity(preflight):
                raise RuntimeError(f"runtime binding changed before task {source_task}")
            task_rows = [row for row in specs["tasks"] if row["source_task"] == source_task]
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                futures = {}
                for row in task_rows:
                    for arm, root in (("baseline", BASELINE_ROOT), ("candidate", CANDIDATE_ROOT)):
                        futures[
                            pool.submit(
                                run_one,
                                row,
                                arm,
                                root,
                                preflight[arm],
                                preflight["prompt_sha256"][source_task],
                                staging_root,
                            )
                        ] = (row, arm)
                for future in concurrent.futures.as_completed(futures):
                    row, arm = futures[future]
                    try:
                        record = future.result()
                    except Exception as exc:
                        record = {
                            "pair_id": row["task_id"],
                            "source_task": row["source_task"],
                            "arm": arm,
                            "provider": row["provider"],
                            "reasoning_effort": "max",
                            "return_code": None,
                            "timeout": False,
                            "duration_seconds": None,
                            "retry_count": 0,
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                            "valid": False,
                        }
                    records.append(record)
                    print(
                        json.dumps(
                            {
                                key: record.get(key)
                                for key in ("pair_id", "arm", "provider", "valid", "duration_seconds")
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )
        order = {row["task_id"]: index for index, row in enumerate(specs["tasks"])}
        records.sort(key=lambda row: (order[row["pair_id"]], ARMS.index(row["arm"])))
        postflight_error: str | None = None
        try:
            postflight = preflight_payload(candidate_commit, frozen_specs_sha256)
        except Exception as exc:
            postflight = None
            postflight_error = f"{type(exc).__name__}: {exc}"
        binding_stable = bool(
            postflight and binding_identity(postflight) == binding_identity(preflight)
        )
        manifest = {
            **preflight,
            "postflight": postflight,
            "postflight_error": postflight_error,
            "binding_stable": binding_stable,
            "records": records,
            "valid_calls": sum(bool(row.get("valid")) for row in records),
        }
        (staging_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        staging_root.replace(OUTPUT_ROOT)
    except Exception:
        # Preserve the staging directory for diagnosis; a fresh run uses a new directory.
        raise
    expected = int(preflight["calls_planned"])
    print(
        json.dumps(
            {
                "manifest": str(OUTPUT_ROOT / "manifest.json"),
                "valid_calls": manifest["valid_calls"],
                "expected_calls": expected,
                "binding_stable": manifest["binding_stable"],
                "retry_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0 if manifest["valid_calls"] == expected and manifest["binding_stable"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--candidate-commit", required=True)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight_payload(args.candidate_commit), ensure_ascii=False, indent=2))
        return 0
    return execute(args.candidate_commit)


if __name__ == "__main__":
    raise SystemExit(main())
