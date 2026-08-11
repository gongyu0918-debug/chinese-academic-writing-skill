from __future__ import annotations

"""Build exact blinded attribution packets from frozen writer outputs and maps."""

import argparse
import tempfile
from pathlib import Path

from attribution_common import ATTRIBUTION_ROOT, JUDGES, PACKETS_ROOT, load_specs, packet_text


def build(judges: list[str]) -> int:
    if judges != list(JUDGES):
        raise RuntimeError("all three preregistered judge packets must be built atomically")
    if PACKETS_ROOT.exists():
        raise RuntimeError(f"attribution packets already exist: {PACKETS_ROOT}")
    task_ids = [row["task_id"] for row in load_specs()["tasks"]]
    staging = Path(tempfile.mkdtemp(prefix="attribution-packets.incomplete-", dir=ATTRIBUTION_ROOT))
    staged_packets = staging / "packets"
    count = 0
    for judge_id in judges:
        for task_id in task_ids:
            packet, _, _, _, _ = packet_text(judge_id, task_id)
            path = staged_packets / judge_id / f"{task_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(packet, encoding="utf-8", newline="\n")
            count += 1
    expected_files = {
        f"{judge}/{task_id}.md" for judge in JUDGES for task_id in task_ids
    }
    actual_files = {
        path.relative_to(staged_packets).as_posix()
        for path in staged_packets.rglob("*.md")
    }
    if actual_files != expected_files:
        raise RuntimeError("staged attribution packet set is incomplete")
    staged_packets.replace(PACKETS_ROOT)
    staging.rmdir()
    print(f"ATTRIBUTION_PACKETS={count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    return build(list(JUDGES))


if __name__ == "__main__":
    raise SystemExit(main())
