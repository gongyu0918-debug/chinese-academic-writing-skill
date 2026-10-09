"""Independent native semantic reviewer; public archive excludes reasoning."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import argparse
from coverage_runner import CLI, CATALOG, ROOT, HERE, dump, sha

parser = argparse.ArgumentParser()
parser.add_argument('mode')
parser.add_argument('batch', nargs='?')
parser.add_argument('--model', default='alibaba-token-plan-responses/glm-5.3')
parser.add_argument('--output')
parser.add_argument('--groups', nargs='+', type=int)
args = parser.parse_args()
mode = args.mode
if args.batch:
    completed = HERE / args.batch / 'results.json'
    if not completed.exists():
        raise SystemExit('Batch is still pending; do not turn missing drafts into technical or semantic failures.')
out = HERE / (args.output or ('review-' + mode))
out.mkdir(exist_ok=False)
runtime = Path(tempfile.mkdtemp(prefix='review-runtime-', dir=HERE))
profile = runtime / 'native-profile'
profile.mkdir()
(profile / 'config.toml').write_bytes(b'approval_policy = "never"\nsandbox_mode = "workspace-write"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n')
env = dict(os.environ, CODEX_HOME=str(profile), OPENAI_API_KEY='opencodex-loopback', CODEX_API_KEY='opencodex-loopback')
model = args.model
packets = []
if mode == 'audit':
    files = ['SKILL.md'] + ['references/' + p.name for p in sorted((ROOT/'chinese-academic-writing-assistant/references').glob('*.md'))]
    text = '\n\n'.join(name + '\n' + (ROOT/'chinese-academic-writing-assistant'/name).read_text(encoding='utf-8-sig') for name in files)
    request = '审计以下当前论文写作规则。不要修改、检索、调用工具或委派。用具体位置和原句审查歧义、互相冲突与适用范围；每个真问题写两种合理执行解释、触发场景、风险、最小修订。灵活措辞本身不算问题。特别检查研究材料与核验、授权修改与作者未决事项、阶段与版本、有限分析和因果、主次与正文交付；不自动加规则。最多六项，另列疑似但不改项。不要用Python判断。\n\n' + text
    packets.append(('audit', request))
elif mode == 'long':
    batch = HERE / args.batch
    binding = json.loads((batch/'binding.json').read_text(encoding='utf-8-sig'))
    for mi in (0,1):
        arms = ['main','candidate'] if mi == 0 else ['candidate','main']
        mapping = dict(zip(('X','Y'), arms))
        request = '独立语义审阅三阶段长稿。只按每轮原任务及当时可见材料判断，禁止工具、联网和委派，不改写正文。X/Y为隐藏规则版本的两个独立链条。每阶段都是新会话，仅携带前轮可见交付稿与状态，不能假定读过未给的前节或文件。逐链逐阶段定位事实、来源定位、研究状态、未决事项、正文范围与制作旁白问题；审稿意见也须回读其所审文本，不凑问题。不要把未给凭证说成作者不存在凭证。任务摘编允许作者据材料分析，但不允许虚构亲自访问或完整读取原PDF。两链比对无问题则明确。不要把完成调用或保存状态等于语义通过。\n'
        for name, case in binding['spec'].items():
            request += '\n案例 '+name
            for stage, user_request in enumerate(case['requests'],1):
                request += '\n阶段 '+str(stage)+' 原任务\n'+user_request
                for label, arm in mapping.items():
                    final=batch/f'm{mi}-{name}-{arm}-s{stage}.final.txt'
                    request += '\n链 '+label+' 本轮交付\n'+(final.read_text(encoding='utf-8-sig') if final.exists() else '[无终稿，技术无效]')
        dump(out/f'model{mi}.mapping.json', {'model_index':mi,'mapping':mapping})
        packets.append(('model'+str(mi),request))
else:
    batch = HERE / args.batch
    binding = json.loads((batch/'binding.json').read_text(encoding='utf-8-sig'))
    cases = binding['spec']
    groups = [list(cases)[i:i+2] for i in range(0,len(cases),2)]
    for index, names in enumerate(groups):
        if args.groups is not None and index not in args.groups:
            continue
        request = '独立语义审阅。只按原任务及材料判断给定稿件，不调用工具、联网或委派，不改写正文。文件标签已去掉main/candidate，仅称X/Y；规则候选与目的不提供。逐对说明事实、状态、对象、推断强度、交付范围与过审的具体差别；无实质问题明确可用。数值/原材料不变，有限作者解释不等于新增事实，未显著不等于不存在，尚未核验不等于材料缺失。审稿意见自身也可能过强。只报能指出位置与依据的问题，不凑意见；单次差别不是规则因果或可复现结论。\n'
        for name in names:
            request += '\n任务 ' + name + '\n' + '\n'.join(cases[name]['requests'])
            for mi in (0,1):
                request += '\n作者模型 ' + str(mi) + '\n'
                arms = ['candidate','main'] if (mi+index)%2 else ['main','candidate']
                for label, arm in zip(('X','Y'), arms):
                    final = batch/f'm{mi}-{name}-{arm}-s1.final.txt'
                    request += '\n稿 ' + label + '\n' + (final.read_text(encoding='utf-8-sig') if final.exists() else '[无终稿，技术无效，不作语义判定]')
        dump(out/f'group{index}.mapping.json', {'cases':names, 'mapping':{str(mi): dict(zip(('X','Y'), ['candidate','main'] if (mi+index)%2 else ['main','candidate'])) for mi in (0,1)}})
        packets.append(('group'+str(index), request))

def invoke(name,prompt):
    work = runtime/name
    work.mkdir()
    final = out/(name+'.final.md')
    (out/(name+'.prompt.txt')).write_bytes(prompt.encode())
    cmd = [str(CLI),'exec','--skip-git-repo-check','-C',str(work),'-m',model,
        '-c','approval_policy="never"','-c','project_doc_max_bytes=0','-c','features.plugins=false',
        '-c','features.apps=false','-c','features.memories=false','-c','model_reasoning_effort="max"',
        '-c','openai_base_url="http://127.0.0.1:10100/v1"','-c',f'model_catalog_json="{CATALOG.as_posix()}"',
        '--json','--output-last-message',str(final),'-']
    print('START '+name,flush=True)
    try:
        r = subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=420,env=env,cwd=work)
        rc, output, stderr = r.returncode,r.stdout,r.stderr
    except subprocess.TimeoutExpired as e:
        rc=None
        output=e.stdout or b''
        stderr=e.stderr or b''
        if isinstance(output,bytes):output=output.decode('utf-8','replace')
        if isinstance(stderr,bytes):stderr=stderr.decode('utf-8','replace')
    events=[]
    for line in output.splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    visible=[e for e in events if e.get('type') in ('thread.started','turn.started','turn.completed','turn.failed','error') or (e.get('type') in ('item.started','item.completed') and e.get('item',{}).get('type') in ('agent_message','command_execution','web_search','error'))]
    (out/(name+'.trace.jsonl')).write_bytes(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in visible).encode())
    (runtime/(name+'.stderr.txt')).write_bytes(stderr.encode())
    dump(out/(name+'.result.json'),{'model':model,'effort':'max','returncode':rc,'prompt_sha256':sha(prompt.encode()),
        'draft_sha256':sha(final.read_bytes()) if final.exists() else None,
        'visible_tool_items':[e for e in visible if e.get('item',{}).get('type') in ('command_execution','web_search')],
        'runtime':str(runtime),'session_profile':str(profile),'call_completed':rc==0 and final.exists(),
        'semantic_review_completed':None})
    print('END '+name+' rc='+str(rc),flush=True)
with ThreadPoolExecutor(max_workers=1) as pool:
    list(pool.map(lambda p:invoke(*p),packets))
