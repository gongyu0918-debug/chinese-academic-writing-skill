# v0.0.3 网络检索与引用真实链测试

## 结论

**FAIL：检索链真实可用，引用结构可用，但成品语义引用尚不能判定为完整可用。**

测试日期：2026-07-13

候选 Skill 提交：`834f12cb00686107b90305773a9dba6d6c799b05`

writer / verifier 模型 ID：`unavailable`

## 真实链结果

| 环节 | 结果 | 证据 |
| --- | --- | --- |
| 默认离线 | PASS | 无授权 writer 未联网，缺来源时拒绝编写“最新进展” |
| 明确授权检索 | PASS | 找到并核验 1 篇元分析、3 篇实证；4 个 DOI 均解析为真实论文 |
| 访问层级 | PASS | 3 篇取得可读全文或完整出版页面；Cho & MacArthur 仅按出版方预览使用，没有升级为全文 |
| 元数据边界 | PASS | 仅给题名和 DOI 时，writer 未把元数据升级为研究结论，`WEB_USED=false` |
| 检索后隔离写稿 | PASS | 第二轮 writer 报告 `TEST_WEB_USED=false`，只使用上一轮 4 篇来源 |
| 引用结构 | PASS | `[1]—[4]` 与文后条目双向对应；缺失条目消融被高严重度阻断，未使用条目可检出 |
| 语义支持 | FAIL | 冷审发现 1 处相关/预测被写成近似因果，1 处关系对象归因含混 |
| 撤稿状态 | FAIL | Crossref 和出版方本次未见通知，但 OpenAlex 的 4/4 `is_retracted=false` 记录只能复现 2/4 |
| 成品洁净度 | PASS | 无检索、账本、路由、门禁和校验过程残留；prose lint 无高风险项 |

## 本地审计与消融

- 原始成品：4 次编号引用、4 条文后条目、利用率 100%，无高风险结构错误；`citation_audit.py --strict` 退出 0。
- `prose_lint.py --delivery-mode body-only --format --structure --strict --fail-on high`：无命中，退出 0。
- 删除 `[4]` 文后条目：检出 `missing-reference-entry`，严重度 high，退出 1。
- 加入未使用 `[5]`：检出 `unused-reference-entry`，严重度 low；默认和 strict 均不把低风险项误作硬失败。
- 将第 4 篇 DOI 从 `...101252` 篡改为真实但无关的 `...101253`：结构脚本退出 0；联网核验显示该 DOI 对应混合教学研究，证明 DOI 语义一致性必须由联网核验承担，不能由结构扫描器替代。
- 本地扫描把含分号的长复句拆成多个候选，原始成品的标记覆盖为 2/9；引用均位于对应完整句末，冷审确认 4/4 映射，但该覆盖统计存在低估候选。本轮只有一个新鲜成品复现，按约定记录，不做单例修复。

## 阻断详情

1. Cho & MacArthur 原文为“非指令性反馈预测复杂修订，复杂修订与质量改善相关”，成品写成“非指令性意见引发的复杂修订”，升级了因果强度。
2. Huisman et al.（2018）原文未相关的是“反馈充分性感知、修改意愿”与写作增幅，成品句法可能把该结果错误归到“解释性评论”。
3. Gao et al. 的“解决建议”预测更稳定，成品把“具体问题和解决建议”并列为同等关键，属于非阻断精度问题。
4. 元数据边界输出虽正确拒绝越权结论，但没有使用“参考文献”标题，属于单次格式问题。

以上问题尚未达到“至少 3 个输出、2 个任务、2 个 writer 重复”的 Prompt 修复门槛。本轮不修改 Skill，不进行一例一修。

## 主要来源

- https://www.tandfonline.com/doi/abs/10.1080/02602938.2018.1545896
- https://www.sciencedirect.com/science/article/pii/S0959475209000747
- https://www.tandfonline.com/doi/abs/10.1080/02602938.2018.1424318
- https://www.sciencedirect.com/science/article/pii/S0191491X23000184
- https://www.lrdc.pitt.edu/schunn/papers/Gao-An-Schunn-SEE.pdf
- https://www.sciencedirect.com/science/article/abs/pii/S0191491X23000196
