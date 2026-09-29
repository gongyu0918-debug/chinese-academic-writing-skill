"""Native isolated Codex drafting pairs: main versus a frozen working candidate."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
MODELS = ['alibaba-token-plan-responses/qwen3.8-flash','ollama-cloud/glm-5.3-flash']
CASES = {'P1_discussion': '只依据以下材料，为课程论文写“检索提示与文献回查”的讨论小节，约450字，只交正文。研究问题是页边提示是否帮助读者回查原始文献。两班均完成同一阅读任务，甲班36人、乙班34人，非随机分班；甲班材料有页边提示，乙班没有。甲班24人回查了原始文献，乙班15人回查。另一轮课堂中，两班均使用提示，甲班36人中22人回查，乙班34人中17人回查；前后两轮文章题材不同，不能直接作为效果复验。访谈甲班8人，5人说提示使来源位置容易找到，3人说原本就习惯回查，未采访其余学生。作者判断：提示可能降低寻找来源的困难，但回查还可能与既有习惯有关，现有材料不能单独确定提示作用。另有教务台账：两班分别新增6把和4把椅子，甲班换了窗帘，乙班添了盆栽；这些记录未与回查行为关联。讨论以研究问题为中心，不要求逐条介绍材料，不写管理建议。', 'P2_revision': '只依据原稿材料修改下面课程论文的讨论小节，主题是线上预约是否与爽约变化有关，约350字，只交改后正文。可以重新安排详略，不能新增事实或建议。原稿：甲服务点2024年有120次预约、18次爽约，2025年改用线上预约后有150次预约、15次爽约。爽约次数减少，预约总数增加。2025年同时延长了周末开放时间，未记录两项变化各自的作用。乙服务点同年也改用线上预约，2024年100次预约、10次爽约，2025年130次预约、13次爽约。作者认为甲点变化可能与预约方式或开放时间有关，乙点的记录提示不能把甲点观察直接推广。两点台账另列甲点修理3台打印机、购置2台风扇，乙点修理1台打印机、购置4台风扇；这些事项未与预约记录关联。打印机和风扇数量不同。总之，甲点的爽约次数下降，但不能只用甲点判断预约方式。也就是说，两个服务点的变化并不完全相同，需要结合各自情况看待。', 'P3_required': '依据以下已读来源写独立文献综述“检索卡片与回查行为”的述评，约450字，只交正文。导师明确要求S1至S5逐篇各用一句呈现主要内容并保留来源ID，随后综合比较证据对回查行为的支持，不可省掉任一来源。S1：非随机两组各20人，同一任务中有检索卡片组14人回查原始文献，无卡片组9人回查，未记录原因。S2：另一次任务的两组各18人，有卡片组11人回查，无卡片组12人回查，分组方式未交代。S3：访谈10人，其中7人认为卡片美观、3人不喜欢颜色，没有记录回查行为。S4：设计者分析6种卡片布局，仅描述字体与配色，没有用户测试。S5：观察12名读者使用可折叠卡片，8人展开卡片，其中5人随后回查来源；没有对照组。可以在材料范围内综合分析，不能把S3的好感当成回查增加，不能从S4声称布局有效；不要因为S2方向相反就省掉它。'}


def fingerprint(path: Path) -> str:
    rows = [f"{p.relative_to(path).as_posix()}:{hashlib.sha256(p.read_bytes()).hexdigest()}" for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    return hashlib.sha256('\n'.join(rows).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    baseline = parser.add_mutually_exclusive_group()
    baseline.add_argument('--baseline-ref', default='main', help='Git baseline; a non-main ref is named baseline in artifacts.')
    baseline.add_argument('--baseline-dir', help='Explicit frozen Skill baseline; no Git commit is claimed for its contents.')
    parser.add_argument('--candidate-dir', help='Explicit frozen Skill directory for an attributable subset comparison.')
    parser.add_argument('--candidate-skill-name', default='chinese-academic-writing-assistant', help='Candidate installation folder for a separately named product smoke test.')
    parser.add_argument('--models', nargs='+', type=int, default=[0, 1])
    parser.add_argument('--cases', nargs='+', choices=list(CASES), default=[c for c in CASES if c != 'review_existing_docx'])
    parser.add_argument('--input-file', help='Existing DOCX for the explicit review_existing_docx case; copied unchanged into each isolated workspace.')
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--effort', choices=['max','xhigh','high','medium'], default='max')
    parser.add_argument('--inherit-agent-docs', action='store_true', help='Retain host AGENTS.md context for an explicit harness comparison.')
    parser.add_argument('--isolated-profile', action='store_true', help='Use a temporary Codex profile with the same execution policy and the local provider proxy.')
    parser.add_argument('--review-host', action='store_true', help='Expose the same bounded native subagent host to both arms; child defaults use the selected writer model.')
    parser.add_argument('--retain-session-metadata', action='store_true', help='Retain isolated native session records for child-model and context provenance.')
    parser.add_argument('--ordinary-only', action='store_true', help='Compare ordinary Skill writing in both arms without optional Hook enhancement.')
    parser.add_argument('--utf8-read', action='store_true', help='Give both arms the same file-encoding instruction after a witnessed Windows decoding failure.')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.candidate_skill_name):
        parser.error('candidate skill name must be a simple lowercase slug')
    needs_input = 'review_existing_docx' in args.cases
    if needs_input != bool(args.input_file):
        parser.error('review_existing_docx requires --input-file; other cases do not use input files')
    input_bytes = None
    input_path = None
    input_sha256 = None
    if needs_input:
        input_path = Path(args.input_file).resolve()
        if not input_path.is_file() or input_path.suffix.lower() != '.docx':
            parser.error('--input-file must name an existing .docx file')
        input_bytes = input_path.read_bytes()
        input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    if needs_input:
        (out / 'inputs').mkdir()
        (out / 'inputs/received-application.docx').write_bytes(input_bytes)
    runtime = Path(tempfile.mkdtemp(prefix='cow-native-'+out.name+'-'))
    eval_environment = os.environ.copy()
    if args.isolated_profile:
        eval_profile = runtime / 'codex-profile'
        eval_profile.mkdir()
        (eval_profile / 'config.toml').write_text('approval_policy = "never"\nsandbox_mode = "danger-full-access"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n', encoding='utf-8')
        # Child-process profile only; use the existing local proxy's non-secret
        # placeholder key. No account credentials or global files are copied.
        eval_environment.update(CODEX_HOME=str(eval_profile), OPENAI_API_KEY='opencodex-loopback', CODEX_API_KEY='opencodex-loopback')
    binaries = Path(os.environ['LOCALAPPDATA'])/'OpenAI/Codex/bin'
    candidates = [p for p in [binaries/'codex.exe', *binaries.glob('*/codex.exe')] if p.is_file()]
    cli = max(candidates, key=lambda p: tuple(int(x) for x in re.search(r'(\d+)\.(\d+)\.(\d+)', subprocess.check_output([str(p),'--version'],text=True)).groups()))
    catalog = Path.home()/'.codex/opencodex-catalog.json'
    snapshots = {}
    commit = None if args.baseline_dir else subprocess.check_output(['git','rev-parse',args.baseline_ref], cwd=ROOT, text=True).strip()
    baseline_arm = 'main' if not args.baseline_dir and args.baseline_ref == 'main' else 'baseline'
    base = out/'snapshots/main'; base.mkdir(parents=True)
    if args.baseline_dir:
        shutil.copytree(Path(args.baseline_dir).resolve(),base,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    else:
        for name in subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'chinese-academic-writing-assistant'], cwd=ROOT, text=True).splitlines():
            target = base/Path(name).relative_to('chinese-academic-writing-assistant'); target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT))
    candidate = out/'snapshots/candidate'
    candidate_source = Path(args.candidate_dir).resolve() if args.candidate_dir else ROOT/'chinese-academic-writing-assistant'
    shutil.copytree(candidate_source,candidate,ignore=shutil.ignore_patterns('__pycache__','*.pyc','hooks'))
    snapshots = {baseline_arm:base,'candidate':candidate}
    binding = {'main_commit':commit,'candidate_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'fingerprints':{arm:fingerprint(path) for arm,path in snapshots.items()},'models':[MODELS[i] for i in args.models], 'cases':{k:CASES[k] for k in args.cases}, 'cli':str(cli),'cli_version':subprocess.check_output([str(cli),'--version'],text=True).strip(),'effort':args.effort,'runtime':str(runtime),'permissions':'inherited-host-config','timeout':args.timeout}
    binding['agent_documents'] = 'inherited' if args.inherit_agent_docs else 'project_doc_max_bytes=0'
    binding['baseline_ref'] = 'snapshot' if args.baseline_dir else args.baseline_ref
    binding['baseline_source'] = str(Path(args.baseline_dir).resolve()) if args.baseline_dir else None
    binding['candidate_source'] = str(candidate_source)
    binding['candidate_skill_name'] = args.candidate_skill_name
    binding['baseline_commit'] = commit
    binding['main_commit'] = subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    binding['profile'] = 'temporary-no-user-documents-or-credentials' if args.isolated_profile else 'host-profile'
    runner_source = Path(__file__).read_bytes()
    binding['runner_sha256'] = hashlib.sha256(runner_source).hexdigest()
    (out / 'runner-source.py').write_bytes(runner_source)
    binding['prompt_prefix'] = '使用本目录 .agents/skills/chinese-academic-writing-assistant/SKILL.md。本轮只写稿，不委派子代理；独立复核由另外的审稿会话统一执行。不联网。\n\n'
    if args.ordinary_only:
        binding['prompt_prefix'] += '使用普通写作能力，不启用 Hook。\n\n'
    binding['ordinary_only'] = args.ordinary_only
    if args.utf8_read:
        binding['prompt_prefix'] += '本目录文本文件为 UTF-8 编码，读取时显式指定 UTF-8 解码。\n\n'
    binding['utf8_read'] = args.utf8_read
    binding['runtime_layout'] = 'each call has a separate parent, workspace and temporary directory'
    if 'delivery_cleanup_existing' in args.cases:
        binding['text_fixture'] = {'source': str(CLEANUP_FIXTURE), 'sha256': hashlib.sha256(CLEANUP_FIXTURE.read_bytes()).hexdigest(), 'transformation': 'none'}
    if args.retain_session_metadata and not args.isolated_profile:
        raise ValueError('Session metadata retention requires an isolated profile.')
    binding['session_metadata'] = 'retained in isolated profile' if args.retain_session_metadata else 'ephemeral'
    binding['review_host'] = {'multi_agent_v2': True, 'enabled': args.review_host, 'max_threads': 3 if args.review_host else None, 'max_depth': 1 if args.review_host else None, 'child_model': 'same selected writer model' if args.review_host else 'host defaults', 'child_usage': 'root JSON usage is not assumed to include child usage'}
    if needs_input:
        binding['input_document'] = {'source': str(input_path), 'name': 'received-application.docx', 'sha256': input_sha256}
    (out/'binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2),encoding='utf-8')

    def run_pair(index: int, case_id: str):
        results=[]
        for arm in ([baseline_arm,'candidate'] if index%2==0 else ['candidate',baseline_arm]):
            run_root=runtime/f'm{index}-{case_id}-{arm}'
            skill_name = args.candidate_skill_name if arm == 'candidate' else 'chinese-academic-writing-assistant'
            work=run_root/'workspace'; skill=work/'.agents/skills'/skill_name
            shutil.copytree(snapshots[arm],skill)
            staged_input = work / 'received-application.docx' if case_id == 'review_existing_docx' else None
            if staged_input is not None:
                staged_input.write_bytes(input_bytes)
            scratch=run_root/'tmp'; scratch.mkdir()
            call_environment={**eval_environment, 'TEMP':str(scratch), 'TMP':str(scratch), 'TMPDIR':str(scratch)}
            prefix=out/f'm{index}-{case_id}-{arm}'
            final=Path(str(prefix)+'.final.txt')
            prompt=binding['prompt_prefix'].replace('.agents/skills/chinese-academic-writing-assistant/SKILL.md', f'.agents/skills/{skill_name}/SKILL.md')+CASES[case_id]
            command=[str(cli),'exec','--ephemeral','--skip-git-repo-check','-C',str(work),'-m',MODELS[index],'-c','approval_policy="never"','-c','features.plugins=false','-c','features.apps=false','-c','features.memories=false','-c','openai_base_url="http://127.0.0.1:10100/v1"','-c',f'model_catalog_json="{catalog.as_posix()}"','--json','--output-last-message',str(final),'-']
            command[-1:-1]=['-c',f'model_reasoning_effort="{args.effort}"']
            if not args.inherit_agent_docs:
                command[-1:-1]=['-c','project_doc_max_bytes=0']
            if args.review_host:
                command[-1:-1]=['-c','features.multi_agent=true','-c','features.multi_agent_v2=true','-c','agents.max_threads=3','-c','agents.max_depth=1','-c',f'agents.default_subagent_model="{MODELS[index]}"']
                command[-1:-1]=['-c',f'agents.default_subagent_reasoning_effort="{args.effort}"']
            if args.retain_session_metadata:
                command.remove('--ephemeral')
            started=time.monotonic(); error=None
            print(f'START {index} {case_id} {arm}',flush=True)
            try:
                done=subprocess.run(command,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=args.timeout,env=call_environment,cwd=work)
                code=done.returncode;stdout=done.stdout;stderr=done.stderr
            except subprocess.TimeoutExpired as exc:
                code=None; error='timeout'
                stdout=exc.stdout or '';stderr=exc.stderr or ''
                if isinstance(stdout,bytes): stdout=stdout.decode('utf-8','replace')
                if isinstance(stderr,bytes): stderr=stderr.decode('utf-8','replace')
            Path(str(prefix)+'.trace.jsonl').write_text(stdout,encoding='utf-8')
            Path(str(prefix)+'.stderr.txt').write_text(stderr,encoding='utf-8')
            events=[]
            for line in stdout.splitlines():
                try: events.append(json.loads(line))
                except json.JSONDecodeError: pass
            calls=[x['item'] for x in events if isinstance(x.get('item'),dict) and x['item'].get('type')=='command_execution' and x.get('type')=='item.completed']
            commands=re.sub(r'/+', '/', '\n'.join(x.get('command','') for x in calls).replace('\\','/').lower())
            text=final.read_text(encoding='utf-8') if final.exists() else ''
            invalid=[]
            if code!=0 or error: invalid.append(error or f'exit_{code}')
            if not text.strip(): invalid.append('missing_final')
            bound_entry = (skill / 'SKILL.md').read_text(encoding='utf-8-sig').replace('\r\n', '\n').strip()
            entry_returned = any(
                x.get('exit_code') == 0 and bound_entry in x.get('aggregated_output', '').replace('\r\n', '\n')
                for x in calls
            )
            if f'{skill_name}/skill.md' not in commands and not entry_returned:
                invalid.append('missing_skill_read_trace')
            foreign=[x for x in calls if ('/.codex/skills/' in x.get('command','').replace('\\','/').lower() or '/plugins/cache/' in x.get('command','').replace('\\','/').lower())]
            if foreign: invalid.append('foreign_skill_read')
            if '开发与验证' in stdout or '所有代码和文档改动提交' in stdout or '仅保留完整 Pro 安装' in stdout:
                invalid.append('maintenance_instructions_contamination')
            result={'model':MODELS[index],'effort':args.effort,'case':case_id,'arm':arm,'returncode':code,'seconds':round(time.monotonic()-started,2),'invalid':invalid,'draft_sha256':hashlib.sha256(text.encode()).hexdigest(),'commands':calls,'usage':[x.get('usage') for x in events if x.get('type')=='turn.completed']}
            if args.review_host:
                result['collaboration_items']=[x['item'] for x in events if isinstance(x.get('item'),dict) and 'collab' in x['item'].get('type','') and x.get('type')=='item.completed']
            if staged_input is not None:
                after_hash = hashlib.sha256(staged_input.read_bytes()).hexdigest() if staged_input.is_file() else None
                result['input_document'] = {'path': str(staged_input), 'before_sha256': input_sha256, 'after_sha256': after_hash, 'unchanged': after_hash == input_sha256}
            Path(str(prefix)+'.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(f'END {index} {case_id} {arm} invalid={invalid} seconds={result["seconds"]}',flush=True)
            results.append(result)
        return results

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(run_pair,i,c) for i in args.models for c in args.cases]
        results=[row for future in futures for row in future.result()]
    (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
