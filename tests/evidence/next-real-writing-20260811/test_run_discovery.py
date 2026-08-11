from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("run_discovery.py")
SPEC = importlib.util.spec_from_file_location("next_real_writing_discovery", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load run_discovery.py")
DISCOVERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DISCOVERY
SPEC.loader.exec_module(DISCOVERY)


READS = [
    "chinese-academic-writing-assistant/SKILL.md",
    "chinese-academic-writing-assistant/references/academic-writing.md",
    "chinese-academic-writing-assistant/references/anti-ai-writing.md",
]


def command_event(command: str, output: str = "content", exit_code: int = 0) -> str:
    return json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "aggregated_output": output,
                "exit_code": exit_code,
                "status": "completed" if exit_code == 0 else "failed",
            },
        }
    )


def get_content_command(path: str) -> str:
    return f"pwsh -Command \"Get-Content -Raw -LiteralPath '{path}'\""


class TraceValidationTests(unittest.TestCase):
    def write_trace(self, lines: list[str]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "trace.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_accepts_three_independent_successful_reads(self) -> None:
        trace = self.write_trace([command_event(get_content_command(path)) for path in READS])
        self.assertEqual((True, []), DISCOVERY.trace_valid(trace, READS))

    def test_accepts_safe_powershell_process_flags(self) -> None:
        lines = [
            command_event(
                f"pwsh -NoLogo -NoProfile -NonInteractive -Command \""
                f"Get-Content -Raw -LiteralPath '{path}'\""
            )
            for path in READS
        ]
        trace = self.write_trace(lines)
        self.assertEqual((True, []), DISCOVERY.trace_valid(trace, READS))

    def test_rejects_failed_path_echo(self) -> None:
        command = "Write-Output " + " ".join(READS)
        trace = self.write_trace([command_event(command, output="", exit_code=1)])
        valid, issues = DISCOVERY.trace_valid(trace, READS)
        self.assertFalse(valid)
        self.assertEqual(3, sum(item.startswith("missing_successful_independent_read:") for item in issues))

    def test_rejects_combined_multi_file_read(self) -> None:
        command = (
            "pwsh -Command \"Get-Content -Raw -LiteralPath '"
            + "','".join(READS)
            + "'\""
        )
        trace = self.write_trace([command_event(command)])
        valid, issues = DISCOVERY.trace_valid(trace, READS)
        self.assertFalse(valid)
        self.assertEqual(3, sum(item.startswith("missing_successful_independent_read:") for item in issues))

    def test_rejects_unrelated_read_followed_by_path_echo(self) -> None:
        lines = [
            command_event(
                "pwsh -Command \"Get-Content -Raw -LiteralPath 'task_specs.json'; "
                f"Write-Output '{path}'\""
            )
            for path in READS
        ]
        trace = self.write_trace(lines)
        valid, issues = DISCOVERY.trace_valid(trace, READS)
        self.assertFalse(valid)
        self.assertEqual(3, sum(item.startswith("missing_successful_independent_read:") for item in issues))

    def test_rejects_echoed_full_fake_command(self) -> None:
        lines = [
            command_event(
                "cmd /c echo -Command \"Get-Content -Raw -LiteralPath '"
                f"{path}'\""
            )
            for path in READS
        ]
        trace = self.write_trace(lines)
        valid, issues = DISCOVERY.trace_valid(trace, READS)
        self.assertFalse(valid)
        self.assertEqual(3, sum(item.startswith("missing_successful_independent_read:") for item in issues))

    def test_allows_current_root_but_rejects_sibling_worktree(self) -> None:
        base_lines = [command_event(get_content_command(path)) for path in READS]
        allowed = self.write_trace(
            base_lines
            + [command_event(f'pwsh -Command "Get-ChildItem {DISCOVERY.BASELINE_ROOT}"')]
        )
        self.assertEqual((True, []), DISCOVERY.trace_valid(allowed, READS))

        sibling = DISCOVERY.BASELINE_ROOT.parent / "unrelated-candidate"
        blocked = self.write_trace(
            base_lines + [command_event(f'pwsh -Command "Get-ChildItem {sibling}"')]
        )
        valid, issues = DISCOVERY.trace_valid(blocked, READS)
        self.assertFalse(valid)
        self.assertIn("forbidden_trace:other_worktree", issues)

    def test_rejects_web_tool_trace(self) -> None:
        lines = [command_event(get_content_command(path)) for path in READS]
        lines.append(json.dumps({"type": "item.completed", "item": {"type": "web_search"}}))
        trace = self.write_trace(lines)
        valid, issues = DISCOVERY.trace_valid(trace, READS)
        self.assertFalse(valid)
        self.assertIn("forbidden_tool_type:web_search", issues)


if __name__ == "__main__":
    unittest.main()
