# 研究来源与复用边界

## 已发布中文公文写作 Skill 1.6.0

- 冻结 tag：`v1.6.0^{commit}=0f6ec603993d5595e784fa7079837e299d1b0da3`。
- 可复用方法：只删有唯一替代承载的重复示例；使用风险题和反向控制题共同验证；脚本只给 finding，不宣称语义正确或自动改稿；固定 provider/model/effort、首个 final、运行根指纹和匿名包。
- 可借鉴但不能照搬：公文的短稿路由、信息选择和文种叶去重思想。
- 不迁移：主送、落款、附件、请批、采购、Hook 未决状态等公文专属规则；1.6.0 的公文语义裁决也不改变学术材料的研究状态和证据强度。

## 市场竞品

1. `bahayonghang/academic-writing-skills`：以模块路由把表达、去 AI 味、逻辑、引用和格式拆开；`deai` 脚本只做只读检测，语义保真仍由模型和作者复核。可借鉴最小模块加载和受保护内容；不复制其 LaTeX 专属工具链、固定密度分数和大模块数量。
   - https://github.com/bahayonghang/academic-writing-skills
2. `WenyuChiou/academic-writing-skills`：区分轻量任务与整稿项目，强调 claim-evidence、只审不改和按研究设计加载最小 reference。可借鉴任务复杂度分层；不把投稿生命周期和项目状态塞进短稿路径。
   - https://github.com/WenyuChiou/academic-writing-skills
3. `AIScientists-Dev/academic-humanizer`：先锁定数字、公式、引用和合法 hedge，再处理模板化表达。可借鉴保护性反例；不复制单文件长规则、固定返回 change report 或绝对标点禁令。
   - https://github.com/AIScientists-Dev/academic-humanizer
4. `momo2young/humanize-academic-writing`：本地规则检测和文本分析与写作规则分离。可借鉴具体位置 finding；不把未经校准的规则加权称为“AI probability”。
   - https://github.com/momo2young/humanize-academic-writing
5. SkillHub `unclecheng-reduce-ai-perception`：有最小改动与轮次上限，但鼓励口语、第一人称、感官细节和故意不完整，不适合学术写作事实与体裁边界，仅作反例。
   - https://skillhub.cn/skills/unclecheng-reduce-ai-perception

## 当前决策

当前 Skill 已有“入口＋唯一专项叶＋按需横切层”，合法组合低于 8,000 字符，不引入更多模块。先用真实输出确认问题，再决定是否做单例提示删除、正向自然化、lint 候选校准或信息选择原子；没有跨模型根因时只保留测试证据，不修改运行包。
