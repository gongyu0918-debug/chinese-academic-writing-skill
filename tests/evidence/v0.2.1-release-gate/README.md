# v0.2.1 发布记录

用户授权向 GitHub、SkillHub.cn 与 ClawHub 发布 `v0.2.1`（WorkBuddy 因本月限额暂缓，不安装全局技能）。

- GitHub / SkillHub 使用 MIT 协议的 13 文件确定性打包产物（ZIP SHA-256：`126895427bf8a306220278abcdd8ef46a29720aeeb45b8713c818aad158ef286`）；ClawHub 按渠道规则使用 MIT-0 元数据及不含 `LICENSE.md` 的 12 文件目录包。
- 发布标签固定在产品提交 `4422b0a2895ccc38d9ddef052a0c12ac356c64b7`，后续回执提交不移动该标签。
- 对外发布说明严格聚焦使用体验优化，不包含内部模型、评测、脚本实现或工程细节。

截至回执记录时间，三渠道各提交一次，实际状态如下：

| 渠道 | `0.2.1` 当前状态 | 核验记录 |
| --- | --- | --- |
| [GitHub](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/releases/tag/v0.2.1) | **已公开** | Release `457845849`；下载附件 SHA-256 与本地包完全一致 |
| [SkillHub.cn](https://skillhub.cn/skills/chinese-academic-writing-assistant) | **已受理，审核/传播中（pending）** | `skillId: 98987`、`versionId: 550167`；`reviewStatus` / `securityScanStatus` / `contentAuditStatus` 上传时为 `pending`，公开搜索尚显示 `0.1.11`，待平台审核完成后自动生效 |
| [ClawHub](https://clawhub.ai/gongyu0918-debug/chinese-academic-writing-assistant) | **已受理，审核/传播中（pending-publication）** | `versionId: k976ympbz9b64q56vhn2wvh48d8jxw31`；12 文件指纹 `cd7685ee...`，公开 `latestVersion` 尚显示 `0.1.11`，待平台发布流程完成 |
| WorkBuddy | **本月暂缓** | 本月限额已满，本轮未构建或提交桌面包 |

完整脱敏回执字段见 [RELEASE-RECEIPT.json](RELEASE-RECEIPT.json)。
