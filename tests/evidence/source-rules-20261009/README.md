# 真实来源规则研究与实写证据

最终决定：新增模板提示取消，运行版本保持0.1.7。本目录是维护证据，不进入Skill分发包。

- RESEARCH.md：已发表论文、高校填充范例的来源绑定、实际读取范围及6类审稿判据。
- ADJUDICATION.md：每题观察、独立意见纠偏、因果边界与取消理由。
- candidate-rule.txt：取消的入口原子，不能当作当前默认规则。
- R1、R2：冻结规则、完整请求、原始可见终稿、返回状态、过滤后的工具trace及模型会话绑定。
- cold-R1、cold-R2：匿名复核请求、实际意见、随机映射及元数据；技术超时如实保留。
- RUN-RECORD.json：24次写稿、23份终稿、1次技术未完成；这些不是质量通过数。
- source-bytes.json、source-agent-binding.json：来源字节与独立来源代理身份/范围。原PDF、全文及页面截图保存在忽略区。

实际调用命令（在研究Worktree执行）：

```
py -3 -B .release\source-rules\run_r1.py --output tests\evidence\source-rules-20261009\R1 --models 0 1 --isolated-profile --ordinary-only --retain-session-metadata --effort max --timeout 200
py -3 -B .release\source-rules\run_r2.py --output tests\evidence\source-rules-20261009\R2 --models 0 1 --isolated-profile --ordinary-only --retain-session-metadata --effort max --timeout 200
```

调用器只发起模型与保存证据，不用Python断言或字数指标评判Markdown规则。来源代理与冷审均独立于起草上下文，不归档隐藏推理。独立冷审4次请求仅2份报告完成；另一份超时包还违反不用工具的约束，不能计通过。R1的recovery-runner-current.py是加入超时保存后的归档版本，不冒充R1原始执行文件。本轮没有生产Python改动。

公开snapshots仅保留实际加载的入口、普通/开题主叶、文风层和许可证，避免重复提交未执行的生产Python。full-snapshot-file-manifest.json记录当时完整包的原始字节及换行归一化哈希，binding.json的全树指纹仍指当时完整冻结包；原全树已留存在主目录忽略区。MANIFEST记录捕获字节与文本换行归一化哈希，Git检出换行改变不能误报文字改动。
