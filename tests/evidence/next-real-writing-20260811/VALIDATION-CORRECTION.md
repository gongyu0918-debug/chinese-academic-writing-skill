# 发现轮 trace 有效性修正

发现轮首次封存的 manifest 将 MiniMax D2 记为技术无效，唯一原因是 `forbidden_trace:.release/worktrees`。复核原始 trace 后确认：

- 三个规定的中文论文 Skill 文件均以独立 `Get-Content -Raw -LiteralPath` 命令成功读取；
- 模型没有读取其他 Skill、Git 历史、证据目录或其他实验分支；
- 触发旧规则的是模型随后列出当前冻结运行根 `matrix-baseline-v008`，该路径本身位于 `.release/worktrees` 下，但不是“其他 worktree”。

修正只改变 trace 分类器：允许当前冻结运行根，仍拒绝同级其他 worktree。现有 12 个 prompt、final、trace 和 stderr 均不替换，不发起模型重试。`revalidate_discovery.py` 在原文件上重算技术有效性，并把首次 manifest 原字节保存为 `manifest.before-validation-correction.json`。
