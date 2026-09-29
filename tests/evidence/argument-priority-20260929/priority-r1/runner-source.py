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
MODELS = ['alibaba-token-plan-responses/deepseek-v4.1-flash', 'ollama-cloud/glm-5.3-flash']
CASES = {'A_discussion': '请依据作者材料为课程论文写“反馈对象与修订选择”讨论小节，约450字，只交正文。中心问题：学生如何在不同反馈中选择修订对象。24名学生各完成一次初稿和一次修订；教师在初稿中分别标出主张与证据错位、来源遗漏。修订记录显示，15人优先调整主张与证据的对应，6人只补来源，3人没有修改。访谈摘录：7人说能看出具体哪条证据不贴合主张，4人说补来源更容易；11人均来自前两组，其余未访谈。作者观点：反馈对象是否清楚、修改是否容易，可能共同影响选择。另有课堂管理记录：课程共8周，每周90分钟，第3周换过教室，作业系统收齐24份，两次下雨延迟下课。没有对照组，也未评价修订后的质量。下一节另写教学建议。', 'B_review': '写独立文献综述中的“检索提示与证据回查”一节，约450字，只交正文并保留来源ID。只用以下已读原文摘录。研究问题：提示是否有助于读者回到与判断相关的证据。L1：48名成人随机使用有提示或无提示的在线说明，带提示组更常回到对应段落；作者未测理解正确率。L2：36名成人完成另一种说明任务，提示组与对照组回查次数接近，但提示组更多回到无关段落；作者认为提示内容的相关性值得进一步考察。L3：12名培训学员访谈，8人称醒目标记便于找到需要复查的位置，未记录实际点击。L4：问卷调查80名本科生，56人喜欢浅色界面，未测试提示或回查。L5：系统设计说明介绍了导航栏、下载按钮、账户设置三个模块，没有读者实验。文献对象、任务和测量不相同。不得编造综合效应，不需要逐篇摘要或另附文献表。', 'C_proposal': '根据材料写开题报告“研究内容与已有基础”小节，约400字，只交正文。研究问题：同一历史事件在两版地方教材中如何调整叙述次序。作者已整理2010年版和2022年版教材，核对出都涉及该事件的18个段落，已抄录各段原文并核对页码；只完成12个段落的次序标记，其余6个尚未标记。作者拟比较事件起因、经过和结果的叙述位置；这三个维度已与导师确认。作者尚未判断变化原因，拟在完成全部标记后结合教材编写说明作解释，编写说明尚未取得。作者还整理了教材封面颜色、定价及纸张尺寸，不拟研究装帧与发行。进度另节写，本节不写时间表。研究成果尚未形成。学校要求先写研究内容，再写已有基础。', 'D_control': '请压缩这段论文讨论至约220字，只交改后正文，保持原判断和引用。研究问题是维修时长是否下降。原稿：本研究比较甲站2023年和2024年维修记录。2023年有60条记录，平均维修时长为5天；2024年有90条记录，平均为3天。从年度均值看，维修时长有所缩短。但2023年仅登记已结案工单，2024年同时登记已结案与未结案工单，且两年未结案事项的时长计算口径没有说明。因此，记录均值的变化尚不能被直接解释为维修效率改善。另一处同期运行记录显示，紧急维修工单由10条增至25条，工单构成也有变化。[R1] 两年的工作人员人数均为8人，前台公告栏分别在3月和4月重新张贴。作者认为应先核对登记和计算口径，再讨论两年时长差异，不宜仅凭均值对效率作确定判断。本研究没有另外调查服务评价。[R1] 原始材料与本段一致，引用R1是作者的记录汇编。'}


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

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_pair,i,c) for i in args.models for c in args.cases]
        results=[row for future in futures for row in future.result()]
    (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
