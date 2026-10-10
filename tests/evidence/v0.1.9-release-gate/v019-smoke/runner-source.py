"""Run fresh native writing sessions; archive visible results, never grade semantics."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
HERE = Path(__file__).parent
# Runtime stays in ignored staging; only visible frozen evidence is committed.
MODELS = ['alibaba-token-plan-responses/qwen3.8-flash', 'ollama-cloud/glm-5.3-flash']
CLI = Path('C:/Users/admin/AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe')
CATALOG = Path('C:/Users/admin/.codex/opencodex-catalog.json')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--candidate-dir')
    parser.add_argument('--models', nargs='+', type=int, default=[0, 1])
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding='utf-8-sig'))
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    commit = subprocess.check_output(['git', 'rev-parse', 'v0.1.8^{}'], cwd=ROOT, text=True).strip()
    snapshots = {'main': out / 'snapshots/main'}
    shutil.copytree(ROOT / '.release/v019-smoke-baseline', snapshots['main'], ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if args.candidate_dir:
        snapshots['candidate'] = out / 'snapshots/candidate'
        shutil.copytree(Path(args.candidate_dir), snapshots['candidate'], ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    runtime = Path(tempfile.mkdtemp(prefix=out.name + '-', dir=HERE))
    profile = runtime / 'native-profile'
    profile.mkdir()
    (profile / 'config.toml').write_bytes(b'approval_policy = "never"\nsandbox_mode = "workspace-write"\nproject_doc_max_bytes = 0\n[windows]\nsandbox = "unelevated"\n')
    env = dict(os.environ, CODEX_HOME=str(profile), OPENAI_API_KEY='opencodex-loopback', CODEX_API_KEY='opencodex-loopback')
    actual_catalog = json.loads(CATALOG.read_text(encoding='utf-8-sig'))
    selected = [m for m in actual_catalog['models'] if m.get('slug') in MODELS]
    dump(out / 'selected-catalog-metadata.json', {'catalog_sha256': sha(CATALOG.read_bytes()), 'models': [{k:m.get(k) for k in ('slug','display_name','supported_reasoning_levels','default_reasoning_level')} for m in selected]})
    dump(out / 'binding.json', {'baseline_commit': commit, 'models': [MODELS[i] for i in args.models],
         'effort': 'max', 'runtime': str(runtime), 'spec': spec,
         'cli_version': subprocess.check_output([str(CLI), '--version'], text=True).strip(),
         'input_mode': 'Full routed rules inline, new native session each step; previous visible output carried as state',
         'not_proven': ['Autonomous file loading', 'Hook integration', 'Whole thesis or submission writing'],
         'runner_sha256': sha(Path(__file__).read_bytes())})
    shutil.copyfile(__file__, out / 'runner-source.py')
    def sequence(index, case_id, case):
        results = []
        arms = list(snapshots)
        if index % 2:
            arms.reverse()
        for arm in arms:
            previous = ''
            for stage, user_request in enumerate(case['requests'], 1):
                stem = f'm{index}-{case_id}-{arm}-s{stage}'
                work = runtime / stem
                work.mkdir()
                final = out / (stem + '.final.txt')
                files = ['SKILL.md', 'references/' + case['leaf'] + '.md']
                if case.get('format') and (snapshots[arm] / 'references/academic-text-format.md').exists():
                    files.append('references/academic-text-format.md')
                if case.get('long'):
                    files.append('references/long-form-consistency.md')
                if case.get('style', True):
                    files.append('references/anti-ai-writing.md')
                parts = ['使用以下完整冻结规则完成用户任务。只依据规则与给定材料，不调用工具、不联网、不委派；独立复核由另一个会话完成。']
                for name in files:
                    parts.append(name + '：\n' + (snapshots[arm] / name).read_text(encoding='utf-8-sig'))
                if previous:
                    parts.append('前一独立会话保存的交付稿与工作状态（恢复时仍须核对本轮最新版材料）：\n' + previous)
                parts.append('用户任务：\n' + user_request)
                prompt = '\n\n'.join(parts)
                (out / (stem + '.prompt.txt')).write_bytes(prompt.encode())
                command = [str(CLI), 'exec', '--skip-git-repo-check', '-C', str(work), '-m', MODELS[index],
                    '-c', 'approval_policy="never"', '-c', 'features.plugins=false', '-c', 'features.apps=false',
                    '-c', 'features.memories=false', '-c', 'project_doc_max_bytes=0', '-c', 'model_reasoning_effort="max"',
                    '-c', 'openai_base_url="http://127.0.0.1:10100/v1"', '-c', f'model_catalog_json="{CATALOG.as_posix()}"',
                    '--json', '--output-last-message', str(final), '-']
                print('START ' + stem, flush=True)
                started = time.monotonic()
                try:
                    done = subprocess.run(command, input=prompt, text=True, encoding='utf-8', errors='replace',
                        capture_output=True, timeout=args.timeout, cwd=work, env=env)
                    code, stdout, stderr = done.returncode, done.stdout, done.stderr
                except subprocess.TimeoutExpired as exc:
                    code = None
                    stdout = exc.stdout or b''
                    stderr = exc.stderr or b''
                    if isinstance(stdout, bytes): stdout = stdout.decode('utf-8', 'replace')
                    if isinstance(stderr, bytes): stderr = stderr.decode('utf-8', 'replace')
                events = []
                for line in stdout.splitlines():
                    try: events.append(json.loads(line))
                    except json.JSONDecodeError: pass
                # Store only visible messages and execution metadata.
                visible = [e for e in events if e.get('type') in ('thread.started', 'turn.started', 'turn.completed', 'turn.failed', 'error')
                    or (e.get('type') in ('item.started', 'item.completed') and e.get('item', {}).get('type') in ('agent_message', 'command_execution', 'web_search', 'error'))]
                (out / (stem + '.trace.jsonl')).write_bytes(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in visible).encode())
                (runtime / (stem + '.stderr.txt')).write_bytes(stderr.encode())
                final_bytes = final.read_bytes() if final.exists() else b''
                invalid = []
                if code != 0: invalid.append('timeout' if code is None else 'exit_' + str(code))
                if not final_bytes.strip(): invalid.append('missing_final')
                calls = [e['item'] for e in events if e.get('type') == 'item.completed' and e.get('item', {}).get('type') in ('command_execution', 'web_search')]
                if calls: invalid.append('unexpected_tool_use')
                thread_ids = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
                result = {'model': MODELS[index], 'effort': 'max', 'case': case_id, 'arm': arm, 'stage': stage,
                    'returncode': code, 'invalid': invalid, 'thread_ids': thread_ids,
                    'seconds': round(time.monotonic() - started, 2), 'prompt_sha256': sha(prompt.encode()),
                    'draft_sha256': sha(final_bytes), 'rules_loaded_inline': files, 'prior_output_sha256': sha(previous.encode()) if previous else None,
                    'quality_pass': None, 'usage': [e.get('usage') for e in events if e.get('type') == 'turn.completed']}
                dump(out / (stem + '.result.json'), result)
                results.append(result)
                print('END ' + stem + ' invalid=' + repr(invalid), flush=True)
                if invalid:
                    break
                previous = final_bytes.decode('utf-8-sig').replace('\r\n', '\n')
                if case.get('long'):
                    (work / 'saved-visible-state.md').write_bytes(previous.encode())
        return results
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(sequence, i, name, case) for i in args.models for name, case in spec.items()]
        rows = [row for future in futures for row in future.result()]
    dump(out / 'results.json', rows)
    session_rows = []
    for path in (profile / 'sessions').rglob('*.jsonl'):
        meta = {'file_name': path.name, 'context': []}
        for line in path.read_text(encoding='utf-8').splitlines():
            try: e = json.loads(line)
            except json.JSONDecodeError: continue
            p = e.get('payload', {})
            if e.get('type') == 'session_meta': meta['session_id'] = p.get('id')
            if e.get('type') == 'turn_context':
                m = {k:p.get(k) for k in ('model', 'model_provider', 'effort') if k in p}
                if m not in meta['context']: meta['context'].append(m)
        session_rows.append(meta)
    dump(out / 'session-models.json', session_rows)
    print(json.dumps({'calls': len(rows), 'execution_invalid': sum(bool(r['invalid']) for r in rows), 'quality_passes': None}), flush=True)

if __name__ == '__main__':
    run()
