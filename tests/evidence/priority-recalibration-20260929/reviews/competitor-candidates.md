我核对的是 `main@297d458d`，产品目录无差异；本轮只读，未改文件。相比之下，PaperQA 和 Academic Research Skills 的可用机制大多已被本库的证据账本、独立复核或路由规则覆盖，直接照搬会变成流程负担，所以只保留以下两个窄候选。

**候选 1：引用角色三分**

来源：[Scite: How are citations classified](https://help.researchsolutions.com/hc/en-us/articles/31949617584148-How-are-citations-classified)。机制是把引用语句分为 supporting、contrasting、mentioning，判断依据是修辞功能而非情感倾向；仅提及不提供证据，supporting/contrasting 才构成证据关系。

本库差异：[citation-research.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/citation-research.md:10) 已有 `引用角色` 字段，但没有定义三类角色及其使用边界；[academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:9) 也没有把“仅提及”与“证据引用”分开。

建议落点：在 `citation-research.md` 的“来源与证据判断”中加一句，例如“引用角色至少分为支持、对照、仅提及；仅提及不能作为论断证据，只可交代背景或方法；对照引用须保留原文差异和证据。”如需影响综述写作，可在 `academic-literature-review.md` 的来源覆盖表处同步一句。

正向任务：给 3 篇材料，分别对应支持、对照、仅提及，要求写一段综述。看候选是否保留对照证据，且不把“仅提及”当作证据。
反控任务：给一段方法性引用，来源只提供实验方法。看候选是否仍允许其作为方法引用，而不误判为“不支持”。

**候选 2：摘要先筛，后读全文**

来源：[Elicit: Systematic Reviews](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit)。机制是先锁定研究问题与纳入条件，再进行摘要筛选，随后才进入全文筛选；每个决策都回到原文引句。

本库差异：[academic-literature-review.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-literature-review.md:9) 已记录全文/摘要层级和覆盖范围，但没有规定“先摘要筛选、后全文读取”的顺序。

建议落点：在 `academic-literature-review.md` 的“来源覆盖与组织”中加一句，例如“材料同时含摘要与全文且数量较多时，先按研究问题和纳入边界筛读摘要，只对直接相关来源读全文；未通过筛选的来源留在账本，不进入正文。”

正向任务：给 10–15 篇混合相关与弱相关文献，要求写综述。看候选是否先筛摘要、只展开直接相关来源，而不是平均介绍。
反控任务：给 2 篇明显直接相关的短综述材料。看候选是否不因新增规则而过度筛选或误删必要来源。

测试建议：在现有隔离 worktree 中做同题 baseline/candidate 双臂，每条候选至少一正一反；不要把 PaperQA 的 `evidence_k`、固定来源数或自动重排搬进来。

---

Scite 窄改可保留，但要说成“引用关系适配”，不是照搬分类器。

现有规则已覆盖“来源是否支持论断”和“归因不得移接”，但没有明确“多篇转述同一研究不等于多次独立验证”。这确实是独立缺口，适合在 `academic-literature-review.md` 加一句：

> 综合证据数量时，区分独立研究结果与对同一结果的转述；多篇仅转述同一研究不计为多次独立验证，方法、背景或试剂引用按其实际作用保留。

这句与 Scite 机制的适配点是：Scite 区分“提供证据”与“仅提及/复述”，且明确方法、试剂、软件引用不自动算支持。把它转成中文综述里的“独立结果 vs 转述”是合理的窄化，不会误伤方法引用。

Elicit 这条建议取消。你指出的风险成立：先只读“直接相关”全文，确实可能漏掉摘要未交代的关键反证或限制。本库已有来源层级和覆盖表，再加“摘要先筛”会变成硬流程，且不是安全小原子。若要借 Elicit，只剩“先锁定研究问题与纳入条件”，这已由现有规则覆盖，因此不再凑数。
