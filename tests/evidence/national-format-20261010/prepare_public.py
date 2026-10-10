"""Archive already completed runs; this does not grade manuscript quality."""
from pathlib import Path
import hashlib, json, shutil

root = Path(__file__).parent
out = root / 'public'
out.mkdir(exist_ok=True)
summaries = []
for name in ('round1', 'round2', 'round3', 'round4', 'round5-control'):
    source = root / name
    target = out / name
    target.mkdir(exist_ok=True)
    shutil.copytree(source / 'snapshots', target / 'snapshots', dirs_exist_ok=True)
    rows = json.loads((source / 'results.json').read_text(encoding='utf-8'))
    pairs = {}
    for row in rows:
        pairs.setdefault((row['model'], row['case']), []).append(row)
    summaries.append({
        'round': name, 'calls': len(rows),
        'execution_invalid': [
            {k: row[k] for k in ('model', 'case', 'arm', 'thread_ids', 'invalid')}
            for row in rows if row['invalid']],
        'valid_pairs': sum(len(pair) == 2 and all(not r['invalid'] for r in pair) for pair in pairs.values()),
        'quality_pass': None,
    })
    for path in source.iterdir():
        if not path.is_file():
            continue
        if path.name.endswith('.trace.jsonl'):
            visible = []
            for line in path.read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                item = event.get('item', {})
                if item and item.get('type') != 'agent_message':
                    event['item'] = {k: item[k] for k in ('id', 'type', 'status', 'exit_code') if k in item}
                visible.append(event)
            (target / path.name).write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in visible), encoding='utf-8')
        else:
            shutil.copyfile(path, target / path.name)
for name in ('cases.json', 'cases2.json', 'cases3.json', 'cases4.json', 'cases5.json', 'SOURCES.md',
             'make_review.py', 'archive_visible.py', 'prepare_public.py', 'verify_archive.py', 'record_review_status.py'):
    shutil.copyfile(root / name, out / name)
summary = {
    'baseline_commit': '718887ad7dd08b26fe3a49fcd7578633746b4dc6',
    'date_bjt': '2026-10-10', 'rounds': summaries,
    'calls': sum(s['calls'] for s in summaries),
    'execution_invalid': sum(len(s['execution_invalid']) for s in summaries),
    'valid_pairs': sum(s['valid_pairs'] for s in summaries),
    'quality_pass': None,
    'limits': ['Constructed excerpt tasks, not full theses', 'Inline frozen rules, not autonomous loading',
               'Native reviewers share one inherited model', 'No Word/PDF manuscript layout acceptance'],
    'trace_archive_policy': 'Visible agent messages and execution metadata; non-message tool arguments and outputs removed',
}
(out / 'RUN-SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: summary[k] for k in ('calls', 'execution_invalid', 'valid_pairs', 'quality_pass')}, ensure_ascii=False))
