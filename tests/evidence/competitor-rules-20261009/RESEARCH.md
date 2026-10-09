# 公开写作Skill比较与候选选择

查看日期2026-10-09。来源为公开作者仓库/原始Gist，未安装竞品，不以宣传、star、榜单或仓库规模评定效果。来源URL的main可变化；本记录只描述本轮实际打开页面，未声称永久提交固定。四源不是全部市场，英文科研/个人论文规则不等于中文本科、硕士、课程论文的通用规范。

| 来源与定位 | 值得研究的决策 | 与当前版本比较 | 本轮处理 |
| --- | --- | --- | --- |
| [FabianRitter academic-writing](https://github.com/FabianRitter/paper-writing-agents/blob/main/skills/academic-writing/SKILL.md)，4.2 Ambiguous pronouns、6 Revision Workflow | 有歧义的回指补明对象；按反馈范围作最小修改 | 当前有事实主体、章节衔接与最小修改保护，但未具体说明含混回指的处理 | 只隔离尝试回指原子；有材料可澄清才补明，无法确定不猜，清楚回指照留 |
| [hungntt Academic Polisher](https://gist.github.com/hungntt/38ef18cebbe22984c93d1162dba4cd58)，Choose the Revision Strength、Sentence-Level Editing、Compression Rules | 修改力度随任务变化；先减赘述再减次要例子，保住实质推理与限定；含混代词可换具体对象 | 当前主叶、主次入口和ANTI-AI保护区大体覆盖前两项；回指原子有局部增量 | 不复制同义规则；以它对回指、理论限定的保护作为候选副作用检查 |
| [K-Dense scientific-writing](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-writing/SKILL.md) Scientific fidelity，以及[writing_principles](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-writing/references/writing_principles.md) Numbers and units、Language review | 数字概念、分母、单位和范围一致；不靠任意文风阈值证明质量 | 当前证据账本、事实与数字锁定、长稿一致性已有覆盖 | 不引入逐句ID、固定登记表、人审每句门禁，也不把完整报告要求扩张为每段必须写全材料 |
| [AlessandroCaforio write-section](https://github.com/AlessandroCaforio/Academic-Writing/blob/main/.claude/skills/write-section/SKILL.md)，Pre-Writing Protocol、Multi-Pass Workflow | 先读目标和证据，再规划、起草、复核；样稿只校准声音 | 当前逐段简报、长稿状态、作者风格基线、独立复核已覆盖 | 不引入某篇经济学论文的固定文件、第一人称、词数和章节模板 |

## 主次的取舍

竞品压缩次要例子的思路可借鉴，但当前入口已经明确：根据研究问题和章节任务决定详略；关键反证、分歧及改变判断的限定是重点，背景旁支可以收束；明确逐项要求另核对。不再添加“所有数据/所有来源都必须入正文”的检查。竞争规则也不可以改变用户当前文本的未知状态。

## 唯一实验原子

候选只在共用ANTI-AI复核层增加一段回指澄清规则，全文见candidate-rule.txt。未更改三个主叶、联网权限、主次要求、研究状态、版本号或Python产品实现。R1用普通论文四题；R2用开题报告和独立综述各一题。每题两条writer路线，各路线冻结max effort和双臂完整规则输入。材料为本轮新构造，实际生成稿件用于语义比较，不冒充真实客户论文。

Python只复用已有CLI批量调用、保存输出、绑定输入与匿名分组；不按词频、字数、句位或单元测试判定效果。正文评判由未参与写稿的宿主subagent与主审结合原始材料完成。


## 独立来源审计与主审取舍

来源审计由未参与实验起草的宿主subagent完成，实际路线为DeepSeek V4.1 Flash/max，原始可见意见见reviews/source-audit.md。其三项建议仍是建议，不是验证结论：

- 结果方向与阴性/未显著/等效区分：后者是具体的潜在规则缺口，但当前入口已经保护影响判断的反证、分歧和限定，不能把整体结果保真都称为未覆盖；也不能把完整报告要求变成每段必须列全阴性结果。本轮不扩展统计有效性判定，没有新鲜任务验证，不加入。
- 按中文措辞固定五档修改力度：当前已有范围、最小局部修改、压缩顺序与保护项；用户的明确范围比单个动词更准确。不将英文动词档位硬译成默认中文工作流，不加入。
- 数字口径及零/缺失/未测区分：当前已有数字、主体、研究状态与长稿一致性保护，细分口径仍可作为后续有具体错稿时的候选；本轮没有为它产生独立实写证据，不加入。

这三项没有伪装成已合并更新。唯一运行候选仍是回指澄清与清楚回指保护；初版过审后只收窄同一原子，没有叠加以上建议。
