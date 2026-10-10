# 必要英语规则与当前规则审计

主审取舍、失败稿和实际范围见[ADJUDICATION.md](ADJUDICATION.md)，规则盘点见[AUDIT.md](AUDIT.md)，规范依据见[SOURCES.md](SOURCES.md)。本轮是中文稿必要英语与文字格式的开发小改，公开版本仍0.1.8。

- R1—R3：36次main/v1，35次执行有效、17完整有效配对。
- R4：8次v1/v2消融，7次执行有效、3完整有效配对。
- R5：12次main/v2新中文控制，6完整有效配对；不能计作全部语义通过。
- 合计56次CLI写稿，2次工具违规排除；所有错误与无效稿均保留，quality_pass不由Python填写。
- native：规则审计、两份完整匿名冷审、一份未完成冷审和一份自主选页试用。实际模型字段见native-models.json；不把昵称当作多模型。

两个外部writer路线与max effort冻结。运行脚本只负责原生CLI调用和可见归档，完整规则以内联输入保存；自主文件选页只有native试用路径实际观察。匿名包身份在packet-mapping.json，原始规格和完整输入/稿件哈希可回查。

FORMAT-HANDOFF.json区别当前本机规则阅读、指定任务询问和未取得的远端资料；PACKAGE-CHECK.json仅证明13文件白名单与六项打包测试，不能证明写作质量。0.1.8-format.1为.release中的本地审阅包，没有发布或安装。

只提交规则快照、任务、可见返回、报告、元数据和哈希；不提交原始会话隐藏推理、凭据、native profiles、stderr或官方规范全文。MANIFEST.json绑定冻结证据字节，LIFECYCLE.json在合并回收后另记。
