# 发布执行

用户此前已授权GitHub、SkillHub、ClawHub 0.1.6与桌面WorkBuddy更新，随后明确先完成真实规则小改，禁止虚拟发版。复用academic-release-016隔离工作树完成研究与发布，不重复创建。最初空版本准备已取消并仅本机存档；本次运行内容包含通过实写准入的主次原子。三个平台各提交一次，受理与公开传播分别核验；完成后保存必要本机产物并回收托管worktree。

产品标签固定d64877435d3efab7f5ac9eba3e492c5bf6d37713。GitHub、SkillHub、ClawHub各执行一次发布；两个市场均获得明确受理回执，后续只读查状态，不重复上传。已下载GitHub资产核对哈希，桌面WorkBuddy按同一标签交付。

最终只读复查：SkillHub仍公开0.1.5且新版签名不可查，ClawHub新版详情不可查；受理回执均有效，未重复提交。产品包、原始平台回执、旧准备包及诊断stderr已保存在主仓库.release/release-v0.1.6-20260929，哈希复核通过；公开稿件/冻结树/模型元数据已入Git。无运行中的writer或review进程。P/Q的独立临时执行profile保留，位置见worktree-lifecycle.json，不声称所有系统临时目录已删除。托管worktree在合并后使用archive_worktree回收。

工作树回收完成：archive_worktree归档后，附件类型已变为archived_worktree，git worktree list已无academic-release-016，原目录Test-Path为False。必要本机产物在主仓库.release/release-v0.1.6-20260929，Git证据已合并推送；产品标签仍固定d6487743。既有历史实验/发行检出未改动。
