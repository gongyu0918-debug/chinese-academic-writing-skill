# v0.0.8 发布门禁轮报告（对 v0.0.7 无回退验证）

日期：2026-08-09。环境：codex-cli 0.144.6，模型 gpt-5.6-sol，只读沙箱，剔除 `[agents]` 表的独立 CODEX_HOME（`C:\Users\admin\.codex-writer-v008`），每个“任务 × arm”与每个裁判均为全新会话。

## 版本固定

- Baseline：tag v0.0.7（`4d36a40`），worktree `ab-v008-baseline`。
- Candidate：tag v0.0.8（`09b89a6`），worktree `release-v0.0.8`（分支 codex/release-v0.0.8）。

## 任务（全部为开发轮未见的新任务、新材料）

- R1 修稿＋文风复核（县博物馆公教活动，旧稿含否定尾簇、无依据因果归因种子）
- R2 纯检测（职校生就业焦虑草稿，只检测不修改；含真实研究限制不得误报）
- R3 开题据材料起草（农村电商服务站，六节、保留 M1/M2/M3/[S1] 标注）
- R4 只审不改（社区健身器材管护草稿，含引文升级、无数据因果、数字越界等种子）

## 机械门禁

`python -B mechanical_gate.py --specs specs/release.json --raw-dir raw --output mechanical/release.json`
结果：MECHANICAL_GATE=PASS，8/8 输出通过（字数区间、六节结构、M/S 标签字面量、无过程泄漏）。

## 盲评

judge-1、judge-2 独立双盲映射（seed `v0.0.8-release-gate-2026-08-09`），每侧硬状态先于文风比较。两位裁判结论完全一致，无分裂，未启用 judge-3：

| 任务 | 两侧硬状态 | judge-1 | judge-2 |
| --- | --- | --- | --- |
| R1 | 双 PASS | candidate | candidate |
| R2 | 双 PASS | candidate | candidate |
| R3 | 双 PASS | candidate | candidate |
| R4 | 双 PASS | baseline | baseline |

`python -B score_results.py ...`：MERGE_GATE=PASS，DECIDED=4，CANDIDATE_WINS=3，BASELINE_WINS=1，candidate_only_hard_fail=false。

## 判定（按 PREREGISTRATION.md）

1. 无可复现的 candidate-only 硬 FAIL——满足（全程零硬 FAIL）。
2. 已决定任务 Candidate 胜数（3）不少于 Baseline（1）——满足。
3. 无与 DIFF 无关的需剔除波动。

结论：0.0.8 相对 0.0.7 无回退，且在新任务上整体优于基线；R4 基线胜出为单任务偏好差异（两侧均 PASS，无硬错误），不构成回退。发布门禁通过，准予发布。

## 复现入口

任务与外层说明：`tasks/`、`writer-prompt-R*.md`；写手成品：`raw/`；机械门禁：`mechanical/release.json`；映射与裁决：`maps/`、`judgments/`（per-task 原始 JSON 在 `judgments/judge-*/per-task/`）；汇总：`scores/release.json`。
