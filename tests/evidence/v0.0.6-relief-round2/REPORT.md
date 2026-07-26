# 第二轮运行时减载验证

## 范围

- 固定基线：`3ef5703e0328fcfb5aa1e1392cf0df46cf7fdf48`
- 入口摘要候选：`9972aef`
- 专项叶建议分类候选：`c256536`
- ANTI-AI 摘要候选：`ba5f145`
- 三项均从固定基线建立独立 branch 和 worktree，未在 `main` 上试改。

本轮只删除已经由其他运行层完整承接的复述。材料门禁、来源语义门禁、段落自主成段、长稿状态包、全文复核顺序和脚本只读边界均未改动。

## 确定性验证

| 候选 | 归一化运行 Markdown | 减少 | unittest | quick_validate | diff check |
| --- | ---: | ---: | --- | --- | --- |
| 基线 | 14,425 | — | 122/122 | PASS | PASS |
| 入口摘要 | 14,323 | 102 | 122/122 | PASS | PASS |
| 专项叶建议分类 | 14,187 | 238 | 122/122 | PASS | PASS |
| ANTI-AI 摘要 | 14,317 | 108 | 122/122 | PASS | PASS |

Windows 全局 `core.autocrlf=true` 会把新 worktree 中封存的 `v0.0.3-live-citation` 原始证据检出为 CRLF，导致其 SHA-256 与仓库中的 LF 封存值不一致。验证时仅将该封存目录按 Git blob 临时还原为 LF，122 项通过后恢复默认检出；没有修改或提交封存证据。

## 隔离写作与盲评

writer 只读取自己一侧的入口和按需 reference，不读取其他 worktree、diff、测试、竞品或删减说明。judge 使用新上下文，只读取原任务和匿名成品，先检查事实、来源、研究状态、输出模式和用户禁止项，再比较直接可用性、自然度、冗余和修改成本。匿名映射在评审完成后写入 `anonymous-map.json`。

### 入口摘要

| 任务 | 匿名结论 | 解盲 |
| --- | --- | --- |
| P02 只有题目的开题降级 | B 胜 | Candidate 胜 |
| L02 无来源且禁联网的综述降级 | A 胜 | Candidate 胜 |
| X03 无原文的 AIGC 规避请求 | B 胜 | Candidate 胜 |

三题均无单侧硬回退。结果：Candidate 3 胜、Baseline 0 胜，接受。

### 专项叶建议分类

| 任务 | 匿名结论 | 解盲 |
| --- | --- | --- |
| A01 稀疏材料提纲与按需建议 | B 胜 | Candidate 胜 |
| P01 开题起草与计划状态 | A 胜 | Candidate 胜 |
| L01 分层来源独立综述 | B 胜 | Candidate 胜 |

三题均无单侧硬回退。结果：Candidate 3 胜、Baseline 0 胜，接受。

### ANTI-AI 摘要

两名独立 judge 使用同一匿名包复核，没有换题、改 prompt 或调整候选。

| 任务 | Judge 1 | Judge 2 | 解盲汇总 |
| --- | --- | --- | --- |
| H01 无依据否定与虚设对比 | 平 | 平 | Candidate 0、Baseline 0、平 2 |
| H02 重复固定搭配与句首 | A 胜 | A 胜 | Baseline 2 胜 |
| H03 必要否定不得误删 | A 胜 | B 胜 | Candidate 1 胜、Baseline 1 胜 |

合计 Candidate 1 胜、Baseline 3 胜、2 平。虽然两侧硬边界均通过，但 H02 出现可重复的基线软质量优势，因此拒绝合并，不继续拆词救援。

## 决定

- 接受 `9972aef`：删除入口非规范性摘要复述。
- 接受 `c256536`：四类正文后建议只由入口定义，三个叶子保留各自的任务焦点和禁止项。
- 拒绝 `ba5f145`：分支保留用于归因，不进入 integration 或 `main`。

integration 相对基线净减少 340 个 LF 归一化运行时 Markdown 字符。原始匿名稿和 judge 回执保存在本目录。
