# 引用模块外部方案比较（2026-07-14）

本轮只吸收工作流思想，未复制第三方代码或原文。

| 方案 | 核心做法 | 本项目取舍 |
| --- | --- | --- |
| [RE-paper-writing / claim-evidence-map](https://github.com/Research-Equality/RE-paper-writing/blob/main/skills/claim-evidence-map/SKILL.md) | 将主张拆分并绑定证据锚点、支持状态 | 采用“原子论断—来源”账本思想，按中文论文任务重写 |
| [RE-paper-writing / citation-verification-gate](https://github.com/Research-Equality/RE-paper-writing/blob/main/skills/citation-verification-gate/SKILL.md) | 把引文验证作为写作后的独立门禁 | 采用写后反向核对，但不复制其字段或实现 |
| [Hermes research paper writing](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/skills/bundled/research/research-research-paper-writing.md) | 搜索、交叉验证、生成书目、核对论断后再加入正文 | 采用分阶段顺序；仍坚持本 Skill 默认不联网 |
| [Claude Scholar citation verification](https://github.com/Galaxy-Dawn/claude-scholar/blob/main/skills/citation-verification/SKILL.md) | 记录证据、允许措辞及不可增强的边界 | 采用允许/禁止增强措辞思想，改写为紧凑证据账本 |
| [PaperQA prompts](https://github.com/Future-House/paper-qa/blob/main/src/paperqa/prompts.py) | 只使用上下文中的来源键；证据不足时拒绝回答 | 保留稳定来源 ID 和证据不足降级 |
| [Nature citation skills](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-citation) | 区分元数据候选、正文支持和 DOI 身份错配 | 采用 DOI 回读匹配与元数据不能支持观点的边界 |
| [Academic research skills claim alignment](https://github.com/Imbad0202/academic-research-skills/blob/main/academic-pipeline/agents/claim_ref_alignment_audit_agent.md) | 将正文论断与检索摘录作语义对齐 | 仅借鉴分层判定思路；其 CC BY-NC 许可不适合直接并入 MIT 代码 |
| [ClawHub academic writing](https://clawhub.ai/modestyrichards/skills/modesty-academic-writing) | 侧重文献真实性、编号与格式 | 不足以阻断“真实文献支持错误论断”，不单独采用 |
| [ClawHub citation management](https://clawhub.ai/wu-uk/skills/citation-check-citation-management) | 侧重元数据、BibTeX 与文献管理 | 只借鉴元数据核对；不采用统一引用率或声望阈值 |

采用的最小分层为：检索发现 → 文献身份 → 原文证据 → 论断语义 → 出版状态 → 格式与双向对应。Crossref 的 [REST API 文档](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) 和 [Retraction Watch 数据说明](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/)用于确认出版状态渠道；数据库未返回关系只能记为未确认，不能证明未撤稿。
