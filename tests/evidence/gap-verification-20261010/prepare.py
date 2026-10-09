from pathlib import Path
import json, hashlib, shutil, subprocess

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
HERE = Path(__file__).parent
def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

candidate = HERE/'source-scope-candidate'
shutil.copytree(ROOT/'chinese-academic-writing-assistant', candidate)
entry = candidate/'SKILL.md'
text = entry.read_text(encoding='utf-8-sig')
old = '用户提供材料不等于来源已核验。'
new = '作者提供的原始数据、记录和底稿可按实际记载使用，不代表其真实性已获独立核验；已知冲突仍须保留或报告。外部文献按下列访问层级与核验状态判断，用户提供不等于已核验。'
assert text.count(old)==1
text = text.replace(old,new)
text = text.replace('- 待核验来源：不进入最终正文，只可出现在审稿意见或正文后“其他修改建议”的核验项中。', '- 待核验的外部来源：仅为检索线索、身份或内容支持尚未确定的文献不进入最终正文，只可出现在审稿意见或正文后“其他修改建议”的核验项中。')
entry.write_text(text, encoding='utf-8')

cases = {
 'A_raw_interviews': {'leaf':'academic-writing','requests':[
  '依据作者提供的访谈记录起草硕士论文中的“家人帮助与办事选择”一段，只交正文，不联网。记录已经可读，但没有经过第三方真实性核验，不是外部文献。记录R11：受访者说女儿帮她预约了服务，她自己没有操作手机，觉得女儿比较熟悉。R12：受访者说先自己试过，未成功后请邻居帮忙。R13：受访者说工作人员在现场为她办理。作者要比较不同帮助来源，不要称三人全部依赖家庭，不推测年龄、社区、人群比例、长期能力和帮助发生的更多时间顺序。保留记录ID，不把记录改成逐字引语；可作有限比较，不声称资料真实性已经核验。']},
 'B_mixed_levels': {'leaf':'academic-literature-review','requests':[
  '据下面材料写一段独立文献综述，回答“已有材料如何区分获取帮助与能力变化”，只交正文并保留来源ID，不联网。L1为作者交来的可读论文摘要摘编，身份在本轮材料中无冲突：调查记录了求助来源与当次服务是否办妥的关联，未测前后能力变化。L2仅有题名《数字互助与持续学习》和2024年元数据，正文和摘要未取得，不能据题名猜观点。L3是一条待核验搜索线索，作者年份未确定，片段称互助促进能力。不要把L2/L3写成研究发现，不虚构引语和页码，也不把当前材料未覆盖写成整个领域空白。材料摘编不是原文引语。']},
 'C_raw_conflict': {'leaf':'academic-proposal','requests':[
  '修改开题报告已有基础一段，只交可成立的正文及必要未决意见，不联网。作者提供的原始台账T1已可读，逐项列入样本A、B、C、D四份记录；汇总页却记“已收集5份”，差异尚未解决，无更正依据。作者未提供这些记录的具体内容，后续拟继续收集材料，但没有给日期、数量和分析步骤。底稿：“本研究已收集5份记录，完成比较分析并发现共同变化机制，下一阶段将于11月追加10份。”不得替作者选4或5，不把作者提供当成冲突已解决，也不要因未有第三方真实性核验而说台账不可读或资料不存在。']},
 'D_process_absence': {'leaf':'academic-writing','requests':[
  '修改论文一段，只交改稿，不联网。作者给出公开年报中2019年费用记录摘编Y1：本节所读年报项目“服务收入”100.00万元，“服务费用”125.00万元。论文只需呈现报表口径差异；作者是否另持原始凭证、是否亲自访谈或到过机构均未给出。不要作算术推导，也不判断真实盈亏。底稿：“年报记录服务费用125.00万元、服务收入100.00万元，两个报表项目金额不同，因此机构亏损25.00万元；作者没有访问该机构，也没有任何一手资料。”按已有材料删去越界断言，保留Y1及两项数字，不新增理由或研究过程，不声称机构没有其他科目。']},
 'E_undecided_edit': {'leaf':'academic-writing','long':True,'style':False,'requests':[
  '修改论文两节，交改后的两节及必要未决意见，不联网。授权删除重复及无依据断言，未授权判断概念X与Y是否相同。作者原始登记表S1使用“参与”，S2使用“到场”，仅确认两表标签不同，术语关系尚未定。最新版目标正文如下（两节原文都已给出）：2.1 记录范围：S1用参与，S2用到场，标签不同。两张表各有自己的标签。2.2 术语关系：S1用参与，S2用到场，标签不同，所以X和Y必然同义，统计时应该合并。不选择同义或异义，不替作者定合并方式，不新增人数、定义与原因。']},
 'F_review_target': {'leaf':'academic-writing','requests':[
  '只审论文中的一个目标句，不改稿，不联网，按位置、严重度、问题、依据、建议给意见；没有实际问题可以说明。允许的材料M1：受访者说由儿子帮忙提交了表单，本次事项办妥，记录没有前后能力测量。目标句：“这一记录提示，家人代办可能为当次事项的完成提供了便利，但不能据此判断受访者的长期能力是否变化[M1]。”审查范围只限这个句子，不审下面的对照示例。对照示例（不是底稿，不在范围内）：“干预8周显著增强所有学生的自我效能。”不要将未直接测量某解释一律作为否定有限作者分析的理由。']},
 'G_primary_secondary': {'leaf':'academic-writing','requests':[
  '依据材料起草“办理成功不等于独立操作”一段，只交正文，不联网。主要证据：观察O1记录三次事项全部办妥，其中两次由现场工作人员操作，一次由当事人自己操作；不能据此认定当事人都能独立操作。必要反证O2：另一次事项中当事人独立完成全部操作，材料没有其前后能力测量。背景仅需一笔：这些事项均在同一个服务点办理，服务点名称、地区、日期和人员身份未给。重点比较完成结果与操作主体，同时解释O2为何不能被删掉，也不把单次独立完成说成长期能力提升。保留O1/O2，不平均展开背景，不添机制或对策。']},
 'H_quote_protection': {'leaf':'academic-writing','requests':[
  '压缩论文段落，只交改稿，不联网。作者访谈逐字引语Q1，定位为作者记录第2段，必须原样保留：“我不是不会办，是这次让女儿替我办了。”记录中没有能力测量。底稿：“受访者表示：‘我不是不会办，是这次让女儿替我办了。’（Q1，作者记录第2段）这证明她已经具有稳定的独立操作能力，家人代办显著提升了数字技能。我们没有提供干预周期，没有提供家庭收入，没有提供长期追踪，没有提供其他地区，因此不能说明任何问题。”删除确定能力、因果和外围否定，保留引语归属及不能从当次代办判断能力的必要边界；不要把引语改成作者实证发现，不新增变量或原因。']}
}
dump(HERE/'source-scope-tasks.json',cases)
dump(HERE/'PREREGISTRATION.json', {
 'date_beijing':'2026-10-10','baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'question':'C1原始材料与待核验外部来源的单变量消歧；其他旧问题用新任务检查',
 'models':['alibaba-token-plan-responses/qwen3.8-flash','ollama-cloud/glm-5.3-flash'],'effort':'max',
 'candidate_files':['SKILL.md'],'unchanged':['all six reference files','production scripts','published version'],
 'semantic_criteria':['按可读记录工作而不冒称真实性核验','身份冲突不放行','摘要/元数据/线索不跨层','不把未给作者过程写成没有发生','已给目标不得误认缺失','只审不换对象','重点保留反证与必要限定','引语与数据不篡改'],
 'admission':'候选独有硬交付/事实失败需复现与诊断；不得靠总调用数抵消。若无明确收益或稳定行为支持，仅记录消歧候选，不合入产品。失败与分歧全存档。',
 'quality_scoring':'Independent semantic review and manual reread only; no Python/unit-test semantic gate',
 'corpus':'This batch consists of controlled fresh cases, not additional real thesis coverage',
 'gaps':['Actual file/state recovery tested separately','No whole-thesis, doctoral, formatting or desktop validation claim']
})
print(json.dumps({'cases':len(cases),'baseline':'eb598fe','candidate':'single source-scope concept in SKILL.md'},ensure_ascii=False))
