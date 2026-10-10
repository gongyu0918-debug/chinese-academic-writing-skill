from pathlib import Path
import json

HERE = Path(__file__).parent
sections = {
 'kdense-literature':'Core Workflow; Search Strategy; Records, Reports, and Studies; Common Pitfalls',
 'kdense-peer-review':'Full SKILL: intake, claim/evidence, statistics, proportional comments and limits',
 'kdense-citations':'SKILL workflow, metadata enrichment, validation and integration/limits',
 'marazii-peer-review':'Selected sections: Long-work handling; Draft stage; Steps 3-5; Draft mode. Not full 102KB file.',
 'snl-survey':'Selected sections: Triage depth; Deepen evidence/craft; Synthesize and final corpus check. Not deep reference files.',
 'besser-review':'Full research-paper-review SKILL',
 'docxology-review':'Full academic-paper-reviewer SKILL; no linked infrastructure or reference audit',
 'victor-citation':'Full citation_rules.md, including Secondary Citation; no A-E definition found in this file',
 'ecylmz-audit':'Full research-integrity-audit SKILL; deep protocol references not opened',
 'paperqa-prompts':'Agent full file; main re-read citation/QA/summary/iteration constants; no code executed',
 'storyengine-system':'Agent full file; main selected Core Directives, phases and contradiction/state boundaries',
 'storyengine-draft':'Full draft-chapter prompt; not a scientific writing model',
 'xiao-proposal':'Full proposal-writing-rules; no CNKI/browser integration run',
 'xiao-review':'Full review-writing-rules; no full workflow product test',
 'yanlin-writing':'Agent full SKILL; main selected discipline/workflow/humanization/checklist rules',
 'yanlin-social':'Agent full template; main re-read chapter and report template selections',
 'renzo-standardizer':'Full fork SKILL; linked workflows not inspected beyond the two named files',
 'renzo-style':'Full AIGC style-governance file; referenced upstream not re-read',
 'renzo-gates':'Full quality-gates file; no scripts executed'
}
rows=[]
for p in sorted((HERE/'sources').glob('*.receipt.json')):
    row=json.loads(p.read_text(encoding='utf-8'))
    if row['id'] not in sections: continue
    row['rule_reading_completed']=True
    row['read_scope']=sections[row['id']]
    row['competitor_effectiveness_verified']=False
    row['license_check']='GitHub repository metadata; not full license interpretation'
    row.pop('local_file',None)
    rows.append(row)
assert len(rows)==19
(HERE/'SOURCE-LEDGER.json').write_bytes((json.dumps({'date_beijing':'2026-10-10','project_families':12,'pinned_rule_files':19,'count_scope':'Rules read in full or specified sections; fork/upstream counted once; not full product evaluations','sources':rows},ensure_ascii=False,indent=2)+'\n').encode())
print('19 file locators, 12 project families; no quality score.')
