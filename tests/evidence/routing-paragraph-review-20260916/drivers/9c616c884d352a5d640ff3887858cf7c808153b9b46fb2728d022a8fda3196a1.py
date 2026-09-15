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
MODELS = ["alibaba-token-plan/qwen3.8-flash", "alibaba-token-plan-2/qwen3.8-flash", "command-code/deepseek-deepseek-v4.1-flash", "minimax-cn/MiniMax-M3", "ollama-cloud/glm-5.3-flash"]
CASES = {'N1_results': '请依据下面的已完成研究材料，写课程论文的‘结果与讨论’部分，约500字，直接给正文。研究问题是小组协作中任务提示与学生修订行为的关系。研究在同一门课程的两个班开展，A班28人，B班30人。A班使用含修订提示的任务单，B班使用普通任务单；两班均完成两次同类写作练习，教师相同。教师记录显示，A班有19人第二次提交时调整了论据与主张的对应关系，B班有12人；A班有7人补充了来源标注，B班有6人。这是两个自然班的课堂记录，分班不是随机的，初始写作水平未作统一测量。作者的解释是：任务单中的提示可能使修订对象更具体。现有记录只覆盖这两次练习。论文下一节单独讨论教学建议。', 'N2_rewrite': '请润色下面论文的两段讨论，删掉多余重复，表达自然简洁，保持材料原意与必要限制。只交改后正文。原始记录为：12名受访者中，8人提到办理进度可见能减少反复咨询，4人表示仍需电话确认；访谈仅询问使用体验，没有测量等待时间，研究没有跨机构样本。底稿：‘访谈材料表明，办理进度的可见性与受访者的咨询体验相联系。12名受访者中，8人认为查看进度能减少反复咨询，4人表示仍需电话确认。因此，进度可见性可能有助于受访者判断是否需要继续询问。这不等于手续已经缩减，也不能说明窗口数量有所增加，亦不能说明部门间资源实现整合。\n\n从信息需求看，8名受访者的回答集中于是否还需要再次询问，4名受访者则保留电话确认。这一差异提示，进度展示提供了判断线索，但部分受访者仍需要进一步确认。这里讨论的是主观咨询体验，访谈没有测量等待时间，因此不能把回答解释为办理速度已经提高。本研究不讨论全体居民，也不说明所有机构都具有相同情况，不涉及不同城市的长期发展，更不承诺改革成效。’', 'P1_paragraph': '我们按段落推进论文。当前只写第三章第二段，180—240字，写完等我给下一段材料，只回复这一段。该段任务是解释材料中‘借阅请求集中于午休时段’这一观察。上一段已经交代：连续四周记录某学院资料室180次借阅请求，其中午休时段102次，其他开放时段78次。作者另有10人的访谈摘录，6人说上午课程结束后会顺路来取资料，4人没有说明选择时段的原因。下一段准备讨论资料领取方式，目前已有预约柜试用反馈但这轮不写。本段可引用的作者判断：课程结束后的时间衔接可能是午休请求集中的一个原因。不要再重写上一段。', 'P2_proposal': '开题报告逐段写，先给‘已有研究基础’这一段，150—220字，暂时不要展开后面的研究安排。题目为《地方博物馆馆藏说明文本的叙事组织》。作者已整理某馆公开展陈手册的2020年和2024年两个版本，并标出其中都出现的24件藏品条目；已核对两版条目标题和排列顺序，还未比较具体措辞。导师已同意把这24件藏品说明作为研究对象。后续计划是比较同件藏品在两版文本中的叙述顺序，具体分析类别下次讨论。本次只输出所要的一段正文。', 'P3_literature': '请根据以下已读原文摘录，为独立文献综述写一个约250字的自然段，讨论‘提示位置与读者回查行为’，暂不写其他主题。保留来源ID，不需要另附来源表或参考文献表。S1：在40名成人完成的说明书阅读任务中，研究者将提示放在步骤旁边，记录到多数回查发生在操作步骤切换时。S2：对36名成人的另一项说明书阅读研究把提示集中放在文末，访谈中有受试者说查找提示需要往返翻页，研究没有统计回查次数。S3：对20名职业培训学员的观察显示，带页边索引的材料中，回查主要集中于首次操作阶段。三项研究对象和任务均不同。直接交这一段正文。', 'R1_review': '请只审下面课程论文的讨论段，重点检查AI味、结构、逻辑、重复和流水账，给出简短具体的修改意见，不代写。可核对材料：研究统计了某小区30份报修记录，12份涉及照明、10份涉及门禁、8份涉及其他设施；平均处理时间分别为2天、4天、3天。没有调查满意度，也没有记录延迟原因。底稿：‘首先，从照明来看，12份报修涉及照明，平均处理时间为2天，这体现了照明维修工作的持续推进。其次，从门禁来看，10份报修涉及门禁，平均处理时间为4天，这体现了门禁维修工作的稳步推进。最后，从其他设施来看，8份报修涉及其他设施，平均处理时间为3天，这体现了其他设施维修工作的有效推进。可见，维修服务水平得到全面提升，居民满意度持续提高。本组记录没有调查满意度，因此不能据此判断居民是否满意。’', 'T1': '课程论文暂定题目《社区公告栏信息更新的日常组织》，目前只有这个题目。给一个可供讨论的简短提纲，标出需要补的核心材料，不写正文。', 'T2': '只给开题报告二级提纲，每节一句职责，不写正文。题目《地方博物馆馆藏说明文本的叙事组织》。作者已整理某馆2020年和2024年展陈手册，标出两版都出现的24件藏品；导师同意以这些藏品说明为对象。拟比较同件藏品说明的叙述顺序，分析类别仍待讨论。学校栏目是：研究基础、研究问题、研究内容与方法、进度。作者只确定10月完成文本对读，12月完成初稿。', 'T3': '按以下三项已读摘要，给一份独立文献综述的提纲，每个主题后说明可以用哪些来源ID，不写正文。范围是提示位置与读者回查行为。A：40名成人的说明书阅读中，步骤旁提示条件下的回查主要发生于步骤切换。B：另一项36名成人研究将提示放在文末，部分受试者称查提示需要往返翻页，没有记录回查次数。C：20名职业培训学员使用页边索引材料，回查主要发生在首次操作阶段。各项研究对象和任务不同。', 'T4': '只依据本题原文摘录核对下面论文讨论及引文，不联网，不改稿；指出有依据和需要修正的具体判断即可。A原文：在本次12名受访者中，8人称能看到办理进度后会减少反复咨询，4人仍会电话确认。访谈只询问体验，没有计时。B原文：另外一个服务中心的10名工作人员认为，统一答复模板便于解释同类问题；研究未记录公众咨询次数。待审段：‘进度可见性可能为部分受访者判断是否继续询问提供线索，这是本文基于访谈所作的解释。[A] A与B共同证明统一模板通过进度可见性减少了公众等待时间。[A][B]’', 'T5': '请依次完成两个小任务。第一，为课程论文写一个80字以内的结果段，只陈述：30份报修记录中，12份为照明，10份为门禁，8份为其他设施，平均处理时间分别为2天、4天、3天。第二，另写社区停水通知，通知材料我还没给。分别标明处理结果。', 'T6': '请只审下面论文两节的整体结构、逻辑、重复和AI味，一次给简明意见，不改稿，不在磁盘保存论文状态。实际材料：30份报修记录，12份照明、10份门禁、8份其他；平均处理时间分别为2天、4天、3天。没有满意度数据和延迟原因记录。第一节：‘本组共有30份报修记录，其中照明12份，门禁10份，其他设施8份，平均处理时间分别为2天、4天、3天。门禁类平均处理时间最长。’第二节：‘从类别分布看，照明12份，门禁10份，其他设施8份，平均处理时间分别为2天、4天、3天。这些数字充分证明服务水平全面提升，公众满意度稳步提高。总体而言，本项工作持续推进，服务机制不断完善。’', 'T7': '只修改这段开题中的进度安排，按我刚确定的新安排写成一段，不解释。原稿：‘10月完成文本对读，11月整理访谈材料，12月完成初稿。’最新安排：取消访谈，10月仍完成文本对读，11月对比藏品说明的叙述顺序，12月完成初稿。分析类别尚未确定，正文不要代拟。', 'T8': '只审这个独立文献综述短段，不代写，简要指出来源归因和论证问题。来源A摘要说：40名成人在步骤旁提示条件下，回查主要发生于步骤切换。来源B摘要说：36名成人面对文末提示时，部分人称查找需往返翻页，但未统计回查次数。底稿：‘A、B一致发现，文末提示会增加回查次数，因此已有研究已经证实提示位置决定阅读效率。’', 'T9': '只用本题原文核验后修改论文这一段，80字以内，只交改后这一段，不另附表或参考文献清单，沿用我已有的编号。原文[7]：12名受访者中8人称进度可见能减少反复咨询，4人仍会电话确认，访谈只询问体验。底稿：‘进度展示使所有受访者减少了咨询次数。[7] 作者据此认为，进度可见性可能为部分受访者判断是否继续询问提供线索。’', 'chain_scope': '请按论文段落分工只写当前一段，180字以内。前一段已交代两年数据来自归档邮件，本段评价转交频次是否下降：2014年36封归档邮件中12封有转交，2016年40封中5封有转交；2014年只保存已结案邮件，2016年保存全部邮件。下段才介绍归档制度变化经过。写好后请独立复核段落职责、逻辑、重复与语言，按意见修改，只交本段正文。'}

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
    candidates = [binaries/'codex.exe', *binaries.glob('*/codex.exe')]
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
    binding['prompt_prefix'] = '使用本目录 .agents/skills/chinese-academic-writing-assistant/SKILL.md。\n\n'
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
    binding['review_host'] = {'enabled': args.review_host, 'max_threads': 3 if args.review_host else None, 'max_depth': 1 if args.review_host else None, 'child_model': 'same selected writer model' if args.review_host else 'host defaults', 'child_usage': 'root JSON usage is not assumed to include child usage'}
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
                command[-1:-1]=['-c','features.multi_agent=true','-c','agents.max_threads=3','-c','agents.max_depth=1','-c',f'agents.default_subagent_model="{MODELS[index]}"']
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
