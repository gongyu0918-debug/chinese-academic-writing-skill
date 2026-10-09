"""Archive visible research artifacts; never score writing or copy native profiles."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
LOCAL = ROOT / '.release/corpus-expansion-20261009'
OUT = LOCAL / 'export'
OUT.mkdir(exist_ok=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)

for name in ('CORPUS.md', 'candidate-rule.txt', 'numeric-rule.txt', 'pilot-tasks.json',
             'numeric-tasks.json', 'confirmation-tasks.json', 'numeric-r3-tasks.json',
             'pilot-review.md', 'numeric-review-R1.md', 'numeric-review-R1b.md',
             'numeric-review-R2.md', 'numeric-review-R2b.md', 'numeric-review-R3.md',
             'numeric-review-R3b.md', 'finance-reader.md', 'proposal-logistics-reader.md',
             'proposal-supplement-agent.md'):
    path = LOCAL / name
    if path.is_file():
        copy(path, OUT / name)

used = ['SKILL.md', 'references/academic-writing.md', 'references/anti-ai-writing.md', 'LICENSE.md']
totals = []
for batch in ('pilot-R1', 'numeric-R1', 'numeric-R2', 'numeric-R3'):
    source = LOCAL / batch
    target = OUT / batch
    target.mkdir(exist_ok=True)
    binding = json.loads((source / 'binding.json').read_text(encoding='utf-8'))
    copy(source / 'binding.json', target / 'binding.json')
    copy(source / 'runner-source.py', target / 'runner-source.py')
    rows = json.loads((source / 'results.json').read_text(encoding='utf-8'))
    copy(source / 'results.json', target / 'results.json')
    complete_manifest = []
    for arm in ('main', 'candidate'):
        snapshot = source / 'snapshots' / arm
        for path in sorted(snapshot.rglob('*')):
            if path.is_file():
                data = path.read_bytes()
                row = {'arm': arm, 'path': path.relative_to(snapshot).as_posix(), 'bytes': len(data), 'sha256': sha(data)}
                if path.suffix.lower() in ('.md', '.yaml', '.py', '.txt'):
                    row['newline_normalized_sha256'] = sha(data.decode('utf-8-sig').replace('\r\n', '\n').encode())
                complete_manifest.append(row)
        for name in used:
            copy(snapshot / name, target / 'snapshots' / arm / name)
    dump(target / 'full-snapshot-file-manifest.json', complete_manifest)
    before = (source / 'snapshots/main/references/academic-writing.md').read_text(encoding='utf-8-sig').splitlines(True)
    after = (source / 'snapshots/candidate/references/academic-writing.md').read_text(encoding='utf-8-sig').splitlines(True)
    (target / 'candidate.diff').write_text(''.join(difflib.unified_diff(before, after, fromfile='main/academic-writing.md', tofile='candidate/academic-writing.md')), encoding='utf-8')
    for row in rows:
        index = binding['models'].index(row['model'])
        stem = f"m{index}-{row['case']}-{row['arm']}"
        for suffix in ('.final.txt', '.result.json'):
            copy(source / (stem + suffix), target / (stem + suffix))
        # Keep only visible messages and execution metadata, never reasoning items.
        filtered = []
        for line in (source / (stem + '.trace.jsonl')).read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = event.get('type')
            item = event.get('item', {})
            if kind in ('thread.started', 'turn.started', 'turn.completed', 'turn.failed', 'error') or (kind in ('item.started', 'item.completed') and item.get('type') in ('agent_message', 'command_execution', 'web_search', 'error')):
                filtered.append(event)
        (target / (stem + '.trace.jsonl')).write_text(''.join(json.dumps(event, ensure_ascii=False) + '\n' for event in filtered), encoding='utf-8')
        snapshot = source / 'snapshots' / row['arm']
        prompt = '本轮使用下列完整冻结规则完成末尾用户请求。只根据这些规则及给定材料直接成稿，不调用任何工具、不读取文件、不联网、不委派；独立复核由另一会话执行。\n\n入口规则：\n' + (snapshot / 'SKILL.md').read_text(encoding='utf-8-sig') + '\n\n本任务唯一专项叶 academic-writing.md：\n' + (snapshot / 'references/academic-writing.md').read_text(encoding='utf-8-sig') + '\n\n本次文风任务的完整复核层：\n' + (snapshot / 'references/anti-ai-writing.md').read_text(encoding='utf-8-sig') + '\n\n用户请求：\n' + binding['cases'][row['case']]
        if sha(prompt.encode()) != row['prompt_sha256']:
            raise RuntimeError('Prompt archive mismatch: ' + stem)
        if sha((source / (stem + '.final.txt')).read_bytes()) != row['draft_sha256']:
            raise RuntimeError('Draft archive mismatch: ' + stem)
        (target / (stem + '.prompt.txt')).write_bytes(prompt.encode('utf-8'))
    runtime = Path(binding['runtime'])
    session_models = []
    for path in (runtime / 'codex-profile' / 'sessions').rglob('*.jsonl'):
        context_rows = []
        session_id = None
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get('payload', {})
            if event.get('type') == 'session_meta':
                session_id = payload.get('id')
            if event.get('type') == 'turn_context':
                fields = {k: payload.get(k) for k in ('model', 'model_provider', 'effort') if k in payload}
                if fields not in context_rows:
                    context_rows.append(fields)
        session_models.append({'session_id': session_id, 'context': context_rows})
    dump(target / 'session-models.json', session_models)
    totals.append({'batch': batch, 'calls': len(rows), 'pairs': len(rows) // 2,
                   'process_completed': sum(row['returncode'] == 0 for row in rows),
                   'execution_invalid_records': [row for row in rows if row['invalid']],
                   'quality_passes': None})

source_bytes = []
for name in ('bnu-mpa-cost-proposal', 'cau-herder-quant', 'applied-aas-patch',
             'applied-xlxb-ai', 'applied-jlakes-co2-http', 'tianjin-slp-archive',
             'tianjin-turboshaft-archive', 'tianjin-finance-archive', 'tianjin-logistics-archive'):
    receipt = json.loads((LOCAL / 'sources' / (name + '.receipt.json')).read_text(encoding='utf-8'))
    data = (LOCAL / 'sources' / (name + '.pdf')).read_bytes()
    if sha(data) != receipt['sha256']:
        raise RuntimeError('Source byte mismatch: ' + name)
    source_bytes.append({'id': name, 'url': receipt['url'], 'final_url': receipt.get('final_url'),
                         'bytes': len(data), 'sha256': sha(data), 'container_pages': receipt['pages'],
                         'download_receipt_status': receipt.get('status'),
                         'reading_status': 'See CORPUS.md; download receipt is not reading proof'})
dump(OUT / 'source-bytes.json', source_bytes)
dump(OUT / 'RUN-RECORD.json', {'baseline': '07f8a0ad405083ab1fc98d80cd1dd40ce4e3645e',
     'runtime_version': '0.1.7', 'batches': totals,
     'calls': sum(x['calls'] for x in totals), 'pairs': sum(x['pairs'] for x in totals),
     'input': 'Full frozen entry + ordinary leaf + anti-ai layer supplied inline in every call',
     'not_proven': ['autonomous routing', 'file loading', 'Hook integration', 'long manuscript behavior', 'statistical or engineering validity'],
     'quality_passes': None, 'python_purpose': 'Model invocation, PDF extraction, and artifact archiving only'})

session_dir = Path('C:/Users/admin/.codex/sessions/2026/10/09')
agent_ids = {'social-and-proposal': '01a11eba-560d-7890-8c09-da73edeccbba',
             'humanities-and-review': '01a11eba-573f-75e3-bedf-88fb26c72a90',
             'applied': '01a11eba-58cb-7431-b362-df7b044e2102',
             'independent-review': '01a11ed1-a797-7761-963f-7831d78bddb6',
             'proposal-supplement': '01a11ee3-00b1-7a03-a9e1-7e75443d6c37',
             'R3-review': '01a11ee6-d162-7652-8e86-4f039e081f44'}
agent_rows = []
for role, agent_id in agent_ids.items():
    files = list(session_dir.glob('*' + agent_id + '.jsonl'))
    contexts = []
    for path in files:
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get('type') == 'turn_context':
                payload = event.get('payload', {})
                item = {k: payload.get(k) for k in ('model', 'model_provider', 'effort') if k in payload}
                if item not in contexts:
                    contexts.append(item)
    agent_rows.append({'role': role, 'agent_id': agent_id, 'context_metadata': contexts,
                       'native_reasoning_archived': False})
dump(OUT / 'agent-models.json', agent_rows)
dump(OUT / 'REVIEW-STATUS.json', {
    'reading': {'papers_with_all_body_sections_read': 13, 'filled_proposals_read': 3,
                'references': 'Distribution and use only, not all references verified',
                'supplement_agent': {'id': agent_ids['proposal-supplement'],
                                     'status': 'errored', 'full_read_report_completed': False,
                                     'error': 'DataInspectionFailed on image input',
                                     'recovered_by': 'Main reviewer read full logistics proposal and inspected key pages'},
                'source_synthesis_audit': {'papers': 12, 'proposals': 2,
                                           'not_covered': ['B3 finance paper', 'P3 logistics proposal']}},
    'writing_review': {'pilot-R1': ['pilot-review.md'],
                       'numeric-R1': ['numeric-review-R1.md', 'numeric-review-R1b.md'],
                       'numeric-R2': ['numeric-review-R2.md', 'numeric-review-R2b.md'],
                       'numeric-R3': ['numeric-review-R3.md', 'numeric-review-R3b.md'],
                       'R3_blinding': 'Rule hidden in first pass; filenames identify arms, not fully anonymous',
                       'R3_rule_attribution': 'First reviewer subsequently read only the unique diff and rule',
                       'final_adjudication': 'Main reviewer checked materials and visible drafts; reviewer opinions are not ground truth'},
    'decision': 'Cancel both default rule additions; preserve research evidence only',
    'public_archive_excludes': ['Original PDFs and full source extractions', 'Native profiles',
                               'Hidden reasoning', 'Credentials']})
copy(Path(__file__), OUT / 'archive-source.py')
reader_reports = []
for name, ids, role in (
    ('social-agent.md', ['S1', 'S2', 'S3'], 'social-and-proposal'),
    ('humanities-agent.md', ['H1', 'H2', 'H3'], 'humanities-and-review'),
    ('applied-agent.md', ['A1', 'A2', 'A3'], 'applied'),
    ('proposal-pairs-agent.md', ['B1', 'B2', 'P1', 'P2'], 'social-and-proposal'),
    ('bnu-reader.md', ['M1'], 'main'),
    ('finance-reader.md', ['B3'], 'main'),
    ('proposal-logistics-reader.md', ['P3'], 'main'),
    ('source-synthesis-audit.md', ['S1', 'S2', 'S3', 'H1', 'H2', 'H3', 'A1', 'A2', 'A3', 'M1', 'B1', 'B2', 'P1', 'P2'], 'humanities-and-review'),
):
    data = (LOCAL / name).read_bytes()
    reader_reports.append({'local_report': name, 'source_ids': ids, 'reader_role': role,
                           'agent_id': agent_ids.get(role), 'sha256': sha(data),
                           'bytes': len(data), 'coverage': 'See CORPUS.md',
                           'public_report_included': (OUT / name).is_file(),
                           'local_original_retained': True})
dump(OUT / 'SOURCE-READERS.json', reader_reports)
manifest = []
for path in sorted(OUT.rglob('*')):
    if not path.is_file() or path.name in ('MANIFEST.json', 'LIFECYCLE.json'):
        continue
    data = path.read_bytes()
    row = {'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)}
    if path.suffix.lower() in ('.md', '.txt', '.json', '.jsonl', '.py', '.diff'):
        row['newline_normalized_sha256'] = sha(data.decode('utf-8-sig').replace('\r\n', '\n').encode('utf-8'))
    manifest.append(row)
dump(OUT / 'MANIFEST.json', {'excluded': ['MANIFEST.json', 'LIFECYCLE.json'], 'files': manifest})
print(json.dumps({'calls_archived': sum(x['calls'] for x in totals), 'pairs': sum(x['pairs'] for x in totals),
                  'sources_byte_bound': len(source_bytes), 'path': str(OUT)}, ensure_ascii=False))
