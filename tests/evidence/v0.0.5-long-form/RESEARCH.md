# 长稿稳定与全文一致性方案检索

本轮只新增长稿状态与全文复核层，不调整段落生成规则。检索和源码核对得到以下可复用机制：

- [SNL-UCSB paper-writing-skill](https://github.com/SNL-UCSB/paper-writing-skill)：借鉴 `project_context.md`、章节论点与证据分配、合稿后的跨章节 Integration；不采用固定句长、零限制语、全主动语态和固定首句。
- [RE-paper-writing](https://github.com/Research-Equality/RE-paper-writing)：借鉴跨会话 `paper-memory-ledger`，只记录已有证据支持的稳定事实，未知项不得猜测，状态文件不得替代当前稿件。
- [Hermes research-paper-writing](https://github.com/nousresearch/hermes-agent/blob/main/skills/research/research-paper-writing/SKILL.md)：借鉴局部复核与全文二次复核分离，以及全文阶段检查冗余、术语、叙事链和前文承诺。
- [vibe-paper-writing](https://github.com/Zhangyanbo/vibe-paper-writing/blob/main/tasks/paper-review.md)：借鉴跨章节矛盾、术语、符号、图表引用的独立检查；作者判断不明确时不自动解决。
- [academic-writing-agents](https://github.com/andrehuang/academic-writing-agents)：借鉴先诊断、后修改、再复验，以及带位置和严重度的持久问题记录；不以多代理数量代替证据核验。
- [K-Dense scientific-writing](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/scientific-writing/SKILL.md)：借鉴修订阶段检查全文主线、术语、符号、图表和引文；不采用统一 IMRaD、英文句长或列表比例。

据此采用三项设计：耐久 `paper-state.md`、只规定章节职责的 `section-briefs/`、合稿后按硬边界到语言整理执行的全文复核。机械脚本只查跨文件重复、显式术语组、指定缩写和 LaTeX 交叉引用，所有非结构命中均为回读候选。
