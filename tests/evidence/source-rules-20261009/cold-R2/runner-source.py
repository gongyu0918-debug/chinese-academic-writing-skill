from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,random,subprocess,sys,time
root=Path(sys.argv[1]);round_id=sys.argv[2];evidence=root/'tests/evidence/source-rules-20261009';run=evidence/round_id
dest=evidence/('cold-'+round_id);dest.mkdir(exist_ok=False)
local=root/'.release/source-rule-review'/round_id;local.mkdir(parents=True,exist_ok=False)
profile=local/'profile';profile.mkdir();(profile/'config.toml').write_text('approval_policy = "never"\nsandbox_mode = "workspace-write"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n',encoding='utf-8')
binding=json.loads((run/'binding.json').read_text(encoding='utf-8'));cli=binding['cli'];catalog_path=Path('C:/Users/admin/.codex/opencodex-catalog.json');catalog=json.loads(catalog_path.read_text(encoding='utf-8'));model='alibaba-token-plan-responses/glm-5.3';choice=next(m for m in catalog['models'] if m['slug']==model);assert 'max' in [x['effort'] for x in choice['supported_reasoning_levels']]
(dest/'model-catalog.json').write_text(json.dumps(choice,ensure_ascii=False,indent=2),encoding='utf-8')
criteria='''你是未参与起草的独立语义复核者。不使用任何工具，不联网，不委派。以下X/Y仅是匿名文本，每对独立随机，不能据标签猜版本。只依据完整用户请求及所给材料判断：事实和对象归属、计划/已完成状态、范围、是否直接交付所需正文/意见、修改负担。不要以更长、审稿点更多或旁支更全加分；在材料内的有限分析不当作新增事实，未确定项不能猜定；用户已经给完整正文却称缺失是交付失败。逐对给X优/Y优/持平/不可比和简短原句依据；分清技术未完成、双方问题和实质改进，校验该字句确实在稿中。没有模板或上下文支持，不自行添加格式要求或方法判定。每对最多250中文字，不判断整套Skill是否稳定，不猜候选DIFF，不给统计显著性结论。'''
mapping={};results=json.loads((run/'results.json').read_text(encoding='utf-8'))
def call(mi):
    packet=[]
    for j,(case,request) in enumerate(binding['cases'].items()):
        names=[f'm{mi}-{case}-main',f'm{mi}-{case}-candidate'];random.Random(round_id+'-'+str(mi)+'-'+case).shuffle(names)
        pair_id=f'{round_id}-{mi}-{j+1}';mapping[pair_id]={label:name for label,name in zip(('X','Y'),names)}
        text=f'## {pair_id}\n完整请求与材料：\n{request}\n'
        for label,name in zip(('X','Y'),names):
            row=next(r for r in results if r['model']==binding['models'][mi] and r['case']==case and r['arm']==('candidate' if name.endswith('-candidate') else 'main'))
            path=run/(name+'.final.txt');draft=path.read_text(encoding='utf-8') if path.exists() else '[无终稿]'
            text+=f'\n### {label}\n技术状态：{json.dumps(row["invalid"],ensure_ascii=False)}\n{draft}\n'
        packet.append(text)
    prompt=criteria+'\n\n'+'\n\n'.join(packet);(dest/f'm{mi}.prompt.txt').write_text(prompt,encoding='utf-8')
    work=local/f'work-m{mi}';work.mkdir();env={**os.environ,'CODEX_HOME':str(profile),'OPENAI_API_KEY':'opencodex-loopback','CODEX_API_KEY':'opencodex-loopback'}
    final=dest/f'm{mi}.final.txt';cmd=[cli,'exec','--skip-git-repo-check','-C',str(work),'-m',model,'-c','approval_policy="never"','-c','features.plugins=false','-c','features.apps=false','-c','features.memories=false','-c','project_doc_max_bytes=0','-c','openai_base_url="http://127.0.0.1:10100/v1"','-c',f'model_catalog_json="{catalog_path.as_posix()}"','-c','model_reasoning_effort="max"','--json','--output-last-message',str(final),'-']
    print(f'START {round_id} cold {mi}',flush=True);started=time.monotonic();timed_out=False
    try:
        done=subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=260,env=env,cwd=work)
    except subprocess.TimeoutExpired as exc:
        timed_out=True
        def as_text(value):return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else (value or '')
        done=subprocess.CompletedProcess(cmd,124,as_text(exc.stdout),as_text(exc.stderr))
    (local/f'm{mi}.stderr.txt').write_text(done.stderr,encoding='utf-8')
    events=[]
    for line in done.stdout.splitlines():
        try:event=json.loads(line)
        except json.JSONDecodeError:continue
        if event.get('item',{}).get('type') not in ('reasoning','reasoning_summary'):events.append(event)
    (dest/f'm{mi}.trace.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in events)+'\n',encoding='utf-8')
    tools=[x['item'] for x in events if x.get('item',{}).get('type') not in ('agent_message','reasoning','reasoning_summary') and x.get('type')=='item.completed']
    row={'requested_model':model,'effort':'max','returncode':done.returncode,'timed_out':timed_out,'seconds':round(time.monotonic()-started,2),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest() if final.exists() else None,'unexpected_items':tools,'quality_not_inferred_from_return':True}
    (dest/f'm{mi}.result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8');print(f'END {round_id} cold {mi} exit={done.returncode}',flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(call,(0,1)))
(dest/'blind-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
records=[]
for path in (profile/'sessions').rglob('*.jsonl'):
    events=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()];meta=next(x['payload'] for x in events if x['type']=='session_meta');context=[x['payload'] for x in events if x['type']=='turn_context'][-1];texts=[c['text'] for x in events if x.get('type')=='response_item' and x.get('payload',{}).get('role')=='user' for c in x['payload'].get('content',[]) if c.get('type')=='input_text'];prompt=max(texts,key=len).replace('\r\n','\n');mi=int(Path(meta['cwd']).name[-1]);records.append({'id':meta['id'],'model':context['model'],'effort':context['effort'],'packet':mi,'prompt_hash_match':hashlib.sha256(prompt.encode()).hexdigest()==rows[mi]['prompt_sha256'],'hidden_reasoning_archived':False})
assert len(records)==2 and all(r['model']==model and r['effort']=='max' and r['prompt_hash_match'] for r in records)
(dest/'session-models.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');(dest/'runner-source.py').write_bytes(Path(__file__).read_bytes())
print('Independent review session metadata bound.',flush=True)
