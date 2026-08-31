from __future__ import annotations

"""Run a zero-retry, five-provider real-writing matrix for one frozen Skill arm."""

import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(r"C:\Users\admin\.codex\opencodex-catalog.json")
OPENAI_BASE_URL = "http://127.0.0.1:10100/v1"
TIMEOUT_SECONDS = 1200
REQUIRED_READS = ("SKILL.md", "references/academic-writing.md")
FORBIDDEN_MARKERS = (
    "tests/evidence",
    "git diff",
    "git log",
    "git show",
    "c:/users/admin/.agents",
    "c:/users/admin/.codex/skills",
)
READ_RE = re.compile(r"(?i)get-content\s+-raw\s+-literalpath\s+['\"]([^'\"]+)['\"]")


@dataclass(frozen=True)
class Provider:
    name: str
    model: str


PROVIDERS = (
    Provider("alibaba2", "alibaba-token-plan-2/deepseek-v4-flash-0731"),
    Provider("alibaba1", "alibaba-token-plan/deepseek-v4-flash-0731"),
    Provider("ollama", "ollama-cloud/deepseek-v4-flash:0731"),
    Provider("opencode", "opencode-go/deepseek-v4-flash"),
    Provider("minimax", "minimax-cn/MiniMax-M3"),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def skill_manifest(root: Path) -> dict[str, str]:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in files}


