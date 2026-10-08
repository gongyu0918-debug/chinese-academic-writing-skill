实际普通论文叶为 `academic-writing.md`，不是 `academic-paper.md`；当前路由表已正确指向该文件。以下为截至当前已确认的四个具体位置结果：

- **版本冲突裁决**（[SKILL.md:40](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:40)、[academic-proposal.md:31](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-proposal.md:31)、[long-form-consistency.md:23](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:23)）：问题在于三处规则方向一致，但对“用户已明确指定最新版”时是否可直接按该版执行仍不显式。现有保护是均要求不静默改动、冲突先确认或取得更正依据。实际缺口偏执行风险，不是规则漏洞。最小建议是在入口或开题叶补一句“用户已指定版本时按该版执行；未指定或影响不可变项时再请求确认”。

- **只审不改与局部修改授权**（[SKILL.md:29](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:29)、[long-form-consistency.md:60](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/long-form-consistency.md:60)）：问题在于入口允许“先审后改”，长稿叶却把直接修复限定为“最新版材料唯一确定的机械问题”。现有保护是避免代作者做论点、概念或矛盾取舍。实际缺口是非机械但已明确授权的局部修改是否可执行不够清楚。最小建议是标明该限制适用于需要作者取舍的问题，不排除用户已给出依据的局部修改。

- **阶段词与开题状态对齐**（[SKILL.md:17](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:17)、[academic-proposal.md:7](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/references/academic-proposal.md:7)）：问题在于入口用“拟开展/进行中/已完成”，开题叶只定义“已有基础/拟开展工作/预期结果”。现有保护是开题叶明确区分计划状态与已确认栏目。实际缺口是 `进行中` 在开题叶无显式映射，可能被误归入已有或拟开展。最小建议是补一行“进行中事项按已完成部分＋拟开展后续记录，或按模板标为进行中”。

- **普通论文叶文件名核对**（[SKILL.md:21](F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant/SKILL.md:21)）：问题在于用户提示的 `academic-paper.md` 不存在，实际文件为 `academic-writing.md`。现有保护是路由表与磁盘文件一致，未出现断链。实际缺口仅为命名差异，不影响执行。最小建议是后续交接统一使用 `academic-writing.md`，不改规则。

<oai-mem-citation>
<citation_entries>
MEMORY.md:47-47|note=[academic skill entry and audit tool context]
MEMORY.md:228-228|note=[status preservation preference]
</citation_entries>
<rollout_ids>
</rollout_ids>
</oai-mem-citation>
