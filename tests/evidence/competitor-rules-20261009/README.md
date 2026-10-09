# 2026-10-09 竞品规则研究与实写

四份公开原始Skill与当前规则逐项比较见RESEARCH.md；候选初版及收窄版见candidate-rule.txt、repaired-rule.txt。四轮共44次完整返回、22个双臂配对，其中包含拒绝已给文本的交付失败；完成响应数不是可用稿数或质量通过数。最终取舍见ADJUDICATION.md。

R1四题，R2两题，R3两题，R4三题；每题两路线、每路线旧基线/候选独立会话。writer为Alibaba Qwen3.8 Flash与Ollama GLM5.3 Flash，max，实时catalog支持。R1用了ephemeral调用，只能核验所请求路线、effort及完整命令绑定，没有保留实际native会话元数据。R2—R4共28次实际native输入与模型/effort记录相符；这不证明provider后端身份，也不证明文字有效。绑定和实际原稿见各轮目录。

所有材料为新构造；模型实际生成稿件，不代表真实客户全文、实地研究或来源核验。完整冻结入口、唯一主叶、文风层均供同一任务的双臂内联加载，无工具、联网、子委派；复核另由未参与写稿的宿主代理执行。该通路验证规则文本，不验证自主文件路由、客户端集成或安装。

R3/H在原稿后未显式关闭正文范围，尾随约束可能被当成正文。其“制作残留”意见不用于版本优劣判断；R4用明确正文括界和新数值修正输入设计。所有原输出保留，不事后清洗。

## 实写调用命令

在本轮隔离工作树下依次运行现成批量调用器的临时适配副本：

```powershell
py -3 -B .release\run_competitor.py --output tests\evidence\competitor-rules-20261009\R1 --models 0 1 --isolated-profile --ordinary-only --effort max --timeout 200
py -3 -B .release\run_competitor_confirmation.py --output tests\evidence\competitor-rules-20261009\R2 --models 0 1 --isolated-profile --ordinary-only --retain-session-metadata --effort max --timeout 200
py -3 -B .release\run_competitor_repaired.py --output tests\evidence\competitor-rules-20261009\R3 --models 0 1 --isolated-profile --ordinary-only --retain-session-metadata --effort max --timeout 200
py -3 -B .release\run_competitor_final.py --output tests\evidence\competitor-rules-20261009\R4 --models 0 1 --isolated-profile --ordinary-only --retain-session-metadata --effort max --timeout 200
```

这里只用Python复用模型调用、输出保存和匿名分组；没有生产Python改动，没有Python单元测试、词频、字数或规则词句门禁。每轮原始runner-source.py和冻结规则留存，可据其重建调用；旧题重放仅供证据核对，后续验证仍应新题。

提交前将调用器放在证据父目录的4个临时runtime移到本工作树.release/competitor-runtime，公开文件不含临时profile、工作空间副本或隐藏推理。第一次git add因这些临时副本的Windows路径过长未成功、没有提交或发布；清理归档范围后再提交。原绑定运行期路径未篡改，移动记录见runtime-relocation.json。

GLM批量冷审m0可见trace有web_search(query=test)，违背本轮禁工具条件，该调用不计受控独立验证；原记录保留。有效独立CLI复核为GLM m1的5对和Qwen Max各上下文的G/I/K三对，共8对。剩余Qwen H/J分别有输入边界和共有拒审限制，不声称全部22对独立通过。
