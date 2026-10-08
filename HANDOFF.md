# 中文论文写作 HANDOFF

## 与公文仓库的关系和权限边界

- 本论文 skill 脱胎于中文公文写作 skill 的事实边界、材料保真和分层复核经验，但已经拆成独立产品、独立目录和独立 Git 历史。
- 公文仓库位置：`F:\\Workspaces\\chinese-official-writing-skill`。
- 后续线程可以只读查阅公文仓库的提交历史、Prompt、代码、测试证据以及事实保真、引用核对、分层复核等通用经验。仓库作者已明确授权本项目复用其自有代码和 Prompt，但必须完成论文场景适配并在实现中注明来源。
- 未经用户对公文仓库另行明确授权，后续线程不得修改、删除、移动、提交、合并、打 tag、推送、发布、同步或重建公文仓库中的任何文件、镜像和发行包。
- 论文相关修改、测试、提交和发布准备全部在本仓库完成；不得把论文入口、论文 reference 或论文测试回写公文仓库。
- 可复用高频表达扫描、引语保护、只报告不自动替换等通用实现；不得引入公文文种、行文关系、办理要素和格式规则，也不得形成对公文仓库文件或运行路径的依赖。

## 当前状态

- 2026-09-29 用户明确Worktree中小步试验与主次验收尺度后，准入P主次规则和Q2独立证据区分，运行差异仅入口第2步与独立综述叶一条；Q第一版、Elicit硬筛流程取消。本轮28次请求、27份终稿、1次通道失败，最终规则的独立匿名审阅与主审取舍完成，未宣称所有稿件质量通过。0.1.6已发布至GitHub（标签d6487743，下载资产哈希一致）；SkillHub versionId 388710、ClawHub versionId k9769gtwb2mmt873j8jmzz1s2s8famns各受理一次，公开索引/签名和新版详情仍待传播。桌面WorkBuddy已交付0.1.6无Hooks包，字节与标签一致，未实装。发布回执见 `tests/evidence/v0.1.6-release-gate/RELEASE-RECEIPT.json`。详见 `tests/evidence/priority-recalibration-20260929/`。

- 2026-09-29 用户进一步要求实际、稳定的产品改进后，取消仅更新元数据的0.1.6发布；三个平台均未提交0.1.6，README仍为0.1.5。桌面WorkBuddy由0.1.4同步到已发布0.1.5，12文件无Hooks包绑定v0.1.5标签，旧包保留；包内容、元数据顺序、确定性ZIP及桌面哈希通过，未做客户端实装。记录见 `tests/evidence/stable-delivery-20260929/`。

- 2026-09-29 完成当前规则与四项竞品的独立审阅，并对两版“按研究问题安排详略”的入口原子实写。最终决定取消两版新增运行提示，运行树恢复本轮基线 `55668ef9`（写作规则仍为 v0.1.5）：局部选材与证据分层改善未形成跨模型稳定净收益，必列来源虽保住，仍出现证据范围收窄、旁支和重复解释。原始错误、审阅误判、技术超时、模型绑定及逐稿取舍见 `tests/evidence/argument-priority-20260929/`。未升级版本、推送、发布或更新本机安装。

- 2026-09-16 已发布 v0.1.5：产品标签指向 `32950f07f1b257ab071ae1d202818e9a5100d3c4`，GitHub Release `389528303` 已公开且下载资产哈希匹配；SkillHub versionId `316954`、ClawHub versionId `k97amgvcq41pnd5f5g9mdzdyd58efaqh` 均已受理，各提交一次。SkillHub 公开版本已为 0.1.5，平台签名有效且内容指纹匹配；ClawHub 新版详情仍暂不可查，待平台审核/传播。复用 `1242e414` 写稿冷审证据，发布准备不改运行规则；166 项维护测试通过。GitHub/SkillHub 为同一 12 文件 MIT ZIP，ClawHub 为独立 11 文件 MIT-0 包。WorkBuddy 本轮未更新。详见 `tests/evidence/v0.1.5-release-gate/RELEASE-RECEIPT.json`。

