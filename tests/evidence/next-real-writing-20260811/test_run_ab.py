from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_ab


def completed_command(path: str, output: str = "content") -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": f'pwsh -Command "Get-Content -Raw -LiteralPath \'{path}\'"',
            "aggregated_output": output,
            "exit_code": 0,
            "status": "completed",
        },
    }


def paired_command_events(commands: list[dict[str, object]]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for index, completed in enumerate(commands):
        completed_copy = json.loads(json.dumps(completed))
        completed_copy["item"]["id"] = f"command-{index}"
        started_item = {
            "id": f"command-{index}",
            "type": "command_execution",
            "command": completed_copy["item"]["command"],
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        }
        events.append({"type": "item.started", "item": started_item})
        events.append(completed_copy)
    return events


def write_trace(path: Path, commands: list[dict[str, object]], final: str = "成稿") -> None:
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": "t"},
        {"type": "turn.started"},
    ]
    events.extend(paired_command_events(commands))
    events.append({"type": "item.completed", "item": {"type": "agent_message", "text": final}})
    events.append({"type": "turn.completed"})
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )


class RunABTests(unittest.TestCase):
    def test_specs_cover_four_tasks_three_providers_and_two_arms(self) -> None:
        payload = run_ab.load_specs()
        self.assertEqual(12, len(payload["tasks"]))
        self.assertEqual({"H1", "H2", "H3", "H4"}, {row["source_task"] for row in payload["tasks"]})
        self.assertEqual({"alibaba", "ollama", "minimax"}, {row["provider"] for row in payload["tasks"]})
        self.assertEqual(("baseline", "candidate"), run_ab.ARMS)

    def test_trace_accepts_exact_independent_reads_and_one_final(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"content:{required}\n", encoding="utf-8")
            trace = Path(folder) / "trace.jsonl"
            write_trace(trace, [completed_command(path, f"content:{path}\n") for path in run_ab.REQUIRED_READS])
            self.assertEqual([], run_ab.trace_issues(trace, root, "成稿"))

    def test_trace_accepts_one_pre_read_preamble_but_only_one_post_read_final(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"type": "agent_message", "text": "先读取材料。"}},
                *paired_command_events(commands),
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                {"type": "turn.completed"},
            ]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertEqual([], run_ab.trace_issues(trace, root, "成稿"))
            self.assertEqual(1, run_ab.pre_read_preamble_count(trace))

    def test_trace_accepts_one_progress_message_before_all_reads_complete(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            paired = paired_command_events(commands)
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                *paired[:2],
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "继续读取其余两份材料。"},
                },
                *paired[2:],
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                {"type": "turn.completed"},
            ]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertEqual([], run_ab.trace_issues(trace, root, "成稿"))

    def test_trace_rejects_duplicate_final_disguised_as_progress(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            paired = paired_command_events(commands)
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                *paired[:2],
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                *paired[2:],
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                {"type": "turn.completed"},
            ]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertIn("premature_final_message", run_ab.trace_issues(trace, root, "成稿"))

    def test_trace_rejects_progress_message_after_all_reads_complete(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                *paired_command_events(commands),
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "三份材料已经读取完成。"},
                },
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                {"type": "turn.completed"},
            ]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertIn("intermediate_agent_message", run_ab.trace_issues(trace, root, "成稿"))

    def test_trace_rejects_any_non_read_tool_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            trace = Path(folder) / "trace.jsonl"
            events = [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                *paired_command_events(commands),
                {
                    "type": "item.completed",
                    "item": {"type": "file_change", "status": "failed", "changes": []},
                },
                {"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}},
                {"type": "turn.completed"},
            ]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertIn("forbidden_tool_type:file_change", run_ab.trace_issues(trace, root, "成稿"))

    def test_trace_rejects_composite_or_echoed_read(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
            trace = Path(folder) / "trace.jsonl"
            commands = [completed_command(path) for path in run_ab.REQUIRED_READS]
            commands[0]["item"]["command"] += "; Write-Output fake"  # type: ignore[index]
            write_trace(trace, commands)
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertTrue(any(issue.startswith("missing_successful_independent_read") for issue in issues))

    def test_trace_rejects_other_worktree_and_second_final(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
            trace = Path(folder) / "trace.jsonl"
            commands = [completed_command(path) for path in run_ab.REQUIRED_READS]
            commands.append(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": f'pwsh -Command "Get-ChildItem -LiteralPath \'{root.parent / "baseline"}\'"',
                        "aggregated_output": "x",
                        "exit_code": 0,
                        "status": "completed",
                    },
                }
            )
            write_trace(trace, commands)
            with trace.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "成稿"}}, ensure_ascii=False) + "\n")
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertIn("forbidden_trace:other_worktree", issues)
            self.assertIn("intermediate_agent_message", issues)

    def test_trace_rejects_tampered_reads_extra_success_and_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"expected:{required}", encoding="utf-8")
            trace = Path(folder) / "trace.jsonl"
            commands = [completed_command(path, "tampered-content") for path in run_ab.REQUIRED_READS]
            commands.append(completed_command(r"..\baseline\chinese-academic-writing-assistant\SKILL.md", "stolen"))
            write_trace(trace, commands)
            with trace.open("a", encoding="utf-8") as handle:
                handle.write("{malformed\n")
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertIn("malformed_trace_json", issues)
            self.assertIn("unexpected_command", issues)
            self.assertIn("unexpected_command_event_count:4:4", issues)
            self.assertEqual(3, sum(issue.startswith("read_content_mismatch:") for issue in issues))

    def test_trace_rejects_failed_extra_read_even_when_it_returns_content(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
            commands = [completed_command(path) for path in run_ab.REQUIRED_READS]
            extra = completed_command(r"..\baseline\chinese-academic-writing-assistant\SKILL.md", "stolen")
            extra["item"]["exit_code"] = 1  # type: ignore[index]
            trace = Path(folder) / "trace.jsonl"
            write_trace(trace, commands + [extra])
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertIn("unexpected_command", issues)
            self.assertIn("unexpected_command_event_count:4:4", issues)

    def test_trace_rejects_invalid_lifecycle_and_unclosed_extra_command(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "worktrees" / "candidate"
            root.mkdir(parents=True)
            commands = []
            for required in run_ab.REQUIRED_READS:
                target = root / required
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("content", encoding="utf-8")
                commands.append(completed_command(required))
            trace = Path(folder) / "trace.jsonl"
            write_trace(trace, commands)
            events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
            turn_completed = events.pop()
            events.insert(-1, turn_completed)
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertIn("turn_completed_not_last", issues)
            self.assertIn("final_message_not_before_turn_completed", issues)

            write_trace(trace, commands)
            events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
            events[0], events[1] = events[1], events[0]
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            self.assertIn("thread_started_not_first", run_ab.trace_issues(trace, root, "成稿"))

            write_trace(trace, commands)
            events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
            events.insert(
                -2,
                {
                    "type": "item.started",
                    "item": {
                        "id": "unclosed-extra",
                        "type": "command_execution",
                        "command": "pwsh -Command \"Get-Content -Raw -LiteralPath '..\\other\\SKILL.md'\"",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                },
            )
            trace.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )
            issues = run_ab.trace_issues(trace, root, "成稿")
            self.assertIn("unexpected_command_event_count:4:3", issues)
            self.assertIn("command_event_pairing_mismatch", issues)
            self.assertIn("unexpected_command", issues)


if __name__ == "__main__":
    unittest.main()
