# 上轮证据说明的限定与补充

原生只读审计报告见prior-evidence-audit.md。上轮冻结目录不重写，当前补充说明与新证据独立留存。

1. clarity-coverage-20261009/agent.md第9行的“H基线有unexpected_tool_use和无终稿”专指confirmation-R2的Qwen基线；GLM同任务基线有完整终稿。旧批次两次确认轮无终稿均在基线臂（Qwen H、GLM F），不是候选失败，不给候选加分。
2. AUDIT.md第15行“两个组合候选”原意是两个文字版本：展开版用于candidate-R1/confirmation-R2，短版用于minimal-R3，不是“R1与R2两轮”。展开版R1的Qwen D未交付，R2候选全部有终稿但有状态/范围/过审问题；短版R3的K误称缺文本、M审错对象。为避免把候选版本、轮次和技术无效混读，按这三个事实分别引用；审计者把“两个”读作两轮的疑点采纳为表达不清，不采纳其候选版本归属解释。
3. 12次早期启动失败、两包429与一包审核超时的粗分类原有result/binding支持；具体原因在公开包中的指针不充分。本轮补prior-failure-receipts.json：12份原stderr均有“failed to canonicalize CODEX_HOME”；两包429的明确片段在原可见trace中，为“exceeded retry limit, last status: 429 Too Many Requests”，不是stderr。分别保存安全片段及原字节SHA，不复制完整日志、URL、请求头或profile。null returncode按原runner的TimeoutExpired分支及420秒限时判断；不把错误原因片段当作文字质量证据。
4. 来源实际阅读仍由主审原件与阅读窗口支持，公开包没有全文或页图，审计只核对声明一致，不能独立复验“真的读过”。本轮新增PDF42—52另见CORPUS。未覆盖的市场安装、Hook、完整论文等仍未升级为通过。