- 2026-09-16 开发更新：三主叶四模式、离线引用服务、长稿状态与逐段交付的入口/返回/终止已逐边审查；正文复核改为唤醒宿主未参与起草的 subagent，明确只读、有限返回、不递归及能力缺失回退。对成串否定的两版简化提示没有稳定净收益，取消，保留原有上下文判定段；另保留按结果段/讨论段职责审查结构的澄清。正式写稿沿用公文维护模型池与 Codex CLI `max`；原生子会话已核对精确便宜模型。Python 测试移除 53 项 Markdown/历史语义断言、拆分 13 项混合断言，保留 166 项行为、CLI、性能、只读、打包及证据完整性测试。详细取舍、原始稿件、模型偏差和审阅纠偏见 `tests/evidence/routing-paragraph-review-20260916/`。该开发更新随后在 v0.1.5 发布，桌面的 WorkBuddy 包仍为 0.1.4；不能将任意一批技术成功数当作质量通过数。

- v0.1.4 已于 2026-09-08 合并并发布：产品标签指向 `1245fb240d1f4fa69f42a9eb507ec3e5df7a6e72`，GitHub Release `384604774` 的下载资产哈希匹配；skillhub.cn versionId `299494` 与 ClawHub versionId `k975g5w71e3m83xwz08nj8da4s8e00pa` 均已受理且各提交一次。记录时 SkillHub 公开搜索仍为 0.1.3、签名尚不可查，ClawHub 新版本查询亦暂不可用，公开传播和审核结果尚未确认。WorkBuddy 无 Hooks ZIP 已交付桌面，格式与归档哈希通过，未做客户端实装测试。详见 `tests/evidence/v0.1.4-release-gate/RELEASE-RECEIPT.json`。

- 版本0.1.4修复三个只读检查脚本中的引文分句、异常编号范围、LaTeX正文环境、Markdown围栏及异常数字耗时问题；入口与写作规则维持0.1.3，三条已取消提示不回流。最终219项测试通过，独立复核81个组合样本与58项只读测试通过，83份真实稿件的249个扫描结果与基线一致。发布包继续为GitHub/SkillHub的12文件与独立ClawHub的11运行文件；另按用户参考ZIP生成根目录入口、双语元数据及无Hooks的WorkBuddy包。证据及发布状态见 `tests/evidence/v0.1.4-release-gate/`。

- 2026-09-08 完成社区比较写法、结论认识增量、公文依据/可行性区分三点的便宜模型真实写稿验证：DeepSeek V4 Flash 0731 的 Alibaba 与 Ollama 两渠道及 MiniMax M3，共90次请求、83份实际稿件、6次技术无效、1次非正文交付失败。联合候选、单条隔离及全新题未证明新增三条默认提示具有稳定净收益，三条当前文字均已取消，运行版本维持0.1.3。具体改善句、反例、精确模型ID与45个匿名配对见 `tests/evidence/writing-understanding-20260908/README.md`；不得将完成响应数当作质量通过数，或将两条0731渠道当作两个独立模型家族。

