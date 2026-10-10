"""Freeze independently scoped prompt candidates and construct task packets."""
from pathlib import Path
import json, shutil

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
HERE = Path(__file__).parent
source = ROOT / 'chinese-academic-writing-assistant'
rules = {
 'review': ('references/academic-writing.md', '- 按入口统一审稿接口列问题，不重写被审文本。', '- 按入口统一审稿接口列问题，不重写被审文本。\n- 审稿建议与本轮任务、稿件阶段及中心判断相称；材料未报告某项不等于研究没有开展。能用收窄结论、澄清或必要限定解决的问题，不强索不影响当前判断的新研究；确有中心论断缺口时仍指出所需证据，不用篇幅或阶段替它免责。'),
 'reports': ('references/academic-literature-review.md', '- 综合证据时回溯原始研究：对同一结果的多次转述不增加独立证据，准确转述仍可按其来源使用；采用相同方法但基于独立材料或样本的新研究分别判断，不因方法相同合并。', '- 综合证据时回溯原始研究：对同一结果的多次转述不增加独立证据，准确转述仍可按其来源使用；采用相同方法但基于独立材料或样本的新研究分别判断，不因方法相同合并。同一研究的预印本、正式发表与后续报告分别保留来源及各自支持内容；有材料确认样本重叠时，不把报告篇数当独立研究数；仅作者或方法相同不能判定重叠。'),
 'statistics': ('references/academic-writing.md', '- 结论强度随证据收缩；只有论证关系需要时才设置章节收束或过渡，不重复已写边界。', '- 结论强度随证据收缩；只有论证关系需要时才设置章节收束或过渡，不重复已写边界。\n- 统计结果按原材料的检验与结论转述：“未显著”不等于“没有效应”或“等效”。材料已有等效界值、对应分析和明确结论时，可保留其限定范围内的等效结论；不自行补检验、设界值或重算统计有效性。')
}
for key, (name, old, new) in rules.items():
    target = HERE / 'candidates' / key
    if target.exists():
        raise SystemExit('Refuse replacing candidate ' + key)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    p = target / name
    value = p.read_text(encoding='utf-8-sig')
    if value.count(old) != 1: raise SystemExit('Anchor is not unique: ' + name)
    p.write_bytes(value.replace(old, new).encode('utf-8'))
    (HERE / (key+'-rule.txt')).write_bytes(new.encode('utf-8'))

