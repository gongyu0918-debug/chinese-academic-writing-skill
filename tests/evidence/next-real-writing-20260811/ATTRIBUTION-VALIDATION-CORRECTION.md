# 归因轮 trace 验证修正

## 发现的问题

第二整轮 24 份 final 均生成、运行绑定稳定，旧验证器把 `A1-R4 / candidate / ollama` 判为无效。该 trace 只在完成第一个必读后提示“接下来读取另外两份文件”，随后完成剩余两次精确读取并输出唯一 final；没有额外命令、跨根读取、工具越权或 post-read 草稿。

旧规则只允许进度消息出现在第一条命令之前，错误地把“全部必读完成前的单次进度提示”与“全部必读完成后的额外输出”混为一类。这是技术分类器过严，与正文质量或 Candidate DIFF 无关。

## 修正规则

- 仍只允许 1 个 final，另最多允许 1 个进度消息。
- 进度消息必须出现在最后一次必读命令完成之前；可在第一条命令前，也可在必读命令之间，但不得与最终成稿相同，防止把提前输出的 final 伪装成进度提示。
- 最后一个 agent message 必须与 `-o` final 完全一致，并位于全部三次读取之后、`turn.completed` 之前。
- 三次独立精确读取、命令 started/completed 配对、命令总数、内容一致性、工具白名单、工作树隔离和 SHA 规则不变。
- 第一次归因轮的 `A2-R2 / candidate / alibaba` 仍无效：它在三次必读完成后输出进度消息并执行第四条命令，同时触发命令数和额外命令错误。

修正只重算派生的 trace 分类和 valid/closure 字段；原 final、trace、stderr、prompt、commit、runtime fingerprint 及其 SHA-256 不得改变。旧 manifest 以 `manifest.before-validation-correction.json` 原样保留。