- 本仓库从 `chinese-official-writing-skill` 的论文叶拆分而来，展示名为“中文论文写作”，skill name 为 `chinese-academic-writing-assistant`。
- 当前已完成独立入口、三条互斥专项叶、材料与引用门禁、成品残留终检、显式授权后的学术来源检索与引用覆盖层，以及渐进加载的论文 ANTI-AI 和长稿一致性 reference；运行时提供只读 `citation_audit.py`、`prose_lint.py` 和 `manuscript_audit.py`。
- 版本 0.1.3 在普通论文专项叶中区分材料支持的作者分析与新增经验事实，允许有限强度、范围受控的归纳、比较、解释和候选原因，同时禁止把行为、相关、意向或感受升级为总体需求、效果、机制或因果。五条 provider 路线完成 25 个逻辑配对，冷盲审为候选 16 胜、基线 8 胜、平 1；全新同类任务未确认候选独有硬回退，两个无稳定收益的后续原子已取消。该版本已发布至三平台：GitHub Release ID 为 `379508915`，skillhub.cn versionId 为 `277637`，ClawHub versionId 为 `k97b2cq66c2k0k6chpwrymh4qd8dgqsz`。ClawHub 公开 latest、安全与审核已通过；12 个用户上传文件逐项哈希一致，审核后另有 1 个平台生成的 `skill-card.md`。skillhub.cn 已受理并将上传回执中的 latest 指向 0.1.3，公开搜索和签名仍在传播。当前 ClawHub CLI 将 canonical `LICENSE.md` 一并上传，使该版本为 11 个运行文件加 1 个许可证文件，而平台版本元数据仍为 MIT-0；本轮未重复提交，后续发布须恢复独立的 11 文件 ClawHub staging。写稿证据见 `tests/evidence/evidence-bound-inference-r1/result.md`，发布回执见 `tests/evidence/v0.1.3-release-gate/RELEASE-RECEIPT.json`。
- 版本 0.1.2 在 ANTI-AI 叶中增加完整底稿后的保护性外扩删除式复核，只删无独立论证作用的整句或可分离尾部，疑问即保留，不新增 Hook 或自动改写。四个 provider 的探索与扩大确认共得到 19 个完整配对，候选 11 胜、基线 0 胜、8 平，零硬回退。该版本已发布至三平台：GitHub Release ID 为 `374593638`，skillhub.cn versionId 为 `260345`，ClawHub versionId 为 `k974tymqnq7q8ty6vzfecp5h258cwgk2`；SkillHub 公开 latest 与签名仍在审核传播中。写稿证据见 `tests/evidence/protective-expansion-delete-only-20260822/RESULT.md`，发布回执见 `tests/evidence/v0.1.2-release-gate/RELEASE-RECEIPT.json`。
- 版本 0.1.1 只删除开题报告专项叶的一条重复自述，不改路由条件、材料门禁或研究状态规则。三模型双臂真实写稿 6/6 技术有效且完整加载开题叶，未发现候选独有的目标相关硬失败；全量确定性测试 186 项通过。该版本已发布至 GitHub、skillhub.cn 与 ClawHub：GitHub Release ID 为 `372129584`，skillhub.cn versionId 为 `243739`，ClawHub versionId 为 `k97csn1x5xm82ybrt2655w7fsh8cpgnz`；skillhub.cn 公开搜索、latest 与平台签名复核均已通过，脱敏回执见 `tests/evidence/v0.1.1-release-gate/RELEASE-RECEIPT.json`。
- 版本 0.1.0 收窄了长稿与 ANTI-AI 叶的加载优先级，并将 `.academic-writing/` 落盘限于明确跨轮保存或项目写入授权。多章提纲交叉复测的目标原子由 0/3 改善为 3/3；授权只审任务两臂均 3/3 真实落盘，只作语义消歧。24 次独立前向使用和 90 次三模型调用的报告见 `tests/evidence/prompt-gates-20260812/RESULT.md`。ClawHub 0.1.0 已于 2026-08-18 同步发布，versionId 为 `k97ecxj2kya3pkcgxpyadv8nn58cqsjh`；11 个远端文件与 `v0.1.0` 标签逐项哈希一致，审核为 clean。
- 版本 0.0.9 已在提交 `31d3beac65f6e33663463476f0110f65e08fd821` 发布至 GitHub（tag `v0.0.9`），同一份 12 文件 ZIP 已发布至 skillhub.cn（skillId `98987`、versionId `229892`），未更新 ClawHub。上传时安全扫描、内容审核和总体审核均为 `pending`；随后公开搜索已显示 0.0.9，平台签名校验通过且内容指纹完全匹配。发布包 SHA-256 为 `e3873160e4806f1192df3a1afbf256d515b18523af679524fe161f5c2901fe5f`，回执见 `tests/evidence/v0.0.9-release-gate/RELEASE-RECEIPT.json`。封面源图保留在 GitHub，本轮按用户决定不再通过浏览器重发或补传。
- 版本 0.0.8 已发布至 GitHub（tag v0.0.8）、ClawHub 与 skillhub.cn。升级内容依据公文 skill 1.5.40 已验证更新：终稿模式新增三类否定式句尾候选、意义支撑句尾成簇与正文外制作性注记标题检测；ANTI-AI 复核新增连续否定式收口与正向状态承接、纯检测模式输出约定；入口增加终稿 lint 短指针；ANTI-AI 首段加载条件减载为入口指针。开发轮真实写稿 A/B（4 任务双臂＋确认轮 T5/T6）未发现可复现候选独有硬失败，首轮两起候选独有失败经确认轮判定为双臂共有噪声。发布门禁轮（全新任务 R1–R4、全新会话，对 v0.0.7）机械门禁 8/8 通过，双盲裁判一致，已决定任务 Candidate 3 胜、Baseline 1 胜，零硬 FAIL，判定无回退；证据在 `tests/evidence/v0.0.8-release-gate`，回执在 `.release/release-v0.0.8-receipts.json`（未跟踪）。skillhub.cn 0.0.8 已受理，审核与公开 latest 传播以平台为准。
- 当前能力仍限定中文本科论文、硕士学位论文、课程论文、开题报告和独立文献综述。英文论文、投稿、统计分析、答辩、排版和检测规避尚未纳入。
- 项目与 skillhub.cn 使用 MIT；ClawHub 按平台规则采用 MIT-0。后续版本同步至 GitHub、skillhub.cn 与 ClawHub。

