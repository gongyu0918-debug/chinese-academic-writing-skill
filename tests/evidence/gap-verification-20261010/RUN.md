# 执行、命令与验证边界

2026-10-10，北京时间。基线eb598fe5c92109171bee6ea0015241ebc8eeb587；隔离worktree为codex/academic-gap-20261010。本轮候选取消，未改产品规则、运行脚本、发布版本或安装包。

|类别|实际执行结果|不能据此证明|
|---|---|---|
|source-scope-R1/R2/R3|32＋16＋12＝60次，30完整配对；60次rc0、有终稿、无越界工具项|60稿质量通过、候选收益或因果|
|input-diagnostic|4次Qwen仅任务独立调用，4次执行完成；四次识别给定目标，但A仍有外围负担和措辞问题|关闭材料误读、规则致因、后端传输完全正常|
|CLI冷审|11次rc0返回文件，10份语义报告；其中8份输入完整，2份原包相应比较有等待占位；1份仅确认将审|11次完成复核、所有意见正确或全稿通过|
|原生subagent|5个完成：规则审计、旧证据审计、2轮实际磁盘写稿、1轮独立磁盘审稿|5个规则收益配对、全论文/桌面/市场验证|
|归档字节核对|所有已导出prompt/final与原result中的SHA一致；manifest逐文件绑定|正文正确或来源真实|
|维护pending检查|exit1，未创建输出目录，未进入模型调用|产品写作能力提高|

Python没有给任何稿件、规则或审阅打分。未运行全量unittest或标准Skill结构校验，不把这些作为纯文字规则验证。本轮Python仅用于调用原生模型、复制冻结输入、解析可见执行元信息和校对字节；语义判断见ADJUDICATION/RULE-AUDIT。

## 实际命令

工作目录F:\Workspaces\chinese-academic-writing-skill。系统`py -3`未找到安装版本，实际使用桌面bundled Python；这只是执行环境事实，不是需要给写作规则增加Python依赖。下面记录已执行的命令，已有冻结输出目录不可复用覆盖。

```powershell
$taskPy='C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskDir='.release\gap-verification-20261010'
& $taskPy -B "$taskDir\prepare.py"
& $taskPy -B "$taskDir\coverage_runner.py" --spec "$taskDir\source-scope-tasks.json" --output "$taskDir\source-scope-R1" --candidate-dir "$taskDir\source-scope-candidate"
& $taskPy -B "$taskDir\prepare_followups.py"
& $taskPy -B "$taskDir\coverage_runner.py" --spec "$taskDir\confirmation-tasks.json" --output "$taskDir\source-scope-R2" --candidate-dir "$taskDir\source-scope-candidate"
& $taskPy -B "$taskDir\prepare_replay.py"
& $taskPy -B "$taskDir\coverage_runner.py" --spec "$taskDir\replay-tasks.json" --output "$taskDir\source-scope-R3" --candidate-dir "$taskDir\source-scope-candidate"
& $taskPy -B "$taskDir\diagnose_input.py"
& $taskPy -B "$taskDir\review_cli.py" pair source-scope-R1 --model ollama-cloud/glm-5.3-flash --output review-R1
& $taskPy -B "$taskDir\review_cli.py" pair source-scope-R2 --model ollama-cloud/glm-5.3-flash --output review-R2
& $taskPy -B "$taskDir\review_cli.py" pair source-scope-R1 --model ollama-cloud/glm-5.3-flash --output review-R1-complete --groups 3
& $taskPy -B "$taskDir\review_cli.py" pair source-scope-R1 --model ollama-cloud/glm-5.3-flash --output review-R1-fixed --groups 2 3
& $taskPy -B "$taskDir\review_cli.py" pair source-scope-R3 --model ollama-cloud/glm-5.3-flash --output review-R3
& $taskPy -B "$taskDir\prior_failure_receipts.py"
& $taskPy -B "$taskDir\collect_receipts.py"
& $taskPy -B "$taskDir\stage_evidence.py"
```

writer使用原生codex.exe 0.162.0-alpha.2（binding记录实际版本），effort=max，provider/model固定，新建隔离CODEX_HOME，每次新会话，关闭插件/apps/memories与隐式项目文档加载；完整入口和所属reference实际内联。CLI路径及参数以runner-source.py为准，目录中的selected-catalog只保存两条选定模型元信息，不包含API认证。通过现有本地转发入口调用，未复制凭证。

原生subagent未指定模型覆盖，实际turn_context均为alibaba-token-plan-responses/deepseek-v4.1-flash、max，见native-session-models.json。只存可见用户消息、命令/文件改动与终稿，不公开内部推理、完整profile或原生会话原件。

## 审阅helper修复与记录

旧helper在写稿未结束时构造review-R1，E/GLM与G/GLM基线分别变成等待占位。完整结果返回后重审，原包不删除。`results.json`前置检查在创建输出、profile及调用模型之前执行。固定后重审及R3采用call_completed字段，semantic_review_completed为空，语义完成仍由实际报告判定。旧result中的review_completed保持冻结，但仅表示返回文件，不能据此统计完成审稿。

review-preflight-receipt.json记录对未完成批次的真实运行：exit1、未建目录、未调用模型。collect_receipts还核对6个误读会话的用户文本锚点、5个原生会话模型元信息、只读审计前后3个磁盘文件及复制rules；这些都是执行/字节事实。

prior-failure-receipts补上轮12个CODEX_HOME启动错误安全片段、2个原可见trace的429片段以及1个runner限时结果，不将技术失败计入写稿质量。未取得实际填写人文开题，没有运行全论文、桌面WorkBuddy或三市场安装检查。
