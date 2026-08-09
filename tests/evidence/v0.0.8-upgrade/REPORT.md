# v0.0.8 脚本与 AI 检测升级验证报告

## 结论

0.0.8 候选满足用户保留门槛：真实写稿中没有出现可复现的 candidate-only 硬失败，已决定任务 Candidate 胜数不少于 Baseline。首轮两起 candidate-only 硬失败经全新未见任务确认轮检验，均不具候选臂特异性（M 标注丢失在基线会话同样复现；地域臆断未在候选会话复现，反而在基线会话出现同型来源范围失真），按“与 DIFF 无关的波动不在判定范围内”排除出判定。运行包改动合并，版本 0.0.8 构建完成；本轮不发布。

## 固定版本

- Baseline：`4d36a40`（main，运行包与 v0.0.6/v0.0.7 相同），writer 在 detached worktree `ab-v008-baseline`。
- Candidate：worktree `v0.0.8`，运行包改动冻结于 `dca0287`（脚本）与 `dd9bc98`（Prompt）。
- Writer/Judge：codex-cli 0.144.6，默认模型与只读沙箱，每“任务 × arm”全新会话；因用户 config.toml 的 opencodex `[agents]` 表不被 CLI 解析，writer/judge 会话使用剔除该表的独立 CODEX_HOME，其余配置逐字相同。

## 候选原子与来源

S1—S3、D1—D3、R1 见 PREREGISTRATION.md；借鉴来源与交叉验证见 RESEARCH.md；运行包熵审计见 ENTROPY-AUDIT.md。

## 首轮结果（T1—T4）

| 任务 | judge-1 | judge-2 | judge-3 | 结果 |
| --- | --- | --- | --- | --- |
| T1 修稿＋文风复核 | Baseline | Candidate | Candidate | Candidate 2:1 胜，两侧无硬失败 |
| T2 纯检测 | Baseline | Baseline | — | Baseline 胜，两侧无硬失败 |
| T3 开题据材料 | Baseline（candidate FAIL：M 标注丢失） | Baseline | — | Baseline 胜 |
| T4 只审不改 | Baseline（candidate FAIL：外省臆断） | Baseline（candidate WARN 同问题） | — | Baseline 胜 |

机械门禁 8/8 通过（含盲评前门禁修正：判定标准误报、中文编号标题识别、8 元字面量，见提交 `977f4e5`）。

## 归因核查

- 候选 T3/T4 writer 未运行脚本（日志中 python/prose_lint 行仅为入口文本回显）；两任务不加载 ANTI-AI reference；候选与基线的实际差异只有入口新增两句。无机制通路连接该差异与两起失败。
- T2 两裁判偏好基线的显式排除句与结构归纳行；候选检测行数更多并使用了新的否定收口分类，未遗漏基线覆盖的问题点。按已决任务如实记 Baseline 胜。

## 确认轮（T5/T6，全新未见任务，双臂各 2 会话）

| 检查 | b1 | b2 | c1 | c2 | 判定 |
| --- | --- | --- | --- | --- | --- |
| T5 M 标注保留（机械） | PASS | FAIL（M1—M3 全丢） | FAIL（仅丢 M3） | FAIL（全丢） | 双臂均复现，非候选特异 → 噪声 |
| T6 地域/来源范围臆断（盲评） | PASS | FAIL（无依据写“一所县级医院”） | PASS | PASS | 候选未复现；基线出现同型失真 |

T6 成对盲评：judge-4（c1 对 b1）Candidate 胜，两侧 PASS；judge-5（c2 对 b2）Candidate 胜，b2 侧硬 FAIL。

## 门槛重算

已决定任务：T1、T6A、T6B 为 Candidate 胜，T2、T3 为 Baseline 胜（3:2）；T5 机械结果双臂等价不计胜负。可复现 candidate-only 硬 FAIL：无。满足“至少不劣于基线、无回退风险”的保留门槛。

## 噪声与教训记录

1. M 标注丢失在两臂 4/4 会话中出现 3 次：任务措辞“保留来源标注”对 writer 不稳定，后续任务若以标注为硬检查，应在任务文本中显式列出需保留的标签。
2. 来源范围臆断（外省、一所医院）在两臂各出现 1 次：属于审稿任务对未给信息的补全冲动，与版本差异无关，记为后续只审不改任务的常态风险观察项。
3. CLI 与桌面端 config.toml 解析差异：`[agents]` 表导致 codex exec 直接失败；本轮以独立 CODEX_HOME 规避，未改动用户全局配置。

## 确定性验证

- `python -B -m unittest discover -s tests -p "test_*.py"`：142/142 通过（新增 20 项终稿检测器测试）。
- `quick_validate.py chinese-academic-writing-assistant`：通过。
- `git diff --check`：通过。
- 运行包仍为 11 个文件；脚本保持只读（新测试覆盖文件哈希不变）。