## 迁移来源

- `aaba577`：首次在原公文 skill 中加入有边界的中文论文入口。
- `6c85f93`：限制稀疏材料下为凑标准章数而重复提纲。
- `c5d81ce`：将普通论文、开题报告、独立文献综述拆成互斥专项叶，并清除论文页中的公文对照措辞。
- `a2e489658988f404a6ea5a627eda165da89e9a86`：原仓库 1.5.9 发布提交，本仓库三份 reference 取自该版本。
- `c9cdc3aa1f31afa1f5e936f3ef613eed8604e4cd`：拆分开始时原仓库 main 状态。

## 本次拆分修改

1. 新建独立 `chinese-academic-writing-assistant` skill，不复用原仓库 slug、identifier 或发布回执。
2. 以迁移的三份论文专项资料为起点，分别按普通论文、开题报告和独立文献综述完成材料门禁、模式和交付协议适配。
3. 新写完整 `SKILL.md`，用研究问题、证据状态、引用、论证和学术复核组织工作流，不引用公文文种、行文关系、办理要素或公文 reference。
4. 保持“只按给定事实和已核验来源写、材料不足不外扩、不编数据和文献、正文后可给候选建议”的边界。
5. 增加 Prompt 驱动的 ANTI-AI 表达复核：先统计高频句式和词组，再结合前文、材料与论证任务判断，只局部改写确认存在虚设否定、虚假对比或机械重复的句段；不变量包括事实、数字、引用、术语、研究状态、否定范围和论断强度。
6. 将详细 ANTI-AI 规则移至可选共用 reference，只在用户明确要求文风复核或已定位具体模板问题时加载；新增从作者自有公文脚本适配的只读候选扫描器，排除公文文种、办理要素、项目卡片和算力规则。
7. 增加显式授权后的来源检索与引用覆盖 reference；来源检索应另开上下文或轮次，只把紧凑证据账本交给任务叶，ANTI-AI 复核再单独进行。新增只读引用审计脚本，只做引用标记覆盖和结构提示，不代替语义核验，也不按固定比例补引。无模板时富文本使用顺序编码上角标，纯文本和 Markdown 使用 `[1]`，文末列对应参考文献。

