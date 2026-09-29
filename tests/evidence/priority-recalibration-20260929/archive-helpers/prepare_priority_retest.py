from pathlib import Path
import json, shutil, subprocess

root = Path(__file__).resolve().parent.parent
ev = root / 'tests/evidence/priority-recalibration-20260929'
ev.mkdir(parents=True, exist_ok=False)
base = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
local = root / '.release/priority-recalibration'
candidate = local / 'P-priority'
candidate.mkdir(parents=True,exist_ok=False)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',base,'chinese-academic-writing-assistant'],cwd=root,text=True).splitlines():
    p = candidate / Path(name).relative_to('chinese-academic-writing-assistant')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(subprocess.check_output(['git','show',base+':'+name],cwd=root))
prior = root / 'tests/evidence/argument-priority-20260929/priority-r2/snapshots/candidate/SKILL.md'
p = candidate / 'SKILL.md'
old = next(x for x in p.read_text(encoding='utf-8').splitlines() if x.startswith('2. 在规划层'))
new = next(x for x in prior.read_text(encoding='utf-8').splitlines() if x.startswith('2. 在规划层'))
p.write_text(p.read_text(encoding='utf-8').replace(old,new,1),encoding='utf-8',newline='\n')
cases = {
'P1_discussion': '只依据以下材料，为课程论文写“检索提示与文献回查”的讨论小节，约450字，只交正文。研究问题是页边提示是否帮助读者回查原始文献。两班均完成同一阅读任务，甲班36人、乙班34人，非随机分班；甲班材料有页边提示，乙班没有。甲班24人回查了原始文献，乙班15人回查。另一轮课堂中，两班均使用提示，甲班36人中22人回查，乙班34人中17人回查；前后两轮文章题材不同，不能直接作为效果复验。访谈甲班8人，5人说提示使来源位置容易找到，3人说原本就习惯回查，未采访其余学生。作者判断：提示可能降低寻找来源的困难，但回查还可能与既有习惯有关，现有材料不能单独确定提示作用。另有教务台账：两班分别新增6把和4把椅子，甲班换了窗帘，乙班添了盆栽；这些记录未与回查行为关联。讨论以研究问题为中心，不要求逐条介绍材料，不写管理建议。',
'P2_revision': '只依据原稿材料修改下面课程论文的讨论小节，主题是线上预约是否与爽约变化有关，约350字，只交改后正文。可以重新安排详略，不能新增事实或建议。原稿：甲服务点2024年有120次预约、18次爽约，2025年改用线上预约后有150次预约、15次爽约。爽约次数减少，预约总数增加。2025年同时延长了周末开放时间，未记录两项变化各自的作用。乙服务点同年也改用线上预约，2024年100次预约、10次爽约，2025年130次预约、13次爽约。作者认为甲点变化可能与预约方式或开放时间有关，乙点的记录提示不能把甲点观察直接推广。两点台账另列甲点修理3台打印机、购置2台风扇，乙点修理1台打印机、购置4台风扇；这些事项未与预约记录关联。打印机和风扇数量不同。总之，甲点的爽约次数下降，但不能只用甲点判断预约方式。也就是说，两个服务点的变化并不完全相同，需要结合各自情况看待。',
'P3_required': '依据以下已读来源写独立文献综述“检索卡片与回查行为”的述评，约450字，只交正文。导师明确要求S1至S5逐篇各用一句呈现主要内容并保留来源ID，随后综合比较证据对回查行为的支持，不可省掉任一来源。S1：非随机两组各20人，同一任务中有检索卡片组14人回查原始文献，无卡片组9人回查，未记录原因。S2：另一次任务的两组各18人，有卡片组11人回查，无卡片组12人回查，分组方式未交代。S3：访谈10人，其中7人认为卡片美观、3人不喜欢颜色，没有记录回查行为。S4：设计者分析6种卡片布局，仅描述字体与配色，没有用户测试。S5：观察12名读者使用可折叠卡片，8人展开卡片，其中5人随后回查来源；没有对照组。可以在材料范围内综合分析，不能把S3的好感当成回查增加，不能从S4声称布局有效；不要因为S2方向相反就省掉它。'
}
src = (root / 'tests/evidence/argument-priority-20260929/priority-r2/runner-source.py').read_text(encoding='utf-8')
start=src.index('CASES = ')
end=src.index('\n\n\ndef fingerprint',start)
src=src[:start]+'CASES = '+repr(cases)+src[end:]
runner=root/'.release/run_priority_retest.py'
runner.write_text(src,encoding='utf-8',newline='\n')
(ev/'agent.md').write_text('''# 主次判定校准与小规则试验

用户澄清：需要在Worktree工作树中试验小规则，不是worksheet；当前0.1.5不要求修补。复用托管academic-release-016工作树，先复查主次规则取消是否采用过严尺度，再筛选竞品启发的小候选。产品目录暂保持基线。

P候选完整复用上一轮r2入口第2步原文，冻结后不改；其他运行文件来自当前HEAD，内容与已发布0.1.5相同。三道全新模拟材料任务涵盖普通论文讨论、压缩改稿、逐篇必列独立综述；使用两模型两臂独立会话，每个写手仅见自己的Skill和完整题面，禁止联网与再委派，随后交未参与起草者复核。

预登记尺度：核心证据与判断关系更清楚、旁支压缩均可计局部收益；次要信息省略不作遗漏，约数字数不作机械齐长约束。关键反证、用户必列、来源归属、数字和强度单独核对；合理材料内分析可保留。事实外扩必须指出材料与具体句子，再判断与DIFF的关系；双方共病、技术失败和单次文风偏好不直接否决规则。允许持平和适用范围内改善，不要求每题每模型都更好；若无可确认收益仍不凭原则好听合入，也不宣称单轮能保证稳定。

只读子代理分别做旧裁定校准与竞品候选筛选；主代理运行新稿。原审阅记录不改写，纠偏另列。没有新建语义评分脚本、固定比例或复杂状态机。
''',encoding='utf-8',newline='\n')
(ev/'P-candidate.md').write_text(new+'\n',encoding='utf-8',newline='\n')
(ev/'P-cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
catalog=json.loads((Path.home()/'.codex/opencodex-catalog.json').read_text(encoding='utf-8'))
models=catalog if isinstance(catalog,list) else catalog.get('models',[])
selected=[m for m in models if m.get('slug',m.get('id')) in ['alibaba-token-plan-responses/qwen3.8-flash','ollama-cloud/glm-5.3-flash']]
assert len(selected)==2, 'Requested models absent from current catalog'
(ev/'writer-catalog.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'candidate':str(candidate),'baseline':base,'cases':list(cases)},ensure_ascii=False))
