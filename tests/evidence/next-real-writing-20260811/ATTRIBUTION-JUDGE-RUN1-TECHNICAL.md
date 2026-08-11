# 归因主裁判第一次技术运行：调用层无效

- judge-1 manifest SHA-256：`40234450c2113c96a14c21eb44959138fc24849c0b42bc157d91c7730b549d49`。
- judge-2 manifest SHA-256：`3d7d850d80789bd9b46a6239a602900661b8777b972348d0e5d8a72a4f828538`。
- 两名裁判各计划 12 次，24 次均在模型输出前由 API 返回 `invalid_json_schema`，`return_code=1`、`valid_calls=0`，没有生成任何裁判 final。
- 统一错误：response format 根层不允许 `allOf`。该关键字只用于要求 `PRESENT` 时 anchors 非空；本地 `validate_final()` 已独立执行同一约束，因此可从远端 output schema 删除而不改变裁判语义或本地门禁。
- 原结果保存为 `attribution/judgments-run1-invalid-schema/` 与 `attribution/judge-manifests-run1-invalid-schema/`，不进入投票或计分。
- 修复 schema 后必须以新目录完整运行 judge-1、judge-2；本次没有获得模型样本，不能视为某个裁判任务的内容重试。
