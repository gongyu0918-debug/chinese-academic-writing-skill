from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVIDENCE_ROOT = Path(__file__).resolve().parent
SPECS_PATH = EVIDENCE_ROOT / "task_specs.json"
OUTPUT_ROOT = EVIDENCE_ROOT / "discovery"
BASELINE_ROOT = Path(
    r"F:\Workspaces\chinese-academic-writing-skill\.release\worktrees\matrix-baseline-v008"
)
EXPECTED_COMMIT = "09b89a6f49f0d97f5bdd983fe29354636a0f5008"
SKILL_ROOT = BASELINE_ROOT / "chinese-academic-writing-assistant"
CATALOG_PATH = Path(r"C:\Users\admin\.codex\opencodex-catalog.json")
OPENAI_BASE_URL = "http://127.0.0.1:10100/v1"
TIMEOUT_SECONDS = 1200
FORBIDDEN_TRACE_MARKERS = (
    "tests/evidence",
    "git diff",
    "git log",
    "git show",
    "c:/users/admin/.agents",
    "c:/users/admin/.codex/skills",
)
READ_COMMAND_RE = re.compile(
    r'''(?i)^(?:"[^"\r\n]*/(?:pwsh|powershell)(?:\.exe)?"|(?:pwsh|powershell)(?:\.exe)?)\s+(?:-(?:noprofile|noninteractive|nologo)\s+)*-command\s+"get-content\s+-raw\s+-literalpath\s+'([^'\r\n]+)'\s*"\s*$'''
)


@dataclass(frozen=True)
class Provider:
    name: str
    model: str


