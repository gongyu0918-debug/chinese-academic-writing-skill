# v0.1.4 检查脚本修复验证

基线：`da651700d2de1d7ae05198345d4e887f4f638652`。本版只修复三个运行检查脚本中的五类已复现问题；写作入口、六份 reference、配置、运行依赖和文件数量保持原样。此前三条写作候选均已取消，不纳入本版。

## 可核对的变化

| 问题 | 修复前 | 修复后 |
| --- | --- | --- |
| 单行多来源引文中的分号 | 三组合法引文被切断，标记覆盖率0，显式门槛1下 strict失败 | 引文内分号保持完整，句间分号仍分句 |
| 倒序或超预算编号范围 | 三组引文无有效展开、无报告，strict通过 | 高严重度 `unparsed-numeric-citation`，strict失败；合法项仍保留映射 |
| LaTeX 普通正文环境 | document、abstract、enumerate 中的交付旁白均漏检 | 正文正常检出；公式、代码、引语等明确保护环境继续保护 |
| Markdown 围栏 | 更长结束符或未闭合到EOF的示例ref误报为正文缺失标签 | 示例ref不再误报，围栏外真实ref继续检查 |
| 异常长数字 | 两脚本28位数字接x/z/!六例均超过2秒外部超时 | 无歧义数字识别；另消除风险数字分支逐位重复尝试，完整CLI有界完成 |

编号范围的原有安全展开预算仍为差值不超过200，不是引文编号上限。标记覆盖率仍只表示标记存在；不能完整展开时另报结构错误，不把该比率包装成来源有效支持率。相关复现与耗时原始结果见 `citation-fix-proof.json`、`prose-fix-proof.json`、`manuscript-fix-proof.json`。

围栏处理依据 [CommonMark 0.31.2 第4.5节](https://spec.commonmark.org/0.31.2/#fenced-code-blocks)：结束标记同类且长度不少于开头，未闭合块到文件末尾，缩进和信息串按本次覆盖的顶层围栏边界处理。本版未引入完整 Markdown 或 LaTeX 解析器，也不宣称新增对所有嵌套容器、自定义宏和自定义环境的支持。

## 独立审查与修正

独立审查未发现引用脚本的阻断项，但发现三个候选独有的混合格式回退：LaTeX 代码内的 Markdown 围栏遮住了环境外真实引用；已保护环境内的美元号或引号影响后续状态，遮住了真实正文；后续围栏修正曾把注释或行内代码中的伪 LaTeX 起始命令当成真实环境。三处均在发布前修正，并加入交互反例。最终独立复核81/81组合样本、58/58可只读执行的既有测试通过，未观察到剩余阻断项，见 `independent-review.json`。

## 真实稿件回放

使用 `writing-understanding-20260908` 中83份原始稿件，按原决定排除6次技术失败及1次非正文交付失败。来源字节逐项核对旧 manifest，三个检查脚本分别在独立 Python 进程中加载基线与候选。

初轮及最终修复后的249个扫描结果均逐项一致，原稿字节未改变，见 `replay-comparison.json`。此回放验证扫描行为与只读性，不是新一轮模型写作实验，不作为文风改善证据。

## 校验记录

最终全量测试219/219通过，结构校验和回放通过；独立复核及包哈希记入 `validation.json`。测试命令：

```powershell
py -3 -B -m unittest discover -s tests -v
py -3 -B C:\Users\admin\.codex\skills\.system\skill-creator\scripts\quick_validate.py chinese-academic-writing-assistant
py -3 -B tests/evidence/v0.1.4-release-gate/replay_scanners.py --scripts-root chinese-academic-writing-assistant/scripts --evidence-root tests/evidence/writing-understanding-20260908
git diff --check
```

首次完整测试212项通过后，独立复核发现上述两处回退，因此另补交互回归并重新运行最终全量测试。既有临时文件测试在 Windows 沙箱中存在权限限制，最终全量结果来自已获准访问临时目录的运行环境，没有为此放宽断言。

另按用户提供的无Hooks公文WorkBuddy ZIP制作论文版本：根层级与元数据字段顺序保持相同，名称、描述、标签和版本对应中文论文写作0.1.4。只扩充入口元数据，正文与运行文件保持本次正式版本内容，根层级使用 `LICENSE`，不包含Hooks、平台适配器或仓库测试。结构/元数据/文件哈希已校验，未在WorkBuddy客户端实装测试。

发布包继续采用白名单：GitHub/SkillHub为11个运行文件加Markdown许可证；ClawHub采用独立11文件目录，按平台规则使用MIT-0。真实平台回执、公开版本、签名/哈希与审核状态分别记录在 `RELEASE-RECEIPT.json`，受理之后只做只读查询，不因传播延迟重复发布。

三个修改脚本在归档时统一为LF，并通过Git属性固定，避免Windows换行转换造成不同checkout的包哈希差异。规范化前后源码内容相同，规范化后的Git blob逐项等于独立审查记录；原始审查哈希与最终发布字节哈希的映射保存在 `validation.json`。
