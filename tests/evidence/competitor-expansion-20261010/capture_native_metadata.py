"""Capture declared visible session metadata, never internal reasoning."""
from pathlib import Path
import json

HERE=Path(__file__).parent
sessions=Path('C:/Users/admin/.codex/sessions/2026/10/10')
ids=['01a12386-a5e2-7072-b7a9-cbd4fe95a76e','01a12386-a760-7ed2-ad33-01e4b135b71e',
     '01a12390-17a8-79c3-a1d9-1ba65a4f6f48','01a12390-192f-7281-b0a2-adadf6abe523','01a12390-1ad6-75e1-b4cd-69c3afee0f3f',
     '01a12394-697e-78b3-a728-12b615e1eb15']
rows=[]
for identifier in ids:
    row={'agent_id':identifier,'model_contexts':[],'visible_final_messages':[],'metadata_found':False}
    for path in sessions.glob('*'+identifier+'*.jsonl'):
        row['metadata_found']=True
        for line in path.read_text(encoding='utf-8').splitlines():
            try:e=json.loads(line)
            except json.JSONDecodeError:continue
            p=e.get('payload',{})
            if e.get('type')=='turn_context':
                context={k:p.get(k) for k in ('model','model_provider','effort') if k in p}
                if context not in row['model_contexts']:row['model_contexts'].append(context)
            if e.get('type')=='event_msg' and p.get('type')=='task_complete':
                visible=p.get('last_agent_message')
                if isinstance(visible,str) and visible and visible not in row['visible_final_messages']:
                    row['visible_final_messages'].append(visible)
            if e.get('type')=='response_item' and p.get('type')=='message' and p.get('role')=='assistant' and p.get('phase')=='final':
                visible='\n'.join(c.get('text','') for c in p.get('content',[]) if c.get('type')=='output_text')
                if visible and visible not in row['visible_final_messages']:row['visible_final_messages'].append(visible)
    rows.append(row)
(HERE/'native-session-models.json').write_bytes((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode())
for row in rows: print(json.dumps({**{k:row[k] for k in ('agent_id','metadata_found','model_contexts')},'final_count':len(row['visible_final_messages'])},ensure_ascii=False))
