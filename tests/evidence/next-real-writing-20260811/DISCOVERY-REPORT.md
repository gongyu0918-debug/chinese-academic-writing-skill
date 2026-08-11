# 中文论文三模型发现轮报告

## 结论

发现轮 12/12 个调用技术有效，运行包前后均绑定 `v0.0.8^{commit}=09b89a6f49f0d97f5bdd983fe29354636a0f5008` 和 11 文件 fingerprint `0b649ff5a1fb0e3cfca3c25f8a1ecd5c8fc652ab4489cb63fc5531a5dec8e3d3`。三家模型均配置 `max`，每项只有一个 thread、一个 turn、一个 final，`retry_count=0`，没有 timeout。

发现轮不计候选胜负。它确认的最强共性问题是独立文献综述中的“强行综合”：三家 D3 都对未知或未读的样本、地区、方法或测量作跨来源比较；MiniMax 与 Ollama 还把两个变量不同、来源层级不同的相关观察合成统一障碍结论。该问题满足跨 provider 立项条件。

未发现跨 provider 的“先……再……/首先其次”滥用；不据单个句式增加 anti-AI 规则。既有 ANTI-AI 摘要减载和段落边界删除已有真实回退证据，本轮不重做。

## 技术有效性

| 项目 | 结果 |
| --- | --- |
| Provider/model | Alibaba DeepSeek V4 Flash 0731；Ollama DeepSeek V4 Flash 0731；MiniMax M3 |
| Reasoning 配置 | 三家均为 `max`；trace 不证明上游内部实际档位，只证明调用配置 |
| 调用 | 4 题 × 3 provider = 12；首个 final；零重试 |
| 必读 | 36/36 个文件独立读取成功 |
| 绑定 | preflight/postflight commit、干净状态、fingerprint 一致 |
| 模型任务联网 | 未使用 web/MCP/computer 工具；未成功联网取材 |
| 运行时后台请求 | 部分 stderr 记录内部插件目录或 analytics 发送失败，不表述为“进程从未发起公网请求” |

首次 manifest 为 11/12：MiniMax D2 列出当前冻结根时，被旧分类器按 `.release/worktrees` 子串误判为访问其他 worktree。修正只允许当前根并继续拒绝同级其他根；12 组 final/trace/stderr 的 SHA-256 均未变化，未重跑模型。原 manifest 保存在 `discovery/manifest.before-validation-correction.json`。

MiniMax D2 额外产生 32 次命令尝试，多数用于字数统计，其中写临时文件和 patch 均被只读策略拦截；这是 provider 工具抖动，不是 Skill 加载失败。其余任务也只把额外命令作为运行行为记录，不据此改论文 Skill。

## 逐题结果

### D1 普通论文修改

| Provider | 结果 | 证据 |
| --- | --- | --- |
| Alibaba | FAIL | 把“内容分类基本清楚”包装成内容环节短板；断言 4 名未使用者的意见不涉及功能；补写反馈会随对象和时段变化。 |
| MiniMax | WARN | 数字与状态正确；保留“题目：”编辑标签，且 `[M3]` 范围限制重复。 |
| Ollama | FAIL | 从少数反馈推到“提升服务”“信息组织尚可”“接纳态度”，并新增未调查的使用频率维度。 |

共性：Alibaba 与 Ollama 都把反馈计数扩写成整体评价或心理态度。该问题跨普通论文与综述在 Ollama 内复现，但成因覆盖面较大，现有入口已明确禁止材料外结论；本轮不靠再加一条近义禁令修复。

### D2 开题报告

| Provider | 结果 | 证据 |
| --- | --- | --- |
| Alibaba | FAIL | 452 个可见字符，低于 750；另把尚未形成的访谈资料与已有材料并列。 |
| MiniMax | FAIL | 把全部材料写成面向中老年人，并补“覆盖情况”；未明确保留四项访谈设计未定状态。 |
| Ollama | PASS | 857 字；总量、分类余数、研究状态、进度和成果均准确。 |

三家都正确处理了 `48=31+12+5`，没有替 5 份未分类材料命名，因此不为该项增加新规则。Alibaba 的篇幅失败与 MiniMax 的范围扩张未形成同机制跨 provider 复现。

### D3 独立文献综述

| Provider | 结果 | 证据 |
| --- | --- | --- |
| Alibaba | FAIL | 在 S2 地区/样本未知、S3 未读时断言各来源地区、方法、样本互不相同；把未测长期变化反推为短期效果。 |
| MiniMax | FAIL | 在 S2/S4 信息不足时比较样本规模并写“集中于中国城市社区”；把分立观察写成一致阻力。 |
| Ollama | FAIL | 创造“能看不会用”共同故事；把相关升级为障碍、个案协助升级为可行支持，并补机制和个体差异研究议程。 |

共性根因：

1. 三家都把未知维度当成可比较信息。
2. MiniMax 与 Ollama 把主题相近的分立观察合成共同结论。
3. MiniMax 与 Ollama 的综合性判断缺少正确来源 ID 就近承载，Alibaba 开篇也有较轻表现。

当前独立综述叶只写“以多来源比较为基本单位”和“审慎综合”，没有给出何时来源才可比较。下一候选只合并改写这三条职责：来源对同一对象、变量或关系给出可比信息时才归纳；主题相近、维度未知或内容未读不能合成共同结论；观点仍须就近回到正确来源。候选须净减载，并用真共识控制题证明不会把综述退化为逐篇摘要。

### D4 纯检测

| Provider | 结果 | 证据 |
| --- | --- | --- |
| Alibaba | PASS | 命中第二段表达问题、第三段控制旁白和第四段制作残留，保护真实比较与必要限制。 |
| MiniMax | WARN | 主要问题齐全，但漏掉第三段控制旁白，严重度几乎全为高。 |
| Ollama | WARN | 漏第三段控制旁白，表后增加检测说明。 |

D4 的漏检在 MiniMax/Ollama 复现，但现有 production-residue 规则覆盖明确的生成过程；“应在解释结论时保留”也可能在审稿意见中合法出现。没有足够证据把该词面升级为通用 lint 规则，本轮不立项。

## 只读 lint 交叉检查

用当前 `prose_lint.py --structure --delivery-mode body-only` 扫描 D1—D3：Alibaba D1/D3、MiniMax D3、Ollama D1/D3 均出现 `protective-negative-inference` 候选，Ollama D3 共 3 项。部分命中是 S1 明确给出的非因果限制，不能自动删除；lint 结果只用来定位，不作为上述 PASS/FAIL 的依据。

## 候选处置

- 立项：独立综述叶“来源可比性与综合边界”单原子替换；必须净减少运行字符。
- 不立项：`先……再……` 词面禁令、更多 anti-AI 高频词、D4 控制旁白裸词、D2 余数规则、跨体裁再加事实禁令。
- D1—D4 永久作为已见发现题，只用于解释候选来源；后续合入门使用全新 H1—H4 与冻结 A/B。
