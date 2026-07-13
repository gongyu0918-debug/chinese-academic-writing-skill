# 独立冷审

总体：**FAIL**

来源和书目信息真实，篇数、类型、正文—文后映射、默认顺序编码、字数及成品洁净度均合格；但有两处正文证据强度或归因不准确，另有一处撤稿状态核验记录无法复现。

## 逐来源核验

1. Huisman et al.（元分析）：PASS。题名、作者顺序、期刊、2019 年卷期页码及 DOI 均与出版方和 Crossref 一致。可读作者上传期刊排版全文。原文确实纳入 24 项研究；无反馈比较仅 2 项，`g=0.91`；自评比较 3 项，`g=0.33`；教师反馈比较 3 项，合并效应不显著。成品写成“改善更大”“未呈现稳定差异”“研究很少、审慎推广”，强度恰当。
2. Cho & MacArthur：FAIL。书目信息准确。出版方当前明确标为 article preview，可读摘要、完整引言、参与者/场景、初步分析及讨论片段，并非全文；覆盖表对此没有夸大。28 名本科生、现场随机分组、多同伴组获得更多各类反馈等均有支持。硬问题在“非指令性意见引发的复杂修订”：原文是“non-directive feedback predicted complex repairs”，复杂修订再与质量改善相关；反馈类型本身未被随机操纵，不能把“预测”提升为“引发”。
3. Huisman et al.（2018）：FAIL。书目信息准确，出版方提供开放全文。83 名本科生、提供者和接收者改善相近、解释性评论与充分性感知和修改意愿正相关，均获支持。硬问题是“却未直接对应更大的写作增幅”的语法归因：原文未发现直接关系的是“充分性感知、修改意愿”与写作增幅，并未直接检验“解释性评论—写作增幅”。
4. Gao, An & Schunn：PASS，附精度问题。题名、作者、期刊、卷、文章号、DOI 均准确；匹兹堡大学机构域名提供完整出版版 PDF。50 名语言学硕士生、1,356 个可实施反馈单元、联合预测修订质量及相关性设计均有原文支持，因果限定正确。非阻断问题是“具体问题和解决建议较为关键”把两类特征写得同等稳定；原文中“建议/解决方案”是最稳定预测项，“问题识别”仅在部分模型显著或边缘显著。

## 结构与遵循

- 满足至少 1 篇元分析和 2 篇实证；实际为 1 篇元分析、3 篇实证。
- `[1]—[4]` 按首次出现顺序编码，正文与文后条目双向对应，无未使用、缺失、重复或错配来源。
- 纯文本采用 `[n]`，符合 Skill 无模板时的默认引用方式；参考文献著录信息完整。
- 正文共 446 个字符（含 4 个引用标号），去掉引用标号为 434 个字符，落在 300—450 字要求内。
- 成品没有泄露检索、证据账本、路由、门禁、脚本或内部过程。

## 撤稿与更新状态

Crossref 当前 4 条记录均无已登记的 `relation`、`update-to` 或 `updated-by`；出版方可见页面也未显示更正或撤稿通知，但这些只能支持“本次未检出通知”，不能证明绝对不存在。OpenAlex 本次仅能对第 2、4 篇复现 `publishedVersion`、`is_retracted=false`；第 1、3 篇 DOI 直查和题名查询均未返回记录。因此覆盖表“4 篇均经 OpenAlex 确认未撤稿”应改为部分未确认，不能照原表述交付。

## 硬失败

- 第 2 篇把预测关系升级为“引发”。
- 第 3 篇把“未与写作增幅相关”的对象写得含混，可能错误归到解释性评论。
- OpenAlex 对 4 篇均为 `is_retracted=false` 的记录，本次无法完整复现。

## 实际访问的主要 URL

- https://doi.org/10.1080/02602938.2018.1545896
- https://www.researchgate.net/publication/329990438_The_impact_of_formative_peer_feedback_on_higher_education_students%27_academic_writing_a_Meta-Analysis
- https://www.sciencedirect.com/science/article/pii/S0959475209000747
- https://doi.org/10.1080/02602938.2018.1424318
- https://www.tandfonline.com/doi/pdf/10.1080/02602938.2018.1424318
- https://www.sciencedirect.com/science/article/pii/S0191491X23000184
- https://www.lrdc.pitt.edu/schunn/papers/Gao-An-Schunn-SEE.pdf
- https://api.crossref.org/works
- https://api.openalex.org/works
