"""Verify evidence hashes and runtime parity, never manuscript semantics."""
from pathlib import Path
import hashlib, json

root = Path(__file__).parent
out = root / 'public'
worktree = Path('C:/Users/admin/.codex/worktrees/national-format-priority/chinese-academic-writing-skill')
skill = worktree / 'chinese-academic-writing-assistant'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
checks = []
for folder in sorted(out.glob('round*')):
    if not folder.is_dir():
        continue
    rows = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    for row in rows:
        index = 0 if row['model'].startswith('alibaba') else 1
        stem = f"m{index}-{row['case']}-{row['arm']}-s{row['stage']}"
        checks.append({'round': folder.name, 'stem': stem,
                       'prompt_hash_match': sha(folder / (stem + '.prompt.txt')) == row['prompt_sha256'],
                       'draft_hash_match': sha(folder / (stem + '.final.txt')) == row['draft_sha256']})
parity = [{'path': p.relative_to(skill).as_posix(),
           'frozen_hash': sha(out / 'round5-control/snapshots/candidate' / p.relative_to(skill)),
           'worktree_hash': sha(p)} for p in sorted(skill.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
result = {'checks': checks, 'runtime_parity': parity,
          'evidence_hashes_match': all(c['prompt_hash_match'] and c['draft_hash_match'] for c in checks),
          'runtime_matches_last_control': all(c['frozen_hash'] == c['worktree_hash'] for c in parity),
          'does_not_prove': ['Manuscript quality', 'Standards conformity', 'Autonomous rule loading', 'Marketplace publication']}
if not result['evidence_hashes_match'] or not result['runtime_matches_last_control']:
    raise SystemExit('evidence/parity mismatch')
(out / 'INTEGRITY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'bound_outputs': len(checks), 'runtime_files': len(parity),
                 'evidence_hashes_match': result['evidence_hashes_match'],
                 'runtime_matches_last_control': result['runtime_matches_last_control']}))
manifest = [{'path': p.relative_to(out).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ('MANIFEST.json', 'LIFECYCLE.json')]
(out / 'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
