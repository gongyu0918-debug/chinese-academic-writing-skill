# 归因重复轮第一次技术运行：整轮无效

- 原目录运行结束后保存为 `attribution-run1-invalid/`，不覆盖、不补单项。
- manifest SHA-256：`a8bbbf3f9444b835b95dfeaa37943c2a98ae5e68415ecf73878da05cba3e33bd`。
- 24 份 final 均生成，运行根前后绑定稳定；技术有效 23/24。
- 唯一无效调用：`A2-R2 / candidate / alibaba-token-plan/deepseek-v4-flash-0731`。
- 原始 trace 问题：`intermediate_agent_message`、`unexpected_command`、`unexpected_command_event_count:4:4`。模型完成三次必读后先输出“路径写错、重试”，再执行第四条读取命令，违反冻结的三命令和首个 post-read final 契约。
- 该轮不生成匿名 packet、不运行裁判、不进入归因计分。若继续验证，只能在新的 `attribution/` 目录完整重跑 12 对、24 次写稿，重试数仍为 0。
