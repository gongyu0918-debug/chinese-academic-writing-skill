# v0.1.11 发布记录

用户授权向GitHub、SkillHub.cn和ClawHub正式发布。相对0.1.10，四份运行Markdown采用此前冻结的A+B+C组合，分别澄清限定取舍、章节职责、材料用途和旧引文沿用；三个只读脚本不变。发布阶段不再调整规则，版本与渠道元数据另行派生。

复用11个任务、28份初稿、14个配对、4次复核后交付和7次独立审阅，详见[实写记录](../rule-research-20261111/README.md)及[逐稿裁决](../rule-research-20261111/ADJUDICATION.md)。这些是公开原文与构造记录下的实际生成，不是作者真实完整论文验收，也未建立整体优于旧版的结论。

GitHub/SkillHub使用MIT的13文件派生包，ClawHub按仓库渠道约定使用MIT-0元数据及不含MIT许可证文件的12文件canonical包。测试和研究证据只进入GitHub维护资料，不上传到技能市场运行包。

发布前验证冻结字节、白名单、重复构建、渠道预检和166项维护测试；实际上传、公开传播和审核分别记录在[发布回执](RELEASE-RECEIPT.json)。受理不等于审核或公开索引更新。发布标签固定产品提交`e2430067e414da940451b446721fa7c69f813f0f`，后续回执提交不改写该标签。

截至回执时间，三个渠道各提交一次：

| 渠道 | 0.1.11实际状态 | 核验范围 |
| --- | --- | --- |
| [GitHub](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/releases/tag/v0.1.11) | 已公开 | Release 441733192；下载附件SHA-256与本地包完全一致 |
| [SkillHub.cn](https://skillhub.cn/skills/chinese-academic-writing-assistant) | 已公开0.1.11，平台签名验证通过 | versionId 507144；公开索引已更新，签名内容指纹与本地ZIP完全一致；上传时的pending状态另保留在回执中 |
| [ClawHub](https://clawhub.ai/gongyu0918-debug/chinese-academic-writing-assistant) | 已公开0.1.11，审核与安全结论均clean | versionId k979drywb7917q22s6ve1j9ykn8j03ef；MIT-0，公开latest已更新，12个远端文件的SHA-256逐项匹配本地上传包 |

GitHub/SkillHub附件SHA-256为`8f48886c6b364c7ff8a3acb705193bf429e2b45cabb3d3e8cb952328607d7761`。ClawHub上传指纹与预检一致，随后按公开API返回的逐文件SHA-256完成核对；扫描报告另留一条未声明工具范围的提示，非阻断项，没有为消除此提示改动冻结规则。等待平台状态变化期间没有重新上传，也未更新全局技能或桌面包。原始CLI回执留在被忽略的本地`.release/v0.1.11/`，仓库只保存核对后的必要字段。
