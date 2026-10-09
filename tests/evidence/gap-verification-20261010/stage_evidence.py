"""Freeze actual visible evidence and verify byte receipts, without semantic grading."""
from pathlib import Path
import argparse,difflib,hashlib,json,shutil
HERE=Path(__file__).parent
OUT=HERE/'export'
BATCHES=['source-scope-R1','source-scope-R2','source-scope-R3']
REVIEWS=['review-R1','review-R2','review-R1-complete','review-R1-fixed','review-R3']
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def copy(p,q):
    q.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,q)
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
def manifest(out):
    return [{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='ARCHIVE-MANIFEST.json']
def verify(out):
    rows=read(out/'ARCHIVE-MANIFEST.json')
    assert rows==manifest(out),'archive manifest mismatch'
    count=0
    for batch in BATCHES:
        binding=read(out/batch/'binding.json')
        for r in read(out/batch/'results.json'):
            mi=binding['models'].index(r['model'])
            stem=f"m{mi}-{r['case']}-{r['arm']}-s{r['stage']}"
            assert sha((out/batch/(stem+'.prompt.txt')).read_bytes())==r['prompt_sha256']
            assert sha((out/batch/(stem+'.final.txt')).read_bytes())==r['draft_sha256']
            count+=1
    assert count==60,count
    for r in read(out/'input-diagnostic/results.json'):
        stem=r['case']+'-repeat'+str(r['repeat'])
        assert sha((out/'input-diagnostic'/(stem+'.prompt.txt')).read_bytes())==r['prompt_sha256']
        assert sha((out/'input-diagnostic'/(stem+'.final.txt')).read_bytes())==r['draft_sha256']
    for batch in REVIEWS:
        for p in (out/batch).glob('*.result.json'):
            r=read(p);stem=p.name.removesuffix('.result.json')
            assert sha((out/batch/(stem+'.prompt.txt')).read_bytes())==r['prompt_sha256']
            final=out/batch/(stem+'.final.md')
            assert (sha(final.read_bytes()) if final.exists() else None)==r['draft_sha256']
    print(json.dumps({'manifest_files':len(rows),'paired_writer_calls_bound':count,'diagnostic_calls_bound':4,'bytes':sum(x['bytes'] for x in rows),'semantic_quality_result':None},ensure_ascii=False))
parser=argparse.ArgumentParser()
parser.add_argument('--verify-only',type=Path)
args=parser.parse_args()
if args.verify_only:
    verify(args.verify_only)
    raise SystemExit(0)
OUT.mkdir(exist_ok=False)
writer_stats=[]
for batch in BATCHES:
    src=HERE/batch;dst=OUT/batch
    for name in ['binding.json','runner-source.py','results.json','selected-catalog.json','session-models.json']:
        copy(src/name,dst/name)
    binding=read(src/'binding.json');results=read(src/'results.json')
    for row in results:
        mi=binding['models'].index(row['model'])
        stem=f"m{mi}-{row['case']}-{row['arm']}-s{row['stage']}"
        for suffix in ['.prompt.txt','.final.txt','.result.json','.trace.jsonl']:
            p=src/(stem+suffix)
            if p.exists():copy(p,dst/p.name)
    for arm in ['main','candidate']:
        for p in (src/'snapshots'/arm).rglob('*.md'):
            copy(p,dst/'snapshots'/arm/p.relative_to(src/'snapshots'/arm))
    diff='';changed=[]
    for p in (src/'snapshots/main').rglob('*.md'):
        rel=p.relative_to(src/'snapshots/main')
        q=src/'snapshots/candidate'/rel
        a=p.read_text(encoding='utf-8-sig').replace('\r\n','\n')
        b=q.read_text(encoding='utf-8-sig').replace('\r\n','\n')
        if a!=b:
            changed.append(rel.as_posix())
            diff+=''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='main/'+rel.as_posix(),tofile='candidate/'+rel.as_posix()))
    assert changed==['SKILL.md'],changed
    (dst/'rules.diff').write_bytes(diff.encode())
    writer_stats.append({'batch':batch,'calls':len(results),'execution_invalid':sum(bool(r['invalid']) for r in results),'changed_markdown':changed,'quality_pass_count':None})
