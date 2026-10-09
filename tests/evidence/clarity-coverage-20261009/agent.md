# 2026-10-09 规则消歧与扩大覆盖执行记录

用户请求继续覆盖、验证、审计模糊规则。基线bdafeb9，独立托管工作树academic-clarity-1009，分支codex/academic-clarity-20261009。原件/模型profile/抽字/图片留主仓.release，工作树仅规则及公开证据，验收后合并并按AGENTS回收。

主审采用skill-creator及PDF阅读工作流。四名原生subagent为Singer（规则审计）、Pascal（人文来源）、Heisenberg（硕士开题）、Carson（基线冷审）；均未完成终稿报告，已关闭，不计独立完成。Heisenberg只留下候选/失败进度note，Pascal只留下获取脚本；主审接续实际源材料读取。来源代理的自动审批400属于基础设施错误，不是安全审查拒绝，也不意味着原件已经读到。

写稿：已有本机原生CLI通路，Alibaba Qwen3.8 Flash与Ollama GLM5.3 Flash，effort max。隔离空白profile，不改账户配置；完整入口/主叶/相关长稿和文风层内联；每次新会话。各批binding、prompt、终稿、过滤visible trace、实际native model/effort及哈希保留。runner中quality_pass=null从未升级为通过；valid仅调用完成且没有通路违规，不是论文质量分。

独立审计/冷审：Alibaba GLM full首轮audit超时，R1两包429，没有审阅报告。改用Ollama GLM Flash/max新的原生会话；audit、R1/R2/R3和long逐包完整返回后由主审回读。同模型新上下文有偏差，未称不同模型交叉验证；没有让写作者自查冒充独立复核。第二轮H基线有unexpected_tool_use和无终稿，按通路无效单列，不能借其失败给候选加分。

验证只用真实来源阅读、受控实际写稿、独立意见和人工回读；Python用于抽PDF/调用/归档，不当语义判定。没有全套unittest、166项通过或结构校验作为提示词有效证据。归档哈希核验只证明字节及冻结输入一致，不证明行文质量。

范围和结果分别见CORPUS、AUDIT、ADJUDICATION及RUN-SUMMARY；生命周期完成合并/回收后记录于LIFECYCLE。最终合并单变量长稿权责消歧一句，取消来源门禁组合候选；101次写稿85次完整返回、16次通路无效，不能算85份可用稿。long-only六对中五对成立、Qwen未决概念一对两稿共同失败；没有候选独有硬失败，未证明总体质量提升。审计确认的来源对象范围歧义仍未修复。没有发布、打tag、上传市场或替换桌面包。
