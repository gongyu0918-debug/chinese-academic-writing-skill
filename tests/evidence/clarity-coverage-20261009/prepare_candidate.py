"""Prepare two scoped clarification edits in the isolated worktree only."""
from pathlib import Path
import difflib

ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
WT = Path('C:/Users/admin/.codex/worktrees/academic-clarity-1009/chinese-academic-writing-skill')
entry = WT / 'chinese-academic-writing-assistant/SKILL.md'
long = WT / 'chinese-academic-writing-assistant/references/long-form-consistency.md'
old = '- 待核验来源：不进入最终正文，只可出现在审稿意见或正文后“其他修改建议”的核验项中。'
new = '- 待核验的外部来源：只有检索线索、尚未读到支持内容，或身份、内容冲突仍未解决的来源，不进入最终正文，只列为允许交付的核验项。作者已提供的原始记录、数据或底稿可按其实际记载起草；未独立核验真实性不等于材料缺失，也不把这些材料标成已核验来源。已发现的材料冲突仍须处理。'
old_long = '只审不改时按入口审稿接口报告位置、严重度、问题、依据和修改建议。修改任务中，只有正确答案能由最新版材料唯一确定的机械问题才可直接修复；涉及论点取舍、概念合并、矛盾解释或作者声音的问题先报告，不代替作者决定。修复后复查受影响章节、状态项和交叉引用，不重生成无关章节。'
new_long = '只审不改时交意见，不改正文。修改任务按用户已授权的范围调整论证、组织与语言；可由最新版材料唯一确定的机械问题直接修复。需要作者另作决定的论点取舍、概念合并、矛盾解释或声音选择先报告，不把未决选择写成已确定；用户已给取舍或更正依据的，完成对应修改。修复后复查受影响章节、状态项和交叉引用，不重生成无关章节。'
for path, before, after in ((entry, old, new), (long, old_long, new_long)):
    text = path.read_text(encoding='utf-8-sig')
    assert text.count(before) == 1, path
    changed = text.replace(before, after)
    path.write_text(changed, encoding='utf-8', newline='\n')
    diff = ''.join(difflib.unified_diff(text.splitlines(True), changed.splitlines(True), fromfile='main/' + path.name, tofile='candidate/' + path.name))
    (ROOT / '.release/clarity-coverage-20261009' / (path.stem + '.candidate.diff')).write_bytes(diff.encode())
print('Prepared source-status and authorized-revision clarifications; no version change.')
