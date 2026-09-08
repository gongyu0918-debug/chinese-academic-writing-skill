"""One-off writing experiment transport; exact inputs and first responses retained."""
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MODELS = {
    'alibaba2': 'alibaba-token-plan-2/deepseek-v4-flash-0731',
    'ollama': 'ollama-cloud/deepseek-v4-flash:0731',
    'minimax': 'minimax-cn/MiniMax-M3',
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def lane(provider, cases, args):
    for case in cases:
        out = ROOT / 'raw' / args.arm / provider / case['task_id']
        if out.exists():
            print(json.dumps({'existing_preserved': str(out)}), flush=True)
            continue
        out.mkdir(parents=True)
        files = ['SKILL.md', 'references/' + case['leaf']]
        rules = '\n\n'.join((args.skill_root / p).read_text(encoding='utf-8') for p in files)
        payload = {'model': MODELS[provider], 'input': [{'role': 'developer', 'content': rules},
                   {'role': 'user', 'content': case['request']}], 'tools': [],
                   'reasoning': {'effort': 'max'}, 'max_output_tokens': args.max_output_tokens, 'stream': False}
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        (out / 'request.json').write_bytes(data)
        record = {'arm': args.arm, 'task_id': case['task_id'], 'kind': case['kind'],
                  'provider': provider, 'requested_model': MODELS[provider], 'reasoning_effort': 'max',
                  'retry_count': args.attempt, 'request_sha256': digest(data),
                  'skill_files': {p: digest((args.skill_root / p).read_bytes()) for p in files}}
        start = time.monotonic()
        try:
            req = urllib.request.Request('http://127.0.0.1:10100/v1/responses', data=data,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=1000) as response:
                raw = response.read()
            (out / 'response.json').write_bytes(raw)
            obj = json.loads(raw)
            final = ''.join(p.get('text', '') for item in obj.get('output', [])
                            if item.get('type') == 'message' for p in item.get('content', [])
                            if p.get('type') == 'output_text')
            (out / 'final.md').write_text(final, encoding='utf-8')
            record.update(status=obj.get('status'), returned_model=obj.get('model'),
                          usage=obj.get('usage'), final_chars=len(final),
                          final_sha256=digest(final.encode('utf-8')),
                          response_sha256=digest(raw),
                          valid=obj.get('status') == 'completed' and bool(final.strip())
                          and all(x.get('type') in ('reasoning', 'message') for x in obj.get('output', [])))
        except Exception as exc:
            record.update(valid=False, error=type(exc).__name__ + ': ' + str(exc))
        record['seconds'] = round(time.monotonic() - start, 2)
        (out / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(record, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--arm', required=True)
    p.add_argument('--skill-root', type=pathlib.Path, required=True)
    p.add_argument('--cases', type=pathlib.Path, default=ROOT / 'cases.json')
    p.add_argument('--provider', action='append', choices=MODELS)
    p.add_argument('--task', action='append')
    p.add_argument('--max-output-tokens', type=int, default=14000)
    p.add_argument('--attempt', type=int, default=0)
    args = p.parse_args()
    cases = json.loads(args.cases.read_text(encoding='utf-8'))['cases']
    if args.task:
        cases = [case for case in cases if case['task_id'] in args.task]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(lane, provider, cases, args) for provider in (args.provider or list(MODELS))]
        for future in futures:
            future.result()
