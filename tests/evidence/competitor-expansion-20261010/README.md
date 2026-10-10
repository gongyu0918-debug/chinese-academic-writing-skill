# 竞品扩展与小候选首轮证据

北京时间2026-10-10；基线main c60c589908d1e83dba2bc4beb800b816e391f732，产品0.1.8。

本次研究12个项目谱系的19份固定提交规则，含中文开题/论文、综述、科研审稿、引文与长稿状态。详见RESEARCH.md及SOURCE-LEDGER.json。四个原子分别首轮试验，共32次新写稿；31次执行有效、1次工具使用无效。语义由原稿回读和匿名冷审判断，未以Python、单元测试、字数或关键词证明提示词改善。结果见ADJUDICATION.md：无候选准入，产品目录不改。

目录保存自己的研究概括、病例/候选文本、冻结输入、实际完整输出、过滤后的可见执行轨迹、独立报告与主审更正。sources配置和SOURCE-LEDGER只保存出处、哈希及范围，未再发布竞品全文。原始运行账户配置、内部推理、私密会话、原始源码下载件均不进入本目录。runner仅为可复现调度证据，不属于发布Skill。

实际写稿命令（使用宿主已配置native CLI路由，不能在无相同provider配置的环境声称已复现）：

```powershell
& "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B .release/competitor-expansion-20261010/coverage_runner.py --spec .release/competitor-expansion-20261010/review-cases.json --output .release/competitor-expansion-20261010/review-R1 --candidate-dir .release/competitor-expansion-20261010/candidates/review --timeout 300
```

同一命令替换review为reports、statistics、secondary；四组均完成，执行返回码0不代表质量通过。PREREGISTRATION.md与SECONDARY-PREREGISTRATION.md先于对应写稿；快照、binding、result、session-models分别证实使用输入、实际模型和有效性。匿名包映射只供事后核对，审阅者未看。

未完成/风险：只做首轮，没有三轮准入、整稿或客户使用评估；候选有过严审查、材料否认、额外逻辑推论与指定APA格式错误，基线也有失败，冷审发生过漏读/误报。0.1.8不因此被宣称无风险。临时工作树归档核对见WORKTREE-LIFECYCLE.md。
