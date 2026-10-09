"""Collect execution, input and disk byte receipts; never grade prose."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).parent
ROOT=Path('F:/Workspaces/chinese-academic-writing-skill')
SESSIONS=Path('C:/Users/admin/.codex/sessions/2026/10/10')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def events(p):
    for line in p.read_text(encoding='utf-8').splitlines():
        try:yield json.loads(line)
        except json.JSONDecodeError:pass
def model_row(p):
    row={'filename':p.name,'context':[]}
    for e in events(p):
        pl=e.get('payload',{})
        if e.get('type')=='session_meta':row['session_id']=pl.get('id')
        if e.get('type')=='turn_context':
            ctx={k:pl.get(k) for k in ('model','model_provider','effort') if k in pl}
            if ctx not in row['context']:row['context'].append(ctx)
    return row
native=[]
for name,sid in [('rule-audit','01a1218d-11cf-7cb0-a094-823b370faec8'),('prior-evidence-audit','01a1218d-1337-7730-b825-7c3a300b106b'),('disk-stage1','01a12190-8960-75d2-8193-c13beeef70a4'),('disk-stage2','01a12198-f877-7f42-a09a-ed8fca99645b'),('disk-audit','01a1219e-f550-71e0-854c-05b4281d9976')]:
    paths=list(SESSIONS.glob('*'+sid+'.jsonl'))
    assert len(paths)==1,(name,len(paths))
    native.append({'task':name,**model_row(paths[0]),'model_override':False,'final_report_received':True})
dump(HERE/'native-session-models.json',native)
proof=[]
cases=[('source-scope-R1','A_raw_interviews','main',['R11','R12','R13']),('source-scope-R1','C_raw_conflict','candidate',['T1','A、B、C、D','本研究已收集5份记录']),('source-scope-R2','L_existing_target','main',['4.1 名称','4.2 口径','目标正文全文']),('source-scope-R2','L_existing_target','candidate',['4.1 名称','4.2 口径','目标正文全文']),('source-scope-R3','C_raw_conflict','main',['T1','A、B、C、D','本研究已收集5份记录']),('source-scope-R3','L_existing_target','candidate',['4.1 名称','4.2 口径','目标正文全文'])]
for batch,case,arm,anchors in cases:
    b=json.loads((HERE/batch/'binding.json').read_text(encoding='utf-8'))
    stem=f'm0-{case}-{arm}-s1'
    r=json.loads((HERE/batch/(stem+'.result.json')).read_text(encoding='utf-8'))
    profile=Path(b['runtime'])/'native-profile'
    sid=r['thread_ids'][0]
    paths=list((profile/'sessions').rglob('*'+sid+'.jsonl'))
    assert len(paths)==1,(stem,len(paths))
    users=[]
    for e in events(paths[0]):
        pl=e.get('payload',{})
        if e.get('type')=='response_item' and pl.get('type')=='message' and pl.get('role')=='user':
            users.append('\n'.join(x.get('text','') for x in pl.get('content',[]) if isinstance(x,dict)))
    text='\n'.join(users)
    proof.append({'batch':batch,'stem':stem,'session_id':sid,'native_user_content_sha256':sha(text.encode()),'anchors':{a:a in text for a in anchors},'prompt_sha256':r['prompt_sha256'],'claim':'CLI session contains these supplied-text anchors; upstream request body was not captured.'})
    assert all(a in text for a in anchors),stem
dump(HERE/'input-receipts.json',proof)
plan=json.loads((HERE/'input-diagnostic/plan.json').read_text(encoding='utf-8'))
profile=Path(plan['runtime'])/'native-profile'
dump(HERE/'input-diagnostic/session-models.json',[model_row(p) for p in (profile/'sessions').rglob('*.jsonl')])
disk=[]
for rel in ['method.md','.academic-writing/paper-state.md','.academic-writing/section-briefs/method.md']:
    snapshot=(HERE/'disk-stage2'/rel).read_bytes()
    current=(HERE/'disk-project'/rel).read_bytes()
    disk.append({'path':rel,'stage2_sha256':sha(snapshot),'after_audit_sha256':sha(current),'unchanged_by_read_only_audit':snapshot==current})
    assert snapshot==current,rel
for p in (HERE/'disk-project/rules').rglob('*'):
    if p.is_file():
        rel=p.relative_to(HERE/'disk-project/rules')
        source=ROOT/'chinese-academic-writing-assistant'/rel
        assert source.read_bytes()==p.read_bytes(),str(rel)
dump(HERE/'disk-boundary-receipts.json',{'files':disk,'rules_equal_baseline':True,'scope':'snapshot files and copied rules only; text quality is manually judged'})
out=HERE/'preflight-should-not-exist'
assert not out.exists()
cmd=[sys.executable,'-B',str(HERE/'review_cli.py'),'pair','not-a-completed-batch','--output',out.name]
r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
assert r.returncode==1 and not out.exists()
dump(HERE/'review-preflight-receipt.json',{'argv':cmd,'returncode':r.returncode,'stderr':r.stderr.strip(),'output_directory_created':out.exists(),'model_invoked':False,'scope':'early exit before model setup; execution integrity only'})
print(json.dumps({'native_reports':len(native),'supplied_input_receipts':len(proof),'disk_files_unchanged':len(disk),'pending_guard_exit':r.returncode,'diagnostic_sessions':len(list((profile/'sessions').rglob('*.jsonl')))},ensure_ascii=False))
