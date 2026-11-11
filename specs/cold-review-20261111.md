# 中文论文写作 Skill 冷审与竞品对照

审查日期：2026年11月11日。审查基线：`09addbb9430821bed763968f8afa016e5cdccb13`，运行内容为0.1.10。

当前规则对材料保真、来源层级、研究状态、任务范围和段落自主组织已有系统覆盖。优先改进方向是减少偏题的限制说明、厘清材料与论断身份，并检验各章节的具体写作支持。产品形态方面，可借鉴竞品的证据回查、文献组织和修改留痕。本轮确认了一项日志清理工具缺陷，以及测试入口和维护文档的迁移问题；没有据此改动运行规则。

**审查范围与证据口径**

逐篇读取入口与全部七份 reference，核对 README、HANDOFF、42项行为 Spec、评估 Spec、三个运行脚本的能力边界及维护测试。历史重点回读0.1.10采用依据、前期缺口和竞品研究。另由两个独立写作代理完成三个构造材料任务，由主审回读材料判断实际输出；竞品研究与测试审计分别委派独立代理。

“页面”在本报告中指规则页和维护文档。本仓库没有业务前端，本轮未检查外部产品页面的实现。各发现分别标明已有条款、实际输出问题、待验证文本边界或产品机会；优先级表示处理顺序，不表示故障率。竞品采用官方公开资料作功能对照，未作同题实测排名。

**现有八份规则页的覆盖情况**

| 规则页 | 已覆盖 | 薄弱处或下一步核查 |
| --- | --- | --- |
| [入口 SKILL.md](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:15) | 三类稿件、四种模式、材料和研究阶段；缺材料出口；引用层级；逐段推进；独立复核及不可用回退 | 材料身份与核验状态交叉；作者分析的公共口径；复核义务与“语义协作建议”的强度 |
| [普通论文](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:5) | 研究问题到结论的关系；自主成段；有限作者分析；四模式；稿内一致性 | 引言、方法、结果、讨论、结论的具体任务主要以原则概括；学科差异只列线索。属于指导深度问题，不能从篇幅直接推断写作失败 |
| [开题报告](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-proposal.md:5) | 问题、目标、内容、方法、进度对应；计划与结果分开；候选建议出口 | 入口有“进行中”，本页枚举主要为已有、拟开展、预期；方案比较建议与已定方案正文的边界尚可消歧 |
| [独立综述](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:5) | 来源层级、主题综合、来源ID、独立证据、伪研究空白；系统综述材料门槛 | 系统综述协议草案、已有记录转写与方法质量判断未充分分开；转引对象不够明确；同一研究多份报告的归并仍主要依赖人工判断 |
| [来源检索与引用](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:5) | 检索授权、元数据匹配、原子论断映射、支持状态、更新/撤稿状态、引用覆盖和格式 | 沿用作者旧引文与新增来源认证；把撤稿文本作为研究对象的例外；证据回查的交付方式可更易使用 |
| [ANTI-AI复核](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:25) | 引语和术语保护；必要否定与回指；普通润色、只删、只审；局部修改 | “承担任一作用即保留”与后续“只有……才保留”的作用域仍有两种读法；外围限制仍有实际残留 |
| [长稿一致性](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:7) | 状态包、分节简报、最新版核对、授权落盘、冲突处理、全文复核顺序 | 机制已写明；跨会话更正、旧状态淘汰、多人合稿和复核后修稿的端到端稳定性尚需验证 |
| [必要英语与文字格式](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-text-format.md:5) | 适用标准、中英对应、引文体系、片段范围、文字与实际文件版式的交接 | 英文自然度、实际学校模板和真实文件交付仍需分别验证；标准号正确不等于整稿符合条款 |

四项标准的官方页面均显示现行：[GB/T 7713.1-2025](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=36C05B5738C54D42B4B262525320B52F)、[GB/T 7713.2-2022](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=0B963916637B8F34B295FCF4A51A1BE5)、[GB/T 7714-2025](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=C6CE52E55AC09B9C79A20AEA77CEDD14)、[GB/T 6447-2025](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F70F4968628FFF58FF5AE7414A815CC8)。本轮核实版本状态，没有重新认证全部条文。现行的“国标优先”是项目既定策略，不作为新发现的规则错误。

**优先处理的写作问题**

