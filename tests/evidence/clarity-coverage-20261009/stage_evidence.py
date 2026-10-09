"""Archive actual visible research evidence; never grade prose."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
LOCAL = Path(__file__).parent
OUT = LOCAL/'export'
OUT.mkdir(exist_ok=True)
BATCHES = ['baseline-R1','long-baseline','baseline-R1-retry','long-baseline-retry',
           'candidate-R1','confirmation-R2','long-cost-R2','minimal-R3','long-only-R4']
REVIEWS = ['review-audit','review-R1','review-audit-retry','review-R1-retry',
           'review-R2','review-long','review-R3','review-R4']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)

def norm(path):
    return path.read_text(encoding='utf-8-sig').replace('\r\n','\n')

def session_models(profile):
    rows=[]
    for p in (profile/'sessions').rglob('*.jsonl'):
        row={'filename':p.name,'context':[]}
        for line in p.read_text(encoding='utf-8').splitlines():
            try:e=json.loads(line)
            except json.JSONDecodeError:continue
            pl=e.get('payload',{})
            if e.get('type')=='session_meta':row['session_id']=pl.get('id')
            if e.get('type')=='turn_context':
                ctx={k:pl.get(k) for k in ('model','model_provider','effort') if k in pl}
                if ctx not in row['context']:row['context'].append(ctx)
        rows.append(row)
    return rows

writer_stats=[]
for batch in BATCHES:
    src=LOCAL/batch
    if not (src/'results.json').exists():continue
    dst=OUT/batch
    for name in ('binding.json','runner-source.py','results.json','selected-catalog.json','session-models.json'):
        if (src/name).exists():copy(src/name,dst/name)
    binding=json.loads((src/'binding.json').read_text(encoding='utf-8'))
    results=json.loads((src/'results.json').read_text(encoding='utf-8'))
    complete=0
    for row in results:
        mi=binding['models'].index(row['model'])
        stem=f"m{mi}-{row['case']}-{row['arm']}-s{row['stage']}"
        prompt=src/(stem+'.prompt.txt')
        final=src/(stem+'.final.txt')
        assert sha(prompt.read_bytes())==row['prompt_sha256'],stem
        assert sha(final.read_bytes() if final.exists() else b'')==row['draft_sha256'],stem
        if not row['invalid']:complete+=1
        for suffix in ('.prompt.txt','.final.txt','.result.json','.trace.jsonl'):
            if (src/(stem+suffix)).exists():copy(src/(stem+suffix),dst/(stem+suffix))
    changed=[]
    for arm in ('main','candidate'):
        snapshot=src/'snapshots'/arm
        if not snapshot.exists():continue
        for p in snapshot.rglob('*.md'):
            copy(p,dst/'snapshots'/arm/p.relative_to(snapshot))
    base=src/'snapshots/main'
    cand=src/'snapshots/candidate'
    if cand.exists():
        diff=''
        for p in base.rglob('*.md'):
            relative=p.relative_to(base)
            other=cand/relative
            if other.exists() and norm(p)!=norm(other):
                changed.append(relative.as_posix())
                diff+=''.join(difflib.unified_diff(norm(p).splitlines(True),norm(other).splitlines(True),fromfile='main/'+relative.as_posix(),tofile='candidate/'+relative.as_posix()))
        (dst/'candidate.diff').write_bytes(diff.encode())
    writer_stats.append({'batch':batch,'calls':len(results),'visible_completed_without_route_violation':complete,
        'invalid':len(results)-complete,'changed_rule_files':changed,'quality_pass':None})

review_stats=[]
for name in REVIEWS:
    src=LOCAL/name
    if not src.exists():continue
    dst=OUT/name
    for p in src.iterdir():
        if p.is_file() and p.suffix in ('.md','.txt','.json','.jsonl'):
            copy(p,dst/p.name)
    results=[]
    for p in src.glob('*.result.json'):
        r=json.loads(p.read_text(encoding='utf-8'))
        stem=p.name.removesuffix('.result.json')
        prompt=src/(stem+'.prompt.txt')
        final=src/(stem+'.final.md')
        assert sha(prompt.read_bytes())==r['prompt_sha256'],p
        assert (sha(final.read_bytes()) if final.exists() else None)==r['draft_sha256'],p
        results.append({'packet':stem,'model':r['model'],'effort':r['effort'],
            'returncode':r['returncode'],'completed':r['review_completed'] and bool(final.read_bytes().strip()),
            'tool_items':len(r['visible_tool_items'])})
    if results:
        sample=json.loads(next(src.glob('*.result.json')).read_text(encoding='utf-8'))
        dump(dst/'session-models.json',session_models(Path(sample['session_profile'])))
    review_stats.append({'batch':name,'packets':results})

for name in ('README.md','CORPUS.md','AUDIT.md','ADJUDICATION.md','agent.md','AUDIT-SCOPE.md',
             'baseline-tasks.json','confirmation-tasks.json','long-tasks.json','long-cost-compact.json',
             'minimal-tasks.json','long-only-tasks.json','coverage_runner.py','review_cli.py',
             'prepare_candidate.py','prepare_minimal.py','stage_evidence.py',
             'SKILL.candidate.diff','long-form-consistency.candidate.diff'):
    copy(LOCAL/name,OUT/name)
copy(LOCAL/'sources-proposals/download-receipts.json',OUT/'source-download-receipts.json')

coverage=[]
sources=[('G1','sources-proposals/zju-proposal.doc','full proposal','converted PDF1-18; visual PDF15-18'),
         ('G1-final','sources-proposals/zju-final-thesis.docx','identity only','cover and submission date; not thesis full reading'),
         ('G2','sources-proposals/fze-proposal.pdf','full proposal','PDF1-12; visual PDF7; school unconfirmed'),
         ('G2-variant','sources-proposals/fze-degree-proposal.docx','partial variant','instructions, body start; visual converted PDF1-2; not separate proposal'),
         ('H2','ntu-humanities.pdf','partial master thesis','PDF1,5-41,156-162,223-227 (50 of 236 pages); visual PDF225')]
for sid,relative,reading,range_ in sources:
    p=LOCAL/relative
    coverage.append({'id':sid,'local_ignored_file':relative,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,
                     'actual_reading':reading,'covered':range_})
dump(OUT/'source-coverage.json',{'sources':coverage,'not_covered':['doctoral thesis','filled humanities proposal','all external citations'],
    'source_files_exported':False,'alias_in_writing_packet':{'N_humanities_edit/H1':'H2 in CORPUS.md'}})
dump(OUT/'RUN-SUMMARY.json',{'writer_batches':writer_stats,
    'writer_calls':sum(x['calls'] for x in writer_stats),
    'visible_completed_without_route_violation':sum(x['visible_completed_without_route_violation'] for x in writer_stats),
    'invalid':sum(x['invalid'] for x in writer_stats),
    'quality_pass_count':None,'review_batches':review_stats,'subagents_completed':0,
    'checks':['prompt and final bytes match each result SHA256','visible-only trace archive','rule diffs per batch'],
    'not_checks':['semantic Python grading','full unittest','skill structure validity as quality evidence']})
manifest=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
          for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='ARCHIVE-MANIFEST.json']
dump(OUT/'ARCHIVE-MANIFEST.json',manifest)
print(json.dumps({'writer_calls':sum(x['calls'] for x in writer_stats),'visible_completed':sum(x['visible_completed_without_route_violation'] for x in writer_stats),
                  'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest)},ensure_ascii=False))
