# 证据内推断 R1 结果

## 决定

**合并。** 固定基线为 `main@dddda05f044f0402082cb0cd8ff567e68d9238c5`。最终产品改动只在 `references/academic-writing.md` 增加 273 个字符、2 行，区分“材料支持的作者分析”与“新增经验事实”，同时保留主体、样本、情境、变量、研究状态、因果和总体外推边界。R2、R3 两个扩大否定性证据边界的尝试没有形成稳定写稿收益，均已取消并回退；最终产品字节等同于 R1。

## 真实写稿门

- 五条 provider 路线均使用 `max`、隔离 Skill 副本和零质量重试：
  - `alibaba-token-plan-2/deepseek-v4-flash-0731`
  - `alibaba-token-plan/deepseek-v4-flash-0731`
  - `ollama-cloud/deepseek-v4-flash:0731`
  - `opencode-go/deepseek-v4-flash`
  - `minimax-cn/MiniMax-M3`
- 主矩阵为 5 题 × 5 路：基线 25 次、候选 25 次。基线原始 21 次有效，其中 Ollama P1 只是同一允许文件的绝对/相对路径重复读取，被确定性重分类为有效；3 个真技术无效格分别用全新 S1、S2、S3 同类题补齐。候选原始 23 次有效，MiniMax P2、P3 分别用全新 S4、S5 同类题补齐。最终得到 25 个可比较逻辑配对，不用质量重抽覆盖原稿。
- 冷盲审结果：Candidate 16 胜、Baseline 8 胜、平 1；24 个有决定配对中 Candidate 胜率为 66.7%。盲包 SHA-256 为 `a4e810808f899dbda9d1239befb82cc4010c7127538a732e1f29273436f31814`，映射 SHA-256 为 `394758ebe7a29bfa36181169a322bcaefe16799d61388b8761aaff8c41398dc0`。
- 稳定收益集中在审稿反控：候选更少把已经标明为作者推测、且由材料与常识直接支持的有限解释误判为事实外扩或强索次级材料；相关性反控仍保持“相关不等于因果”。

## 败例归因

- OpenCode P2 候选把“未提交者”写成“未进入修订”，Ollama P2 候选回显底稿和分隔符；全新 S4 配对均未复现，不能归因于 DIFF。
- Ollama C2 候选泄露读文件过程；全新 S3 中基线和候选都出现相同行为，属于 provider 行为，不计为候选回退。
- Alibaba1 与 Ollama P1 候选曾出现较强的“需求”措辞。最终 R1 下重新运行全新 S1 配对：Alibaba1 两臂都将登录与学习、认证影响区分开；Ollama 基线使用“访问需求聚集/实际困难”，候选反而收窄为“访问活跃度/可能门槛”。原败例未复现，未确认 DIFF 硬回退。
- R2 的原则性否定边界、R3 的动作化否定边界分别完成 10 次和 10 次候选写稿；二者都未稳定改善 P3，R3 另有一份截断终稿，因此整个原子取消，不进入产品。

## 隔离与工程门

- 源运行清单按 LF 归一比较后，除目标叶外内容一致；`SKILL.md` 原始字节一致。模型只获准读取 `SKILL.md` 与 `references/academic-writing.md`。
- 写稿通过后才增加本轮合同断言；它只固定“允许有限作者分析”和“不得换范围、强因果或唯一归因”两侧语义，不引入新的机械评分门。
- 原始 final、trace、stderr、manifest、盲包与映射保存在忽略目录 `.release/evidence-bound-inference-r1/`，不会进入运行包。

## 复现命令

```powershell
py -3 -B tests/evidence/evidence-bound-inference-r1/run_eval.py --help
py -3 -B tests/evidence/evidence-bound-inference-r1/make_blind_packet.py --help
py -3 -B -m unittest tests.test_skill_contract tests.test_context_and_runtime
py -3 -B -m unittest discover -s tests -p "test_*.py"
git diff --check
```
