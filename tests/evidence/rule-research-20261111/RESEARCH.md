独立竞品规则研究

已只读核对指定四份官方原文、入口和两份写作规则；现有未提交冷审报告保持原状。建议以下三项最小候选，均属文本消歧，实写收益尚待验证。

1. **区分材料用途与核验状态，优先考虑。**

   在[入口第48行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:48)，将“用户提供材料不等于来源已核验”替换为：

   > 用户提供材料不等于来源已核验。另按当前用途区分作者研究记录、待改底稿与外部来源，同一文件可兼具用途；读过底稿不等于核实其所述事实，外部研究不能补成本研究已完成的过程或结果。

   **增量**：现有规则区分全文、摘要和元数据，却未明确“已读原文”可能只是待改底稿。这里补的是材料身份，避免把表述存在误当事实成立。依据 K-Dense 的[证据与起草分离原则](https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/skills/scientific-writing/references/evidence_workflow.md)，作本仓库用途消歧，不移植其逐句标记和人审门禁。

   **必须保留的反例**：纯语言修改可以忠实保留底稿原述，不能因未取得原始数据而拒绝修改；底稿附有研究记录时，也不能整份降为“待核验来源”。

2. **把抽象“章节任务”落实为可判断的职责。**

   在[academic-writing.md 第7行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:7)，替换首句，保留后面的摘要、结论限制：

   > 全文或章节按研究问题分工：引言说明为何提出此问题，文内综述比较已有回答及分歧，方法交代如何取得和处理证据，结果呈现所得发现，讨论判断这些发现支持哪些解释。按学科与既有结构选用，可合章，不强设章名。

   **增量**：入口已有任务链，ANTI-AI 已区分结果与讨论；这里补引言、文内综述和方法的具体判断依据，帮助决定内容放在哪里、展开到什么程度。参考 [K-Dense 章节职责](https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/skills/scientific-writing/references/imrad_structure.md)及 [Fabian §3、§8](https://raw.githubusercontent.com/FabianRitter/paper-writing-agents/main/skills/academic-writing/SKILL.md)，只取职责区分，其固定句数和段落骨架不进入候选。

   **必须保留的反例**：结果与讨论可以合写；理论、文学和史学论文可按推理或史料组织，不为凑齐上述职责新增章节。

3. **将限定保留条件从封闭列举改成具体误读判据。**

   在[anti-ai-writing.md 第38行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:38)，仅替换“只有删去后会使……强度升级时才保留”：

   > 删去后会使当前结论因果化、长期化、范围扩大、强度升级，或使比较基准、指标含义、可成立的替代解释被误读时，保留所需的最短限定。

   **增量**：已有总原则保护必要限制；此处只消除“四种升级才保留”可能形成的过窄解释，让比较口径和解释取舍也有明确判据。K-Dense 的[写作原则](https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/skills/scientific-writing/references/writing_principles.md)强调保留不确定性、替代解释及数值口径，可支持这一推导，但不能证明候选有效。

   **必须保留的反例**：“提高5%”所依赖的基线、“自报满意度”所限定的指标含义不能删；材料列出未测事项，也不意味着正文必须追加整串否定说明。

本轮公开写作材料

[S1] Dell’Acqua等，Organization Science，2026，DOI 10.1287/orsc.2025.21838。已实际读取官方作者机构提供的论文PDF第2页（论文第1页）摘要，未将其余页的检索片段作为已读原文。来源：https://www.hbs.edu/ris/Publication%20Files/dell-acqua-et-al-2026-navigating-the-jagged-technological-frontier_5c589c8c-fbb5-458f-b285-c944746cd717.pdf 。论文为CC BY 4.0：Organization Science. Copyright © 2026 The Author(s). https://doi.org/10.1287/orsc.2025.21838, used under a Creative Commons Attribution License: https://creativecommons.org/licenses/by/4.0/ 。任务采用摘要明确的样本、设计和任务差异，不将2023工作论文与2026发表版数字混用。

[T1-T3] 鲁迅《孔乙己》，维基文库原文第1段与第4段，页面标明公有领域。只使用任务中给出的三个短片段，不从全文其他情节补充人物经历。来源：https://zh.wikisource.org/zh-hans/%E5%AD%94%E4%B9%99%E5%B7%B1 。

其余带数字的研究记录均为本轮明确构造的验证材料。NBER/Science直接页面访问受限，未将其作为本轮已读来源使用。
