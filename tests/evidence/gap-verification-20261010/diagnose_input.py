"""Bounded native task-only probe; detects transport/completion, never grades prose."""
from pathlib import Path
import json, os, subprocess, tempfile, time
from coverage_runner import CLI, CATALOG, HERE, MODELS, dump, sha

OUT=HERE/'input-diagnostic'
OUT.mkdir(exist_ok=False)
runtime=Path(tempfile.mkdtemp(prefix='diagnostic-runtime-',dir=HERE))
profile=runtime/'native-profile'
profile.mkdir()
(profile/'config.toml').write_bytes(b'approval_policy = "never"\nsandbox_mode = "workspace-write"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n')
env=dict(os.environ,CODEX_HOME=str(profile),OPENAI_API_KEY='opencodex-loopback',CODEX_API_KEY='opencodex-loopback')
a=json.loads((HERE/'source-scope-tasks.json').read_text(encoding='utf-8'))['A_raw_interviews']['requests'][0]
l=json.loads((HERE/'confirmation-tasks.json').read_text(encoding='utf-8'))['L_existing_target']['requests'][0]
dump(OUT/'plan.json',{'purpose':'Investigate whether supplied-text refusal also occurs without the large skill packet. Same model/provider/effort, two unchanged tasks, two fresh sessions each. This does not isolate a rule or prove a backend cause.','model':MODELS[0],'effort':'max','tasks':{'A':a,'L':l},'reference_comparisons':['source-scope-R1','source-scope-R2','source-scope-R3'],'not_product_candidate':True,'runtime':str(runtime),'no_more_retries':True})
rows=[]
for repeat in (1,2):
    for case,request in [('A',a),('L',l)]:
        stem=case+'-repeat'+str(repeat)
        work=runtime/stem
        work.mkdir()
        prompt='直接完成以下用户任务，只用给定材料，不联网、不调用工具或委派。\n\n'+request
        final=OUT/(stem+'.final.txt')
        (OUT/(stem+'.prompt.txt')).write_bytes(prompt.encode())
        cmd=[str(CLI),'exec','--skip-git-repo-check','-C',str(work),'-m',MODELS[0],'-c','approval_policy="never"','-c','features.plugins=false','-c','features.apps=false','-c','features.memories=false','-c','project_doc_max_bytes=0','-c','model_reasoning_effort="max"','-c','openai_base_url="http://127.0.0.1:10100/v1"','-c',f'model_catalog_json="{CATALOG.as_posix()}"','--json','--output-last-message',str(final),'-']
        print('START '+stem,flush=True)
        started=time.monotonic()
        try:
            r=subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=300,env=env,cwd=work)
            rc,stdout=r.returncode,r.stdout
        except subprocess.TimeoutExpired as e:
            rc,stdout=None,e.stdout or b''
            if isinstance(stdout,bytes): stdout=stdout.decode('utf-8','replace')
        events=[]
        for line in stdout.splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:pass
        visible=[e for e in events if e.get('type') in ('thread.started','turn.started','turn.completed','turn.failed','error') or (e.get('type') in ('item.started','item.completed') and e.get('item',{}).get('type') in ('agent_message','command_execution','web_search','error'))]
        (OUT/(stem+'.trace.jsonl')).write_bytes(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in visible).encode())
        row={'case':case,'repeat':repeat,'model':MODELS[0],'effort':'max','returncode':rc,'seconds':round(time.monotonic()-started,2),'prompt_sha256':sha(prompt.encode()),'draft_sha256':sha(final.read_bytes() if final.exists() else b''),'completed':rc==0 and final.exists() and bool(final.read_bytes().strip()),'tools_used':any(e.get('item',{}).get('type') in ('command_execution','web_search') for e in visible),'thread_ids':[e.get('thread_id') for e in events if e.get('type')=='thread.started'],'quality_pass':None}
        dump(OUT/(stem+'.result.json'),row)
        rows.append(row)
        print('END '+stem+' rc='+str(rc),flush=True)
dump(OUT/'results.json',rows)