1. **优先验证：外围限制会占用论证位置，已有本轮输出证据。** [ANTI-AI第36行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:36)要求按实际作用保留或删除，但后续保留判据仍可能被不同理解。本轮综述任务只讨论备课劳动，输出却两次延伸到未测教学质量；可删去这两处扩展，保留与备课总时长有关的限定。历史R4/R5的同一道E1题中，候选保留外围说明8/8，基线2/8；新E3两臂各1/4。它们证实具体修改负担，不能换算成全局故障率或某一句规则的因果结论。0.1.10的模式消歧已经采用，应以现版为新基线，不重新把已解决的模式范围列为缺失。

2. **优先验证：普通论文的章节写作支持可以更具体。** [普通论文第7—17行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:7)有正确的结构和分析原则，但对引言怎样建立问题、讨论怎样推进解释、结论怎样回应问题，缺少针对实际材料的示例与取舍。本轮综述探针已经能够综合两份摘要，说明不能将现状描述成“只会守边界、不会论证”。先用新鲜的引言、方法说明、结果和讨论任务比较宿主默认、当前Skill与局部候选；只补能改变实际决策的指导，不追加通用写作教材或固定段落骨架。

3. **优先验证：材料身份、读取层级和核验状态需要分别判断。** [入口第48—53行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:48)将全文、摘要、元数据与待核验来源放在一组规则里；“待核验来源不进入最终正文”又与[保留作者底稿引文](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:35)交叉。建议比较三个独立问题：对象是作者记录、待改底稿还是外部文献；实际读到了什么；本轮是否核验真实性及内容支持。测试应同时包含保留未核验旧引文的语言修改和已知错配的纠正，不能以沿用引文冒充认证，也不能把未核验直接当作已证伪。

4. **后续验证：作者解释、理论命题、候选方案与经验发现的公共边界。** [普通论文第13行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:13)已经明确保护有限作者分析；开题和来源层的限制更强。来源层[第20行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:20)要求整体路径有整体检验支持，对于声称已有机制的正文是必要约束，是否误伤明确请求的理论推演或候选假设仍需实写验证。先辨明论断身份，避免只靠“可能”二字放行，也避免将有据分析一律移到建议区。

5. **后续补齐：文件读取与修改交接。** 当前[DOCX读取函数](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/scripts/prose_lint.py:321)明确只提取主文档正文，排除页眉、批注和审阅说明；脚注、尾注也不从其独立XML部件读取。三个脚本不能据此承担扫描PDF、复杂表格、导师批注、完整修订记录或实际页码回查。应由宿主文件能力交接已读范围、正文与脚注等组成部分、定位及修订状态。缺少这种交接不等于必须新写解析器，也不能把正文扫描宣称为整份文件审核。

6. **后续验证：几处来源服务的窄边界。** 独立综述[第5行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:5)未细分协议草案和完成报告；[第28行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:28)“其来源”的转引对象可以更明确；引用层[第27行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:27)的撤稿限制需要区分采用其结果与研究该文本或撤稿事件。三者是待验证的作用域边界，不是本轮已复现的交付故障。

7. **后续量化：独立复核的契约和成本。** [入口第78行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:78)同时使用“交给”“直接调用”和“语义协作建议”；简单语言修改也进入统一复核。真实独立性、不可用回退和不递归设计应保留。是否需要按任务风险分层，应比较局部润色与长稿的延迟、发现问题的价值和误改负担，不能仅凭感觉取消复核。历史记录已出现独立审阅漏报和过审，主写者仍需回读材料。

**缺少哪些页面和内容**

以下是内容归属建议。缺少独立文件不等于缺少能力；优先改清已有页，只有内容确实较长、可按需加载时才拆新页。

