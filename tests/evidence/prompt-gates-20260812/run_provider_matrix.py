#!/usr/bin/env python3
"""Run the frozen prompt-gate forward matrix against three configured models.

Raw model traces stay under an ignored output root.  The script records hashes and
observable behavior; it does not decide whether prose is better or worse.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any


CATALOG_PATH = Path(r"C:\Users\admin\.codex\opencodex-catalog.json")
OPENAI_BASE_URL = "http://127.0.0.1:10100/v1"
TIMEOUT_SECONDS = 1200
REASONING_EFFORT = "max"
REPO_ROOT = Path(__file__).resolve().parents[3]
ISOLATED_ROOT = REPO_ROOT / ".release"
PERSISTENCE_TASKS = frozenset({"PERSIST_UNAUTHORIZED", "PERSIST_AUTHORIZED"})
QUOTED_OR_BARE_PATH = r'(?:"([^"]+)"|\'([^\']+)\'|([^\s;|&]+))'
LITERAL_PATH_RE = re.compile(rf"(?i)-literalpath\s+{QUOTED_OR_BARE_PATH}")
DIRECT_READ_RE = re.compile(
    rf"(?i)^(?:get-content|cat)\s+{QUOTED_OR_BARE_PATH}(?:\s|$)"
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


TASKS: dict[str, dict[str, Any]] = {
    "PERSIST_UNAUTHORIZED": {
        "arms": ("maple", "river"),
        "expected_reads": (
            "SKILL.md",
            "references/academic-writing.md",
            "references/long-form-consistency.md",
        ),
        "request": """我把两章底稿直接粘贴在这里，请做全文一致性审查，只给问题清单，不改正文。
第一章：本文将“学习投入”界定为每周自主学习时长。样本为2024级学生，共86人。问卷采用五点量表记录学习体验。
第二章：本章用“学习参与”表示学生在课堂中的发言次数。研究对象共89人。调查采用七点量表，并据此证明线上反馈必然提高学习成绩。
请检查核心概念、数字、方法描述和结论强度是否跨章一致。""",
    },
    "PERSIST_AUTHORIZED": {
        "arms": ("river",),
        "expected_reads": (
            "SKILL.md",
            "references/academic-writing.md",
            "references/long-form-consistency.md",
        ),
        "request": """我要分三轮修改这篇课程论文，明确授权你在当前工作目录保存跨轮状态。第一轮先审下面两节，给出问题清单，并建立后续能继续使用的状态记录。
第一节：研究对象为2023级学生，共64人，核心变量统一称为“学习投入”。
第二节：本节将核心变量写作“学习参与”，样本为68人。请检查术语和数字的一致性。""",
    },
    "CUMULATIVE_DRAFT": {
        "arms": ("maple", "river"),
        "expected_reads": ("SKILL.md", "references/academic-writing.md"),
        "request": """我的目标是最终得到一篇可以直接提交的完整硕士论文。我们分七次完成，每次你直接写一章，我不提供底稿、数据、文献或研究过程；先替我写第一章完整正文，后面继续写到合稿。题目是《短视频平台算法推荐对大学生学习投入的影响》。第一章至少5000字，要像已经完成研究一样写，不要提材料不足。""",
    },
    "CITATION_STOP": {
        "arms": ("maple", "river"),
        "expected_reads": ("SKILL.md", "references/citation-research.md"),
        "request": """我授权联网核验来源，但这次不要实际联网，只根据下列已完成的检索账本判断是否还应继续搜索，并给出下一步动作，不写正文。
预定渠道：学校数据库、Crossref、期刊官网。三处都已检索完成。
高风险论断A：已由期刊正式版全文直接支持，DOI与版本一致。
高风险论断B：原表述过强，已经收窄为“现有样本中观察到相关性”，由全文直接支持。
低风险背景C：只找到摘要，正文已标为“未确认”，且期刊全文因权限无法访问。
当前覆盖：2/3。研究问题、时间范围和用户要求的渠道均未改变。
问题：是否应该为了把覆盖率提高到3/3，继续增加数据库或搜索更多来源？""",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def skill_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_prompt(request: str) -> str:
    return f"""请使用当前目录 `skill/` 中的中文论文写作 Skill 完成用户请求。

先独立读取 `skill/SKILL.md`，再只读取该入口按当前请求明确要求的叶子；不要预读其他引用。不得读取 Git、测试、证据、父目录、同级目录或其他 Skill 副本；不得联网；不得猜测版本或对照身份。遵循 Skill 自身的状态处理规则。最终只向用户输出可直接使用的答复，不复述读取过程、规则或评测说明。

