"""Archive visible research evidence only; integrity checks do not score writing."""
from pathlib import Path
import hashlib
import difflib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
WT = Path('C:/Users/admin/.codex/worktrees/academic-competitors-1010/chinese-academic-writing-skill').resolve()
EXPECTED = Path('C:/Users/admin/.codex/worktrees').resolve()
if EXPECTED not in WT.parents or WT.name != 'chinese-academic-writing-skill':
    raise RuntimeError('Unexpected managed worktree target')
if subprocess.check_output(['git','branch','--show-current'],cwd=WT,text=True).strip() != 'codex/academic-competitors-1010':
    raise RuntimeError('Wrong worktree branch')
DEST = WT/'tests/evidence/competitor-expansion-20261010'
if DEST.exists():
    raise RuntimeError('Evidence target exists; inspect rather than overwrite')

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

models = ['alibaba-token-plan-responses/qwen3.8-flash','ollama-cloud/glm-5.3-flash']
metadata = read_json(HERE/'native-session-models.json')
if len(metadata)!=6 or any(not r['metadata_found'] or not r['visible_final_messages'] for r in metadata):
    raise RuntimeError('Native agent final reports or actual metadata incomplete')
source_ledger = read_json(HERE/'SOURCE-LEDGER.json')
if source_ledger['pinned_rule_files']!=19 or len(source_ledger['sources'])!=19:
    raise RuntimeError('Wrong source ledger coverage')
rows=[]
candidate_diffs=['# Four independent candidate deltas (not admitted to product)\n']
for group in ['review','reports','statistics','secondary']:
    batch=HERE/(group+'-R1')
    result=read_json(batch/'results.json')
    if len(result)!=8:
        raise RuntimeError('Wrong call coverage: '+group)
    main=batch/'snapshots/main'
    candidate=batch/'snapshots/candidate'
    changed=[]
    for old in main.rglob('*.md'):
        rel=old.relative_to(main)
        new=candidate/rel
        if not new.is_file():
            raise RuntimeError('Missing candidate input: '+str(rel))
        before=old.read_text(encoding='utf-8-sig').splitlines()
        after=new.read_text(encoding='utf-8-sig').splitlines()
        if before!=after:
            changed.append(rel.as_posix())
            candidate_diffs.append('\n## '+group+' / '+rel.as_posix()+'\n\n```diff\n'+
                                   '\n'.join(difflib.unified_diff(before,after,fromfile='main/'+rel.as_posix(),
                                                                 tofile='candidate/'+rel.as_posix(),lineterm=''))+'\n```\n')
    expected='references/academic-writing.md' if group in ['review','statistics'] else 'references/academic-literature-review.md'
    if changed!=[expected]:
        raise RuntimeError('Unexpected candidate scope: '+group+' '+str(changed))
    native={r['session_id']:r['context'] for r in read_json(batch/'session-models.json')}
    for row in result:
        mi=models.index(row['model'])
        stem=f"m{mi}-{row['case']}-{row['arm']}-s{row['stage']}"
        if digest(batch/(stem+'.prompt.txt'))!=row['prompt_sha256'] or digest(batch/(stem+'.final.txt'))!=row['draft_sha256']:
            raise RuntimeError('Input/output binding mismatch: '+stem)
        if row['quality_pass'] is not None:
            raise RuntimeError('Automatic semantic verdict unexpectedly present')
        for session_id in row['thread_ids']:
            if not any(c.get('model')==row['model'] and c.get('effort')=='max' for c in native.get(session_id,[])):
                raise RuntimeError('Actual model context mismatch: '+stem)
        rows.append({'group':group,'stem':stem,'invalid':row['invalid']})
if len(rows)!=32 or sum(bool(r['invalid']) for r in rows)!=1:
    raise RuntimeError('Unexpected execution coverage')

DEST.mkdir(parents=True)
def copy(path):
    target=DEST/path.relative_to(HERE)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target)

for path in HERE.iterdir():
    if path.is_file() and (path.suffix in ('.md','.json','.py') or path.name.endswith('-rule.txt')):
        copy(path)
for subdir in ['agents','review-packets','candidates']:
    for path in (HERE/subdir).rglob('*'):
        if path.is_file() and path.suffix in ('.md','.json'):
            copy(path)
for group in ['review','reports','statistics','secondary']:
    batch=HERE/(group+'-R1')
    for path in batch.iterdir():
        if path.is_file() and path.name!='selected-catalog.json':
            copy(path)
    catalog=read_json(batch/'selected-catalog.json')
    keys=['slug','display_name','description','default_reasoning_level','supported_reasoning_levels',
          'shell_type','supports_reasoning_summaries','context_window','max_context_window','input_modalities']
    public={'raw_source_sha256':digest(batch/'selected-catalog.json'),
            'scope':'Routing/model fields only; full instruction templates not republished',
            'models':[{k:m[k] for k in keys if k in m} for m in catalog]}
    (DEST/(group+'-R1')/'selected-catalog-metadata.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for path in (batch/'snapshots').rglob('*.md'):
        copy(path)
(DEST/'CANDIDATE-DIFFS.md').write_text('\n'.join(candidate_diffs),encoding='utf-8')

manifest={'date_beijing':'2026-10-10','baseline':'c60c589908d1e83dba2bc4beb800b816e391f732',
          'calls':32,'execution_valid':31,'execution_invalid':1,'complete_valid_pairs':15,
          'semantic_pass_count':None,'meaning':'Counts and hashes verify archive integrity only',
          'file_hashes':{p.relative_to(DEST).as_posix():digest(p) for p in sorted(DEST.rglob('*')) if p.is_file()}}
(DEST/'ARCHIVE-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(manifest['file_hashes'])+1,'calls':32,'execution_valid':31,'execution_invalid':1,
                  'semantic_pass_count':None,'destination':str(DEST)},ensure_ascii=False))