| 内容 | 当前归属与缺口 | 建议落点 |
| --- | --- | --- |
| 引言、方法、结果、讨论、结论的具体写作任务 | 普通论文页已有原则，章级示例和决策指导较薄 | 先在普通论文页试少量有效判据；需要时再拆可选章节支持页 |
| 文献阅读后的证据摘录与多文献比较 | 引用账本、来源覆盖表已经存在；用户回查和复用的交付方式不够具体 | 引用层按需给出论断、原文摘录、定位、支持状态和正文位置，不强制每次展示大表 |
| 导师意见到修改结果的对应 | 已规定最新版与导师建议的地位；没有清楚的逐项处理示例 | 底稿修改模式增加可选的意见、改动位置、处理理由和未决项交付；普通润色仍可只交正文 |
| PDF、DOCX、脚注、批注与修订状态交接 | 大材料有覆盖范围规则；实际读取部件和定位依赖宿主 | 在长稿层补紧凑交接约定，复用现有文件技能 |
| AI使用说明、致谢及其他声明文字 | 机构要求标识有出口；没有专门任务说明 | 属于可选扩展，只能据真实信息和机构要求整理；不生成审批、资助或贡献事实 |
| 系统/范围综述的协议与报告 | 默认叙述性综述；系统综述有真实记录门槛 | 属于产品范围选择；先澄清协议建议和已有记录转写，不直接扩成完整系统综述平台 |

英文全文、博士论文、统计分析与有效性判定、伦理审批、答辩、投稿全流程、文件页面排版和检测规避均不在当前列明范围内。它们需要单独的产品决策；不能作为本轮应立即补齐的漏洞。必要英文、全文一致性和文字格式则已经有规则，主要缺的是行为验证。

**竞品公开能力对照**

