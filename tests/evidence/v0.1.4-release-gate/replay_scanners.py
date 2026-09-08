"""Replay archived real manuscripts through a selected set of read-only scanners."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.scripts_root.resolve()))
    import citation_audit
    import manuscript_audit
    import prose_lint

    root = args.evidence_root
    decision = json.loads((root / "decision.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    excluded = {(item["arm"], item["provider"], item["task_id"])
                for item in decision["adjudicated_delivery_failures"]}
    results = {}
    for record_path in sorted((root / "calls").glob("*/*/*/record.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        key = tuple(record[field] for field in ("arm", "provider", "task_id"))
        if not record["valid"] or key in excluded:
            continue
        source = record_path.parent / "final.md"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == manifest[source.relative_to(root).as_posix()]
        text = source.read_text(encoding="utf-8")
        label = "/".join(key)
        results[label] = {
            "source_sha256": digest,
            "citation": citation_audit.analyze(text),
            "prose": [asdict(item) for item in prose_lint.scan(label, text)],
            "manuscript": manuscript_audit.analyze([(label, text)]),
        }
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    assert len(results) == decision["actual_manuscripts"] == 83
    print(json.dumps({"manuscripts": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
