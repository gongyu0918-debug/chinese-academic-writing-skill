# 竞品借鉴胜出候选当前基线确认轮

## 固定版本

- Baseline：`62012cb`
- Change-impact Candidate：`330e962`
- Citation-faithfulness Candidate：`0145697`

两个候选均来自此前已完成的独立短稿、长稿 A/B。旧证据只用于决定哪些候选值得刷新，不计入本轮胜场。本轮 writer、机械门禁、匿名封包和裁判协议沿用第三轮冻结工具；每个任务与 arm 使用独立新会话。

## 任务

| 候选 | 任务 | 作用 |
| --- | --- | --- |
| change-impact | BC01 普通单节短稿 | 非目标安全性 |
| change-impact | BC02 两节长稿按最新版更正 | 目标任务 |
| change-impact | BC03 全文变更传播审查 | 目标任务 |
| citation-faithfulness | BF01 短文引用纠错 | 目标任务 |
| citation-faithfulness | BF02 多来源长综述 | 目标任务 |
| citation-faithfulness | BF03 长稿引用忠实性审查 | 目标任务 |

## 门槛

每个候选的三项任务都须形成决定；Candidate 至少 2 胜，胜场严格多于 Baseline，已决定任务胜率严格超过 50%，且不得出现 candidate-only 机械或裁判 `FAIL`。两位初评未形成两票同向结论时，启用已冻结的 Judge 3；三票仍无两票同向则该题未决并导致“决定数不足”。任务、字数、映射、稿件和裁判提示冻结后不再调整。