for p in (HERE/'input-diagnostic').iterdir():
    if p.is_file():copy(p,OUT/'input-diagnostic'/p.name)
review_stats=[]
for batch in REVIEWS:
    src=HERE/batch;dst=OUT/batch
    for p in src.iterdir():
        if p.is_file():copy(p,dst/p.name)
    packets=[]
    for p in sorted(src.glob('*.result.json')):
        r=read(p);stem=p.name.removesuffix('.result.json')
        disposition='complete input; semantic report present, manual corrections in ADJUDICATION'
        semantic=True;inputs=True
        if batch=='review-R1' and stem in ['group2','group3']:
            inputs=False
            disposition='partial input: E/GLM main for group2, G/GLM main for group3 was a pending placeholder; affected comparison excluded, rerun in review-R1-fixed'
        if batch=='review-R1-complete':
            semantic=False
            disposition='acknowledgment only; no semantic report, not completed review'
        packets.append({'packet':stem,'model':r['model'],'effort':r['effort'],'returncode':r['returncode'],'call_completed':r['returncode']==0,'semantic_report_present':semantic,'input_complete':inputs,'disposition':disposition,'quality_pass':None})
    sample=read(next(src.glob('*.result.json')))
    dump(dst/'session-models.json',session_models(Path(sample['session_profile'])))
    review_stats.append({'batch':batch,'packets':packets})
for p in HERE.iterdir():
    if p.is_file() and p.suffix in ['.md','.json','.py']:
        copy(p,OUT/p.name)
for name in ['disk-initial','disk-stage1','disk-stage2']:
    for p in (HERE/name).rglob('*'):
        if p.is_file():copy(p,OUT/name/p.relative_to(HERE/name))
for p in (HERE/'disk-project').rglob('*'):
    if p.is_file() and 'rules' not in p.relative_to(HERE/'disk-project').parts:
        copy(p,OUT/'disk-project'/p.relative_to(HERE/'disk-project'))
pdf=Path('F:/Workspaces/chinese-academic-writing-skill/.release/clarity-coverage-20261009/ntu-humanities.pdf')
dump(OUT/'source-coverage.json',{'source_id':'H2','url':'https://tdr.lib.ntu.edu.tw/bitstream/123456789/3784/1/ntu-105-1.pdf','local_only_original':str(pdf),'pdf_sha256':sha(pdf.read_bytes()),'new_pdf_pages':list(range(42,53)),'new_printed_pages':list(range(33,44)),'new_read_pages':11,'prior_read_pages':50,'cumulative_read_pages':61,'total_pdf_pages':236,'visual_check_pdf_pages':[46,50],'full_read':False,'filled_humanities_proposal_added':0,'source_files_exported':False,'controlled_tasks_are_new_real_projects':False})
dump(OUT/'RUN-SUMMARY.json',{'date_beijing':'2026-10-10','baseline_commit':'eb598fe5c92109171bee6ea0015241ebc8eeb587','candidate_admission':'cancelled; no product rule change','writer_batches':writer_stats,'paired_writer_calls':60,'paired_comparisons':30,'fresh_task_pairs':24,'exact_replay_pairs':6,'task_only_diagnostic_calls':4,'total_native_cli_writer_calls':64,'writer_execution_invalid':0,'writer_quality_pass_count':None,'review_batches':review_stats,'cli_review_calls':11,'semantic_review_reports':10,'semantic_reports_with_complete_input':8,'partial_input_reports':2,'acknowledgment_only_calls':1,'native_subagents_completed':5,'native_actual_models':read(HERE/'native-session-models.json'),'production_files_changed':[],'checks':['prompt/final/result SHA256 binding','visible-only trace archive','disk snapshots unchanged by read-only audit','pending-batch early exit'],'not_checks':['semantic Python grading','full unittest','Skill structural validity as quality evidence','whole thesis','autonomous Hook','desktop WorkBuddy','market installation']})
dump(OUT/'ARCHIVE-MANIFEST.json',manifest(OUT))
verify(OUT)
