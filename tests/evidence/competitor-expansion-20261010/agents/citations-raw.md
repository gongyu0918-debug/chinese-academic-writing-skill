检索完成，以下是本轮只读核对的结果。四个项目均与你点名的 K-Dense、Marazii、SNL-UCSB、BESSER-PEARL、docxology 等来源不重复；所有规则均来自实际打开的文件正文（目录仅用于定位），未读记忆、未改文件、未执行竞品、未发送他任务消息。

## 一、comeonvictor/claude-code-deep-research — 引文管理与二手转引

- 作者/项目：个人作者 comeonvictor，"Deep Research skill for Claude Code"。实开文件：[references/citation_rules.md](https://github.com/comeonvictor/claude-code-deep-research/blob/main/references/citation_rules.md)（全文）。
- 可用原子规则（均出自上述文件小节）：
  - "Mandatory Citation Requirements"：每条事实性声明必须含五个要素——作者/机构、发布日期、来源标题、URL/DOI、页码或小节。
  - "Verification Protocol → Before Adding Citation"：加引用前必须依次打开来源 URL、比对引文/数据与原文、核对作者、确认日期、评估来源质量。
  - "Archive Requirements / Broken Link Handling"：新闻类来源留 archive.org 存档链接；社媒截图带时间戳；API 或动态内容注明检索日期；坏链以存档版本标注。
  - "Special Cases → Secondary Citation"：二手转引默认避免，只能标 `(原作者, 年, as cited in 二手作者, 年)`，且必须先尽力找到原始来源。
  - "Common Mistakes to Avoid"：禁用不加具名的归因（"Studies show"、"Experts say"、"According to reports"），必须落到具体来源。
- 局限/不宜移植：仓库 2026-04-10 当日新建、当日推送、0 star，规则本身无任何使用验证；文中提到 A–E 来源评级但该文件无评分细则；MLA 格式与按报告体裁的"引文密度"表不宜移植；"不臆造引用"维度和现有能力同义。
- 许可证：已核实。GitHub API 仓库元数据 license=MIT（未逐行读 LICENSE 文本）。

## 二、ecylmz/academic-writing-skills — 证据追踪与引用完整性

- 作者/项目：ecylmz，agent-neutral 学术写作 skill 套件。实开文件：[AGENTS.md](https://github.com/ecylmz/academic-writing-skills/blob/main/AGENTS.md)、[skills/en/research-integrity-audit/SKILL.md](https://github.com/ecylmz/academic-writing-skills/blob/main/skills/en/research-integrity-audit/SKILL.md)。其引用的 references/ 深层文件未展开（未评估）。
- 可用原子规则：
  - "Safety and Integrity Boundaries"（AGENTS.md）：不得声称某引用支持某句，除非该来源已核验或用户提供了相关段落。
  - "Modes"（SKILL.md）：claim-evidence、citation-integrity、full-integrity 三种审计模式分离，各有固定输出表结构。
  - "Status Labels"：声明级标签 supported / weak / missing / overclaimed / misaligned / requires source check；引用级标签 OK / MISSING_REFERENCE / ORPHAN_REFERENCE / STYLE_INCONSISTENCY / SOURCE_DOES_NOT_SUPPORT / NEEDS_FULL_TEXT_CHECK / INCOMPLETE_METADATA；来源核验结论另设 verified / minor distortion / major distortion / unsupported / unverifiable access / scope mismatch。
  - "Status Labels + Hard Constraints"：来源不可得不得标 supported；全文未读只能标 requires source check / NEEDS_FULL_TEXT_CHECK；全文缺失标 unverified。
  - "Hard Constraints"：不得仅凭标题或摘要主张引用支持，除非声明明确出现在该层级；证据只支持更弱或更窄版本时不得标 supported。
  - "What to Check #3"：声明依赖具体实证结果时，综述不能替代一手来源。
  - "Hard Constraints"：保留既有 citation key，除非用户要求改名（此条与现有"最小改动"同义，不计增量）。
- 局限/不宜移植：仓库无许可证声明，且自述改编自上游项目（.upstream/SOURCE_NOTES 机制），移植前还要核对上游授权链；土耳其论文与英文文章双场景，中文需重写。
- 许可证：未核实。API license=null，仓库根目录无 LICENSE/COPYING 文件，只有 AGENTS.md、SOURCE_NOTES.md、skills/ 等；文本不宜直接移植，只宜吸收思路。

## 三、Future-House/paper-qa — 引文键绑定与证据追踪

- 作者/项目：组织 Future-House，论文问答 RAG 项目（9.3k star，活跃）。实开文件：[src/paperqa/prompts.py](https://github.com/Future-House/paper-qa/blob/main/src/paperqa/prompts.py)（全文）。
- 可用原子规则（按文件内常量定位）：
  - `citation_prompt`：找不到 DOI 就省略，明确禁止编造 "10.xxxx" 式 DOI。
  - `structured_citation_prompt`：title/authors/doi 结构化抽取，任何字段找不到即返回 null。
  - `qa_prompt` + `CITATION_KEY_CONSTRAINTS`：答案每个部分在句末用引用键就近标注；只允许使用上下文里出现的键；并给出合法/非法格式清单（禁止 "and"、分号、键拼接、以 "Author et al. (2023)" 充当键）。
  - `CANNOT_ANSWER_PHRASE`：上下文信息不足时输出固定不可答句，并映射为作答失败状态。
  - `answer_iteration_prompt_template`：迭代重答只能使用当前上下文中的键；旧答案里有、但新上下文没有的键不得沿用——对应"改稿后引用漂移"问题。
  - `summary_prompt`：证据摘要不得直接回答提问；数字、公式、直接引语须显式标注；无关内容回 "Not applicable" 并给 1–10 相关度分。
- 局限/不宜移植：这是代码层 RAG 提示词，"只在上下文内引用"以闭环语料库为前提；`pqac-*` 键格式与 MLA 输出为该系统内部约定，不宜照搬；不含写作体裁与行文规则。
- 许可证：已核实。API license=Apache-2.0（未逐行读 LICENSE 文本）。

## 四、brian-caylor/StoryEngine_Template — 长稿状态协作

- 作者/项目：brian-caylor，面向 Claude Code 的长篇写作脚手架。实开文件：[SYSTEM_PROMPT.md](https://github.com/brian-caylor/StoryEngine_Template/blob/main/story-engine-template/SYSTEM_PROMPT.md)、[prompts/draft-chapter.md](https://github.com/brian-caylor/StoryEngine_Template/blob/main/story-engine-template/prompts/draft-chapter.md)、[LICENSE](https://github.com/brian-caylor/StoryEngine_Template/blob/main/LICENSE)。
- 可用原子规则：
  - "Core Directives 1"（Files Are Memory）：状态不得靠对话历史承载，事实、决定、风格必须落到项目文件，"不在文件里就不存在"。
  - "Core Directives 2" + draft-chapter.md "Step 1"（Read Before Write）：动笔前按固定清单读取上文、场景卡、状态追踪、风格指南、角色文件，明确"不得跳过"。
  - "Core Directives 3" + "PHASE 6 → Post-Draft Update (MANDATORY)" + "Step 5 Self-Check"：每次写完必须更新三处——事实追踪、线索追踪、变更日志——并自查未引入矛盾后才呈现给用户。
  - "Core Directives 4"（User Is the Director）：只提议、用户决定，未经批准不得推进下一阶段。
  - "Emergency Protocols → Contradictions Detected"：发现矛盾立即停止写作，记录变更日志，向用户呈现两个版本请其裁定，再同步更新所有受影响文件后恢复。
  - "Emergency Protocols → Context Window Limits"：超长稿按需定向读取、以状态追踪文件充当压缩摘要、整稿复核按 3–5 章分批。
- 局限/不宜移植：小说体裁字段（voice guide、scene card、POV、线索红黄绿状态）不能直搬到学术写作；多处绑定 Claude Code CLI；迁移时需把"章节/线索"重定义为"论证单元/待核项与待补证据"。
- 许可证：已核实。LICENSE 原文已打开：MIT，Copyright (c) 2026 brian-caylor。

## 待验证建议（4 条，均未落地）

1. 二手转引兜底：无法获得原文时才允许 "as cited in" 双作者标注，并强制在正文显式提示转引（来源一）。对现有能力是新增项，需实测其与"就近绑定"规则是否冲突。
2. 缺失字段置空三件套：缺失 DOI/字段一律置空、禁止 10.xxxx 式假 DOI、重写后旧引用键不得沿用（来源三）。是对"禁止伪引用"的可执行化，须验证现有 Skill 是否已覆盖到同等粒度。
3. 层级与支持状态联动：标题/摘要层级一律不给"已支持"结论，只给需查全文类标签；来源不可得一律标未核验（来源二）。只宜借思路，因该仓库无许可证。
4. 长稿状态"写后必更 + 变更日志 + 矛盾停机"协议：固定更新时点、变更记录格式、冲突时停机并请用户裁决（来源四）。现有"状态文件授权保存"之外的新增是更新时点与冲突处理流程，需在学术长稿场景做字段改写后试验。

本轮检索时间 2026-10-10（UTC+8）；只读完成，无文件改动、无记忆读取、无竞品执行、无跨任务消息。
