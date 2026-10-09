from pathlib import Path
root = Path('F:/Workspaces/chinese-academic-writing-skill/chinese-academic-writing-assistant')
target = Path('C:/Users/admin/.codex/worktrees/academic-clarity-1009/chinese-academic-writing-skill/chinese-academic-writing-assistant')
changes = {
 'SKILL.md': (
 '- 待核验来源：不进入最终正文，只可出现在审稿意见或正文后“其他修改建议”的核验项中。',
 '- 待核验的外部来源：不进入最终正文，只可出现在允许交付的核验项中。作者提供的原始记录、数据与底稿可按实际记载使用；未作外部真实性核验不等于材料缺失，也不标为已核验来源。'),
 'references/long-form-consistency.md': (
 '修改任务中，只有正确答案能由最新版材料唯一确定的机械问题才可直接修复；涉及论点取舍、概念合并、矛盾解释或作者声音的问题先报告，不代替作者决定。',
 '修改任务中，有材料依据且在用户授权范围内的问题可直接修复；涉及论点取舍、概念合并、矛盾解释或作者声音的未决问题先报告，不代替作者决定。')
}
for name, (old, new) in changes.items():
 text = (root/name).read_text(encoding='utf-8-sig')
 assert text.count(old) == 1, name
 (target/name).write_bytes(text.replace(old, new).encode())
 print(name)
