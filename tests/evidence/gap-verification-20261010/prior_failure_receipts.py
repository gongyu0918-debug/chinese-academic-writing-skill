from pathlib import Path
import json,re,hashlib
ROOT=Path('F:/Workspaces/chinese-academic-writing-skill')
OLD=ROOT/'.release/clarity-coverage-20261009'
HERE=Path(__file__).parent
rows=[]
for batch in ('baseline-R1','long-baseline'):
    binding=json.loads((OLD/batch/'binding.json').read_text(encoding='utf-8'))
    for r in json.loads((OLD/batch/'results.json').read_text(encoding='utf-8')):
        mi=binding['models'].index(r['model'])
        stem=f"m{mi}-{r['case']}-{r['arm']}-s{r['stage']}"
        p=Path(binding['runtime'])/(stem+'.stderr.txt')
        raw=p.read_bytes()
        match=re.search(r'failed to canonicalize CODEX_HOME',raw.decode('utf-8','replace'),re.I)
        rows.append({'batch':batch,'stem':stem,'returncode':r['returncode'],'invalid':r['invalid'],'stderr_sha256':hashlib.sha256(raw).hexdigest(),'exact_safe_excerpt':match.group(0) if match else None,'stderr_local_only':str(p)})
for batch in ('review-audit','review-R1'):
    for result in (OLD/batch).glob('*.result.json'):
        r=json.loads(result.read_text(encoding='utf-8'))
        stem=result.name.removesuffix('.result.json')
        p=Path(r['runtime'])/(stem+'.stderr.txt')
        raw=p.read_bytes()
        text=raw.decode('utf-8','replace')
        # Only emit bounded protocol fragments, never URLs, headers, credentials or full stderr.
        fragments=[m.group(0) for pattern in (r'Unexpected status 429',r'HTTP(?:/\d(?:\.\d)?)?\s+429',r'Too Many Requests') for m in re.finditer(pattern,text,re.I)]
        trace=OLD/batch/(stem+'.trace.jsonl')
        trace_raw=trace.read_bytes() if trace.exists() else b''
        trace_fragments=sorted(set(m.group(0) for m in re.finditer(r'exceeded retry limit, last status: 429 Too Many Requests',trace_raw.decode('utf-8','replace'),re.I)))
        rows.append({'batch':batch,'stem':stem,'returncode':r['returncode'],'configured_deadline_seconds':420,'stderr_sha256':hashlib.sha256(raw).hexdigest(),'exact_safe_excerpts':sorted(set(fragments)),'stderr_local_only':str(p),'visible_trace_sha256':hashlib.sha256(trace_raw).hexdigest(),'visible_trace_safe_excerpts':trace_fragments,'visible_trace_local_only':str(trace),'null_returncode_means_runner_timeout':r['returncode'] is None})
(HERE/'prior-failure-receipts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'startup_rows':sum(x['batch'] in ('baseline-R1','long-baseline') for x in rows),'canonicalize_fragments':sum(bool(x.get('exact_safe_excerpt')) for x in rows),'429_rows':sum(bool(x.get('visible_trace_safe_excerpts')) for x in rows),'timeout_rows':sum(bool(x.get('null_returncode_means_runner_timeout')) for x in rows)}))