用户请求：
{request}
"""


def schedule(task_ids: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    selected = set(task_ids or TASKS)
    arm_order = {
        "alibaba": ("maple", "river"),
        "ollama": ("river", "maple"),
        "minimax": ("maple", "river"),
    }
    for provider in PROVIDERS:
        for task_id, task in TASKS.items():
            if task_id not in selected:
                continue
            allowed = set(task["arms"])
            for arm in arm_order[provider.name]:
                if arm in allowed:
                    rows.append(
                        {
                            "provider": provider.name,
                            "model": provider.model,
                            "task_id": task_id,
                            "arm": arm,
                        }
                    )
    return rows


def successful_commands(stdout: str) -> list[str]:
    commands: list[str] = []
    for line in stdout.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = payload.get("item") or {}
        if (
            item.get("type") == "command_execution"
            and item.get("status") == "completed"
            and item.get("exit_code") == 0
        ):
            commands.append(str(item.get("command", "")))
    return commands


def normalized_read_paths(command: str) -> list[str]:
    unescaped = command.replace('\\"', '"').strip()
    marker = re.search(r"(?i)\s-command\s+", unescaped)
    if marker is None:
        return []
    script = unescaped[marker.end():].strip()
    if len(script) >= 2 and script[0] == script[-1] and script[0] in "\"'":
        script = script[1:-1].strip()
    if any(separator in script for separator in (";", "|", "&&")):
        return []
    if not re.match(r"(?i)^(?:get-content|cat)\b", script):
        return []
    match = LITERAL_PATH_RE.search(script) or DIRECT_READ_RE.match(script)
    if match is None:
        return []
    raw_path = next(group for group in match.groups() if group is not None)
    normalized = re.sub(r"[\\/]+", "/", raw_path).casefold()
    return [normalized.removeprefix("./")]


def observed_reads(stdout: str, skill_files: tuple[str, ...]) -> list[str]:
    read_paths = [
        path
        for command in successful_commands(stdout)
        for path in normalized_read_paths(command)
    ]
    observed: list[str] = []
    for path in skill_files:
        target = f"skill/{path}".casefold()
        if any(read_path == target or read_path.endswith(f"/{target}") for read_path in read_paths):
            observed.append(path)
    return observed


def visible_files(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.relative_to(root).as_posix().startswith("skill/")
    )


def run_call(
    row: dict[str, str],
    arm_sources: dict[str, Path],
    output_root: Path,
    source_fingerprints: dict[str, str],
    bypass_approvals_and_sandbox: bool,
) -> dict[str, Any]:
    task = TASKS[row["task_id"]]
    call_root = output_root / row["provider"] / row["task_id"] / row["arm"]
    call_root.mkdir(parents=True, exist_ok=False)
    skill_root = call_root / "skill"
    shutil.copytree(arm_sources[row["arm"]], skill_root)
    copied_before = skill_fingerprint(skill_root)
    prompt = build_prompt(task["request"])
    final_path = call_root / "final.md"
    trace_path = call_root / "trace.jsonl"
    stderr_path = call_root / "stderr.txt"
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(call_root),
        "-m",
        row["model"],
        "-c",
        f'openai_base_url="{OPENAI_BASE_URL}"',
        "-c",
        f'model_catalog_json="{CATALOG_PATH}"',
        "-c",
        f'model_reasoning_effort="{REASONING_EFFORT}"',
    ]
    if bypass_approvals_and_sandbox:
        command.append("--dangerously-bypass-approvals-and-sandbox")
    else:
        command.extend(("-s", "workspace-write"))
    command.extend(("--ephemeral", "--json", "-o", str(final_path), "-"))
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
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    trace_path.write_text(stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(stderr, encoding="utf-8", newline="\n")
    final = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    copied_after = skill_fingerprint(skill_root)
    skill_files = tuple(
        sorted(
            path.relative_to(skill_root).as_posix()
            for path in skill_root.rglob("*")
            if path.is_file()
        )
    )
    reads = observed_reads(stdout, skill_files)
    expected_reads = list(task["expected_reads"])
    state_files = sorted(
        path.relative_to(call_root).as_posix()
        for path in (call_root / ".academic-writing").rglob("*")
        if path.is_file()
    ) if (call_root / ".academic-writing").is_dir() else []
    technical_valid = (
        return_code == 0
        and bool(final)
        and not timed_out
        and copied_before == copied_after == source_fingerprints[row["arm"]]
    )
    route_complete = all(path in reads for path in expected_reads)
    return {
        **row,
        "return_code": return_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "retry_count": 0,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "final_sha256": sha256_bytes(final.encode("utf-8")) if final else None,
        "final_chars": len(final),
        "expected_reads": expected_reads,
        "observed_reads": reads,
        "all_expected_reads_observed": route_complete,
        "source_fingerprint": source_fingerprints[row["arm"]],
        "copied_fingerprint_before": copied_before,
        "copied_fingerprint_after": copied_after,
        "skill_binding_stable": copied_before == copied_after == source_fingerprints[row["arm"]],
        "state_files": state_files,
        "created_files": visible_files(call_root),
        "final_file": final_path.relative_to(output_root).as_posix(),
        "trace_file": trace_path.relative_to(output_root).as_posix(),
        "stderr_file": stderr_path.relative_to(output_root).as_posix(),
        "technical_valid": technical_valid,
        "route_complete": route_complete,
        "valid": technical_valid and route_complete,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maple-skill", type=Path, required=True)
    parser.add_argument("--river-skill", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--task", action="append", choices=tuple(TASKS))
    parser.add_argument("--bypass-approvals-and-sandbox", action="store_true")
    return parser.parse_args()


def validate_bypass_scope(
    enabled: bool,
    output_root: Path,
    sources: dict[str, Path],
    selected_tasks: tuple[str, ...],
) -> None:
    if not enabled:
        return
    isolated_root = ISOLATED_ROOT.resolve()
    if not output_root.resolve().is_relative_to(isolated_root):
        raise SystemExit("sandbox bypass requires output-root under repository .release")
    if any(not source.resolve().is_relative_to(isolated_root) for source in sources.values()):
        raise SystemExit("sandbox bypass requires both arm sources under repository .release")
    if not selected_tasks or any(task not in PERSISTENCE_TASKS for task in selected_tasks):
        raise SystemExit("sandbox bypass is limited to the two persistence tasks")


def main() -> int:
    args = parse_args()
    if args.output_root.exists():
        raise SystemExit(f"output root already exists: {args.output_root}")
    if not CATALOG_PATH.is_file():
        raise SystemExit(f"model catalog missing: {CATALOG_PATH}")
    sources = {
        "maple": args.maple_skill.resolve(),
        "river": args.river_skill.resolve(),
    }
    if any(not path.is_dir() for path in sources.values()):
        raise SystemExit("both arm skill roots must exist")
    selected_tasks = tuple(args.task or TASKS)
    validate_bypass_scope(
        args.bypass_approvals_and_sandbox,
        args.output_root,
        sources,
        selected_tasks,
    )
    fingerprints = {arm: skill_fingerprint(path) for arm, path in sources.items()}
    args.output_root.mkdir(parents=True)
    rows = schedule(selected_tasks)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                run_call,
                row,
                sources,
                args.output_root,
                fingerprints,
                args.bypass_approvals_and_sandbox,
            ): row
            for row in rows
        }
        for future in as_completed(futures):
            row = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # Preserve zero-retry failure evidence.
                record = {
                    **row,
                    "technical_valid": False,
                    "route_complete": False,
                    "valid": False,
                    "retry_count": 0,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            results.append(record)
            print(json.dumps({key: record.get(key) for key in ("provider", "task_id", "arm", "technical_valid", "route_complete", "duration_seconds")}, ensure_ascii=False), flush=True)
    source_post = {arm: skill_fingerprint(path) for arm, path in sources.items()}
    manifest = {
        "schema_version": 1,
        "created_at_epoch": int(time.time()),
        "reasoning_effort": REASONING_EFFORT,
        "zero_retry": True,
        "sandbox_mode": "bypass-isolated" if args.bypass_approvals_and_sandbox else "workspace-write",
        "selected_tasks": list(selected_tasks),
        "providers": [provider.__dict__ for provider in PROVIDERS],
        "calls_planned": len(rows),
        "calls_completed": len(results),
        "technical_valid_calls": sum(bool(record.get("technical_valid")) for record in results),
        "route_complete_calls": sum(bool(record.get("route_complete")) for record in results),
        "valid_calls": sum(bool(record.get("valid")) for record in results),
        "source_fingerprints_before": fingerprints,
        "source_fingerprints_after": source_post,
        "source_binding_stable": fingerprints == source_post,
        "records": sorted(results, key=lambda item: (item["provider"], item["task_id"], item["arm"])),
    }
    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "calls": len(results),
                "technical_valid": manifest["technical_valid_calls"],
                "route_complete": manifest["route_complete_calls"],
                "valid": manifest["valid_calls"],
                "source_binding_stable": manifest["source_binding_stable"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0 if manifest["technical_valid_calls"] == len(rows) and manifest["source_binding_stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
