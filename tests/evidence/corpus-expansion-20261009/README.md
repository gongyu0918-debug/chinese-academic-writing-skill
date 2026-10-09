# 真实论文与开题扩读证据

本轮实际读完13篇论文正文及3份已填写开题报告，完成52份真实写稿/审稿返回、26双臂配对。最终取消比较取舍和数字口径两个新增默认提示，只合并维护阅读样本与评测证据，产品仍为0.1.7。

- CORPUS.md：作者、题名、实际原始URL、真实文种、读到范围与未读声明。
- READINGS.md：从具体段落、表格、开题与论文配对提炼的写作判据、现规则覆盖和反例。
- ADJUDICATION.md：两段候选取舍、局部改善、真实失败、裁判意见纠偏和证据限制。
- pilot-R1、numeric-R1/R2/R3：完整冻结输入、终稿、执行绑定与过滤后的可见trace；未归档隐藏推理。snapshots只保留实际加载文件，完整树指纹与清单指当轮完整快照，不冒充当前缩减目录的指纹。
- source-bytes.json：可得9份本地原件的URL与哈希，不把下载状态当阅读证明；其余来源实际覆盖由来源报告、网页或远程PDF读取记录绑定。
- agent-models.json、RUN-RECORD.json：作者/独立来源与审稿代理的实际模型及调用范围。
- REVIEW-STATUS.json：实际审阅覆盖、补样代理未完成与主审接续范围；MANIFEST.json绑定公开证据字节及文本规范化哈希，LIFECYCLE.json记录提交、合并与工作树回收。

实际新增确认调用：

```
python -B .release\corpus-expansion-20261009\numeric_r3_runner.py --output .release\corpus-expansion-20261009\numeric-R3 --candidate-dir .release\corpus-expansion-20261009\numeric-candidate --isolated-profile --retain-session-metadata --timeout 260 --effort max
```

前轮pilot/numeric/confirmation调用器及冻结快照均保存。Python只做模型调用、文献抽字和证据绑定，不判规则优劣；本轮没有生产Python改动，不跑全量单测或Skill结构校验充当写稿准入。归档哈希核对属于证据完整性，不算语义质量通过。