def skill_fingerprint(manifest: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(manifest, key=str.casefold):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(manifest[relative]))
    return digest.hexdigest()


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if payload.get("schema_version") != 1 or not isinstance(cases, list) or not cases:
        raise RuntimeError("cases.json must contain schema_version=1 and a non-empty cases list")
    ids = [case.get("task_id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(cases) or len(ids) != len(set(ids)):
        raise RuntimeError("task IDs must be non-empty and unique")
    for case in cases:
        if not isinstance(case.get("request"), str) or not case["request"].strip():
            raise RuntimeError(f"case {case.get('task_id')} lacks a request")
    return cases


def build_prompt(request: str) -> str:
    commands = "\n".join(
        f"Get-Content -Raw -LiteralPath 'skill\\{relative.replace('/', chr(92))}'"
        for relative in REQUIRED_READS
    )
    return (
        "这是中文论文写作 Skill 的隔离真实任务。只使用当前目录的 skill，不得读取用户目录中的 Skill、"
        "其他仓库、tests/evidence、Git 历史、历史结果或其他 worktree；不得联网，不得修改文件。\n"
        "第一步必须分别调用 shell_command，逐个完整读取以下文件；一个文件一次命令：\n"
        f"{commands}\n"
        "全部读取成功后再完成任务。若任一文件无法读取，最终只输出 ENV_INVALID。读取完成后不得再调用工具。"
        "最终不得回显命令、规则、读取过程、模型身份、自评、字数或写作过程。\n\n"
        f"{request.strip()}\n"
    )


def completed_commands(trace: str) -> list[str]:
    commands: list[str] = []
    for line in trace.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "command_execution"
            and item.get("status") == "completed"
            and item.get("exit_code") == 0
        ):
            commands.append(str(item.get("command") or ""))
    return commands


def observed_reads(trace: str, copied_skill: Path) -> list[str]:
    reads: list[str] = []
    copied_root = re.sub(r"[\\/]+", "/", str(copied_skill.resolve())).casefold().rstrip("/")
    for command in completed_commands(trace):
        match = READ_RE.search(command.replace('\\"', '"'))
        if match is None:
            continue
        normalized = re.sub(r"[\\/]+", "/", match.group(1)).casefold()
        if normalized.startswith(f"{copied_root}/"):
            normalized = normalized[len(copied_root) + 1 :]
        else:
            normalized = normalized.removeprefix("./").removeprefix("skill/")
        reads.append(normalized)
    return sorted(set(reads))


def trace_forbidden(trace: str) -> list[str]:
    normalized = trace.replace("\\", "/").casefold()
    return [marker for marker in FORBIDDEN_MARKERS if marker in normalized]


def run_one(
    provider: Provider,
    case: dict[str, Any],
    arm: str,
    skill_root: Path,
    source_fingerprint: str,
    output_root: Path,
) -> dict[str, Any]:
    call_root = output_root / provider.name / case["task_id"]
    call_root.mkdir(parents=True, exist_ok=False)
    copied_skill = call_root / "skill"
    shutil.copytree(skill_root, copied_skill)
    copied_before = skill_fingerprint(skill_manifest(copied_skill))
    prompt = build_prompt(case["request"])
    final_path = call_root / "final.md"
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(call_root),
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
        trace = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        trace = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    (call_root / "trace.jsonl").write_text(trace, encoding="utf-8", newline="\n")
    (call_root / "stderr.txt").write_text(stderr, encoding="utf-8", newline="\n")
    final = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    copied_after = skill_fingerprint(skill_manifest(copied_skill))
    reads = observed_reads(trace, copied_skill)
    forbidden = trace_forbidden(trace)
    required_reads = sorted(path.casefold() for path in REQUIRED_READS)
    unexpected_reads = sorted(set(reads) - set(required_reads))
    route_complete = reads == required_reads
    technical_valid = (
        return_code == 0
        and not timed_out
        and bool(final.strip())
        and final.strip() != "ENV_INVALID"
        and copied_before == copied_after == source_fingerprint
        and not forbidden
    )
    return {
        "arm": arm,
        "task_id": case["task_id"],
        "kind": case["kind"],
        "provider": provider.name,
        "model": provider.model,
        "reasoning_effort": "max",
        "retry_count": 0,
        "return_code": return_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "final_file": final_path.relative_to(output_root).as_posix(),
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "final_chars": len(final),
        "observed_reads": reads,
        "unexpected_reads": unexpected_reads,
        "route_complete": route_complete,
        "forbidden_trace_markers": forbidden,
        "skill_binding_stable": copied_before == copied_after == source_fingerprint,
        "technical_valid": technical_valid,
        "valid": technical_valid and route_complete,
    }


def run_provider_lane(
    provider: Provider,
    cases: list[dict[str, Any]],
    arm: str,
    skill_root: Path,
    source_fingerprint: str,
    output_root: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in cases:
        try:
            record = run_one(
                provider,
                case,
                arm,
                skill_root,
                source_fingerprint,
                output_root,
            )
        except Exception as exc:
            record = {
                "arm": arm,
                "provider": provider.name,
                "task_id": case["task_id"],
                "retry_count": 0,
                "technical_valid": False,
                "valid": False,
                "exception": f"{type(exc).__name__}: {exc}",
            }
        records.append(record)
        print(
            json.dumps(
                {key: record.get(key) for key in ("provider", "task_id", "valid", "duration_seconds")},
                ensure_ascii=False,
            ),
            flush=True,
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cases-file", type=Path)
    parser.add_argument("--task-id", action="append")
    parser.add_argument("--provider", action="append", choices=tuple(item.name for item in PROVIDERS))
    parser.add_argument("--workers", type=int, default=5, help="parallel provider lanes; each lane is serial")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence_root = Path(__file__).resolve().parent
    cases_path = args.cases_file.resolve() if args.cases_file else evidence_root / "cases.json"
    cases = load_cases(cases_path)
    if args.task_id:
        requested = set(args.task_id)
        known = {case["task_id"] for case in cases}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"unknown task IDs: {unknown}")
        cases = [case for case in cases if case["task_id"] in requested]
    skill_root = args.skill_root.resolve()
    output_root = args.output_root.resolve()
    if args.workers < 1:
        raise SystemExit("workers must be at least 1")
    if output_root.exists():
        raise SystemExit(f"output root already exists: {output_root}")
    if not skill_root.is_dir() or not CATALOG_PATH.is_file():
        raise SystemExit("skill root or model catalog is missing")
    selected = tuple(item for item in PROVIDERS if not args.provider or item.name in args.provider)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    available = {str(item.get("slug")) for item in catalog.get("models", [])}
    missing = [item.model for item in selected if item.model not in available]
    if missing:
        raise SystemExit(f"models missing from catalog: {missing}")
    source_manifest = skill_manifest(skill_root)
    source_fingerprint = skill_fingerprint(source_manifest)
    output_root.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.workers, len(selected))) as pool:
        futures = {
            pool.submit(
                run_provider_lane,
                provider,
                cases,
                args.arm,
                skill_root,
                source_fingerprint,
                output_root,
            ): provider.name
            for provider in selected
        }
        for future in concurrent.futures.as_completed(futures):
            provider_name = futures[future]
            try:
                lane_records = future.result()
            except Exception as exc:
                raise RuntimeError(f"provider lane failed before recording: {provider_name}") from exc
            records.extend(lane_records)
    source_after = skill_fingerprint(skill_manifest(skill_root))
    records.sort(key=lambda row: (row["provider"], row["task_id"]))
    manifest = {
        "schema_version": 1,
        "arm": args.arm,
        "reasoning_effort": "max",
        "zero_retry": True,
        "cases_sha256": sha256_file(cases_path),
        "source_skill_root": str(skill_root),
        "source_runtime_manifest": source_manifest,
        "source_fingerprint_before": source_fingerprint,
        "source_fingerprint_after": source_after,
        "source_binding_stable": source_fingerprint == source_after,
        "providers": [asdict(item) for item in selected],
        "calls_planned": len(cases) * len(selected),
        "calls_completed": len(records),
        "valid_calls": sum(bool(record.get("valid")) for record in records),
        "records": records,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "calls": manifest["calls_completed"],
                "valid": manifest["valid_calls"],
                "source_binding_stable": manifest["source_binding_stable"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if manifest["valid_calls"] == manifest["calls_planned"] and manifest["source_binding_stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
