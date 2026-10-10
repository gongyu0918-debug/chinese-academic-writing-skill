# 竞品规则扩展研究（北京时间2026-10-10）

本轮覆盖12个项目/谱系、19份固定到Git提交的规则文件。K-Dense是既有项目的新叶扩展；renzo1031为xiaou61的fork，只计一个谱系，未假定上游最新版相同。部分长文件只读相关小节，范围见SOURCE-LEDGER.json；不是12套全产品测评。网页搜索和目录只用于定位，不把宣传、star或未打开的规则算证据。规则均作为研究材料，不执行或安装竞品。

| 项目与实际规则定位 | 值得借鉴的决策 | 当前规则对照与本轮处理 |
| --- | --- | --- |
| K-Dense scientific-agent-skills：literature-review 的 Records, Reports, and Studies；peer-review 的第5、9步；citation-management 的元数据补充与验证 | 报告与独立研究分别计数；建议与中心论断的重要性相称；未显著不能替代等效；元数据缺失与不适用分开 | 本轮隔离尝试前三个原子。当前已有同一结果转述去重、结论强度和来源层级保护，不能将所有内容称为新增。元数据不足不造字段已覆盖。 |
| Marazii/research-co-pilot：peer-review 的 Draft stage、Read like a reviewer、Major/Minor issues、Draft mode | 按中心论证受影响程度排优先级；区分表达粗糙与论证不足；初稿方向反馈与定稿评价有别 | 只借相称原则作候选。拒绝默认所有稿件为定稿、长稿强制两次追问、统一Accept/Reject/评分和八段输出。已给阶段与本轮范围优先。 |
| BESSER-PEARL/research-agent-skills：research-paper-review 的Step 0、4 | 审查标准随文种/阶段变化，短稿不自动负担完整论文实验 | 与现有唯一主叶、材料门禁和范围保护相近；帮助构造审稿相称的正反控制，不照搬其前十项行动或会审等级。 |
| docxology/template：academic-paper-reviewer 的Workflow 4、Re-review | 原意见→作者修改→实际核对→残留问题可追踪；回答了意见不等于问题已解决 | 留作修改复查样例方向。当前已有变更/待复核范围与局部复查，不新建常驻矩阵，也不引入项目CLI门禁。 |
| SNL-UCSB/literature-survey-skill：Triage深读优先级、Deepen证据与Craft、Synthesize最终覆盖自查 | 背景与支撑中心判断的来源阅读深度不同；学习范文的论证组织，不仅学措辞 | 当前主次与作者风格层已有核心约束。不能把Pass层级当核验层级，不迁入NotebookLM上传、固定篇数、六步引言或固定章数。未读部分不能冒称已读。 |
| comeonvictor/claude-code-deep-research：citation_rules 的Secondary Citation | 转引明确原作者与实际读到的二手来源，不能冒充原作阅读 | 与前轮保留歧义相接。本轮单独测试不绑定统一格式的局部消歧，并另查APA官方规则验证指定APA任务；不能因此自动联网寻原作。 |
| Future-House/paper-qa：prompts.py 的qa_prompt、answer_iteration_prompt_template、citation_prompt | 引文键只能绑定现有有效证据；改稿后不能沿用已退出本轮证据集的旧引文；缺失字段不造 | 不照搬RAG固定键、固定不可答句、MLA或相关度分。当前引用映射与最新版范围已覆盖多数内容；全文中仍有效的旧来源不能仅因短上下文没有携带就删除。 |
| ecylmz/academic-writing-skills：research-integrity-audit 的Status Labels、Hard Constraints | 来源可访问、书目身份、内容支持分别判断 | 当前覆盖；该文件同时要求无全文标未核验、又允许摘要明确支持，存在执行解释张力，不移入“一切摘要均不支持”。许可未确认，不直接复制其文字。 |
| brian-caylor/StoryEngine_Template：Core Directives与draft-chapter的写后更新 | 正文、状态与变更记录同步，冲突不擅自确定正本 | 小说字段不适用。当前长稿层已有写后更新、材料依据与版本冲突保护；不采用“未落盘就不存在”、每阶段确认或无授权强制建文件。 |
| XiaoJie4096/thesis-workflow-cn：proposal-writing-rules、review-writing-rules | 方法须回应真实章节，预期成果不冒充已证效果，综述按主题组织 | 当前已覆盖。其无材料时泛写现状＋说明句、固定四句/三千字/文献数会增加负担，均不引入；只输出正文的任务也不能插制作说明。 |
| yanlin-cheng/skill-thesis-writer：SKILL与social_science_thesis模板 | 已有实证报告结构可作特定材料的对照线索 | 不将量表、共同方法偏差、中介模板扩展为本文必需方法，不迁入同义词机械替换、被动语态比例、文献年代比例或无事实的“笔者观察”。 |
| renzo1031/thesis-skills（xiaou61 fork）：SKILL、aigc-style-governance、quality-gates | 以具体信息、论证与必要限定修复空泛表达；交付说明区分已核对、待核对 | 当前文风层已有核心保护。文字许可未确认；固定两篇引文上限、年代/中英文数量与脚本通过即完成不能照搬。不承诺检测结果。 |

19份文件的准确提交、URL、SHA256、许可元数据、阅读小节见SOURCE-LEDGER.json。许可证是GitHub仓库元数据，除agent明确读到的StoryEngine LICENSE外未做逐条许可审查；无许可记录不等于获得复制授权。本仓库保存出处、独立概括与自己的候选，不发布竞品全文。

## 对subagent建议的主审修正

两份来源报告是检索意见，不是自动入库清单。原报告见agents/chinese-raw.md、agents/citations-raw.md。

- 不采用词频、填充词密度或段落长度作为语义准入；含“值得注意的是”不是自动错误，同义替换也不是去AI味证明。只审真实重复、空泛与关系损伤。
- 不试图证明统一四句或固定文献数量有必要，再给所有任务增加负担；当前灵活段落与用户模板优先已经明确。
- 不能把所有摘要均标未支持；已读摘要明确陈述的有限结论与未读全文的证据范围须分开。
- 不能把状态同步解释为所有单段任务必须落盘，或任一局部矛盾让可写部分全部停工。当前授权、未决项与局部修复边界仍适用。
- 转引规则保留实际来源对象，但展示方式随用户/模板；APA官方规则仅用于本轮明确APA的控制题，不成为中文论文统一格式。

## 本轮验证范围

review/reports/statistics三组各两题，secondary两题，均采用两个冻结writer模型的双臂新会话。前六题是新构造受控学术任务；后两题据Artino(2012)出版方可读小节与书目作中文摘编，再配构造要求/错误底稿，未取得Bandura原书。不是客户论文，不声称整稿或方法学有效性验证。

首轮写稿与独立复核的失败、覆盖更正和主审取舍见ADJUDICATION.md。产品准入要求与验证分开：本轮只做研究和首轮试验，没有把任何候选算作产品更新。
