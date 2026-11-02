# 0.1.10 发布验证

本次发布沿用已采用C2的实写证据，不追加规则或用包测试判断文章优劣。相对0.1.9，Git运行内容只变动`references/anti-ai-writing.md`的三个文本块。

| 检查 | 结果 |
| --- | --- |
| `python -B -m unittest discover -s tests -p test_skillhub_package_builder.py` | 6项通过，见package-tests.log |
| `python -B -m unittest discover -s tests -p test_release_policy.py` | 11项通过，见release-policy-tests.log |
| Git规范字节与R4/R5冻结候选 | 13文件文本相同；发布包使用Git中的LF字节，避免Windows工作区换行带来无关变更 |
| 白名单与可重复构建 | GitHub/SkillHub为13文件MIT包，重复构建ZIP哈希相同；ClawHub为12文件MIT-0包 |
| 两平台dry-run | SkillHub本地metadata/包检查通过；ClawHub返回would-publish、0.1.10、12文件 |
| 已有实写 | 相同C2在R4+R5共48次写稿、5个不同题目、6次匿名审阅；包括成功、局部残留和具体语义问题 |

原生独立范围审阅由`01a19ce9-a054-7521-b958-550af0f7f252`完成，只读比较v0.1.9、当前Git内容、冻结候选与归因记录。确认C1/v1/v2未进入产品；提示直接复制CRLF工作区会引起额外哈希变化，以及旧README版号需要更新。本发布已经从Git规范字节构建并更新展示版号，两项均纳入preflight.json核对。

首次SkillHub本地dry-run因沙箱临时目录权限失败，改用仓库忽略区作为临时目录后通过；该调用没有发起HTTP发布，不计为发布尝试。本次未重跑166项全量测试，不新增多模型调用，不把执行完成或包一致宣称为整体写作稳定。
