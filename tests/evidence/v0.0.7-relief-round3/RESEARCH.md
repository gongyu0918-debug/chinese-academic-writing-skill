# 第三轮减载与竞品借鉴研究

检索和复核日期：2026-07-31。外部方案只提供候选线索，最终是否采用以本仓库的机械门禁、短稿/长稿真实写作和匿名评审为准。

## 覆盖范围

结合前两轮留存的 `v0.0.4`、`v0.0.5`、`v0.0.6` 研究记录和本轮刷新，共记录 24 个 GitHub、SkillHub.cn、ClawHub 关联条目。跨平台同名包按平台条目记录，不宣称它们一定是 24 个相互独立的代码库。

GitHub 条目包括：

1. [SNL-UCSB paper-writing-skill](https://github.com/SNL-UCSB/paper-writing-skill)
2. [academic-research-skills / academic-paper](https://github.com/Imbad0202/academic-research-skills)
3. [SciWrite](https://github.com/labarba/sciwrite)
4. [Vibe Paper Writing](https://github.com/Zhangyanbo/vibe-paper-writing)
5. [RE-paper-writing](https://github.com/Research-Equality/RE-paper-writing)
6. [Hermes research-paper-writing](https://github.com/NousResearch/hermes-agent)
7. [academic-writing-agents](https://github.com/andrehuang/academic-writing-agents)
8. [K-Dense scientific-writing](https://github.com/K-Dense-AI/scientific-agent-skills)
9. [paper-writing-suite](https://github.com/jin-s13/paper-writing-suite)
10. [nature-skills / nature-polishing](https://github.com/Yuan1z0825/nature-skills)
11. [research-writing-skill](https://github.com/Norman-bury/research-writing-skill)
12. [codex-claude-academic-skills / research-writing-skill](https://github.com/zLanqing/codex-claude-academic-skills)
13. [OpenJudge paper-review](https://github.com/agentscope-ai/OpenJudge)
14. [AIPOCH medical-research-skills](https://github.com/aipoch/medical-research-skills)
15. [humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic)
16. [article-writing-skills](https://github.com/IrtezaAsadRizvi/article-writing-skills)

SkillHub.cn 条目包括：

17. [academic-writing-polisher](https://skillhub.cn/skills/academic-writing-polisher)
18. [chinese-academic-writing](https://skillhub.cn/skills/chinese-academic-writing)
19. [paper-engineering-assistant](https://skillhub.cn/skills/paper-engineering-assistant)
20. [paperdown](https://skillhub.cn/skills/paperdown)
21. [thesis-tutor](https://skillhub.cn/skills/thesis-tutor)

ClawHub 条目包括：

22. [academic-writing](https://clawhub.ai/teamolab/skills/academic-writing)
23. [academic-writing-refiner](https://clawhub.ai/zihan-zhu/skills/academic-writing-refiner)
24. [paper-engineering-assistant](https://clawhub.ai/mrchenkuan/skills/paper-engineering-assistant)

## 本轮深读的八个实现

| 实现 | 固定版本 | 可借鉴点 | 不采用点 |
| --- | --- | --- | --- |
| paper-writing-suite | `5d6e424` | 入口保持薄，只选择最小任务路由；文献身份、书目信息、论断支持分开核验 | 不再增加第二套路由或状态文件 |
| nature-polishing | `d5c9dee` | 按章节功能校准时态、限定语和论断强度 | 固定 30 词句长和英文期刊风格不适用于中文学位论文 |
| research-writing-skill | `6f79595` | 保留事实、数据、限定条件，正文优先连续段落 | 固定项目目录、完整 LaTeX 工程和大量阶段产物不应成为默认前置条件 |
| OpenJudge paper-review | `2151def` | 全文审查与参考文献核验分层，输出保留位置和严重度 | 会议评分制、固定多代理审稿不能替代中文论文的事实包门禁 |
| AIPOCH medical-research-skills | `f5ef65b` | 先识别研究类型，再走专门逻辑；来源真实性作为硬约束 | 医学专用报告规范和大规模技能编排不迁移为通用中文论文默认规则 |
| ClawHub academic-writing-polisher | `1.0.1` | 最小修改、保存作者声音 | 固定报告结构和入口宣传话语不进入运行时 |
| ClawHub academic-writing-refiner | `1.0.0` | 按章节功能润色，清楚的原句不为统一风格重写 | 强制段首承接、段末预告和会议专属结构不普遍适用 |
| ClawHub paper-engineering-assistant | `1.0.1` | 变更后追踪框架、摘要和正文的影响关系 | 每次修改后强制全量双向同步、固定目录和自动重写会放大维护成本 |

## 高校规范与论文文体

本轮核对的正式资源包括：

- [西北政法大学硕士研究生学位论文写作规范](https://grs.nwupl.edu.cn/hlgl/gzzd/40449.htm)
- [兰州大学研究生学位论文写作参考规范](https://ge.lzu.edu.cn/xueweishouyu/guizhangzhidu/lunwenguanli/2020/1223/158947.html)
- [同济大学研究生学位论文写作指南](https://gs.tongji.edu.cn/info/1063/1754.htm)
- [上海海事大学研究生学位论文撰写规范](https://gs.shmtu.edu.cn/2023/0905/c8089a215413/page.htm)
- [复旦大学继续教育学院本科毕业论文规定](https://cce.fudan.edu.cn/be/d7/c14097a179927/page.htm)
- [北京大学哲学系学术规范与论文写作资源](https://lib.phil.pku.edu.cn/node/56876)

可稳定归纳的共同要求是：

1. 论文围绕明确研究问题或中心论点展开，章节之间形成可回查的论证关系；
2. 材料、数据、方法和结论相互对应，来源层级和论断强度不能混用；
3. 术语、符号、对象、数字和引文在全文保持一致；
4. 结论由正文推出，不简单重复小结，也不加入正文未论证的新事实；
5. 语言准确、朴实、精炼，结构服从学科和论文类型；
6. 高校规范会规定章、节、摘要、参考文献和版式，但没有要求每个自然段采用统一句数、固定句序或等长结构。

因此，本 Skill 只把高校规范沉淀为论证、证据、全文一致性和学科适配原则，不把个别学校的字数、标题层级、字体或参考文献样式升级为跨学校默认规则，也不把少量规范页面冒充“多数毕业论文全文语料仿写”。

## 本轮形成的五条借鉴判断

1. **薄入口、按需加载**值得保留，但继续删除任务叶合同复述没有获得正向证据。
2. **轻量长稿状态**值得保留；变更影响应记录依据、被替代状态和待复核范围，但当前扩展在新基线确认中出现单侧硬失败，暂不合并。
3. **先核对已有引用忠实性，再找缺口**方向最强：两项已决任务均胜出，但第三项三票分裂，未达到预注册决定数，暂不合并。
4. **独立全文审查**应继续覆盖数字、术语、表图、章节承诺、作者待决事项和来源错配；不强制全量自动同步或多代理编排。
5. **段落边界服从论证需要**仍是目标，但删除现有边界提示后短稿超限再次复现，说明当前规则同时承担了篇幅收束作用，不能直接减去。

## 明确排除的反模式

- 固定句长、段长、句数、主题句位置、段末预告和连接词配额；
- 为所有论文强制 IMRaD、三级大纲或统一章节比例；
- 强制建立完整项目目录、全量多代理流程或每次修改后重写全文；
- 用同义词替换、随机句式或所谓检测率作为去 AI 味的主要目标；
- 只核对 DOI、格式和引用数量，不回读来源支持的主体、关系、方向、强度与范围；
- 为填满矩阵、达到字数或形成闭环而补造机制、背景、建议和实践成效。
