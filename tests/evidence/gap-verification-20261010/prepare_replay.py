from pathlib import Path
import json
HERE=Path(__file__).parent
first=json.loads((HERE/'source-scope-tasks.json').read_text(encoding='utf-8'))
second=json.loads((HERE/'confirmation-tasks.json').read_text(encoding='utf-8'))
cases={'A_raw_interviews':first['A_raw_interviews'],'C_raw_conflict':first['C_raw_conflict'],'L_existing_target':second['L_existing_target']}
(HERE/'replay-tasks.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'replay-plan.json').write_text(json.dumps({'purpose':'Replay observed material-misread and candidate-only factual/delivery problems with unchanged candidate and exact tasks. This is repetition, not new corpus coverage.','cases':list(cases),'selected_before_replay':['R1 A baseline missed supplied records; candidate inferred different locations','R1 C candidate denied supplied target','R2 L baseline denied supplied sections'],'stop':'One exact replay batch. Preserve all failures; no posthoc prompt coaching or repeated trials until pass. Candidate stays out of product without stable benefit and acceptable boundary behavior.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
