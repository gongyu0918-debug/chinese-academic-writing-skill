from pathlib import Path
import json, hashlib
root=Path(__file__).parent
out=root/'public'
out.mkdir(exist_ok=True)
sessions=Path('C:/Users/admin/.codex/sessions/2026/10/10')
ids=['01a124c7-d9c7-7111-a401-66ba4b26ab3d','01a124d6-8e0b-7900-a12f-4d60e977ec95','01a124d9-8bba-7880-b6a7-14f22517e0fb','01a124db-242a-7d70-815b-06be9fc61903','01a124e7-f70b-7692-9570-c4d804cd0dc9','01a124ea-3152-7962-8495-5ceaef616eed']
items=[]
for agent in ids:
 matches=list(sessions.glob('*'+agent+'.jsonl'))
 record={'agent_id':agent,'actual_context':[], 'visible_messages':[], 'read_actions':[]}
 if matches:
  for line in matches[0].read_text(encoding='utf-8').splitlines():
   try:e=json.loads(line)
   except json.JSONDecodeError: continue
   p=e.get('payload',{})
   if e.get('type')=='turn_context':
    metadata={k:p[k] for k in ('model','model_provider','effort') if k in p}
    if metadata not in record['actual_context']:record['actual_context'].append(metadata)
   if e.get('type')=='response_item' and p.get('type')=='message' and p.get('role')=='assistant' and p.get('phase') in ('commentary','final'):
    texts=[c.get('text','') for c in p.get('content',[]) if c.get('type')=='output_text']
    if texts:record['visible_messages'].append({'phase':p.get('phase'), 'text':'\n'.join(texts)})
   if e.get('type')=='event_msg' and p.get('type')=='task_complete' and p.get('last_agent_message'):
    message={'phase':'final','text':p['last_agent_message']}
    if message not in record['visible_messages']:record['visible_messages'].append(message)
   if e.get('type')=='response_item' and p.get('type')=='function_call':
    record['read_actions'].append({'name':p.get('name'),'call_id':p.get('call_id')})
 record['is_final_report']=any(m.get('phase')=='final' for m in record['visible_messages'])
 items.append(record)
(out/'native-visible.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'agent':r['agent_id'],'final_phase':r['is_final_report'],'messages':len(r['visible_messages']),'model':r['actual_context']} for r in items],ensure_ascii=False))
