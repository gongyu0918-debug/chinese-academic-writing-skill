# 0.0.1 第二轮真实写稿门禁（阻断）

- 被测提交：`dfbe7a4`（完整 SHA 由 Git 记录）。
- 主写稿：12 个 prompt × 2 个独立 writer，共 24 份原始输出；确定性 literal gate 通过。
- 双盲包集合 SHA-256：`a15e639e53ffaf26cdf1afc570c051ab9c9e484f2ed546e90bf60a0e059f7a5e`。
- verifier-1 结果 SHA-256：`8e25a8dbc6f90502ccb73c6e6852d6bc96a365d6fdd1744255e692736e6f55f8`。
- verifier-2 结果 SHA-256：`bc2f8d14b005d280b7c7dff5c3aece28e2ea4cddfaf89e486c5c5dbd7d3c0649`。
- 两名盲 verifier 均为 24 PASS、0 WARN、0 FAIL。

独立基线评审仍发现 P01 阻断项：候选把“输入没有提供访谈对象范围、数量和提纲”改写为研究项目“仍需进一步明确”，并新增“完成开题后续研究写作”。前者把输入缺失升级为项目状态，后者扩大了用户给定的进度与成果范围。L01 另有正文作者年份与文后来源 ID 未就近对应的 WARN。

独立上下文评审为 8 PASS、1 WARN、0 FAIL；唯一 WARN 是刻意移除正确叶后的 P01 `entry-only` 输出补充了过细的拟访谈维度，证明正确叶对约束编排有实际增益。

独立材料评审报出的两项 FAIL 来自消融输入包没有记录完整不变量：writer 实际收到的待审句、题目、方法与日期没有写入 JSON 包，评审只能按可见包将其误判为输出补造。这属于证据设计缺陷，下一轮必须把不变任务信息同时写入 `original_material` 与 `ablated_material`，再由新鲜评审复核。

因此第二轮仍不作为 0.0.1 通过证据，不创建 tag、不发布。目录保留全部原始 writer、匿名包、双盲 verdict、基线、上下文、材料消融与独立评审结果。
