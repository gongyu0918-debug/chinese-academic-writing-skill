# 竞品窄候选与主审取舍

只读子代理：`01a0ed27-2332-7810-a973-bd5ed0f21f0b`，请求`alibaba-token-plan-responses/glm-5.3 / max`。实际会话元数据另行核对。以下为可见建议及主审决定，不是写稿结果。

子代理初提两项：Scite引用角色三分；Elicit摘要先筛后读全文。主审指出Scite分类对象为引用语句与被引研究的证据关系，不能照搬成“方法和背景引用不可支持”；Elicit的硬筛顺序可能排除摘要未交代的必要反证。随后子代理复核结论如下：

> Scite 窄改可保留，但要说成“引用关系适配”，不是照搬分类器。
>
> 现有规则已覆盖“来源是否支持论断”和“归因不得移接”，但没有明确“多篇转述同一研究不等于多次独立验证”。这确实是独立缺口，适合在 `academic-literature-review.md` 加一句。
>
> Elicit 这条建议取消。先只读“直接相关”全文，确实可能漏掉摘要未交代的关键反证或限制。本库已有来源层级和覆盖表，再加“摘要先筛”会变成硬流程，且不是安全小原子。若要借Elicit，只剩“先锁定研究问题与纳入条件”，这已由现有规则覆盖，因此不再凑数。

主审冻结Q为独立研究结果与二手转述的区分，放在独立综述的据材料起草模式，只增加一条。P为PaperQA按当前问题取证的组织原则与用户要求的学术主次适配；并非引入PaperQA检索、top-k或打分。两者分开对稳定基线实写，再决定是否合并。不复制外部代码。

当前轮主审实际打开的官方依据：

- [PaperQA算法](https://github.com/Future-House/paper-qa#paperqa2-algorithm)：按当前查询给证据片段作上下文摘要和相关性选择，用于组织原则的启发，不是篇章提升证明。
- [Scite引用分类](https://help.researchsolutions.com/hc/en-us/articles/31949617584148-How-are-citations-classified)：区分提供证据与仅提及，按修辞功能判断而非情感；仅使用相同方法不等于提供支持。Q是本库对综述证据独立性的适配，不宣称Scite直接规定本库文字。
- [Elicit系统综述](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit)：子代理核对其阶段流程，主审不把系统综述流程搬入普通叙述综述。既有本轮来源核对详见前轮RESEARCH.md。

Academic Research Skills的证据账本、独立复核、阶段交接已有对应规则，不再追加同义提示或状态机。