PROVIDERS = (
    Provider("alibaba", "alibaba-token-plan/deepseek-v4-flash-0731"),
    Provider("ollama", "ollama-cloud/deepseek-v4-flash:0731"),
    Provider("minimax", "minimax-cn/MiniMax-M3"),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_git(*args: str, cwd: Path = BASELINE_ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def runtime_manifest(root: Path = SKILL_ROOT) -> dict[str, str]:
    files = [path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(files, key=lambda item: item.relative_to(root).as_posix().casefold())
    }


def runtime_fingerprint(manifest: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(manifest, key=str.casefold):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(manifest[relative_path]))
    return digest.hexdigest()


def load_specs() -> dict[str, dict[str, Any]]:
    payload = json.loads(SPECS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise RuntimeError("task_specs.json must contain a non-empty object")
    return payload


def catalog_models() -> set[str]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {str(item.get("slug")) for item in payload.get("models", []) if item.get("slug")}


def preflight_payload() -> dict[str, Any]:
    if not BASELINE_ROOT.is_dir():
        raise RuntimeError(f"baseline root missing: {BASELINE_ROOT}")
    if not CATALOG_PATH.is_file():
        raise RuntimeError(f"model catalog missing: {CATALOG_PATH}")
    actual_commit = run_git("rev-parse", "HEAD")
    if actual_commit != EXPECTED_COMMIT:
        raise RuntimeError(f"baseline commit mismatch: {actual_commit}")
    status = run_git("status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError(f"baseline worktree is dirty:\n{status}")
    specs = load_specs()
    required_paths = {
        relative_path
        for spec in specs.values()
        for relative_path in spec["required_reads"]
    }
    missing = [path for path in sorted(required_paths) if not (BASELINE_ROOT / path).is_file()]
    if missing:
        raise RuntimeError(f"required runtime files missing: {missing}")
    available_models = catalog_models()
    missing_models = [provider.model for provider in PROVIDERS if provider.model not in available_models]
    if missing_models:
        raise RuntimeError(f"models missing from catalog: {missing_models}")
    manifest = runtime_manifest()
    return {
        "baseline_commit": actual_commit,
        "baseline_root": str(BASELINE_ROOT),
        "runtime_file_count": len(manifest),
        "runtime_fingerprint": runtime_fingerprint(manifest),
        "tasks": list(specs),
        "providers": [{"name": item.name, "model": item.model} for item in PROVIDERS],
        "reasoning_effort": "max",
        "calls_planned": len(specs) * len(PROVIDERS),
        "retry_count": 0,
    }


def read_commands(required_reads: list[str]) -> str:
    commands = []
    for relative_path in required_reads:
        windows_path = relative_path.replace("/", "\\")
        commands.append(f"Get-Content -Raw -LiteralPath '{windows_path}'")
    return "\n".join(commands)


def build_prompt(task_text: str, required_reads: list[str]) -> str:
    return (
        "这是中文论文写作 Skill 的隔离真实任务。只使用当前工作目录中的 "
        "chinese-academic-writing-assistant，不得读取用户目录中的 Skill、其他仓库、"
        "tests/evidence、Git 历史、其他 worktree 或历史结果；不得联网，不得修改文件。\n"
        "第一步必须分别调用 shell_command，逐个完整读取以下文件；一个文件一次命令：\n"
        f"{read_commands(required_reads)}\n"
        "全部读取成功后再完成任务。若任一文件无法读取，最终只输出 ENV_INVALID。"
        "最终不得回显命令、规则、读取过程、模型身份、自评或写作过程。\n\n"
        f"{task_text.strip()}\n"
    )


def completed_command_items(trace_path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "command_execution"
        ):
            items.append(item)
    return items


def normalize_command_blob(commands: list[str]) -> str:
    return "\n".join(commands).replace("\\\\", "/").replace("\\", "/").lower()


def extracted_read_path(command: str) -> str | None:
    normalized = command.replace("\\\\", "/").replace("\\", "/")
    if any(separator in normalized for separator in (";", "|", "&&", "\r", "\n")):
        return None
    match = READ_COMMAND_RE.fullmatch(normalized)
    if match is None:
        return None
    path = match.group(1).strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.casefold()


def trace_valid(trace_path: Path, required_reads: list[str]) -> tuple[bool, list[str]]:
    command_items = completed_command_items(trace_path)
    commands = [str(item.get("command") or "") for item in command_items]
    blob = normalize_command_blob(commands)
    issues: list[str] = []
    for relative_path in required_reads:
        target = relative_path.casefold()
        valid_item_found = False
        for item in command_items:
            if (
                extracted_read_path(str(item.get("command") or "")) == target
                and item.get("status") == "completed"
                and item.get("exit_code") == 0
                and str(item.get("aggregated_output") or "").strip()
            ):
                valid_item_found = True
                break
        if not valid_item_found:
            issues.append(f"missing_successful_independent_read:{relative_path}")
    for marker in FORBIDDEN_TRACE_MARKERS:
        if marker in blob:
            issues.append(f"forbidden_trace:{marker}")
    worktree_parent = str(BASELINE_ROOT.parent).replace("\\", "/").casefold()
    allowed_root = str(BASELINE_ROOT).replace("\\", "/").casefold()
    for command in commands:
        normalized_command = command.replace("\\\\", "/").replace("\\", "/").casefold()
        without_allowed_root = normalized_command.replace(allowed_root, "")
        if worktree_parent in without_allowed_root:
            issues.append("forbidden_trace:other_worktree")
    forbidden_item_types = {"web_search", "mcp_tool_call", "computer_tool_call"}
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item_type = str((json.loads(line).get("item") or {}).get("type") or "")
        except json.JSONDecodeError:
            continue
        if item_type in forbidden_item_types:
            issues.append(f"forbidden_tool_type:{item_type}")
    return not issues, issues


def final_shape_valid(final: str) -> bool:
    stripped = final.strip()
    if not stripped or "ENV_INVALID" in stripped:
        return False
    forbidden = ("读取过程", "SHA-256", "我先读取", "```powershell", "自评：")
    return not any(marker in stripped for marker in forbidden)


def visible_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def mechanical_issues(final: str, spec: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    count = visible_char_count(final)
    if count < int(spec["min_chars"]):
        issues.append(f"too_short:{count}<{spec['min_chars']}")
    if count > int(spec["max_chars"]):
        issues.append(f"too_long:{count}>{spec['max_chars']}")
    for literal in spec.get("required_literals", []):
        if literal not in final:
            issues.append(f"missing_literal:{literal}")
    for literal in spec.get("forbidden_literals", []):
        if literal in final:
            issues.append(f"forbidden_literal:{literal}")
    return issues


def run_one(
    task_id: str,
    spec: dict[str, Any],
    provider: Provider,
    runtime_fingerprint_value: str,
    output_root: Path,
) -> dict[str, Any]:
    task_text = (EVIDENCE_ROOT / spec["task_file"]).read_text(encoding="utf-8")
    required_reads = list(spec["required_reads"])
    prompt = build_prompt(task_text, required_reads)
    slug = f"{provider.name}-{task_id.lower()}"
    final_path = output_root / f"{slug}.final.md"
    trace_path = output_root / f"{slug}.trace.jsonl"
    stderr_path = output_root / f"{slug}.stderr.txt"
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(BASELINE_ROOT),
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
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout = normalize_text(exc.stdout)
        stderr = normalize_text(exc.stderr)
    trace_path.write_text(normalize_text(stdout), encoding="utf-8", newline="\n")
    stderr_path.write_text(normalize_text(stderr), encoding="utf-8", newline="\n")
    final = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    load_ok, load_issues = trace_valid(trace_path, required_reads)
    shape_ok = final_shape_valid(final)
    return {
        "task": task_id,
        "provider": provider.name,
        "model": provider.model,
        "reasoning_effort": "max",
        "baseline_commit": EXPECTED_COMMIT,
        "runtime_fingerprint": runtime_fingerprint_value,
        "return_code": return_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "retry_count": 0,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "final_file": final_path.name,
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "final_chars_no_whitespace": visible_char_count(final),
        "trace_file": trace_path.name,
        "trace_sha256": sha256_file(trace_path),
        "stderr_file": stderr_path.name,
        "stderr_sha256": sha256_file(stderr_path),
        "trace_load_valid": load_ok,
        "trace_issues": load_issues,
        "final_shape_valid": shape_ok,
        "mechanical_issues": mechanical_issues(final, spec) if final else ["missing_final"],
        "valid": return_code == 0 and not timed_out and load_ok and shape_ok,
    }


def execute() -> int:
    preflight = preflight_payload()
    if OUTPUT_ROOT.exists():
        raise RuntimeError(f"discovery output already exists: {OUTPUT_ROOT}")
    staging_root = Path(
        tempfile.mkdtemp(
            prefix="discovery.incomplete-",
            dir=EVIDENCE_ROOT,
        )
    )
    specs = load_specs()
    records: list[dict[str, Any]] = []
    for task_id, spec in specs.items():
        current_binding = preflight_payload()
        if (
            current_binding["baseline_commit"] != preflight["baseline_commit"]
            or current_binding["runtime_fingerprint"] != preflight["runtime_fingerprint"]
        ):
            raise RuntimeError(f"runtime binding changed before task {task_id}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(PROVIDERS)) as pool:
            futures = {
                pool.submit(
                    run_one,
                    task_id,
                    spec,
                    provider,
                    str(preflight["runtime_fingerprint"]),
                    staging_root,
                ): provider
                for provider in PROVIDERS
            }
            for future in concurrent.futures.as_completed(futures):
                provider = futures[future]
                try:
                    record = future.result()
                except Exception as exc:  # Preserve a failed call without retrying it.
                    record = {
                        "task": task_id,
                        "provider": provider.name,
                        "model": provider.model,
                        "reasoning_effort": "max",
                        "baseline_commit": EXPECTED_COMMIT,
                        "runtime_fingerprint": preflight["runtime_fingerprint"],
                        "return_code": None,
                        "timeout": False,
                        "duration_seconds": None,
                        "retry_count": 0,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "mechanical_issues": ["runner_exception"],
                        "valid": False,
                    }
                records.append(record)
                print(
                    json.dumps(
                        {
                            key: record[key]
                            for key in (
                                "task",
                                "provider",
                                "valid",
                                "duration_seconds",
                                "mechanical_issues",
                            )
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
    provider_order = {item.name: index for index, item in enumerate(PROVIDERS)}
    task_order = {task_id: index for index, task_id in enumerate(specs)}
    records.sort(key=lambda item: (task_order[item["task"]], provider_order[item["provider"]]))
    postflight_error: str | None = None
    try:
        postflight = preflight_payload()
    except Exception as exc:
        postflight = None
        postflight_error = f"{type(exc).__name__}: {exc}"
    binding_stable = bool(
        postflight
        and postflight["baseline_commit"] == preflight["baseline_commit"]
        and postflight["runtime_fingerprint"] == preflight["runtime_fingerprint"]
    )
    manifest = {
        **preflight,
        "postflight": postflight,
        "postflight_error": postflight_error,
        "binding_stable": binding_stable,
        "records": records,
        "valid_calls": sum(bool(item["valid"]) for item in records),
        "mechanical_issue_calls": sum(bool(item["mechanical_issues"]) for item in records),
    }
    manifest_path = staging_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    staging_root.replace(OUTPUT_ROOT)
    manifest_path = OUTPUT_ROOT / "manifest.json"
    expected_calls = int(preflight["calls_planned"])
    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "valid_calls": manifest["valid_calls"],
                "expected_calls": expected_calls,
                "retry_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0 if manifest["valid_calls"] == expected_calls and binding_stable else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight_payload(), ensure_ascii=False, indent=2))
        return 0
    return execute()


if __name__ == "__main__":
    raise SystemExit(main())
