from pathlib import Path
import json

root = Path(__file__).parent
out = root / 'public'
records = json.loads((out / 'native-visible.json').read_text(encoding='utf-8'))
coverage = {
    '01a124c7-d9c7-7111-a401-66ba4b26ab3d': ('Harvey', 'Old baseline priority audit', 0, 'completed', 'No final candidate audit assigned'),
    '01a124d6-8e0b-7900-a12f-4d60e977ec95': ('Pasteur', 'R1 blind pairs', 11, 'completed', ''),
    '01a124d9-8bba-7880-b6a7-14f22517e0fb': ('Curie', 'R2 blind pairs', 6, 'completed', ''),
    '01a124db-242a-7d70-815b-06be9fc61903': ('Bohr', 'R3 blind pairs and final rule audit', 4, 'partial', 'All four pairs covered; three final rules not read'),
    '01a124e7-f70b-7692-9570-c4d804cd0dc9': ('Helmholtz', 'Final three rules and source notes', 0, 'incomplete_closed', 'Closed while running; no final report returned; coverage not inferred from tool calls'),
    '01a124ea-3152-7962-8495-5ceaef616eed': ('Mendel', 'R5 blind pairs', 4, 'completed', ''),
}
result = []
for record in records:
    name, task, pairs, status, limitation = coverage[record['agent_id']]
    result.append({'agent_id': record['agent_id'], 'name': name, 'task': task, 'covered_pairs': pairs,
                   'status': status, 'closed': True, 'model_context': record['actual_context'],
                   'final_report_received': record['is_final_report'], 'limitation': limitation})
(out / 'REVIEW-STATUS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'completed_blind_pairs': sum(r['covered_pairs'] for r in result),
                  'final_rule_independent_pass': None, 'all_agents_closed': True}))