| 对照对象 | 官方资料能支持的能力 | 对本项目有用的借鉴 |
| --- | --- | --- |
| K-Dense Scientific Agent Skills，同类规则技能 | 分别提供[章节结构指导](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-writing/references/imrad_structure.md)、[证据与一致性流程](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-writing/SKILL.md)和[综述检索、筛选与研究报告对应](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/literature-review/SKILL.md) | 参考章节职责及研究与报告的区分；逐句ID、固定登记表和每句人审不直接移入中文片段任务 |
| Elicit，检索与研究综合平台 | [系统综述流程](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit)将筛选、提取字段与支持摘录连接；支持[表格、报告和文献导出](https://support.elicit.com/en/articles/14758189-export-your-data-from-elicit) | 让关键判断能够回到具体原文；字段证据不能外推为所有生成句子均已核验 |
| SciSpace，阅读与写作平台 | [Deep Review](https://scispace.com/help/en/articles/10864812-how-to-use-deep-review-for-advanced-literature-analysis-in-scispace)提供多文献综合和来源摘录回查；[PDF问答](https://scispace.com/help/en/articles/10660595-how-does-chat-with-pdf-work-chat-with-pdf-interacting-with-research-papers-using-ai)可连接笔记与阅读记录 | 改善阅读、摘录、来源定位和成文的衔接 |
| Paperpal，学术编辑平台 | [Reference Checker](https://support.paperpal.com/support/solutions/articles/3000137228-how-does-paperpal-s-reference-checker-work-)检查引用及元数据等风险；[现行PDF页](https://paperpal.com/tools/chat-pdf)列出跨文献比较；[更新日志](https://paperpal.com/productchangelog)记载Word修订导出 | 引用检查与修改记录接到实际稿件；旧FAQ与新产品页有差异，整库导出的当前范围本轮不作结论 |
| Jenni，写作编辑器 | [Reviews](https://help.jenni.ai/docs/ai-tools/reviews/)分别评估论断支持与来源风险；[AI Editing](https://help.jenni.ai/docs/ai-tools/ai-editing/)展示可接受或舍弃的增删差异 | 复用现有支持状态，把具体问题说清，并在重大修改时提供可审阅的改动依据 |
| AMiner，中文科研平台 | [学术搜索](https://docs.aminer.cn/user-guide/features/academic-search/)连接文献与PDF阅读；[沉思](https://docs.aminer.cn/user-guide/features/aminer-thinking/)区分开题和综述模式，支持个人资料及多格式报告导出 | 参考中文任务入口与资料组织；明确仅用指定来源还是可扩展检索 |

知网AI/研学未取得可完整读取的官方功能资料，本轮不判定其能力缺失。以上产品资料也未构成对其中国学位论文国标、院校模板或中文写作质量的全面核验。Elicit的[官方局限说明](https://support.elicit.com/en/articles/14757928-elicit-s-limitations)仍提示可能误解来源；各产品列出引用或审查功能，不能据此推断实际检出率。

本项目可清楚表达的特色，是中文本科、硕士、开题与综述的任务划分，以及作者材料、研究阶段、局部范围和论断强度的共同约束。竞品也明确要求来源和事实保真；竞争改进应落在中文实际稿件的可用性、证据回查和修改负担上。文献库、可点击摘录、版本历史和引用导出属于工具集成机会，规则型Skill能否提供这些体验还取决于宿主。

**维护工具与评测发现**

| 发现 | 证据与影响 | 建议 |
| --- | --- | --- |
| P2，日志清理检查器漏检，已复现 | [load_text_files](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tools/sanitize_public_eval_logs.py:62)不验证目录存在；不存在目录的检查可返回PASS。[检查条件](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tools/sanitize_public_eval_logs.py:25)与实际清理规则不一致，仅含合成会话标识的文本被漏过 | 检查目录和扫描文件数，统一检查与清理的识别范围，补负例。该缺陷不能证明现有归档已经泄漏信息 |
| P2，默认测试入口未说明稀疏检出条件 | [测试导入](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tests/test_prompt_gate_provider_matrix.py:9)和[发布测试初始化](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tests/test_release_policy.py:24)直接依赖隐藏的历史证据；[README命令](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/README.md:86)只列Windows用法 | 明确核心维护检查与历史重放的前置条件，给出macOS/Linux命令和隔离恢复方法；缺证据不得静默算通过 |
| P2，最新证据完整性未纳入默认测试 | [固定回执](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tests/test_release_policy.py:10)主要到0.1.3；[0.1.10检查](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/tests/test_release_policy.py:122)核对README版本。最新两份证据清单未由该套测试覆盖 | 可增加只读的清单与哈希检查；它只验证证据绑定，不评价Markdown语义 |
| P2，旧实验可离线复核，重新生成仍有迁移成本 | Git中的R5驱动固定源机Windows路径、模型列表、端点与effort，审阅驱动依赖源机阶段目录 | 保留历史字节；新实验用宿主默认或本机可用模型，按需配置provider、模型、推理档位、端点和路径。出现真实重复调用需求时再补维护入口 |
| P3，维护文档混有过时现行口吻 | [HANDOFF第106—113行](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/HANDOFF.md:106)仍列旧模型与禁继承要求；与[AGENTS](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/AGENTS.md:5)不一致。行为Spec也保留0.1.9历史基线 | 将当前有效要求集中说明；旧实验条件保持历史身份，不回写冻结证据，不继续追加状态流水账 |

当前采用非锥形稀疏检出，排除了`tests/evidence/`，不代表证据丢失。独立测试审计在临时目录恢复7,388个证据文件后完成166项维护测试，全部通过；当前稀疏工作区直接跑全量会有8条导入或初始化错误。两份最新清单的656项与113项哈希均匹配，R4/R5的48次prompt及终稿绑定匹配，13个运行文件也匹配0.1.10验证清单。临时导出已回收，未改变稀疏配置或Git索引。

这些检查支持实现、只读边界、包结构和证据完整性。它们不证明引用内容获得原文支持、长稿语义一致或整套写作优于竞品。现有[评估Spec](/Users/gongyu/Developer/skills/chinese-academic-writing-skill/specs/evaluation-spec.md:15)对冻结条件、对称重复、盲审纠偏、调用数分母和局部采用的要求合理，应继续沿用。

0.1.10主要采用依据为同一C2的5题、48次规则内联写作和6次匿名审阅。归档已明确不覆盖自主加载、整篇论文、跨轮完整交付或独立复核后自动修稿。本轮三个任务增加了现版的局部行为观察，仍未补齐上述端到端验证。

**建议的处理顺序**

1. 先修日志清理工具的确定缺陷，整理当前有效维护要求和跨平台测试入口；保持历史原稿与冻结条件不变。
2. 以0.1.10为基线验证外围限制的取舍，正例保留真正影响判断的限定，反例删除与当前问题无关的未测事项；不按否定词数验收。
3. 再测材料身份及作者分析的边界，覆盖旧引文沿用、已知错配、原始记录、元数据、有限解释与明确候选方案。
4. 用具体章节任务判断是否值得增加写作指导，随后补长稿更正恢复、意见处理和文件交接。比较完整Skill价值时可增加宿主默认对照；小修仍按实际diff验收。
5. 最后根据实际使用需求接文献库、引用导出或修改留痕。每次只改变可解释的范围，用新材料、必要重复和独立语义审读判断收益与代价，不新增字符串式写作质量门禁。

**本轮写作探针及可复查材料**

三个任务均使用构造材料，生成代理继承宿主默认模型，未另设provider、推理档位或采样参数。两个代理分别处理一项和两项任务；它们报告读取了相应规则，未提供完整路由trace。为控制本轮范围，未再派生复核者，以下由主审独立回读材料判断，未执行复核后的自动修稿。附记中的规则读取说明不属于论文正文。

任务一请求润色并保留事实、数字、引文，正文后最多两条必要建议。材料为发放120份、回收108份、有效96份，58人自述备课时间减少；原文却称有效回收率96%、证明全体教师教学质量提高，并把“资料要自己再确认”的访谈解读为彻底解决可靠性问题。补充记录明确是一次横断面调查，无教学质量指标和对照组。

实际修改稿：

> 本研究于2025年11月在某校开展一次横断面调查，共发放问卷120份，回收108份，其中有效问卷96份。96名受访者中，58人表示使用平台后备课所需时间减少。这一结果反映了部分受访者自述的备课时间变化；由于调查未收集教学质量指标，尚不足以据此判断教学质量是否提高，更不能将结论推广至全体教师。访谈对象甲认为“检索方便，但资料要自己再确认”（访谈A，第3段）。甲的反馈提示，检索便利与资料仍需核实可以同时存在，不能据此认定平台已彻底解决资料可靠性问题。

实际建议指出96%与数量不符，修改稿已改用原始数量；以发放数为分母应为96÷120＝80%，明确口径后再补。该稿保住数量和引语、收回过强结论，没有把错误百分比继续写入正文；这是单个任务的合理处理，不证明所有数字冲突均已解决。

任务二请求约180字的开题“研究基础与后续安排”，只交正文。材料为8人访谈完成，5份逐字稿核对完成、3份正在核对，两个框架候选未定，12份政策文件已收集但未给内容，作者仅计划12月完成其余核对。

实际正文：

> 现阶段的研究基础主要包括访谈材料的积累、逐字稿核对及政策文件收集。目前已完成8人访谈，逐字稿核对工作仍在进行，其中5份已完成核对，其余3份正在核对中。政策文件已收集12份，形成现有资料储备。分析框架有两个候选，具体采用哪一个尚未确定。后续计划在12月完成其余3份逐字稿的核对。

该稿保留分项状态，没有概括未读政策或补研究步骤。开题页的三类枚举没有在本例导致丢失进行中状态，故不将枚举差异认定为已复现故障。

任务三请求本科论文文内综述一段，220—320字，保留[A][B]，围绕“数字资源平台如何改变教师备课劳动”综合材料。摘要[A]为32名中学教师访谈，多数认为统一检索节省寻找素材时间，未测教学质量或长期使用；摘要[B]为另一地区48名中学教师访谈，反映核验、筛选、重新编排工作增加，未统计总时长。[C]只有题名。

实际正文：

> 数字资源平台可能改变备课劳动在不同环节间的分配。在素材获取环节，一地32名中学教师中的多数受访者认为，统一检索入口节省了寻找教学素材的时间[A]；在资源处理环节，另一地区48名中学教师的访谈反映，资源选择增加的同时，核验、筛选和重新编排的工作也有所增多[B]。由此看，检索便利与资料处理负担可能并存，局部省时尚不能说明备课劳动总量下降。关于处理负担的研究未统计备课总时长[B]，关于检索便利的研究也未观察长期使用或测量课堂教学质量[A]。现有证据因而主要呈现教师对具体劳动环节的感受，尚不足以确定平台对总体耗时及教学效果的影响。

该稿完成了按劳动环节比较，保留来源ID，没有从[C]编出观点。需局部处理的部分是“测量课堂教学质量”与结尾“教学效果”的扩展：任务未讨论教学成效，删去后不损害当前劳动分配判断。总时长未统计与自述证据的边界仍与本题相关，应就近保留。这是本轮可定位的偏题限制说明，不是全文质量失败或规则因果实验。

本报告引用的历史对象均在上述Git基线中。稀疏工作区可用`git show HEAD:仓库相对路径`只读复查以下材料：`tests/evidence/rule-attribution-20261102/README.md`及`ADJUDICATION.md`、`tests/evidence/v0.1.10-release-gate/README.md`、`tests/evidence/gap-verification-20261010/GAPS.md`、`tests/evidence/competitor-rules-20261009/RESEARCH.md`。这些历史文件未在本轮改写。
