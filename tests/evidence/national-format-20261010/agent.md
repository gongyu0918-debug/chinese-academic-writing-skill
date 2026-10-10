# 本轮工作记录

- 2026-10-10（北京时间）：按用户“国标优先，必须符合国家标准”明确要求处理格式层；既有外部模型测试和子代理授权沿用。
- 主目录main基线718887a；独立托管工作树national-format-priority，分支codex/national-format-priority。先核对现有附件，没有可复用的活跃托管工作树后创建。历史手工worktree另属旧任务，未改动。
- 读取skill-creator，按需加载；读取pdf技能做标准正文抽取和视觉核对。国家标准全文公开系统核实现行状态，再读学校/出版平台公开正式PDF；范围与哈希见SOURCES.md。
- 先由Harvey审计旧规则六处模板优先冲突。主审区分格式优先级、用户操作范围、材料版本和事实状态，改动六份运行Markdown，README/HANDOFF说明同步。
- R1双路线24调用：初版年份末置、英文任务交中文、开题审稿幻觉等失败保留。R2新任务12调用：冲突处理和英语范围明确后，Qwen书目重复年份及改变出版社。R3新书目8调用：年份不再重复，但一份漏已给作者。R4增加标准7.1.2的明确责任者要求，新书目4调用。
- R5在不改规则的前提下追加两类新控制，8调用、4配对。最终总计56调用，2技术无效，26有效完整配对；执行成功不等于语义质量通过。R4的Qwen候选只作单稿核对，不冒充有效配对。R5英语交付成立，Qwen栏目审阅仍有未分类推未阅读和把研究问题当成已证实属性的过审。
- Pasteur/Curie/Bohr分线匿名实写复核及规则冷审，继承同一实际model；报告和最终覆盖状态单列。主审以请求和原材料裁决，不把盲评判词当标准答案。
- 最终规则追加Helmholtz冷审未返回报告，关闭时running，记未完成；不能以读取动作代替完成。Mendel最终控制盲评4对已完成，累计有效独立盲评25对。所有原生审阅代理均关闭；最终规则仍只有主审语义审计结论。
- 纯Markdown未以全量单测或结构校验准入。已有调用器原样冻结；prepare_public.py、make_review.py、archive_visible.py只整理本轮证据，不是运行脚本或语义评分器。
- 原标准PDF、渲染图、CLI运行私有文件留.release；公开证据只含自写规则、来源定位、构造请求、可见成品、模型/执行元数据和脱敏报告。
- 新证据目录沿用现有.gitattributes的字节保存策略，禁用Git文本换行转换；该策略只保护冻结输入及成品哈希，不是写稿质量判断。
- 提交、合并、代理关闭、托管工作树回收以及回收后的git worktree list见LIFECYCLE.json。当前公共平台版保持0.1.8，本轮不发布或安装。

调用命令使用现有`.release/academic-rule-format-audit/runner.py`，分别传入`cases.json`至`cases5.json`及不同输出目录；核心参数如下（路径按本轮实际机器记录）：

```powershell
& 'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .release/academic-rule-format-audit/runner.py --spec .release/national-format-20261010/cases5.json --output .release/national-format-20261010/round5-control --candidate-dir 'C:\Users\admin\.codex\worktrees\national-format-priority\chinese-academic-writing-skill\chinese-academic-writing-assistant'
git diff --check
```

最后一条模型批次返回8次、0技术无效，正文质量判断仍见ADJUDICATION.md，不能把返回码0当作通过。哈希整理命令为`prepare_public.py`和`verify_archive.py`，只核对56份prompt/成品绑定及最终13文件的冻结字节一致性，不验证自然语言规则效果。
