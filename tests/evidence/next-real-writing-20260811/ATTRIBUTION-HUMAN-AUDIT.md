# 归因轮人工内容复核

## 结论

人工复核支持撤回当前两行候选，但不支持把它表述为“已证实候选造成回退”。自动归因没有达到受控伤害或收益门槛；人工纠正四处高置信漏标后，结论仍是没有 `CAUSAL_HARM`、也没有 `CAUSAL_BENEFIT`。

## 多数标签漏标

1. `A1-R1 / Baseline / FALSE_CROSS_SOURCE_LINK` 应为 `PRESENT`。稿件把 S1/S2 的局部效果与 S3 的体验担忧连接为持续使用的条件链：“即便 AI 反馈在局部指标上有效，其能否被接受并持续使用，仍取决于学生对质量与诚信的感知。”材料没有建立该关系。
2. `A1-R4 / Baseline / FALSE_CROSS_SOURCE_LINK` 应为 `PRESENT`。稿件以 S1 引文准确性不显著和 S3 虚假引文顾虑推出“体验感知未必总能对应到可测量的结果”，跨样本建立了材料未给出的对应关系。
3. `A3-R2 / Candidate / CITATION_LOCALITY_FAILURE` 应为 `PRESENT`。全文只写 `S1`—`S5`，五个任务要求的方括号来源 ID `[S1]`—`[S5]` 全部缺失；机械门已经逐项确认。
4. `A3-R3 / Baseline / CITATION_LOCALITY_FAILURE` 应为 `PRESENT`。“两项研究在论证评分上均未观察到显著差异”把 S2 的不显著移接给 S1；“且都未测量长期保持”又把只明确属于 S2 的边界移接给 S1。

按上述纠正，`FALSE_CROSS_SOURCE_LINK` 从四次双方均未出现改为 `baseline_only=2, neither_present=2`，只能记 `AMBIGUOUS`；`CITATION_LOCALITY_FAILURE` 改为 `candidate_only=1, baseline_only=1, both_present=1, neither_present=1`，仍为 `NO_DIRECTIONAL_SIGNAL`。其余三个原子的多数标签未发现改变门结论的错误。

## 减负与去 AI 味

- 24 稿可见字符总量从 Baseline 11,434 降至 Candidate 11,162，只减少 272 字符（2.4%）。分 provider 为 Ollama -563、Alibaba -338、MiniMax +629，表现为一部分截短、一部分膨胀，不是稳定减负。
- 机械合规 Baseline 9/12、Candidate 5/12。Candidate 有五次低于字数下限、一次高于上限，并有一次整组方括号来源 ID 缺失。
- 两臂都反复出现材料外背景、未知任务或情境解释、访谈共现因果化、来源状态和文献类型误写、事实移接、题目泄漏、字数失控与来源 ID 格式错误。
- “效果层面—体验层面—综合来看”等模板链没有显示出稳定改善。

## 表述边界

两行候选本身语义合理，人工复核没有证明其导致稳定回退。撤回依据是没有达到收益门、机械合规下降且目标判断仍有未定项；来源可比性、未读材料边界和来源就近原则保留为待重写、待用全新任务验证的设计目标。
