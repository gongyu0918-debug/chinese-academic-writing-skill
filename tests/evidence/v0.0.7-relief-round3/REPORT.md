# v0.0.7 第三轮减载与竞品借鉴验证报告

## 结论

本轮没有运行时规则满足合并门槛。三个继续减载候选全部拒绝；五个旧竞品借鉴候选中，三个旧轮已拒绝，两个旧轮胜出方向在当前 `62012cb` 基线上重新确认后仍未达到零损门槛。因此主线不合并任何候选 reference 或入口删改，只合并评测工具、冻结任务、原始成品、匿名判决、研究记录和失败处置。

## 固定版本

- Baseline：`62012cb`
- Leaf contract relief：`75fc6a0`
- Paragraph boundary relief：`3b2e25c`
- Host-neutral phases：`614f5ed`
- Refreshed change impact：`330e962`
- Refreshed citation faithfulness：`0145697`

## 继续减载结果

| 候选 | 机械结果 | 匿名决定 | 硬阻断 | 处置 |
| --- | --- | --- | --- | --- |
| leaf | 8/8 通过 | Candidate 1 胜、Baseline 2 胜、1 项三票仍分裂 | L03 出现 candidate-only `FAIL` | 拒绝 |
| paragraph | 原轮 P02 基线超长、P03 双方超长、P04 候选 1564/1500 超长 | 已决 Candidate 2 胜、Baseline 1 胜 | P04 candidate-only `FAIL` | 启动一次性确认 |
| paragraph 确认 | PC01 Candidate 1161/1100 超长；PC02 Candidate 通过 | 机械门禁已触发停止，不再盲评 | 短稿超限在未见任务复现 | 拒绝 |
| host-neutral | 原轮 12/12 通过 | Candidate 2 胜、Baseline 4 胜 | H01、H03-R3 出现 candidate-only `FAIL` | 拒绝 |

paragraph 的 P04 只超出 64 个汉字，原轮质量胜率为 66.7%，因此按用户允许的“少数错误是否为波动”规则预注册两个未见任务。PC01 再次超出 61 个汉字，证明短稿超限具有可复现方向，不能按统计噪声放行。

## 竞品借鉴候选处置

旧轮五个独立 worktree 已完成短稿、长稿 A/B：

- 作者认可状态：短稿和长稿均出现单侧硬回退，拒绝；
- 研究问题闭合矩阵：诱发为填满关系而扩写，拒绝；
- 文体来源优先级：长稿超限并出现材料外展开，拒绝；
- 变更影响：旧轮短长稿正向，进入当前基线刷新；
- 引用忠实度优先：旧轮短长稿正向，进入当前基线刷新。

当前基线确认结果：

| 候选 | 机械结果 | 最终匿名决定 | 严格门槛 | 处置 |
| --- | --- | --- | --- | --- |
| change-impact | 6/6 通过 | Candidate 2 胜、Baseline 1 胜，66.7% | BC03 出现 candidate-only `FAIL` | 拒绝 |
| citation-faithfulness | 6/6 通过 | 已决 Candidate 2 胜、Baseline 0 胜；BF02 三票为平局、Candidate、Baseline | 仅 2 项形成决定，低于预注册 3 项 | 暂不合并 |

引用忠实度是本轮最强方向：BF01、BF03 均由三位裁判一致判 Candidate 胜，且没有 candidate-only `FAIL`；BF02 两侧都出现来源边界问题，三票无法形成多数。预注册要求三项全部形成决定，本轮不追加第四裁判或换题救援。

## 评测工具修正

所有修正都发生在对应盲评前，并单独提交：

1. `c7b77cc`：将 Codex CLI 不支持的 `allOf`、`uniqueItems` 约束等价移到后置语义校验，并补齐严格结构化输出要求；真实匿名包冒烟退出 0。
2. `ec8760f`：允许两侧同时 `FAIL` 时记录质量偏好；单侧失败仍必须选择非失败侧，机械评分仍记 `BOTH_HARD_FAIL`。
3. `7af8bc6`：删除会把“不称为实验组和控制组”误判成旧术语残留的纯字符串门禁；修正前结果单独保留，旧数字门禁不变。
4. `90ed619` / `62012cb`：把密封证据目录固定为 LF，消除 Windows 新 worktree 的 SHA-256 假失败。

## 测试规模

- 继续减载：原轮 28 份冻结 writer 成品，paragraph 一次性确认轮另有 4 份；leaf 与 host 使用第三评审，paragraph 确认轮由机械门禁停止。
- 竞品刷新：12 份当前基线 writer 成品；两个候选均包含短稿、1800—2200 字长稿和全文/引用审查。
- 裁判均为逐任务独立新会话；左右映射由固定种子生成，初评两位映射不同。
- Writer 和 Judge 均运行 Codex CLI 默认模型 `gpt-5.6-sol`、medium reasoning、只读沙箱。

CLI 全程出现模型缓存字段、插件图标、远端插件目录和 PowerShell shell snapshot 警告；所有纳入证据的 writer/judge 命令退出码均为 0。警告属于运行环境噪声，不计为 Skill 通过或失败。

## 主线处置

- 不合并 `codex/exp-leaf-contract-relief`。
- 不合并 `codex/exp-paragraph-boundary-relief`。
- 不合并 `codex/exp-host-neutral-phases`。
- 不合并 `codex/refresh-change-impact`。
- 不合并 `codex/refresh-citation-faithfulness`。
- 合并 `codex/eval-v007-relief` 的评测证据与工具修正；该分支不改运行目录。

下一轮若继续引用忠实度方向，应建立全新的候选和任务，不复用 BF01—BF03，不把本轮未决项改判为胜出。下一轮不应继续删除段落边界提示；应先研究不增加高熵公式的篇幅收束机制。