## 已有验证证据

原仓库 1.5.9 发布前曾使用 6 个未见 prompt 覆盖普通论文提纲、开题报告、独立文献综述和论文改稿，独立 verifier 全部判为 PASS；未观察到补造事实、数据或文献，也未观察到公文结构混入论文输出。运行环境未提供可核验精确模型 ID，因此这些结果只属于独立真实写稿 sanity，不代表跨模型统计结论。

原始证据仍保存在原仓库：

- `tests/evidence/release-1.5.9-routing/`
- `tests/evidence/academic-leaf-isolation-20260713/`
- `tests/evidence/minimal-fix-gate-20260713/`

## 迭代顺序

1. 先冻结一个可归因的 Prompt、reference 或同源成熟实现原子，复用现有工具做真实写稿 A/B，不先开发新解析器、胶水或工程门；允许直接复用作者自有公文项目的成熟实现，不以字符最少代替功能完整。
2. 先按事实与来源保真、结论强度、直接可用性和修改负担盲审，再判断问题是否能由本次 DIFF 解释；与 DIFF 无关的模型波动和技术故障只记录，不计候选回退。基于已给事实形成的合理推断、归因、比较、论点、论据、解释和建议不是新增事实；只有冒充来源内容、研究发现、已验证机制或确定状态时才按事实外扩处理。
   主次审阅按研究问题、章节任务和材料的实际作用判断详略，关键反证、分歧及改变结论的限定属于论证重点；用户要求逐项呈现的内容单独核对。材料篇数、正反立场或段落长短不决定轻重。区分任务与版本的执行优先级、证据强度、正文详略三个层次；对不需进入正文的旁支不以“列得更全”加分。主次省略与展开按用户用途判断，持平不算回退，旁支更多不算更全；局部收益与稿件错误、交付问题分开登记。规则规格明确化与稳定质量提升是两项结论，不要求每题每模型都更好。原取消候选须经新的用户范围与实写复核才能准入；本轮P复测记录见priority-recalibration-20260929，不新增Python语义门。
3. 样本不足时增加全新真实写稿，不向用户交付 `HOLD`。Markdown 规则以新鲜成稿和未参与起草的宿主 subagent 独立语义评审决定取舍，不为规则措辞、词频、路由语义或写稿优劣设置 Python 门禁，收益成立后也不补替代语义测试。Python 实现改动须运行与行为、CLI、安全、性能和打包相关的最小测试。
4. 发现硬回退时保留已验证的正向原子，先确认是否与 DIFF 有关，再拆出最小修正并用新鲜样本复测；只有整体无收益、最小修正后仍持续净负，或核心机制与任务目标冲突时才取消。最终只交付“合并”或“取消”。

## 后续线程应先做的工作

1. 冷审独立入口与三份 reference，确认 `chinese-academic-writing-assistant` 的路由、边界和本地验证证据。
2. 若扩展英文论文，先单独设计语言路由和引用规范，不直接翻译中文 Prompt，也不要让中英文链同时加载。
3. 先用当前候选真实写稿，再由独立宿主复核者审查 AI 味、整体结构、逻辑、重复、流水账及段落范围；旧稿和起草者自查不能代替这一层。Python 或打包改动运行相关最小测试，整体验证使用 `py -3 -B -m unittest discover -s tests -v`。保留历史证据的结构与字节验证；`tools/check_academic_outputs.py` 和 `tools/check_language_hygiene_outputs.py` 仅重放旧实验，其严格计数、固定词句、阈值和判词不作为当前写稿或规则发布的准入门。
4. 每次发布前分别核对 GitHub、skillhub.cn 与 ClawHub 的 slug/identifier、账号状态和现有版本，不得沿用其他项目的平台 ID、标签或发布回执。
5. 各平台发布包遵循仓库机器策略，图标作为 SkillHub 平台资料单独维护。发布后只提交不含凭据的三平台回执；原始包、临时目录和本机回执只留在 `.release/`。
6. 不继承原公文 skill 的版本号、平台 ID、标签、审核结果和发布承诺；新产品从独立版本策略开始。
7. 文风规则取舍依据真实稿件中可归因、可复现的收益与损害；样本不足时扩大新鲜写稿，旧实验的 3/2/2 计数只解释其历史设计。事实、数据、引用、因果、否定范围和研究状态错误经独立复核确认后，应修正对应稿件并做 DIFF 归因。Python 词表、启发式和保护区改动仍须复现具体缺陷并回归，保留只读与候选定位的行为测试；不得因卸下 Markdown 语义门而删除扫描功能或放松其测试。
8. 长稿层下一步优先做真正跨会话、跨学科的旧基线/候选配对消融，验证 `paper-state.md` 的状态更新、冲突合并、旧状态淘汰和文体漂移控制；不要因当前单组四章前向任务继续增加段落级规则。

