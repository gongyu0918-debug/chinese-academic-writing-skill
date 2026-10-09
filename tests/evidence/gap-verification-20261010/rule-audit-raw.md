# 只读语义审计报告

## 范围与完成度

本轮已逐行完整读取指定范围内的全部 7 个文件：

- [SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:1)（读至末行 L90）
- [academic-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:1)（56 行）
- [academic-proposal.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-proposal.md:1)（49 行）
- [academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:1)（54 行）
- [citation-research.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:1)（37 行）
- [anti-ai-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:1)（62 行）
- [long-form-consistency.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:1)（70 行）

未覆盖：`LICENSE.md`、`agents/openai.yaml`、`scripts/citation_audit.py`、`scripts/manuscript_audit.py`、`scripts/prose_lint.py`。文档中提到脚本行为的位置（anti-ai-writing.md:23、citation-research.md:37、long-form-consistency.md:64-70）只按文本语义记录，没有运行脚本或读代码验证。未读历史证据与本轮候选，未联网，未委派，未修改文件；中止指令后未再读取或执行任何内容。以下结论只基于上述已读文本，没有把未执行的检查当作已完成。

## 问题 1：用户材料的"已读"与"已核验"边界会决定离线正文能否使用该材料

**位置**：[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:46) L46、L48、L51；相关条文在 [citation-research.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:3) L3、L16。

**原句**：
> L46：用户提供材料不等于来源已核验。
> L48：已读原文：可在原文证据范围内转述；直接引语必须保留可回查定位。
> L51：待核验来源：不进入最终正文，只可出现在审稿意见或正文后"其他修改建议"的核验项中。

**两种合理解释**：
A（按访问层级放行）：用户提供且已读的原文、摘要按 L48/L49 使用；"核验状态"只记录外部核验进度，不足时限制论断强度，不自动禁止转述。
B（按核验状态封禁）："用户提供材料不等于来源已核验"意味着该材料仍属"待核验来源"，按 L51 不得进入正文；"已读原文"只适用于已经完成核验的来源，离线又无联网授权时，用户粘贴的全文只能用于理解、收缩正文或列入核验项。

**触发场景**：用户离线粘贴一篇期刊论文全文和书目信息，要求写综述正文。A 直接写出含该文献论断的段落；B 不把该文献写进正文，改交核验清单或要求先授权联网。citation-research.md:3 说"离线核验直接使用用户提供的原文、摘要和书目信息"，支持 A；SKILL.md:46 的措辞支持 B。

**最小修订**：在 L51 前定义"待核验来源"为"尚未读到内容、只有转述、题名或书目线索的来源"；在 L46 后补一句"已读的原文或摘要可在其内容范围内使用；核验状态不足时在账本标注并限制论断强度，不自动降为待核验来源；来源存在性与版本核验按 L53 与联网授权另行处理"。

**证据限制**：文件没有给"待核验来源"下定义，也没有说明"核验状态"字段与四个层级是否互斥；未读 scripts 和历史材料，无法从实现层确认账本行为。A、B 都能从现有句子推出，且会改变正文是否包含该材料。

## 问题 2："进行中"的研究事项在开题报告里没有归属，写着写着会变成未开展或已完成

**位置**：[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:17) L17；[academic-proposal.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-proposal.md:7) L7、L15（关联 L23）。

**原句**：
> SKILL.md L17：阶段区分拟开展、进行中和已完成。
> academic-proposal.md L7：严格区分三类表述：`已有基础`只写已经完成且有材料支持的工作，`拟开展工作`只写作者已经提出的研究安排，`预期结果`只写计划希望获得的产出，不写成已经证实的发现。
> academic-proposal.md L15：说明已有基础与拟开展事项分别放在哪里。

**两种合理解释**：
A（并入拟开展）：未完成的工作统一按"已提出、待开展"表述，避免写成既成事实。
B（拆写实际进度）：已发生的部分（如已完成问卷设计、已访谈人数）归入已有基础或单独说明"正在进行"，剩余安排归入拟开展工作；但 L7 只列三类、L15 只说两栏，执行者无法确定"进行中"能否显式写出。

**触发场景**：材料为"已完成问卷设计，正在预调研，计划下学期正式发放 300 份"，要写开题报告的"进度与已有条件"段。A 产出"拟开展预调研和问卷发放"；B 产出"问卷设计已完成，预调研正在进行，拟于下学期发放"。前者会把已开始写成未开始。

**最小修订**：在 L7 补"进行中的事项写已发生的进度与剩余安排：已发生部分列入已有基础，其余列入拟开展工作；不写成尚未开始，也不写成已完成"。

**证据限制**：SKILL 的"阶段"是否与开题三表述同层，文件没有绑定，也没有给"进行中"的示例；proposal L23 只限制"进度与成果不得超出作者明确给出的任务和时间"，没有回答归类问题。

## 问题 3：系统综述条件下能交付什么，"按材料处理"没有说明产物边界

**位置**：[academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:5) L5；[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:11) L11；[citation-research.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:21) L21。

**原句**：
> L5：只有用户提供真实检索协议、数据库与检索式、筛选标准和完整筛选记录时，才可按材料处理系统综述；否则不生成"系统综述"结论、PRISMA 流程、检索数量、排除数量或纳入研究数量。
> SKILL.md L11：不处理英文论文全文、投稿全流程、科研伦理审批、统计分析或有效性判定……给定输入与公式均可核对时，可做简单算术，但不据此补充统计或因果结论。
> citation-research.md L21：不因缺少检索协议和筛选记录生成系统综述、PRISMA 流程或研究数量。

