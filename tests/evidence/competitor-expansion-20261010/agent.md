# 竞品多范围研究记录（北京时间2026-10-10）

任务：继续查找可利用竞品规则，对照当前0.1.8，控制新增负担，提供实际写稿证据。基线main c60c589；新建托管worktree academic-competitors-1010，分支codex/academic-competitors-1010。创建前没有空闲附着工作树；其他历史手工实验不是本任务，不代为回收。

主审先做英文科学写作/审稿与当前规则对照。Noether(01a12386-a5e2-7072-b7a9-cbd4fe95a76e)并行查中文项目，Anscombe(01a12386-a760-7ed2-ad33-01e4b135b71e)查引文/证据/长稿协作；两者均已交最终报告并关闭。其建议逐项经主审取舍，未直接入库。

写稿使用既有native CLI运行器，两条writer路线/provider/effort保持与本项目前轮相同。Python只用于公开源码取证、CLI调度、匿名包与字节归档，未运行单元测试或机械语义评分。本轮独立复核Nash(01a12390-17a8-79c3-a1d9-1ba65a4f6f48)/Locke(01a12390-192f-7281-b0a2-adadf6abe523)/Newton(01a12390-1ad6-75e1-b4cd-69c3afee0f3f)/Mill(01a12394-697e-78b3-a728-12b615e1eb15)读取各自匿名完整稿包，实际意见和覆盖缺口均保留，另列主审复查。独立者均未参与起草，沿用父模型设置；实际会话字段另由native-session-models.json记录，不把昵称算不同模型。

四个候选各自在忽略的.release内单独修改一条主叶；当前产品目录无改动。资料与模型输出留在本轮独立证据目录，源码原件仍在忽略区。冻结证据、提交并合并后回收托管worktree，最终核对见WORKTREE-LIFECYCLE.md。只研究，不发布、打tag、push或更新桌面包。

首轮完成32次实际写稿（31执行有效、1工具使用无效），主审回读全部输出。四个冷审角色均已交最终报告并关闭，来源研究两角色也已关闭；保留Newton覆盖补充、各报告漏读/误报与主审不同意的结论。四候选均未准入，未把调用数、字段完整或cold reviewer的“可用”当作通过率。native-session-models核对六agent均为继承父模型的deepseek-v4.1-flash/max，不称多模型评委。writer会话逐个核对qwen3.8-flash与glm-5.3-flash/max。

归档首检拒绝写入：最初捕获器只看response_item.phase=final，而该native版本的结束报告位于event_msg.task_complete.last_agent_message，造成全部报告计数为0。核对实际日志字段后补采可见结束消息，未采内部推理，未重跑写稿或改动原报告；再次核对完成模型、输入输出绑定后才写证据目录。该修复只是归档兼容，不作为规则改善。