## 写稿与冷审模型规范

自 2026-09-21 起，后续实验遵循中文公文项目当前模型规范，并在调用前核对实时 model catalog。旧 `MODELS.md` 和历史 evidence 只记录当轮实际路线，不因当前换模而回写。

- Alibaba writer：`alibaba-token-plan-responses/deepseek-v4.1-flash`、`alibaba-token-plan-responses/qwen3.8-flash`。非 Alibaba writer 仍可使用 `command-code/deepseek-deepseek-v4.1-flash`、`minimax-cn/MiniMax-M3`、`ollama-cloud/glm-5.3-flash`，按任务分散 provider。
- Alibaba 独立冷审：`alibaba-token-plan-responses/glm-5.3`、`alibaba-token-plan-responses/qwen3.8-max`。非 Alibaba 冷审仍可使用 `ollama-cloud/kimi-k3`、`xai/grok-4.6`。
- 新任务不再调用 `alibaba-token-plan` 或 `alibaba-token-plan-2`。不使用 Astra 作为写作或冷审子智能体，不让子代理无意继承主模型；显式指定模型和受支持的 effort，并核对实际会话元数据。
- 外部 provider 的 Desktop 子任务若出现加密任务不可读，改用已有明文 Codex CLI 批量通路。每个候选在隔离目录读取自己的规则；正文作者和独立复核者分开上下文，保存可见稿件、意见及模型来源，不归档隐藏推理。
- 不把“按词表没报错”“成功读了 SKILL”“模型返回了文字”当作正文质量通过；也不把冷审意见当标准答案。对照原始材料核实否定对象、状态、作者分析和真正越界，保留技术无效及不采纳意见的理由。

## 不应回流的内容

- 不复制公文文种表、主送与落款规则、行文关系、办理要素、GB/T 9704 或 AI 算力专项。
- 不用“不要像公文”“区别于公文”等反向提示组织论文规则。
- 不把旧测试中的匿名样稿当成事实、模板或默认正文。

## 2026-10-09 当前规则筛查闭环

用户重新确认论文项目后，在academic-rule-screen-1009隔离工作树筛查当前入口、三主叶、来源/长稿/文风层，并对共用独立证据候选及最小修订做32次构造材料实写、16完整配对。两版候选均取消，运行规则保持0.1.6基线；没有发布、推送或桌面更新。筛查位置、候选完整树、失败稿、独立复核范围与最终理由见tests/evidence/rule-screen-20261009/SCREENING.md和ADJUDICATION.md。

文件隔离评测3次调用未能可靠读取各自冻结副本，停止且不计配对；后续用完整冻结入口和唯一主叶的文本输入完成验证，实际完整输入与prompt哈希逐次核对。这条通路仅验证规则文本行为，不证明自主加载或客户端集成。R2独立冷审覆盖Qwen作者4对；R1盲审未完成，未被当作通过。当前基线同样存在漏材料/过宽审查意见，不能用取消候选宣称现版无风险。