**两种合理解释**：
A（条件满足即升级）：可用完整记录写系统综述体例的正文，并可从记录中如实转写检索、排除、纳入数量与 PRISMA 流程，属于可核对的简单算术；不做合并统计、偏倚或有效性判定。
B（仅按材料组织）：即使记录完整，也只能把记录作为材料组织、转写，仍不生成系统综述结论、PRISMA 流程与数量，因为这些属于方法学产物，文件的能力不足以核实协议真实完整。

**触发场景**：用户给出协议、数据库、检索式、筛选标准、完整筛选记录，要求"照这些写一篇系统综述"。A 交付含 PRISMA 与数量的系统综述正文；B 交付叙述性综述正文加记录整理或建议，不写这些方法学内容。

**最小修订**：在 L5 补"满足条件时，可在记录范围内如实转写检索、筛选与计数并据此组织正文；不生成记录未包含的流程或数量，不做统计合并、偏倚或有效性判定，不声称已核验方法学"。

**证据限制**："真实、完整"由谁按什么证据判定，文件未说；SKILL.md L11 排除"统计分析或有效性判定"与允许"简单算术"的边界没有覆盖 PRISMA；未读 scripts，无法确认是否存在工具层支持。

## 问题 4：创建 `.academic-writing/` 的"授权"指用户同意还是项目可写，决定只审任务会不会留下状态文件

**位置**：[long-form-consistency.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:9) L9；[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:68) L68（关联 L55）。

**原句**：
> L9：只有用户明确要求跨轮次保存状态，或已经授权写入当前项目时，才在 `.academic-writing/` 下维护工作文件；该授权对只审、只读或粘贴文本任务同样有效。未获上述授权时，所有任务只在当前上下文按同一结构维护，不创建 `.academic-writing/`。

**两种合理解释**：
A（项目写授权即可）：用户已允许在该项目写文件（如让 skill 改稿、保存成稿）时，长稿任务可创建 `.academic-writing/` 状态包与分节简报；文本还特别说明该授权对只审、只读任务同样有效，所以只审任务也可能新增文件。
B（仅限状态文件授权）：只有用户明确要求跨轮保存状态或明确同意创建状态文件时才能建；写正文、改稿或目录可写的授权不覆盖辅助状态目录，只审任务一律不新增文件。

**触发场景**：用户说"项目文件你可以直接写；这一章只审，不要改稿"，或"这两章改好存到项目里"。A 会在项目里留下 `.academic-writing/`；B 只交付审稿意见或正文，不留状态目录。对只审任务，差别是是否产生用户没有要求的文件。

**最小修订**：把 L9 的"已经授权写入当前项目"改为"用户明确同意创建状态文件或明确要求跨轮持久化"，并补"写正文或改稿的授权不自动包含 `.academic-writing/`"。如果本意就是项目可写即可创建，则应在 L9 明说"项目写权限包含该目录"。

**证据限制**：文件没有定义"授权"来自对话同意还是宿主的文件写权限；我没有检查宿主权限配置或该 skill 的运行环境，只判断文本层面的歧义与交付后果。

## 问题 5：准确转述能否替代原始研究，引用对象与"转引"标注会不同

**位置**：[academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:28) L28；[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:48) L48、L51；[citation-research.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:25) L25。

**原句**：
> L28：综合证据时回溯原始研究：对同一结果的多次转述不增加独立证据，准确转述仍可按其来源使用；采用相同方法但基于独立材料或样本的新研究分别判断，不因方法相同合并。

**两种合理解释**：
A（按实际读到来源）：只读到转述时，内容按实际来源（那篇综述）标注，必要时写"转引"；未读的原始研究仍是未核验来源，不能按 L48 当作本文已核验的原文结论。
B（按原始来源）："准确转述仍可按其来源使用"被读成可以用转述内容支撑原始研究的结论，直接引用原始文献，无需先读到原始研究全文。

**触发场景**：用户只给一篇 2022 年综述，其中准确转述 1998 年实验结论，要求写"研究现状"。A 写"（2022 综述转述）1998 年研究发现…"或以 2022 综述为引用对象；B 直接写"某（1998）发现…"并著录 1998 年原始文献。文后清单、引用责任和 citation-research.md L25 要求的"回到原文"复核都会不同。

**最小修订**：在 L28 补"只读到转述、未读到原始研究时，不得把转述内容作为已核验的原始研究结论使用；按实际读到的来源标注并注明转引，或先取得并核对原文"。

**证据限制**：文件没有给"转引"标注规则，也没说"准确"由谁证明；本轮不能联网核对任何具体文献，无法用实例判定哪种执行会产生错误引用；学校或期刊模板对此的优先规则也未在这两份文件中说明。

## 未列为问题的候选

- 复核委派层级（SKILL.md:76、82）：缺 subagent 或禁用时已有落地路径，分歧只影响是否多一层复核，不改变交付内容。
- 引用著录格式与"不处理排版"（SKILL.md:11、53；citation-research.md:35）：具体条款已把引用格式与文内标号纳入范围，边界可由"文档版式、页面排版"吸收。
- 纯检测模式与脚本参数（SKILL.md:84；anti-ai-writing.md:23、56）：只影响可选脚本参数；脚本代码不在本次范围，证据不足。
- "章节起草"与"不得代写整篇提交稿"（SKILL.md:12、61）：属于需要维护者定界的政策问题，现有文本有明确禁止语，未按文档歧义处理。

主次详略相关条款（SKILL.md:60、academic-writing.md:9、academic-literature-review.md:26-28）交叉阅读后没有发现会改变交付的冲突。以上 5 项为达到同一门槛的条目；未修改任何文件。
