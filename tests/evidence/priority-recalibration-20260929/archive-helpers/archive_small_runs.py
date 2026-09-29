from pathlib import Path
import argparse, hashlib, json, shutil, random

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('name')
args=parser.parse_args()
src=root/args.source
dest=root/'tests/evidence/priority-recalibration-20260929'/args.name
assert not dest.exists()
assert (src/'results.json').is_file(), 'Run not complete'
dest.mkdir()
transforms=[]
for path in sorted(src.rglob('*')):
    if not path.is_file() or path.name.endswith('.stderr.txt'): continue
    relative=path.relative_to(src)
    target=dest/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    original=path.read_bytes()
    if path.name.endswith('.trace.jsonl'):
        kept=[]
        for line in original.decode('utf-8').splitlines():
            try: event=json.loads(line)
            except json.JSONDecodeError: continue
            if event.get('type') not in ('thread.started','turn.started','turn.completed','turn.failed','error','item.completed'):continue
            item=event.get('item',{})
            if item.get('type') in ('reasoning','reasoning_summary'):continue
            kept.append(event)
        data=('\n'.join(json.dumps(x,ensure_ascii=False) for x in kept)+'\n').encode('utf-8')
    else:data=original
    target.write_bytes(data)
    transforms.append({'path':relative.as_posix(),'original_sha256':hashlib.sha256(original).hexdigest(),'archive_sha256':hashlib.sha256(data).hexdigest(),'changed':original!=data})
(dest/'archive-transforms.json').write_text(json.dumps(transforms,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
binding=json.loads((src/'binding.json').read_text(encoding='utf-8'))
sessions=[]
for p in (Path(binding['runtime'])/'codex-profile/sessions').rglob('*.jsonl'):
    identity={};models=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        try: event=json.loads(line)
        except json.JSONDecodeError:continue
        if event.get('type')=='session_meta':
            identity={k:v for k,v in event['payload'].items() if k in ('id','timestamp','cwd','cli_version','model_provider','source')}
        if event.get('type')=='turn_context':
            model={k:v for k,v in event['payload'].items() if k in ('model','effort')}
            if model not in models: models.append(model)
    sessions.append({'identity':identity,'models':models,'raw_session_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(dest/'session-models.json').write_text(json.dumps(sessions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
results=json.loads((src/'results.json').read_text(encoding='utf-8'))
blind=root/'.release/priority-recalibration'/f'{args.name}-blind'
blind.mkdir()
mapping={};rng=random.Random('priority-recalibration-'+args.name)
valid=[]
for model in sorted(set(x['model'] for x in results)):
    packet=['# 匿名成稿审阅\n\n按每题完整请求和材料核对。X/Y标签每题独立随机；标签不表示同一版本。稿件包括原始前言和尾注，不做清洗。不要访问其他目录、映射或规则快照。\n']
    for case in binding['cases']:
        rows=[x for x in results if x['case']==case and x['model']==model]
        if len(rows)!=2 or any(x['invalid'] for x in rows):continue
        rng.shuffle(rows)
        pair=f'{args.name}-{len(mapping)+1}'
        packet.append(f'## {pair}\n\n原始请求与全部材料：\n\n{binding["cases"][case]}\n')
        mapping[pair]={}
        for label,row in zip(('X','Y'),rows):
            files=list(src.glob(f'm*-{case}-{row["arm"]}.result.json'))
            result_file=next(p for p in files if json.loads(p.read_text(encoding='utf-8'))['model']==model)
            final=result_file.with_name(result_file.name.replace('.result.json','.final.txt'))
            packet.append(f'### {label}\n\n{final.read_text(encoding="utf-8")}\n')
            mapping[pair][label]={'case':case,'model':model,'arm':row['arm'],'file':final.name}
        valid.append(pair)
    (blind/f'm{binding["models"].index(model)}.md').write_text('\n'.join(packet),encoding='utf-8')
(dest/'blind-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copytree(blind,dest/'blind')
print(json.dumps({'archive':str(dest),'blind':str(blind),'complete_pairs':len(valid),'sessions':len(sessions),'invalid':sum(bool(x['invalid']) for x in results)},ensure_ascii=False))
