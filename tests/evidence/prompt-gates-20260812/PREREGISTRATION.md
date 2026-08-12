# 中文论文写作 Prompt 门禁候选预注册

## 基线与范围

- 基线：`main@2eee3de1a3ba87a604637ec1929c695d5ae1c399`。
- 候选只允许修改 `SKILL.md`、`references/citation-research.md`、`references/long-form-consistency.md` 及对应合同测试。
- 不改三个专项叶、ANTI-AI 叶、运行脚本、frontmatter、SkillHub 元数据或发布文件。
- 本轮不发布、不合并到 `main`。

## 目标原子

1. `CUMULATIVE_WHOLE_DRAFT_BOUNDARY`：按章节、文件或轮次拆分不能绕过整篇可提交稿代写边界。
2. `READ_ONLY_LONGFORM_NO_PERSIST`：只审、只读或粘贴长稿任务未经授权不得创建 `.academic-writing/` 或其他状态文件。
3. `LONGFORM_LOAD_PRECEDENCE`：多章提纲不读长稿层；跨轮单节只有确需恢复其他章节状态时才读；明确全文一致性筛查仍读取。
4. `ANTI_AI_LOAD_PRECEDENCE`：提纲、清单、范围说明和原始摘录不读 ANTI-AI；正文或审稿结果有明确文风目标时，在内容与证据复核后读取；普通起草或事实审查未提出文风目标时不读。
5. `CITATION_STOP_CONDITION`：高风险论断已支持或已删除、收窄、标为未确认，且预定渠道已完成或权限耗尽时停止；不得仅为抬高覆盖数字无限扩搜。
6. `SKILL_ROOT_SCRIPT_PATH`：`scripts/...` 明确相对包含 `SKILL.md` 的 Skill 根目录解析，不相对用户项目当前目录猜测。

## 判定

- 确定性合同必须全部通过，原有 165 项测试不得回退，标准 Skill 校验和 `git diff --check` 必须通过。
- 隔离盲用只判断上述目标原子。题目泄漏、字数、格式偏好、无关事实错误或模型随机措辞只记录，不计候选负例。
- 单次未触发目标行为不证明收益；候选出现任一可复现目标原子伤害则回滚对应规则。
- 不以无关胜负抵消目标原子伤害，也不因无关错误把候选判负。

## 保留边界

- 不删除材料、来源层级、引用语义、研究状态、系统综述、必要否定或整篇代写门禁。
- 不规定固定句序、句数、段长、章数或统一段落骨架。
- 不把静态 finding、关键词命中或单次输出偏好当作真实回退。
