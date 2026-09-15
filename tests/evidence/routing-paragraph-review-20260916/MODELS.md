# 正式模型与历史排除

遵循用户 2026-09-16 的纠正：写稿与冷审采用中文公文项目维护模型池，正式写稿 reasoning effort 为 `max`，通过 Codex CLI 批量执行。只读参考公文仓库，未修改其中内容。绑定的源文件及 SHA-256 见 `audit-history/model-policy-binding.json`。

当前模型来自公文仓库提交 `82cc2819` 附近的维护记录及已运行驱动：`maintenance/tests/evidence/mit-script-delivery-r1/run_eval.py`、`maintenance/tests/evidence/anti-ai-concrete-rules-20260914/run_cold_cli.py`。本机 catalog 对所有所选模型均声明支持 `max`。这些是本次调用的精确标识，不保证以后仍可用。

| 用途 | 精确模型 ID | 努力级别 |
|---|---|---|
| 正式写稿渠道 0 | `alibaba-token-plan/qwen3.8-flash` | max |
| 正式写稿渠道 1 | `alibaba-token-plan-2/qwen3.8-flash` | max |
| 正式写稿渠道 2 | `command-code/deepseek-deepseek-v4.1-flash` | max |
| 正式写稿渠道 3 | `minimax-cn/MiniMax-M3` | max |
| 正式写稿渠道 4 | `ollama-cloud/glm-5.3-flash` | max |
| 规则冷审、首批匿名审阅 | `alibaba-token-plan-2/qwen3.8-max` | max |
| 规则冷审、路线与后续匿名审阅 | `ollama-cloud/kimi-k3` | max |

五条写作渠道是四个模型家族，两个 Qwen 渠道不冒充不同家族。`xai/grok-4.6` 属维护冷审池，本轮未调用。不将 0731、V4 Flash、V4.1 Flash 混称。早期 40 次 API `high` 调用仅为探索，不能冒充符合本轮维护规范的 `max` 证据。

正式 CLI 为 `codex-cli 0.154.0-alpha.6.2`；每次调用在隔离目录安装单份冻结 Skill，使用独立临时 CODEX_HOME，无用户文档、凭据、插件、apps、memories 或 Hook。通过既有本地模型代理发请求；驱动中的 `opencodex-loopback` 是非秘密本地占位符，不是账户密钥。提示、模型、努力级别、CLI、版本和输入指纹见每批 `binding.json`。文件编码提示在两臂一致。

V2 组显式启用宿主 `multi_agent_v2`；原生子代理默认模型与对应便宜 writer 相同、努力级别也是 max，并限制深度。不能只依赖 root JSON 的工具事件数来判断实际委派：初始 legacy 组的 DeepSeek 也确实派生了两个子代理。保留的隔离会话元数据可确认子模型、父子关系；Qwen 的两条关键首段审阅链明确使用 `fork_turns: none`。root usage 不假定包含子代理费用，未汇总为完整收费统计。

模型纠正前误用了 Astra 辅助审查及段落测试，另有 Luna 探索和中断任务；已停止，均不作为正式写稿验收或正式冷审依据。Desktop 外部 provider 子任务出现 `unreadable_encrypted_agent_task`，未作为成稿。后续全部采用明文原生 CLI。历史初查、原始探索与正式记录分别保存，不能反向声称本轮从未调用 Astra。

归档不包含隐藏推理。CLI trace 移除了 reasoning/analysis 项，仅作 JSON 重序列化；原始哈希及转换规则在 `trace-transformations.json`。子会话仅摘取身份、模型与可见消息，完整原始会话留在本机临时目录。探索响应仅归档稿件、请求、回执与原始文件哈希，不公开 API 隐藏推理段。
