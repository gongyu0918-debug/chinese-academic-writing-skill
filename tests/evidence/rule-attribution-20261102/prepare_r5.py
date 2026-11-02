"""Prepare the bounded follow-up without changing any frozen rule bytes."""
from pathlib import Path
import json
import hashlib

stage = Path(__file__).resolve().parent
root = stage.parent.parent
prior = json.loads((root / 'tests/evidence/rule-tuning-20261102/R4/binding.json').read_text(encoding='utf-8-sig'))['spec']
new = {
    'leaf': 'academic-writing',
    'requests': ['以下为虚构论文的局部润色测试。只改【正文】中的一段，可删冗余并修复句法，保留数字、来源ID、研究状态与有限解释，只交正文。\n【正文】\n而这并不是说完全没有说明作用，也不能说能保证一切。24次课程预约操作记录中，15次先打开课程筛选栏，9次直接使用搜索框[K6]。本文据此认为，筛选栏可能是部分使用者缩小课程查找范围的起点。另一时段的观察仍在进行，相关记录尚未纳入本段。这样的理解不意味着每个人都要用筛选栏，也不能证明学生的成绩已经提高，更不能说明所有选课平台都能减轻教师负担。\n【背景，非正文】\n本段只讨论上述24次记录中的课程查找起点。材料没有测学生成绩与教师工作量。原稿开头没有需要保留的前文转折；允许正常语言修复，不增原因或新结论。']
}
cases = {}
for name, case in [('E1_fragment', prior['E1_fragment_r1']), ('E3_course_search', new)]:
    for repeat in (1, 2):
        cases[f'{name}_r{repeat}'] = case
target = stage / 'R5-attribution.json'
assert not target.exists()
data = (json.dumps(cases, ensure_ascii=False, indent=2) + '\n').encode()
target.write_bytes(data)
candidate = root / 'tests/evidence/rule-tuning-20261102/R4/snapshots/candidate/references/anti-ai-writing.md'
manifest = {'spec_sha256': hashlib.sha256(data).hexdigest(), 'candidate_anti_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(), 'planned_calls': 16, 'unchanged_candidate_from': 'R4/v3/C2', 'original_E1_request_unchanged': cases['E1_fragment_r1'] == prior['E1_fragment_r1']}
(stage / 'R5-prepared.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode())
print(json.dumps(manifest))
