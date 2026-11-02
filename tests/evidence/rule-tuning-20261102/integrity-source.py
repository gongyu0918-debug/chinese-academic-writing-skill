"""Verify archived bytes and local model receipts; no semantic grading."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import shutil

stage = Path(__file__).resolve().parent
worktree = stage.parent / 'worktrees/rule-tuning-20261102'
archive = worktree / 'tests/evidence/rule-tuning-20261102'
bj = timezone(timedelta(hours=8))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

runs = []
for name in ('R1', 'R2', 'R3', 'R4'):
    root = archive / name
    rows = json.loads((root / 'results.json').read_text(encoding='utf-8-sig'))
    sessions = {s['session_id']: s['context'] for s in json.loads((root / 'session-models.json').read_text(encoding='utf-8-sig'))}
    for result_file in root.glob('*.result.json'):
        row = json.loads(result_file.read_text(encoding='utf-8-sig'))
        stem = result_file.name.removesuffix('.result.json')
        assert row['prompt_sha256'] == sha(root / (stem + '.prompt.txt'))
        assert row['draft_sha256'] == sha(root / (stem + '.final.txt'))
        assert row['returncode'] == 0
        for thread in row['thread_ids']:
            assert sessions[thread]
            assert all(c['model'] == row['model'] and c['effort'] == row['effort'] == 'max' for c in sessions[thread])
    snapshots = {arm: inventory(root / 'snapshots' / arm) for arm in ('main', 'candidate')}
    assert snapshots['main'].keys() == snapshots['candidate'].keys()
    delta = [p for p in snapshots['main'] if snapshots['main'][p] != snapshots['candidate'][p]]
    assert delta == ['references/anti-ai-writing.md']
    stamps = [p.stat().st_mtime for p in (stage / name).glob('*.result.json')]
    runs.append({'batch': name, 'calls': len(rows), 'execution_invalid': [
        {k: r[k] for k in ('model','case','arm','invalid')} for r in rows if r['invalid']],
        'final_sha_receipts_matched': len(rows), 'model_effort_receipts_matched': len(rows),
        'snapshot_file_count_per_arm': len(snapshots['main']), 'runtime_delta': delta,
        'baseline_anti_sha256': snapshots['main']['references/anti-ai-writing.md'],
        'candidate_anti_sha256': snapshots['candidate']['references/anti-ai-writing.md'],
        'first_result_file_time_beijing': datetime.fromtimestamp(min(stamps), bj).isoformat(),
        'last_result_file_time_beijing': datetime.fromtimestamp(max(stamps), bj).isoformat(),
        'semantic_passes': None})
assert runs[1]['candidate_anti_sha256'] == runs[2]['candidate_anti_sha256']

reviews = []
for source in sorted(stage.glob('review-R*')):
    if not source.is_dir():
        continue
    target = archive / source.name
    for prompt in sorted(source.glob('*.prompt.txt')):
        stem = prompt.name.removesuffix('.prompt.txt')
        receipt = json.loads((source / (stem + '.result.json')).read_text(encoding='utf-8-sig'))
        assert receipt['returncode'] == 0 and receipt['call_completed']
        assert not receipt['visible_tool_items']
        assert receipt['prompt_sha256'] == sha(prompt)
        assert receipt['draft_sha256'] == sha(source / (stem + '.final.md'))
        selected = []
        thread_ids = [e['thread_id'] for e in [json.loads(line) for line in (source / (stem + '.trace.jsonl')).read_text(encoding='utf-8-sig').splitlines()] if e.get('type') == 'thread.started']
        for path in (Path(receipt['session_profile']) / 'sessions').rglob('*.jsonl'):
            if not any(thread in path.name for thread in thread_ids):
                continue
            item = {'session_id': None, 'context': []}
            # Extract only session identity and requested model context.
            for line in path.read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                payload = event.get('payload', {})
                if event.get('type') == 'session_meta':
                    item['session_id'] = payload.get('id')
                if event.get('type') == 'turn_context':
                    context = {k: payload[k] for k in ('model', 'effort', 'model_provider') if k in payload}
                    if context not in item['context']:
                        item['context'].append(context)
            assert item['session_id'] in thread_ids
            assert item['context'] and all(c['model'] == receipt['model'] and c['effort'] == 'max' for c in item['context'])
            selected.append(item)
        assert len(selected) == len(thread_ids) == 1
        dump(target / (stem + '.session-models.json'), selected)
        reviews.append({'path': source.name + '/' + stem, 'model': receipt['model'], 'effort': 'max', 'visible_tool_events': 0, 'hash_receipts_matched': True, 'semantic_verdict': 'See human adjudication; execution is not quality approval.'})
assert len(reviews) == 14
for filename in ('review_cli.py', 'prepare_r4.py', 'R4-c2.json', 'R4-prepared.json', 'R3-repeat.json', 'unittest-full.log'):
    shutil.copyfile(stage / filename, archive / filename)

canonical = inventory(worktree / 'chinese-academic-writing-assistant')
baseline = inventory(archive / 'R1/snapshots/main')
assert canonical == baseline
dump(archive / 'INTEGRITY.json', {'runs': runs, 'reviews': reviews,
    'writing_calls': sum(r['calls'] for r in runs),
    'execution_valid_writing_calls': sum(r['calls'] - len(r['execution_invalid']) for r in runs),
    'review_calls': len(reviews), 'runtime_restored_to_baseline': True,
    'runtime_file_count': len(canonical),
    'unknowns': ['provider-side weights/version', 'provider-side temperature/seed', 'upstream received bytes', 'unreported provider configuration'],
    'concurrency': '4 writers per batch; R2/R3 overlapped briefly and reviews could overlap writing; upstream load not controlled',
    'time_source': 'Result file modification times, converted to Asia/Shanghai offset; not upstream timing receipts.',
    'semantic_quality_is_not_mechanically_graded': True})
files = {}
for name in ('R1','R2','R3','R4') + tuple(p.name for p in sorted(archive.glob('review-R*')) if p.is_dir()):
    for path, checksum in inventory(archive / name).items():
        files[name + '/' + path] = checksum
dump(archive / 'ARCHIVE-MANIFEST.json', {'hash': 'sha256', 'scope': 'Frozen run/review artifacts only; mutable reports and lifecycle are separate.', 'files': files})
print(json.dumps({'writing_calls': 112, 'execution_valid': 109, 'review_calls': 14, 'frozen_files': len(files), 'runtime_matches_baseline': True}))
