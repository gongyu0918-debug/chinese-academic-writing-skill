"""Archive the attribution follow-up and verify bytes, never grade prose."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

stage = Path(__file__).resolve().parent
repo = stage.parent.parent
worktree = repo / '.release/worktrees/rule-attribution-20261102'
archive = worktree / 'tests/evidence/rule-attribution-20261102'
previous = repo / 'tests/evidence/rule-tuning-20261102'
bj = timezone(timedelta(hours=8))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def copy_frozen(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == source.read_bytes(), target
    else:
        target.write_bytes(source.read_bytes())

for name in ('R5', 'review-R5-qwen', 'review-R5-minimax'):
    source = stage / name
    assert source.is_dir()
    for path in sorted(source.rglob('*')):
        if path.is_file():
            assert path.suffix in ('.json', '.jsonl', '.txt', '.md', '.py', '.yaml'), path
            assert 'native-profile' not in path.parts
            copy_frozen(path, archive / name / path.relative_to(source))
for name in ('R5-attribution.json', 'R5-prepared.json', 'prepare_r5.py', 'review_cli.py', 'archive_r5.py'):
    copy_frozen(stage / name, archive / name)

root = archive / 'R5'
binding = json.loads((root / 'binding.json').read_text(encoding='utf-8-sig'))
rows = json.loads((root / 'results.json').read_text(encoding='utf-8-sig'))
assert len(rows) == 16
assert not any(row['invalid'] for row in rows)
sessions = {s['session_id']: s['context'] for s in json.loads((root / 'session-models.json').read_text(encoding='utf-8-sig'))}
for receipt in root.glob('*.result.json'):
    row = json.loads(receipt.read_text(encoding='utf-8-sig'))
    stem = receipt.name.removesuffix('.result.json')
    assert row['prompt_sha256'] == sha(root / (stem + '.prompt.txt'))
    assert row['draft_sha256'] == sha(root / (stem + '.final.txt'))
    assert row['returncode'] == 0 and not row['invalid']
    events = [json.loads(line) for line in (root / (stem + '.trace.jsonl')).read_text(encoding='utf-8-sig').splitlines()]
    messages = [e['item']['text'] for e in events if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'agent_message']
    assert len(messages) == 1
    assert messages[0].replace('\r\n', '\n').strip() == (root / (stem + '.final.txt')).read_text(encoding='utf-8-sig').strip()
    for thread in row['thread_ids']:
        assert sessions[thread]
        assert all(c['model'] == row['model'] and c['effort'] == row['effort'] == 'max' for c in sessions[thread])

snapshots = {arm: inventory(root / 'snapshots' / arm) for arm in ('main', 'candidate')}
assert all(len(files) == 13 for files in snapshots.values())
assert snapshots['main'].keys() == snapshots['candidate'].keys()
delta = [p for p in snapshots['main'] if snapshots['main'][p] != snapshots['candidate'][p]]
assert delta == ['references/anti-ai-writing.md']
for arm in snapshots:
    assert snapshots[arm] == inventory(previous / 'R4/snapshots' / arm)
previous_binding = json.loads((previous / 'R4/binding.json').read_text(encoding='utf-8-sig'))
for name in ('E1_fragment_r1', 'E1_fragment_r2'):
    assert binding['spec'][name] == previous_binding['spec'][name]
assert sha(root / 'runner-source.py') == binding['runner_sha256']

reviews = []
for name in ('review-R5-qwen', 'review-R5-minimax'):
    folder = archive / name
    for result in folder.glob('*.result.json'):
        receipt = json.loads(result.read_text(encoding='utf-8-sig'))
        stem = result.name.removesuffix('.result.json')
        assert receipt['returncode'] == 0 and receipt['call_completed'] and not receipt['visible_tool_items']
        assert receipt['prompt_sha256'] == sha(folder / (stem + '.prompt.txt'))
        assert receipt['draft_sha256'] == sha(folder / (stem + '.final.md'))
        events = [json.loads(line) for line in (folder / (stem + '.trace.jsonl')).read_text(encoding='utf-8-sig').splitlines()]
        ids = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
        contexts = []
        for path in (Path(receipt['session_profile']) / 'sessions').rglob('*.jsonl'):
            if not any(thread in path.name for thread in ids):
                continue
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                event = json.loads(line)
                if event.get('type') == 'turn_context':
                    payload = event['payload']
                    context = {k: payload.get(k) for k in ('model', 'model_provider', 'effort')}
                    if context not in contexts:
                        contexts.append(context)
        assert contexts and all(c['model'] == receipt['model'] and c['effort'] == 'max' for c in contexts)
        dump(folder / (stem + '.session-models.json'), {'thread_ids': ids, 'contexts': contexts})
        reviews.append({'directory': name, 'group': stem, 'model': receipt['model'], 'effort': 'max', 'execution_valid': True, 'semantic_judgment': 'See ADJUDICATION.md; completion is not correctness.'})

old_manifest = json.loads((previous / 'ARCHIVE-MANIFEST.json').read_text(encoding='utf-8-sig'))
assert all(sha(worktree / 'tests/evidence/rule-tuning-20261102' / p) == digest for p, digest in old_manifest['files'].items())
stamps = [(stage / 'R5' / p.name).stat().st_mtime for p in root.glob('*.result.json')]
integrity = {
    'writer_calls': len(rows), 'execution_invalid': 0, 'valid_pairs': 8,
    'distinct_tasks': 2, 'new_task_count': 1, 'reviews': reviews,
    'snapshot_files_per_arm': 13, 'runtime_delta': delta,
    'snapshots_equal_R4': True, 'original_E1_request_unchanged': True,
    'prompt_and_draft_hashes_verified': 16, 'model_effort_receipts_verified': 16,
    'visible_messages_match_finals': 16, 'prior_frozen_files_verified': len(old_manifest['files']),
    'first_result_time_beijing': datetime.fromtimestamp(min(stamps), bj).isoformat(),
    'last_result_time_beijing': datetime.fromtimestamp(max(stamps), bj).isoformat(),
    'semantic_pass_count': None,
    'boundary': 'Local prompt bytes and model receipts verified; provider seed, temperature, weights and received HTTP bytes remain unknown.'
}
dump(archive / 'INTEGRITY.json', integrity)
frozen = {}
for name in ('R5', 'review-R5-qwen', 'review-R5-minimax'):
    for path, digest in inventory(archive / name).items():
        frozen[name + '/' + path] = digest
for name in ('R5-attribution.json', 'R5-prepared.json', 'prepare_r5.py', 'review_cli.py', 'archive_r5.py', 'PREREGISTRATION.md'):
    frozen[name] = sha(archive / name)
dump(archive / 'ARCHIVE-MANIFEST.json', {'hash': 'sha256', 'scope': 'Frozen inputs, outputs and drivers only; adjudication and lifecycle can be updated.', 'files': frozen})
print(json.dumps({'writers': 16, 'reviews': len(reviews), 'frozen_files': len(frozen), 'integrity': 'verified'}, ensure_ascii=False))
