from pathlib import Path
import argparse,json,hashlib
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('id');parser.add_argument('name');args=parser.parse_args()
paths=list((Path.home()/'.codex/sessions/2026/09/29').glob('*'+args.id+'.jsonl'))
assert len(paths)==1
data=paths[0].read_bytes(); finals=[]; models=[]; identity={}
for line in data.decode('utf-8').splitlines():
    try:e=json.loads(line)
    except json.JSONDecodeError:continue
    p=e.get('payload',{})
    if e.get('type')=='session_meta':identity={k:v for k,v in p.items() if k in ('id','timestamp','cwd','cli_version','model_provider','source')}
    if e.get('type')=='turn_context':
        m={k:v for k,v in p.items() if k in ('model','effort')}
        if m not in models:models.append(m)
    if e.get('type')=='event_msg' and p.get('type')=='task_complete' and p.get('last_agent_message'):
        finals.append(p['last_agent_message'])
assert finals,'No completed visible final'
out=root/'tests/evidence/priority-recalibration-20260929/reviews';out.mkdir(exist_ok=True)
(out/(args.name+'.md')).write_text('\n\n---\n\n'.join(finals)+'\n',encoding='utf-8',newline='\n')
(out/(args.name+'-session.json')).write_text(json.dumps({'identity':identity,'models':models,'raw_sha256':hashlib.sha256(data).hexdigest(),'visible_final_count':len(finals)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'id':args.id,'models':models,'visible_finals':len(finals)},ensure_ascii=False))
