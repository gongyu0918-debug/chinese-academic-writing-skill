# DIFF 因果归因重复轮预注册

## 为什么另做归因轮

第三整轮的原始严格门结果永久保留：Candidate 机械覆盖后 7 胜、Baseline 5 胜，Candidate-only hard fail 存在，原扩展门为 FAIL。该结果说明这批单次成稿不能直接发布候选，但不能自动证明每个判负都由两行 DIFF 导致。

两份独立内容审计均指出，多数 Candidate 失分来自漏来源方括号、擅加题目、数字或文献类型误写、因果升级和 provider 随机措辞，缺少从“来源可比性与综合边界”DIFF 到错误的机制路径。用户进一步明确：与 DIFF 无关的单次波动不得计为规则回退。归因轮只检验仍属 `AMBIGUOUS` 的三组，不改写原门结果，也不用归因轮重新挑候选措辞。

## 冻结对象

- Baseline：`v0.0.8^{commit}` = `09b89a6f49f0d97f5bdd983fe29354636a0f5008`。
- Candidate：运行提交 `66ea04b18d066ac3f2ed075cb91b5a1659c1a131`。
- 唯一运行差异仍为 `references/academic-literature-review.md`，Candidate 净减 8 字符。
- 任务复用 H2/H4 是为了重复检验已见错误类别，不计作新鲜候选胜负；每次仍为全新 ephemeral 会话、首个 post-read final、零模型重试。

## 三组疑点与重复矩阵

每组运行 4 个独立 replicate，每个 replicate 在两个全新 ephemeral 会话中并发启动 Baseline 和 Candidate，共 12 对、24 次写稿。成对并发避免把固定先后顺序误当成 arm 效应：

| 组 | provider / task | 只检验的 DIFF 相关疑点 |
| --- | --- | --- |
| A1 | Ollama / H4 | `FALSE_CROSS_SOURCE_LINK`：把正向与不显著结果写成伪一致，或把 S1/S2 效果与 S3 体验强连成速度导致同质化 |
| A2 | Alibaba / H2 | `STABILITY_AMPLIFICATION`：把合法共同方向升级为稳定、可重复、稳健或可推广；`LEGAL_SYNTHESIS_MISSING`：没有明确联合归纳 S1/S2 均观察到参与提升 |
| A3 | MiniMax / H4 | `UNKNOWN_DIMENSION_EXPLANATION`：用材料未知维度解释差异；`CITATION_LOCALITY_FAILURE`：提到来源内容却遗漏、错配或远离必需来源标记 |

漏方括号、加题目、普通语言偏好和其他材料外事实仍记录，但除非属于上表目标类别，不计 DIFF 回退。相同错误若 Baseline 同样复现，计 provider/task 固有风险，不计 Candidate-only 回退。

## 技术与盲审

- 三组均配置原 provider/model 与 `model_reasoning_effort=max`；两臂使用相同 task、prompt、超时和只读权限。
- 24/24 调用必须通过第三整轮同一输入快照、三命令配对、运行指纹、post-read final 和 SHA 门禁；任何技术无效使整轮无效，不补跑单项。
- 固定种子 `academic-synthesis-attribution-20260811-v1` 预先生成三名裁判各自平衡且不同的映射。先运行两名裁判；某一 target/side 标签不一致或出现 `UNCERTAIN`、`UNJUDGEABLE` 时，才对相应 pair 启用第三裁判。
- 裁判只判断每组预定义风险原子在左右稿中 `PRESENT`、`ABSENT`、`UNCERTAIN` 或 `UNJUDGEABLE`，不得给总体文风胜负。`PRESENT` 必须给出原稿逐字锚点；漏题目、其他事实错误等只进入 `unrelated_errors`，不得影响 target 标签。
- 对每个 target/arm 取两票多数；没有两票同向则该 target/pair 不可计分。两臂共同出现、共同未出现均保留在绝对质量记录中，但不提供方向性归因。

## 因果判定

对每个风险原子分别统计 4 个 replicate。每个可计分 pair 归为 `candidate_only`、`baseline_only`、`both_present` 或 `neither_present`：

- 只有 `candidate_only >= 3` 且 `baseline_only == 0`，才确认 `CAUSAL_HARM`。
- 只有 `baseline_only >= 3` 且 `candidate_only == 0`，才确认 `CAUSAL_BENEFIT`。
- 两个方向的独有出现数都不超过 1，记 `NO_DIRECTIONAL_SIGNAL`。
- 其余完整结果记 `AMBIGUOUS`；少于 4 个可计分 pair 记 `INSUFFICIENT`。二者都不是规则回退，但必须作为剩余风险报告，不能包装成收益。
- 归因轮只决定错误能否归因于 DIFF；原机械错误和原始严格门报告不删除、不改写。

最终分开给出两个结论：任一原子为 `CAUSAL_HARM` 时回退门 FAIL；没有确认伤害时回退门 PASS。候选还必须至少有一个 `CAUSAL_BENEFIT`、H2 原始阳性控制语义覆盖达到 2/3、完整工程回归通过，才进入最终人工合并判断。`AMBIGUOUS`、`INSUFFICIENT` 不伪装成判负，但逐项列为剩余风险。
