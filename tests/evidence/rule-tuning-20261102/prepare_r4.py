"""Freeze the prespecified isolated candidate and test requests, without grading."""
from pathlib import Path
import json
import shutil
import hashlib

root = Path(__file__).resolve().parent
repo = root.parent.parent
candidate = root / 'candidate-v3-c2'
shutil.copytree(repo / '.release/worktrees/rule-tuning-20261102/chinese-academic-writing-assistant', candidate)
r1 = json.loads((root / 'R1.json').read_text(encoding='utf-8-sig'))
cases = {k: v for k, v in r1.items() if k.startswith(('D2_', 'D3_'))}
new = {
    'E1_fragment': {
        'leaf': 'academic-writing',
        'requests': ['以下为虚构论文的局部润色测试。只改【正文】中的一段，可删冗余并修复句法，保留数字、来源ID、研究状态与有限解释，只交正文。\n【正文】\n但这并不是不能说明任何情况，也不能说能保证全部事情。16份窗口取号记录中，10份在查询屏后直接取号，6份转去询问工作人员[T4]。本文据此认为，查询屏可能是部分使用者确认取号入口的线索。相邻窗口的观察还在进行，相关记录尚未纳入本段。上述理解并不意味着每个人都必须看屏幕，更不能证明大厅满意度已经提高，也不说明所有政务服务都能提速。\n【背景，非正文】\n本段只讨论上述16份记录中的入口确认。材料没有测满意度与总体办理时长。原稿开头没有需要保留的前文转折；允许正常语言修复，不增原因或新结论。']
    },
    'E2_review_scope': {
        'leaf': 'academic-writing',
        'requests': ['以下为虚构方法段。只审不改，严格按“位置—问题—建议”给出有材料依据的意见，不提供替换句。\n【原稿】\n本研究使用经研究者人工复核的61份票据记录[A7]。扫描识别仅用于寻找候选日期，最终日期以票据原件为准。另有7份因纸张破损而无法确认日期，已从月份分布比较中排除；记录不能用于计算个体消费频率。这样的处理不意味着任何电子识别软件都不可信，也不能保证所有商户的记账质量，更不能代表所有年份的消费变化。\n【材料和审查范围，非正文】\n本段交代实际取数方法与证据范围。票据没有可用的个人标识；月份分布比较只使用可确认日期的记录，不比较不同年份。软件评价与商户记账质量不是本研究对象。重点审查方法必要限定与无关兜底，保留研究者人工复核这一来源归属，不作外部来源认证。']
    }
}
for name, case in new.items():
    for repeat in (1, 2):
        cases[f'{name}_r{repeat}'] = case
data = (json.dumps(cases, ensure_ascii=False, indent=2) + '\n').encode()
(root / 'R4-c2.json').write_bytes(data)
binding = {'candidate': 'v3-c2', 'spec_sha256': hashlib.sha256(data).hexdigest(),
           'anti_ai_sha256': hashlib.sha256((candidate / 'references/anti-ai-writing.md').read_bytes()).hexdigest(),
           'requests': len(cases), 'planned_calls': len(cases) * 4,
           'only_runtime_delta_from_baseline': 'references/anti-ai-writing.md'}
(root / 'R4-prepared.json').write_bytes((json.dumps(binding, indent=2) + '\n').encode())
print(json.dumps(binding))
