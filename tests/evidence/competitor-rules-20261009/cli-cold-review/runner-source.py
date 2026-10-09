from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, subprocess, time
root=Path('C:/Users/admin/.codex/worktrees/academic-competitor-1009/chinese-academic-writing-skill')
evidence=root/'tests/evidence/competitor-rules-20261009'
dest=evidence/'cli-cold-review'
dest.mkdir(exist_ok=False)
local=root/'.release/competitor-cold-profile'
local.mkdir(exist_ok=False)
profile=local/'codex-profile'
profile.mkdir()
(profile/'config.toml').write_text('approval_policy = "never"\nsandbox_mode = "workspace-write"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n',encoding='utf-8')
catalog_path=Path('C:/Users/admin/.codex/opencodex-catalog.json')
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
model='alibaba-token-plan-responses/glm-5.3'
choice=next(m for m in catalog['models'] if m['slug']==model)
assert 'max' in [x['effort'] for x in choice['supported_reasoning_levels']]
(dest/'model-catalog.json').write_text(json.dumps(choice,ensure_ascii=False,indent=2),encoding='utf-8')
cli=json.loads((evidence/'R4/binding.json').read_text(encoding='utf-8'))['cli']
env={**os.environ,'CODEX_HOME':str(profile),'OPENAI_API_KEY':'opencodex-loopback','CODEX_API_KEY':'opencodex-loopback'}
criteria='''你是未参与起草的独立语义复核者。不调用工具、不联网、不派生代理，不读取任何其他文件。以下每题X/Y独立随机，标签不表示同一版本。只按原始请求和完整材料审实际稿件，不按更长、意见更多或旁支更全加分。清楚的回指、必要解释、有限文本分析可以保留；不强求先行词紧邻；主次按实际用途，背景可压缩，不要求逐项保全除非用户明确要求。正文齐全却称缺失是交付失败；不能由这种失败推断规则DIFF原因。真正不可确定的来源不得猜归属。R3/H在原段后没有闭合界标，有尾随任务约束；制作残留意见不作为这题版本优劣依据，只比较前三句并注明输入歧义。每对给X优/Y优/持平/双方失败及1-2句材料证据；列双方具体错误和修改建议；约1500中文字内，不宣称某版全局安全或揣测哪个版本。'''
def call(mi):
    work=local/f'work-m{mi}'
    work.mkdir()
    prompt=criteria+'\n\n'+'\n\n'.join((evidence/run/'blind'/f'm{mi}.md').read_text(encoding='utf-8') for run in ('R3','R4'))
    (dest/f'm{mi}.prompt.txt').write_text(prompt,encoding='utf-8')
    prefix=dest/f'm{mi}'
    cmd=[cli,'exec','--skip-git-repo-check','-C',str(work),'-m',model,'-c','approval_policy="never"','-c','features.plugins=false','-c','features.apps=false','-c','features.memories=false','-c','project_doc_max_bytes=0','-c','openai_base_url="http://127.0.0.1:10100/v1"','-c',f'model_catalog_json="{catalog_path.as_posix()}"','-c','model_reasoning_effort="max"','--json','--output-last-message',str(prefix)+'.final.txt','-']
    print(f'START cold m{mi}',flush=True)
    start=time.monotonic()
    done=subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=300,env=env,cwd=work)
    (local/f'm{mi}.stderr.txt').write_text(done.stderr,encoding='utf-8')
    trace=[]
    for line in done.stdout.splitlines():
        try:event=json.loads(line)
        except json.JSONDecodeError:continue
        if event.get('type') in ('thread.started','turn.started','turn.completed','turn.failed','error','item.completed') and event.get('item',{}).get('type') not in ('reasoning','reasoning_summary'):
            trace.append(event)
    (dest/f'm{mi}.trace.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in trace)+'\n',encoding='utf-8')
    final=Path(str(prefix)+'.final.txt')
    result={'model_requested':model,'effort_requested':'max','returncode':done.returncode,'seconds':round(time.monotonic()-start,2),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest() if final.exists() else None,'semantic_pass':'not inferred from response','scope':'five anonymous repaired pairs, writer route m'+str(mi)}
    (dest/f'm{mi}.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'END cold m{mi} exit={done.returncode} seconds={result["seconds"]}',flush=True)
    return result
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(call,(0,1)))
records=[]
for path in (profile/'sessions').rglob('*.jsonl'):
    events=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
    meta=next(x['payload'] for x in events if x['type']=='session_meta')
    context=[x['payload'] for x in events if x['type']=='turn_context'][-1]
    texts=[c['text'] for x in events if x.get('type')=='response_item' and x.get('payload',{}).get('role')=='user' for c in x['payload'].get('content',[]) if c.get('type')=='input_text']
    prompt=max(texts,key=len).replace('\r\n','\n')
    mi=int(Path(meta['cwd']).name[-1])
    records.append({'id':meta['id'],'model':context['model'],'effort':context['effort'],'writer_packet':mi,'prompt_hash_match':hashlib.sha256(prompt.encode()).hexdigest()==results[mi]['prompt_sha256'],'hidden_reasoning_archived':False})
assert len(records)==2 and all(r['model']==model and r['effort']=='max' and r['prompt_hash_match'] for r in records)
(dest/'session-models.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(dest/'runner-source.py').write_bytes(Path(__file__).read_bytes())
print('Two independent native CLI review calls completed and input/model metadata bound.',flush=True)
