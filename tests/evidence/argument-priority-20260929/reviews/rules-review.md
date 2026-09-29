# 原始只读子代理报告

会话：01a0ec9c-f9d7-7613-83ee-f20181eefefd。以下为可见报告，主审核对和不采纳意见另见 RESEARCH.md。

核对完成：worktree 中冻结原子与主流程描述一致（仅 SKILL.md 第2步一处未提交改动 + 未跟踪 `tests/evidence/argument-priority-20260929/`，原 main 未动）；公文侧 accurate-rejudge 与 stable-2.0.18 的边界原句也已定位。以下为只读报告。

---

# 只读审阅报告：学术 Skill 引入公文“主次层级、分清轻重”

**报告边界**：本报告由当前会话模型 qwen3.8-max 完成（属 [HANDOFF.md](F:/Workspaces/chinese-academic-writing-skill/HANDOFF.md:86) 冷审模型池内），全程只读：未修改文件、未提交、未派生代理、未联网。审阅对象为学术仓库稳定版 main@`55668ef`（v0.1.5 后 2 个未推送提交）与公文仓库 main@`adfbdd6d7`（2.0.18 后）。未打开 worktree 中任何 A/B 稿件文件，未研究维护工具实现；公文仓库按 [HANDOFF.md](F:/Workspaces/chinese-academic-writing-skill/HANDOFF.md:8) 权限边界只读。

## 一、公文新思路：确切位置、提交与验证边界

产品面现行规则只有一处共性句：[writing-rules.md](F:/Workspaces/chinese-official-writing-skill/chinese-official-writing/references/writing-rules.md:25) 第 25 行，“成稿先明确全文主旨并据此安排篇幅；每段围绕一个要点，核心事项作为主体，背景、反面观点和边界只占其对主旨所需的篇幅。复核时合并无新增信息的重复论证；用户指定必须逐项呈现的内容照办。”准入提交 `988124f6c`（2026-09-28）。关键演化：R1 原句含“直接服务主旨的事实和有据分析**写充分**”（[r1-rule.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/global-main-point-20260928/r1-rule.md:5)），因 P3 反方控制题中候选两次出现过强状态推断而被删（[result.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/global-main-point-20260928/result.md:9)），R2 仅保留主旨、段落要点、主次篇幅、用户点名照办四项。准入自述边界（result.md:13）：“准入证明的是产品明确表达主次结构要求并通过本轮有限实写；不证明模型已稳定写出更聚焦的每篇文章。”

用户今日确认的边界与仓库证据一致：`8c301834a`（accurate-rejudge-20260929）复判 18 篇新稿后结论为“产品主次原则保留；稳定净收益仍未证实”（[result.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/accurate-rejudge-20260929/result.md:3)，第 51 行明确“不能称主次优化已经验收，也不因单篇波动删除合理原则”）；专项有效指 `08920c3bf`（2.0.18）在 [genre-playbook-project-application.md](F:/Workspaces/chinese-official-writing-skill/chinese-official-writing/references/genre-playbook-project-application.md:19) 第 19 行的正文/附件分工与归属规则，其证据是 [actual-project-focus-20260929/result.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/actual-project-focus-20260929/result.md:13) 两次独立成稿分工清楚，以及 [release-notes.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/release-2.0.18-20260929/release-notes.md:3) 三条专项改动。

对学术适配最有约束力的三条否定性证据：其一，更早的泛化候选两次 HOLD——[focus-gate-review-20260928/result.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/focus-gate-review-20260928/result.md:30)（无稳定净提升）与 [focus-length-readback-20260928/result.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/focus-length-readback-20260928/result.md:24)（写手贴约数下沿、旁支占正文，“不支持继续把相近禁止句堆进共性规则”）；其二，“明确无关记录排除”窄规则在 G1/G2 复现局部选材收益，但因候选新增“将督促”等材料外安排未定清而暂不恢复合入（accurate-rejudge result.md:53-60）；其三，全部结论都以“同模型同题面同交付约定”分臂、事实/强度错误与详略收益分开登记为前提（[test-matrix.md](F:/Workspaces/chinese-official-writing-skill/maintenance/tests/evidence/stable-2.0.18-20260929/test-matrix.md:15)）。

## 二、学术侧现行规则：缺口、重复、冲突与过约束证据

**缺口（原子填补的是真实空白）**：学术侧涉及篇幅的规则有五处——[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:60) 第 60 行（规划层“分配篇幅”）、[academic-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:7) 第 7 行（“规划层负责材料和篇幅”）与第 17 行（偏短只展开已有证据、偏长先删重复旁白铺垫）、[long-form-consistency.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:33) 第 33 行（无明确范围不自设均匀篇幅）、[anti-ai-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:38) 第 38 行（不为满足篇幅恢复已删内容）。五处都只管“多长/怎么删”，没有任何一处给出“按材料对当前问题的作用分配详略”的正面标准；公文侧被证实的失败模式（无关台账占整节、重复边界说明贴下沿）在学术规则中同样无对应约束。