cases = {
 'review': {
  'A_narrow_history': {'leaf':'academic-writing','style':False,'requests':['只审课程论文中一个结果段，不改稿，不联网；按位置、严重度、问题、依据、修改建议给真实问题，没有问题可以说明。本文任务仅比较1934与1935年一份地方校刊中活动名称，不推论全国教育制度、政策效果或活动规模。已读材料为校刊两年目录，1934年目录用“读书会”，1935年目录用“读书讨论会”。目标段：“两年目录所用活动名称不同，1934年为‘读书会’，1935年为‘读书讨论会’[D1][D2]。这一名称变化只能反映所读两份目录的表述，尚不能说明实际活动形式是否变化。”文中未报告访谈、计量分析与全国样本；其他章节不在本轮范围。']},
  'B_central_overclaim': {'leaf':'academic-writing','style':False,'requests':['只审硕士论文的讨论段，不改稿，不联网；按位置、严重度、问题、依据、修改建议输出。给定记录O3来自一个服务点：5次办事中4次由工作人员代为操作，1次由当事人独立操作；只记录当次操作主体，没有前后能力测量。目标段：“上述观察已证明该服务点居民长期数字能力显著提升[O3]。”其他章节未提供。请围绕这个中心判断审查。']}
 },
 'reports': {
  'C_same_study': {'leaf':'academic-literature-review','style':False,'requests':['据材料修改独立叙述性综述一段，只交改稿，不联网，保留P1/P2/P3。P1为研究T的预印本摘要：2022年同一服务点招募80人，结果是求助来源与当次办妥有关。P2为研究T正式论文摘要：明确沿用P1的同一80人样本和同一结果，补充讨论限制；并无新增参与者或新测量。P3为研究U的论文摘要：2023年另一服务点独立招募75人，用相同方法得同方向关联。三份摘要均已读且文献身份无冲突。底稿：“三项独立研究都证明帮助提升长期能力，证据因而三次获得复制[P1][P2][P3]。”本段只比较当次办妥与求助来源，不作方法学评分或PRISMA计数。']},
  'D_independent_unknown': {'leaf':'academic-literature-review','style':False,'requests':['据三份已读摘要写一段叙述性综述，只交正文，保留U1/U2/U3，不联网。U1和U2作者相同、问卷方法相同，但摘要未给队列名称、地点、招募日期或样本对应关系，无法判定是否同一研究。U1报告求助来源与当次办妥有关，U2只报告参与者的帮助满意度。U3使用同样问卷方法，摘要明确为另一地点独立招募的64人样本，报告求助来源与当次办妥有关。说明当前证据能比较什么，不替U1/U2判定重叠、不因方法相同合并U3、不虚构独立研究总数或领域共识。']}
 },
 'statistics': {
  'E_nonsignificant': {'leaf':'academic-writing','style':False,'requests':['据作者提供的分析摘要修改论文结果段，只交改稿，不联网，不重新分析。摘要S1：问卷两组平均分差0.8分，95%置信区间为-1.2至2.8分，双侧差异检验p=0.43；作者的统计结论为本次检验未达到显著水平，没有开展等效或非劣分析。底稿：“两组完全相同，该安排没有任何效应，两种办法已经证明等效[S1]。”保留数字与来源ID，仅准确呈现作者已给结论。']},
  'F_reported_equivalence': {'leaf':'academic-writing','style':False,'requests':['据作者已提供的分析摘要起草论文结果段，只交正文，不联网，不重算或认证统计有效性。S2分析摘要：事先设定等效界值为-3至3分，使用对应的双单侧等效检验；平均分差0.4分，90%置信区间为-1.1至1.9分；作者明确报告“在本样本、本指标、预设界值内满足等效判据”。这些是已完成分析，不是拟安排。保留数字、S2与结论范围，不能把有限等效写成完全相同或所有情境无效，也不要仅因没有显著差异就一律删去作者已经报告的等效结论。']}
 }
}
for key, spec in cases.items():
    (HERE / (key+'-cases.json')).write_bytes((json.dumps(spec, ensure_ascii=False, indent=2)+'\n').encode())

runner = (ROOT/'tests/evidence/gap-verification-20261010/coverage_runner.py').read_text(encoding='utf-8-sig')
runner = runner.replace("HERE = Path(__file__).parent", "HERE = Path(__file__).parent\n# Runtime stays in ignored staging; only visible frozen evidence is committed.")
(HERE/'coverage_runner.py').write_bytes(runner.encode())
(HERE/'PREREGISTRATION.md').write_text('''# 竞品扩展候选验证预登记（北京时间2026-10-10）

基线c60c589，产品版本0.1.8。三个候选独立冻结，互不叠加：审稿建议相称、报告与研究区分、未显著与等效转述。R1每个候选两任务，两条writer路线双臂，共24次全新会话；按既有运行器冻结模型/provider/effort=max，不依据单元测试、关键词或长度判断收益。实际返回的目录/会话字段须另核实；失效调用单列。

六项为本轮构造的受控学术任务，不冒充真实客户论文或已公开实证研究。起草者不能联网或工具操作；完整当前入口、对应主叶按双臂输入，未检验自主加载或Hook。审阅者看匿名稿与原材料，不看候选；主审回读原任务纠正漏报/误报。

即使一轮有收益，亦不直接合并产品。只有同一原子跨至少三轮新任务稳定收益、无可复现候选独有硬错，才考虑小改；否则保留证据与候选建议。必要时最多收窄同一原子，再做未见任务和消融。对已覆盖规则优先不重复添加。
''', encoding='utf-8')
print('Prepared 3 independent candidates and 6 fresh tasks; no product file edited.')
