# 归因裁判无关日志验证修正

## 发现的问题

修复远端 schema 后，judge-1 12/12 技术有效，judge-2 11/12。唯一旧无效记录 `judge-2 / A1-R3` 已生成完整 JSON、trace 与 final，目标 `FALSE_CROSS_SOURCE_LINK` 的标签和锚点均通过；失败仅来自 `unrelated_errors.right` 的一段日志 quote 省略了原稿中 `[S4]` 两侧的 Markdown 反引号。

`unrelated_errors` 在预注册中只作绝对质量日志，不影响 target 标签、第三审触发或因果分数。把其 Markdown 级引用漂移升级为整票无效，会让与 DIFF 无关的格式波动反向控制目标判断，属于过严门禁。

## 修正规则

- 五个预注册 target 的集合、顺序、标签和左右映射不变。
- target 为 `PRESENT` 时仍必须给出对应侧原稿中的逐字锚点；非逐字 target anchor 继续使裁判调用无效。
- `unrelated_errors` 仍要求左右数组、非空 code 和非空 quote，但其 quote 不再承担逐字硬门，也不进入任何因果计数。
- 两份主裁判结果都会重验，但只允许重写 judge-2 manifest 的 `issues`、`valid` 与 `valid_calls` 派生字段。judge-1 manifest 必须保持原 SHA。
- 24 份裁判 final、trace、stderr 及其 SHA-256 不得改变。judge-2 原 manifest 按原 SHA 备份；只允许 `judge-2 / A1-R3` 从 `unrelated_errors:right:quote_not_verbatim` 改为无 issue。
