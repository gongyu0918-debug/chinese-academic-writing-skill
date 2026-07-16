import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = ROOT / "HANDOFF.md"
SKILL_DIR = ROOT / "chinese-academic-writing-assistant"
SKILL_PATH = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
REFERENCE_DIR = SKILL_DIR / "references"
PROSE_LINT = SKILL_DIR / "scripts" / "prose_lint.py"
CITATION_AUDIT = SKILL_DIR / "scripts" / "citation_audit.py"
TASK_REFERENCES = {
    "academic-writing.md",
    "academic-proposal.md",
    "academic-literature-review.md",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    _, frontmatter, _ = normalized.split("---\n", 2)
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line: {line!r}")
        fields[key.strip()] = value.strip()
    return fields


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.openai = OPENAI_YAML.read_text(encoding="utf-8")
        cls.references = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(REFERENCE_DIR.glob("*.md"))
        }
        cls.prose_lint = PROSE_LINT.read_text(encoding="utf-8")
        cls.citation_audit = CITATION_AUDIT.read_text(encoding="utf-8")
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")

    def test_frontmatter_has_only_name_and_description(self) -> None:
        fields = parse_frontmatter(self.skill)
        self.assertEqual({"name", "description"}, set(fields))
        self.assertEqual("chinese-academic-writing-assistant", fields["name"])
        self.assertGreater(len(fields["description"]), 40)

    def test_openai_metadata_uses_new_invocation_name(self) -> None:
        self.assertIn('display_name: "中文论文写作"', self.openai)
        self.assertIn("$chinese-academic-writing-assistant", self.openai)
        self.assertNotRegex(
            self.openai,
            r"\$chinese-academic-writing(?!-assistant)",
        )

    def test_four_dimensional_route_and_nested_routes_are_explicit(self) -> None:
        for marker in (
            "最终交付物 × 操作模式 × 材料状态 × 研究阶段",
            "普通论文或论文中的文献综述章节",
            "开题报告及其中的研究现状、研究述评",
            "最终交付物本身为独立文献综述",
            "每个原子任务只读取一个专项叶",
        ):
            self.assertIn(marker, self.skill)

    def test_nonacademic_artifact_stops_and_transfers(self) -> None:
        for marker in (
            "路由以最终交付物的文种为准",
            "立即停止本 Skill 的起草",
            "不输出正文",
            "不补充或推断办理要素",
            "正式通知或公文写作能力",
        ):
            self.assertIn(marker, self.skill)

    def test_user_facing_copy_hides_process_and_audience_labels(self) -> None:
        for marker in (
            "用户给出的受众定位、版本用途和制作要求只作为写作约束",
            "不把“本轮未提供”“需作者确认”等制作回合标签写进正文",
            "没有材料依据，不写进开题正文",
            "确需提醒时移到正文后建议",
        ):
            self.assertIn(marker, self.skill + "".join(self.references.values()))

    def test_final_copy_check_removes_repeated_explanations_and_tail_notes(self) -> None:
        for marker in (
            "同一材料或证据边界只在首次必要位置说明",
            "研究状态用“已、拟、尚未”等正文时态和语气表达",
            "删除制作回合或版本标签、写作控制旁白",
            "必要的结论限制应就近融入对应论断",
            "不另作小字式尾注",
        ):
            self.assertIn(marker, self.skill)

    def test_material_gates_are_explicit(self) -> None:
        for marker in (
            "无目标文本不能执行底稿修改",
            "只有题目时，不形成完整论文或完整开题设计",
            "常识性判断都不是事实证据",
            "输入中没有某项内容，只能说明现有材料不含该项",
            "不扩写招募、访谈提纲、编码、分析步骤、写作环节、进度任务或成果范围",
            "不预选统计检验、结果方向、显著性表达或因果模板",
            "独立综述没有可用来源且用户未授权检索时，不写综述正文",
            "未完整读取时明确已覆盖和未覆盖部分",
        ):
            self.assertIn(marker, self.skill)

    def test_evidence_and_citation_contract_is_explicit(self) -> None:
        for marker in (
            "材料 ID、来源层级",
            "已读原文",
            "已读摘要",
            "仅有元数据",
            "待核验来源",
            "来源是否存在、元数据是否一致、原文是否支持当前论断、著录格式是否符合要求",
            "DOI 存在不等于论点获得支持",
        ):
            self.assertIn(marker, self.skill)

    def test_citation_research_is_explicitly_authorized_and_progressive(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "默认不联网",
            "题目含“最新、当前、近年”，出现 DOI、URL，或者材料不足，都不构成授权",
            "授权只覆盖本次约定的主题、范围和轮次",
            "来源层与 ANTI-AI 层不得同阶段加载",
            "不自设统一合格比例",
            "不用无关来源抬高数字",
        ):
            self.assertIn(marker, self.skill + citation)
        self.assertIn("scripts/citation_audit.py", self.skill)

    def test_default_citation_style_distinguishes_rich_text_from_markdown(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "富文本中的 `[1]` 设为上角标",
            "纯文本和 Markdown 无法可靠保留上标格式时使用 `[1]`",
            "文末设置“参考文献”",
            "正文标号与文后条目双向对应",
            "不得把全部标号机械堆在段末",
        ):
            self.assertIn(marker, self.skill + citation)

    def test_source_authority_and_coverage_contract_is_not_a_black_box_score(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "匹配性和内容支持优先于名气",
            "期刊名、被引量和作者声望只作辅助信号",
            "获得有效支持的应引用论断数 / 应引用论断总数（N/M）",
            "高风险论断",
            "不能单独证明权威或质量",
        ):
            self.assertIn(marker, citation)

    def test_citation_identity_and_atomic_claim_contract_are_explicit(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "DOI 能解析仍须回读并匹配题名、第一作者、年份或版本族",
            "指向其他论文即阻断",
            "主体—关系—对象—方向或否定—范围",
            "描述、相关、预测、中介、因果和机制不得互换",
            "局部中介不得拼成未经检验的完整路径",
            "否定结果必须保留原主语和关系对象",
            "不能从“A 与 B 相关、B 与 C 不相关”推出“A 与 C 不相关”",
            "允许措辞、禁止增强措辞",
            "标题句、段首判断、过渡句和段末综合同样是待核验论断",
            "只有来源明确检验整体路径时",
            "降调词不能为未检验路径补足证据",
            "不替它们新增方向、作用或路径",
        ):
            self.assertIn(marker, citation)

    def test_post_writing_semantic_gate_precedes_citation_formatting(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "写后语义门禁",
            "先逐句检查段首、过渡和段末综合",
            "按每个引文反向提取原子论断及其来源 ID",
            "主体、关系对象、方向、否定、强度、数字、样本和范围",
            "支持、部分支持、含混、冲突、无法核验",
            "只有“支持”可直接保留",
            "任一例即阻断相应正文交付",
            "不因尚未跨任务复现而放行",
            "该门禁先于角标与文后格式检查",
        ):
            self.assertIn(marker, citation)

    def test_publication_status_check_never_upgrades_missing_records(self) -> None:
        citation = self.references["citation-research.md"]
        for marker in (
            "出版状态记录实际核验渠道和日期",
            "只有预定渠道均成功返回可识别的当前文献记录",
            "本次未检出更新",
            "不得写成“确认未撤稿”",
            "任一渠道无记录、请求失败或只返回空关系时，优先记“未确认”",
            "不能据此推断状态正常或被其他渠道的空结果抵消",
            "OpenAlex 等聚合状态只作辅助",
        ):
            self.assertIn(marker, citation)

    def test_integrity_standards_and_review_interface_are_explicit(self) -> None:
        for marker in (
            "不得代写整篇提交稿",
            "GB/T 7714-2025",
            "GB/T 7713.1-2025",
            "不得声称“完全符合”",
            "位置—严重度—问题—依据—修改建议",
        ):
            self.assertIn(marker, self.skill)

    def test_optional_post_text_suggestion_categories_are_complete(self) -> None:
        categories = {"可补充论点", "可补充论据", "可补充论述", "其他修改建议"}
        for category in categories:
            self.assertIn(category, self.skill)
            for name in TASK_REFERENCES:
                self.assertIn(category, self.references[name])
        self.assertIn("按实际需要给出", self.skill)
        self.assertIn("没有实际建议的类别不输出", self.skill)

    def test_leaf_specific_contracts_exist_without_global_rule_copies(self) -> None:
        self.assertEqual(
            TASK_REFERENCES | {"anti-ai-writing.md", "citation-research.md"},
            set(self.references),
        )
        writing = self.references["academic-writing.md"]
        proposal = self.references["academic-proposal.md"]
        review = self.references["academic-literature-review.md"]
        for marker in (
            "单段润色",
            "段落是最小可充分论证单元",
            "不要求固定句序、句数、首句位置、收束句或等长段落",
            "同学科、同层级、同类范文",
            "摘要、结论和研究不足",
        ):
            self.assertIn(marker, writing)
        for marker in ("已有基础", "拟开展工作", "预期结果", "三种模式"):
            self.assertIn(marker, proposal)
        for marker in (
            "不补行业趋势",
            "不先替后续材料分类",
            "输入缺失不等于项目尚未确定",
            "进度与成果不得超出作者明确给出的任务和时间",
        ):
            self.assertIn(marker, proposal)
        for marker in ("来源覆盖表", "普通叙述性综述", "PRISMA", "三种模式"):
            self.assertIn(marker, review)
        for marker in (
            "实际使用来源",
            "提及但未用于观点",
            "静默遗漏",
            "必须在对应论断后保留该 ID",
            "不能替代正文中的就近标注",
            "作者—年份表述不能替代用户要求保留的来源 ID",
        ):
            self.assertIn(marker, review)
        for content in self.references.values():
            self.assertNotIn("默认不扩展检索", content)
            self.assertNotIn("位置—严重度—问题—依据—修改建议", content)
            self.assertNotIn("GB/T 7714", content)

    def test_anti_ai_reference_is_progressive_cross_cutting_layer(self) -> None:
        anti_ai = self.references["anti-ai-writing.md"]
        for marker in (
            "在唯一专项叶完成内容与证据复核后",
            "不是第四种任务叶",
            "只有用户明确要求文风、去模板化或语言质量复核",
            "普通起草、事实审查",
            "scripts/prose_lint.py",
        ):
            self.assertIn(marker, self.skill)
        for marker in (
            "候选，不是证明文本有错或由 AI 生成",
            "没有能指出具体位置、上下文依据和语义问题的候选时，保持原文",
            "第二遍不应为了“更像人写”继续换词或重排",
            "不强行注入观点、情绪或口语",
        ):
            self.assertIn(marker, anti_ai)
        self.assertIn("至少三个独立输出", self.handoff)
        self.assertIn("单例和未达阈值的问题只记录", self.handoff)
        self.assertIn("不适用于事实、数据、引用", self.handoff)

    def test_review_contract_keeps_fields_but_allows_scale_appropriate_forms(self) -> None:
        for marker in (
            "位置—严重度—问题—依据—修改建议",
            "承载形式服从用户和文本规模",
            "短段可用表格",
            "长稿可用总评、阻断项和分节问题",
        ):
            self.assertIn(marker, self.skill)

    def test_sample_identity_cannot_be_inferred_from_context(self) -> None:
        self.assertIn("样本称谓按原文保留", self.skill)
        self.assertIn("不从场景推定身份", self.skill)

    def test_process_leak_exceptions_never_cover_the_models_own_workflow(self) -> None:
        for marker in (
            "只有用户明确要求逐字保留的待审原文",
            "任务本身确需讨论这些词的测试记录",
            "该例外不允许说明模型自身的处理过程",
        ):
            self.assertIn(marker, self.skill)

    def test_prose_lint_is_report_only_and_academically_adapted(self) -> None:
        for marker in (
            "without rewriting",
            "user-owned",
            "Matches and frequencies are review candidates",
            "--delivery-mode",
            "--strict",
        ):
            self.assertIn(marker, self.prose_lint)
        for forbidden in ("--fix", "AI 算力", "主送机关", "发文字号", "项目卡片"):
            self.assertNotIn(forbidden, self.prose_lint)

    def test_citation_audit_is_read_only_and_has_no_default_quota(self) -> None:
        for marker in (
            "Read-only citation coverage",
            "never rewrites",
            "--minimum-marker-coverage",
            "no default is assumed",
        ):
            self.assertIn(marker, self.citation_audit)
        for forbidden in ("--fix", "write_text(", "write_bytes("):
            self.assertNotIn(forbidden, self.citation_audit)
        self.assertIn("sys.dont_write_bytecode = True", self.citation_audit)

    def test_runtime_prompt_has_no_version_or_legacy_invocation(self) -> None:
        runtime = self.skill + self.openai + "".join(self.references.values())
        self.assertNotIn("0.0.1", runtime)
        self.assertIsNone(
            re.search(r"\$chinese-academic-writing(?!-assistant)", runtime)
        )


if __name__ == "__main__":
    unittest.main()
