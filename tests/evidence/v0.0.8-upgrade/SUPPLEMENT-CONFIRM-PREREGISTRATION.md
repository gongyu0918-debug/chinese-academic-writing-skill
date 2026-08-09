# T3/T4 候选独有失败确认轮预注册（2026-08-09）

首轮结果：T1 分裂（judge-3 判 Candidate 胜，2:1 决定 Candidate）；T2、T3、T4 均判 Baseline。T3 出现 judge-1 认定的 candidate-only 硬 FAIL（未保留 M1—M3 材料来源标注，人工核对属实：候选稿 0 处 M 标注，基线稿 3 处）；T4 出现 judge-1 认定的 candidate-only 硬 FAIL（把 [S1] 的“东部某省”研究无依据地写成“外省/外地”研究，judge-2 对同一问题记 WARN，人工核对属实）。

归因核查：候选 T3/T4 writer 未运行脚本（日志中 python/prose_lint 行仅为读取入口文本的回显）；两任务不加载 ANTI-AI reference；候选与基线的实际差异只有入口新增的两句（终稿 lint 短指针、纯检测路由句）。无机制通路把这两句与掉标注或地域臆断相连。按用户门槛“与 DIFF 无关的波动不在判定范围内”，需先验证可复现性再归类。

## 确认轮设计

全部使用全新未见任务，不复用 T3/T4；writer 与首轮同环境（同一 CODEX_HOME、只读沙箱、全新会话），臂仍为 Baseline worktree（4d36a40）与 Candidate worktree（运行包冻结于 dca0287/dd9bc98）。

| 任务 | 复验目标 | 臂与会话 | 判定方式 |
| --- | --- | --- | --- |
| T5 开题据材料（新事实包，M 标注必须保留） | M 标注丢失 | b1、b2、c1、c2 | 机械门禁 required_literals 含 M1、M2、M3 |
| T6 只审不改（新草稿，省份—县关系未明的地域陷阱） | 无依据地域关系臆断 | b1、b2、c1、c2 | c1 对 b1、c2 对 b2 各一名盲评；无依据写成外省/外地/异地关系即硬 FAIL |

## 决定规则

1. T5：任一 candidate 会话丢失 M1—M3 标注 → 失败复现 → 拒绝候选。两侧全部保留 → 记单次噪声。
2. T6：任一 candidate 会话被盲判无依据地域关系硬 FAIL → 失败复现 → 拒绝候选。两个 candidate 会话均无此类硬 FAIL → 记单次噪声。
3. 两项均未复现时，T3/T4 的两起 candidate-only 失败按“与 DIFF 无关的单次波动”排除出判定；合并门槛按首轮其余判定与确认轮成对结果重算：不得出现可复现 candidate-only 硬 FAIL，且已决定任务 Candidate 胜数不少于 Baseline。
4. 任一项复现即整体拒绝 0.0.8 运行包改动；不做针对性微调后再测救援。
