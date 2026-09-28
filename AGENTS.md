# 仓库协作约定

- 验证、发布需要隔离时，优先复用空闲的 worktree；确需新建时记录用途，避免每轮测试都永久留一个检出。
- 临时 worktree 在验收完成、必要的改动合并和证据留存后，于同一任务内回收。回收前核对未提交改动、未合并提交、忽略文件以及仍在使用该目录的任务；有待处理成果时保留并说明。
- Codex 托管的 worktree 用 `archive_worktree` 回收，手工创建的用 `git worktree remove`；结束会话或合并分支不算完成回收。回收后用 `git worktree list` 核对，长期保留的 worktree 写明用途。