**重复（原子未引入，正确）**：公文 R2 的“合并无新增信息的重复论证”在学术侧已有两处等价物——[anti-ai-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:13) 第 13 行的流水账定义（“相邻内容只换说法重复同一观察、没有增加本节所需的信息”）和 [SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:80) 第 80 行复核重点（重复表述、逐项流水账）。冻结原子没有搬入合并句，避免了第三处重复。

**冲突点（原子已规避两处）**：公文 R2 “背景、反面观点和边界只占其对主旨所需的篇幅”与学术保护区直接冲突——[anti-ai-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/anti-ai-writing.md:27) 第 27 行明确“反证、研究限制和材料明确记载的争议可以保留”，第 34 行删除式复核把“必要的结论限制、证据冲突”列为承担作用即保留项。冻结原子第二句“会改变判断的反证、分歧和必要限定仍属论证重点，不能因篇幅少或不支持主张而降为次要”正是学术必需的改写，公文原句不可直搬。另一处：公文“每段围绕一个要点”与 [academic-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:9) 第 9 行的段落模型（同一子主张的证据、解释和限定保持在一起；立场改变才分段）不相容，原子保留了“最小论证单元”原句、未导入“每段一个要点”，处理正确。

**残余观察点（判定阶段需单列）**：原子的“充分展开”与被删的公文 R1 “写充分”措辞同源，而 R1 正是该措辞在反方控制题诱发过强状态推断（global-main-point result.md:9，R2 仍残留一稿“运行压力并存”偏强句）。学术侧虽有锁定项（anti-ai-writing.md:7、30）和有限强度规则（academic-writing.md:13）兜底，A/B 判定仍应把“强度升级、补 bridging 分析、把相关推成机制”登记为候选独有风险线索，与详略收益分开。

**优先级区分（用户要求的核心）**：[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:40) 第 40 行是规则执行优先级（用户要求 > 模板 > 最新底稿 > 旧稿），原子只改第 2 步的内容组织标准，未触碰第 40 行，两个层次分开了。一处结构差异需要控制题验证：公文 R2 把“用户指定必须逐项呈现的内容照办”写进同句作逃逸口，冻结原子没有对应句，依赖第 40 行全局优先级、[academic-writing.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-writing.md:11) 第 11 行（学校/导师/载体规范优先）和 [academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:13) 第 13 行（用户给定来源 ID 必须保留）覆盖。“不按来源篇数平均铺排”遇到明确要求逐篇述评的作业时是否被正确压制，是原子相对公文版的唯一未闭合点。

**无固定模板**：原子无比例、无节数、无句数要求，与 long-form-consistency.md:33、47（不转成平均句长、固定段数、配额）相容。

## 三、对冻结原子的结论

worktree（C:/Users/admin/.codex/worktrees/academic-priority/chinese-academic-writing-skill，分支 codex/academic-priority-20260929）中未提交的 SKILL.md 第 2 步改动是当前合适的最小原子：单点落位、作用性详略标准、反证保护、无模板，且未复制公文的两处已知冲突措辞。合入预期应按公文准确口径设定——证明目标是“明确表达详略规格且无候选独有回退”，不是“稳定提升每篇聚焦度”。提交时按 [HANDOFF.md](F:/Workspaces/chinese-academic-writing-skill/HANDOFF.md:7) 要求在证据目录注明适配来源（`988124f6c` 及其前后 HOLD 链），迭代与判定沿用 HANDOFF.md:65-68 的原子冻结、DIFF 归因、只交付“合并/取消”流程。

## 四、适合新鲜 A/B 的场景（对已启动四新题的补充轮设计）

1. **反证保护控制**（对应公文 P3）：讨论节材料含一项与中心判断相反的研究，用户要求“把中心论点写充分”。判定：反证是否保留位置与限定、未被降为套话或删除；单列检查“充分展开”是否诱发强度升级。
2. **综述疏密 + 必列双臂控制**（对应公文 G3 与 test-matrix“指定保留信息不因压缩删掉”）：8–10 篇来源中 2–3 篇直接支撑综述问题；同一材料跑两臂——无特殊要求 vs 明确要求“每篇研究各用一句话述评”。判定：详略疏密是否合理、来源 ID 与归因完整；逐项要求是否压过原子。这是补上第二节所述逃逸口缺证的必要控制。
3. **篇幅区间贴沿**（对应 focus-length-readback HOLD 的成因）：给 3000–3500 字区间、材料仅支撑约 2500 字有效论证的章节。判定：候选是否收缩或移建议，而非用重复边界说明、旁支材料贴下沿；偏短时是否只展开已有证据（academic-writing.md:17），不为达标补造。
4. **底稿修改聚焦压缩**（测原子的修改路径而非起草路径）：底稿背景章占比过高且有两处同义重复论证，要求“压缩聚焦”。判定：是否削减旁支同时不删必要限定与反证（anti-ai-writing.md:27、34），删除式复核“疑问即保留”边界是否被原子 loosening。

执行与判定沿用 HANDOFF.md:83-89 模型规范（便宜写手按任务分散渠道、冷审独立、核对实际会话元数据），并采用 accurate-rejudge 修正后的口径：审稿包携带完整原始请求与匿名全文、两臂同尺度、事实硬错/强度错误/详略收益/单稿波动分开登记（accurate-rejudge result.md:7-15）。本报告不做写稿评审，后续由未参与规则者承担。


