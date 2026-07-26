# 同类论文写作 Skill 对比

检索日期：2026-07-26。GitHub 以固定提交核验，SkillHub.cn 以 CLI 下载的当前包核验，ClawHub 以当前 `inspect` 结果核验。只把竞品作为候选线索，不以下载量或规则数量替代本仓库的真实写作验证。

## 可借鉴的机制

- [paper-writing-suite@5d6e424](https://github.com/jin-s13/paper-writing-suite/tree/5d6e4244e532189099ca5a9c5585b23febcae955)：65 行入口先选覆盖任务的最小路由，再读取对应 reference；入口只保留状态合同和少数门禁。其“文献存在、书目信息完整、当前论断获得支持”分开判断，方向与本仓库一致。
- [vibe-paper-writing@3dc57bf](https://github.com/Zhangyanbo/vibe-paper-writing/tree/3dc57bf350c84fac3c7717143ce394c0e3332dc1)：55 行入口按任务加载 `tasks/`；全文审查覆盖跨章节矛盾、术语、符号和图表引用，修改前先定位前向依赖。
- [Hermes research-paper-writing@dacd8d5](https://github.com/NousResearch/hermes-agent/tree/dacd8d5416f81030e864da06075380d17397e1b7/skills/research/research-paper-writing)：分节只加载贡献摘要、相关证据和必要上下文，局部修订后再做全文复核。其入口约 2,377 行、10.5 万字符，不适合作为本仓库的体量参考。
- [sciwrite@8a57fa7](https://github.com/labarba/sciwrite/tree/8a57fa73d541bdcf7d8501db61c018cb454e9afa)：把全文、单节和定向审查分开；清晰且没有违反规则的句子应保留，不为统一文体而重写。

这些机制在本仓库已经分别由四维路由、证据账本、长稿状态包和全文复核承接。本轮没有新增第二套状态文件或复核清单。

## SkillHub.cn 当前包

- [academic-writing-polisher 1.0.1](https://skillhub.cn/skills/academic-writing-polisher)：最小修改模式和只索取当前段落所需信息可取；固定四段报告、发布宣传进入运行包以及入口版本漂移不取。
- [chinese-academic-writing 0.1.1](https://skillhub.cn/skills/chinese-academic-writing)：按阶段和任务加载 reference 可取；固定三级大纲、每段主题句、统一字数比例和未随包提供的依赖不取。
- [paper-engineering-assistant 1.0.1](https://skillhub.cn/skills/paper-engineering-assistant)：Framework—Summary—Body 三层概念可作线索，但实际脚本含 TODO 和 placeholder，不能替代本仓库已经验证的状态包。
- [paperdown 1.0.0](https://skillhub.cn/skills/paperdown)：保留事实、数字、术语和引用边界可取；“70% 学术 + 30% 自然”、近义词替换表和逐段固定报告不取。
- [thesis-tutor 4.1.3](https://skillhub.cn/skills/thesis-tutor)：190 个文件、约 2.40 MB，混有生成脚本、测试、API Key 命令和版本漂移，是运行时高熵反例。

## ClawHub 当前同类

- [academic-writing 1.0.0](https://clawhub.ai/teamolab/skills/academic-writing)：单文件同时承载来源、格式、结构和输出协议，没有渐进加载和长稿状态。
- [academic-writing-refiner 1.0.0](https://clawhub.ai/mayf3/skills/academic-writing-refiner)：局部手术式修改和保存作者声音可取；固定段首承接、段末预告和标点配额不取。
- [academic-writing-assistant 1.0.0](https://clawhub.ai/earthwalking/skills/academic-writing-assistant)：固定 15–30 词句长、100–250 词段长以及“主题句 + 3–5 论证句 + 结论句”会重新引入段落级微控制，不取；包中还出现未随包提供的脚本命令。

## 对本仓库的约束

下一轮继续优先验证跨文件重复、维护话语和评测话语，不增加固定句数、段长、章节数、统一比例、连接词配额或强制报告模板。长稿状态、最新版优先、引用语义门禁和全文闭合继续作为承重层保留。
