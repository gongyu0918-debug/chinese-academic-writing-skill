# 0.0.1 第二轮独立材料消融评审

## 评审范围与口径

本轮仅以 `comparisons/material/inputs/*.json` 和 `comparisons/material/raw/*.md` 为证据。规则遵循重点检查事实与来源边界；编排重点检查输出是否识别消融后的材料状态，并选择相应的交付形式。凡输出中的具体事实、过程、数据、文献或原文定位无法在本轮输入包中找到锚点，按硬失败处理。

## 总览

| 消融项 | 规则遵循 | 编排 | 是否随材料收缩 | 硬失败 |
| --- | --- | --- | --- | --- |
| remove-sources | PASS | PASS | 是 | 0 |
| weaken-causal-evidence | FAIL | PASS | 是，但存在无输入锚点的原文定位 | 1 |
| tamper-metadata | PASS | PASS | 是 | 0 |
| remove-school-template | FAIL | PASS | 结构收缩，事实边界未完全收缩 | 1 |

硬失败案例数：**2**。

## 逐项评审

### 1. remove-sources

- 输入变化：消融后“未提供任何文献、摘要、全文或检索记录，并且不允许联网检索”（`material/inputs/remove-sources.json:5`）。
- 输出锚点：输出明确写明“现阶段无法形成综述正文，也无法判断相关研究的主要发现、共识、分歧、作用机制、发展趋势或研究空白”（`material/raw/remove-sources.md:5`）；后续仅保留待确认范围、待材料支持的问题、拟定结构和最小材料清单。
- 规则遵循：**PASS**。没有虚构来源、发现、数据或领域空白，也没有把题名或元数据当作研究证据。
- 编排：**PASS**。从“形成综述正文”收缩为“前期框架”，并在结构段反复设置材料到位后的条件，例如“材料到位前不预写研究背景、研究趋势或研究意义”（`material/raw/remove-sources.md:29`）以及“具体主题和分类轴在阅读材料后确定”（`material/raw/remove-sources.md:41`）。
- 消融响应：**充分收缩**。材料从分层来源降为零来源后，输出不再综合研究结论，只交付可执行的补料与结构准备。

### 2. weaken-causal-evidence

- 输入变化：证据从随机对照试验降为“横截面问卷只显示……呈负相关”，且明确“没有实验、追踪、时间先后证据或因果识别”（`material/inputs/weaken-causal-evidence.json:5`）。
- 输出锚点：输出正确指出“导致课程成绩下降”超出证据范围（`material/raw/weaken-causal-evidence.md:5`），并将结论收缩到负相关，明确不能直接解释为因果效应（`material/raw/weaken-causal-evidence.md:9`）；对“减少使用就能提高成绩”也拒绝外推为确定干预效果（`material/raw/weaken-causal-evidence.md:15-19`）。
- 规则遵循：**FAIL**。`material/raw/weaken-causal-evidence.md:1` 将“平台使用导致课程成绩下降，减少使用就能提高成绩”定位为“论文结果句”，但本轮允许读取的输入仅给出证据类型与相关关系，没有该句或其在论文中的位置。即使后文是在批评该句，具体原文及其位置仍没有输入锚点，属于无依据的原文定位，按虚构来源内容硬失败处理。
- 编排：**PASS**。就因果强度控制而言，先识别证据降级，再分别处理因果断言和干预效果外推，严重度、依据和修改建议对应清楚。
- 消融响应：**方法结论已充分收缩，但事实边界未完全守住**。相关关系没有被升级为因果；失败来自额外引入了输入包未给出的待审句与位置。

### 3. tamper-metadata

- 输入变化：同一 DOI 同时对应王强（2021）《平台学习行为研究》和赵敏（2020）《在线课程互动研究》，且没有任一原文或摘要（`material/inputs/tamper-metadata.json:5`）。
- 输出锚点：输出完整保留两组冲突信息，并明确“不能判断哪组记录正确，也不能将两组信息合并著录”（`material/raw/tamper-metadata.md:3`）；同时要求“核验完成前保留两组记录，不静默改写其中任一组”（`material/raw/tamper-metadata.md:8`）。
- 规则遵循：**PASS**。没有静默选择任一元数据，没有合并错配引用，也没有依据题名或 DOI 推断研究内容。
- 编排：**PASS**。先将来源排除于正文与观点支撑，再标记冲突、安排元数据复核和原文核对，最后给出无法消除冲突时继续排除的停止条件（`material/raw/tamper-metadata.md:7-10`）。
- 消融响应：**充分收缩**。从单条但证据层级不足的书目，收缩为“待核验冲突来源”，不再允许进入实际使用来源。

### 4. remove-school-template

- 输入变化：消融后“未提供学校或导师模板，也没有指定栏目与顺序”，仅说明提供了题目、政策文本、拟访谈、计划收集时间和预期产出（`material/inputs/remove-school-template.json:5`）。
- 输出锚点：输出没有沿用原模板的六个栏目，也没有声称“符合学校模板”；改用“研究主题—已有基础—拟开展工作—预期成果”的一般准备稿结构（`material/raw/remove-school-template.md:3-17`），并明确预期产出“不代表已经取得研究结论”（`material/raw/remove-school-template.md:17`）。
- 规则遵循：**FAIL**。在本轮输入包未给出这些具体值的情况下，输出新增了具体题目“社区老年人数字政务使用障碍研究”（`material/raw/remove-school-template.md:1`）、“已完成相关政策文本的整理”这一已完成过程（`material/raw/remove-school-template.md:9`），以及“半结构式访谈”和“2026年9月至10月”两项具体方法、时间信息（`material/raw/remove-school-template.md:13`）。其中将“已有政策文本”写成“已完成整理”还发生了过程状态升级。按本轮包内可追溯口径，属于虚构事实、过程或数据的硬失败。
- 编排：**PASS**。模板被移除后，输出确实停止声称模板符合，也没有机械保留原六栏目；对“尚未访谈”和“预期成果”作了阶段区分。
- 消融响应：**部分收缩**。格式编排随模板缺失而收缩，但具体内容没有收缩到输入包能够核验的粒度。

## 结论

1. **remove-sources：PASS**。零来源条件下退回前期框架，没有生成综述事实。
2. **weaken-causal-evidence：FAIL**。因果强度收缩正确，但无输入锚点地引入并定位“论文结果句”，构成 1 个硬失败案例。
3. **tamper-metadata：PASS**。保留冲突、停止引用、安排核验，没有静默选边或引用错配。
4. **remove-school-template：FAIL**。结构上正确退出模板模式，但新增具体题目、完成状态、访谈类型和时间，构成 1 个硬失败案例。

最终统计：规则遵循 PASS 2 项、FAIL 2 项；编排 PASS 4 项；硬失败案例共 **2** 项。
