# 原始竞品子代理报告

会话：01a0ec9c-fb24-76a3-9a88-5675c8884349。主审核对与纠偏另见 RESEARCH.md；以下为原始可见报告。

查询日期均为 2026-09-29。本轮只读，未改仓库、未运行外部代码、未派生代理；以下只取本次实际打开的 GitHub/官方帮助原文，不把营销页当效果证明。本库基线见 [SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:15)、[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:31)、[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:44)、[SKILL.md](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:74)，实验规范见 [HANDOFF.md](F:/Workspaces/chinese-academic-writing-skill/HANDOFF.md:81)。

1. **Academic Research Skills for Claude Code**  
   - URL: [GitHub](https://github.com/Imbad0202/academic-research-skills)  
   - 可学机制：阶段矩阵把“研究—写作—完整性质检—评审—修订—定稿”拆成明确主次，2.5/4.5 为强制完整性质检；`data_access_level`、Material Passport、claim audit 和 run ledger 把证据边界显式化；`academic-paper/SKILL.md` 里还有 phase-by-phase 调用、最大 2 轮修订、Critical 问题阻断进入定稿。  
   - 本库差异：本库已有三主叶、四模式、材料门禁和独立复核，但没有这类全流程状态机和多层契约。  
   - 不该借鉴：不建议引入 12-agent 编排、模拟期刊评审或多层 Material Passport；对本库的中文单稿写作而言，复杂度会超过用户实际需要。

2. **PaperQA2**  
   - URL: [GitHub](https://github.com/Future-House/paper-qa)  
   - 可学机制：README 的算法是“检索—取证据—生成答案”三段式，核心在 contextual summarization、重排序、`evidence_k` / `answer_max_sources` 这类显式证据预算，并接 Crossref、Semantic Scholar、Unpaywall 做元数据。  
   - 本库差异：本库是写作 Skill，不做自动检索代理和答案生成，材料由用户提供。  
   - 不该借鉴：不要把检索命中当作引用充分或写作质量；PaperQA2 的证据预算也不能直接迁移到中文论文段落组织。

3. **Elicit Systematic Reviews**  
   - URL: [官方帮助中心](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit)  
   - 可学机制：Setup 页先锁定研究问题、PICO/纳入排除条件，再进入 Gather、Screen、Extract、Report；摘要筛选先于全文筛选，每个决策给出原文引句，双评审和阈值调整是显式可选层。  
   - 本库差异：本库不做企业级系统综述，不自动检索 1,000 篇文献，也不做双人筛选。  
   - 不该借鉴：不要照搬大规模筛选、分层套餐或自动综述流程；本库更适合“作者材料有限、逐段写作”的场景。

4. **Scite Citation Classification**  
   - URL: [官方帮助中心](https://help.researchsolutions.com/hc/en-us/articles/31949617584148-How-are-citations-classified)  
   - 可学机制：把引用分成 supporting / contrasting / mentioning，依据“修辞功能”而非情感；同一实验不重复也可算 supporting，单纯使用方法、试剂或软件不算 supporting。  
   - 本库差异：本库的引用审计关注存在性、映射和著录格式，不做全库引用图谱或智能引用分类。  
   - 不该借鉴：不要引入完整 citation graph 或分类模型；对单篇稿件而言，这会把工具复杂度推得过高。

另外，`raw.githubusercontent.com` 在浏览器端被拦截，我改用 GitHub 渲染页读取 ARS 原文；GPT Academic 打开后因规则证据不足，未纳入本结论。除该限制外，核心来源均已实际打开。

可择一至三项做最小实验原子：

1. **内部论点—证据预映射**：起草前仅内部记录每个章节的 claim、证据 ID 和允许强度，不输出到正文。反例风险是短段落被过度结构化，成稿出现机械痕迹。  
2. **复核优先级重排**：独立复核按“事实/来源边界 > claim-evidence 映射 > 结构衔接 > 文风”排序。反例风险是审稿变成清单式，漏掉跨段一致性。  
3. **最小加载门**：只有用户明确要求或多章节长稿时才加载 citation-research / long-form consistency 叶。反例风险是边界过窄导致用户重复请求，或漏掉隐性上下文。  


