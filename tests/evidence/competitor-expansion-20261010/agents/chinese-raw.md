只读检索完成，交 3 个已实际打开原文的中文项目（未凑第 4 个，已排除你点名的英文项目；全程未安装、未执行、未改文件、未用历史记忆、未向其他任务发消息）。

## 来源表（均逐字读取原始文件全文）

| 作者·项目 | 实际读取的文件（路径全称） | 可借鉴决策与适用边界 | 不宜移植的要求 | 许可证 |
|---|---|---|---|---|
| [XiaoJie4096/thesis-workflow-cn](https://github.com/XiaoJie4096/thesis-workflow-cn)（原 MMKLN0，仓库已重命名；面向中文本科全流程） | [skills/thesis-workflow-cn/SKILL.md](https://github.com/XiaoJie4096/thesis-workflow-cn/blob/main/skills/thesis-workflow-cn/SKILL.md)；[thesis-proposal-cn/references/proposal-writing-rules.md](https://github.com/XiaoJie4096/thesis-workflow-cn/blob/main/skills/thesis-workflow-cn/modules/thesis-proposal-cn/references/proposal-writing-rules.md)；[literature-review-cn/references/review-writing-rules.md](https://github.com/XiaoJie4096/thesis-workflow-cn/blob/main/skills/thesis-workflow-cn/modules/literature-review-cn/references/review-writing-rules.md) | 开题：无文献时"不编造作者-年份/题名/数据/政策日期"，只写概括加一句"待结合真实文献补充"说明；研究方法须对应真实章节（"不为装饰加方法"）；预期成果适度。综述：按主题归类、段落通常≥4句、禁"术语+一句话"碎片式；参考文献只从用户材料构建、不外推。边界：本科开题/综述；"说明句是否保留"与你"只输出正文"偏好有冲突，需实测 | WorkBuddy/Kimi WebBridge+知网的检索模块（平台与账号依赖）；">=15条文献、>=3000字"默认值（你方应让位于学校/教师要求）；"每阶段停下问一次"不适用于一次性成稿 | MIT（GitHub API 检出 MIT，仓库含 LICENSE） |
| [yanlin-cheng/skill-thesis-writer](https://github.com/yanlin-cheng/skill-thesis-writer)（本科/研究生，多学科；209 star） | [SKILL.md](https://github.com/yanlin-cheng/skill-thesis-writer/blob/master/SKILL.md)；[assets/templates/social_science_thesis.md](https://github.com/yanlin-cheng/skill-thesis-writer/blob/master/assets/templates/social_science_thesis.md) | 文科/社科骨架：心理学/教育学/管理学必备章节表；摘要五段结构（背景→目的→方法→结果→结论）；量表来源+信效度、共同方法偏差（Harman/ULMC）、Bootstrap 中介等报告句式；"局限与未来方向"三段模板。边界：定量实证社科论文适用，系统设计类/纯综述不适用 | 降AI味=同义词替换表（"此外→值得注意的是"等）——与源3"值得注意的是=填充语应删"直接冲突，机械替换会造新口癖；"笔者观察到"式注入若无真实观察即虚构；硬数字（工科被动语态≥60%、经典:前沿=3:7、近5年占比）是作者约定非规范；"每月同步CSSCI/SCI"属维护宣称，不能当规则 | MulanPSL-2.0（GitHub API 检出） |
| [xiaou61/thesis-skills](https://github.com/xiaou61/thesis-skills)（"接单2年"经验类；[renzo1031/thesis-skills](https://github.com/renzo1031/thesis-skills) 为其 fork，我读的是 fork 快照） | thesis-standardizer/[SKILL.md](https://github.com/renzo1031/thesis-skills/blob/main/thesis-standardizer/SKILL.md)；references/[aigc-style-governance.md](https://github.com/renzo1031/thesis-skills/blob/main/thesis-standardizer/references/aigc-style-governance.md)；references/[quality-gates.md](https://github.com/renzo1031/thesis-skills/blob/main/thesis-standardizer/references/quality-gates.md) | 去AIGC：report-first（先出风格风险报告、确认后只改高风险段）；不承诺绕检测，定位为学术质量/证据密度/来源完整/修订透明；中文AI味模式清单（公式化理论开头、"由此可见/综上所述"式结尾、僵化枚举、无来源归因、填充语、通用正向结论、段节奏雷同）+8个修复动作（删填充、具体化、标 needs_source）。六道质量门+"完成语"（已验证/待人审/缺证据）。边界：商业接单经验，数值默认均为可覆盖项；"不承诺绕检测"框架可直接借 | 脚本与固定工作区布局（thesis-ai-standard/）；"中文12-15条+英文3-5条、近6年、每引用点≤2文献"为作者约定非标准；SKILL.md 存在悬空引用（literature-harvest-workflow.md 在 fork 快照中缺失）；两个仓库均无许可证，文字不得直接复制 | 未核实（上游与 fork API 均 license=null、树中无 LICENSE 文件） |

口径说明：renzo1031 与 xiaou61 按一个项目计；fork 快照止于 2026-05-03，上游 2026-06-06 有推送未读。另有仅见于搜索摘要、未核实归属的仓库（如 ZyhSechub/chinese-thesis-workbench-skill、Gstack4review），未纳入也未当规则。

## 待验证建议（最多 3 条）

1. 两派"填充语"主张需真实稿 A/B：源3主张删"值得注意的是/不难发现"等，源2主张把"此外"替换成"值得注意的是"——用同一篇真实改稿做"删除版 vs 替换版"，以填充词密度和段落节奏做机械门，再决定入库哪一方。
2. 开题"无文献说明句"的保留形态待实测：在"只输出正文"的约束下，测试说明句放正文括注、放正文末尾、或移出正文三种形态的接受度，验证它是否真的必需。
3. 综述"段落≥4句/≥3000字/≥15文献"与"减负、自然"目标存在张力：用一篇真实中文综述做长段落版 vs 精炼版对照，再定是否入库、以软门还是硬门入库。
