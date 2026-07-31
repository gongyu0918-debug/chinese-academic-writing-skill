# Writer 外层说明

你在完成一个真实中文论文写作任务。先完整读取当前工作区的 `chinese-academic-writing-assistant/SKILL.md`，再严格按入口只读取完成当前任务需要的 reference；不得读取 `tests/evidence`、`.release`、Git 历史或当前工作区之外的文件。不要分析 Skill，不要评价规则，不要说明读取过程。随后把所附任务文本视为用户的完整需求，只输出用户要求的最终成品。

L04 直接加载哨兵例外：只读取当前工作区的 `chinese-academic-writing-assistant/references/academic-writing.md`，不得读取入口或其他 reference；随后完成用户任务。该哨兵只检验任务叶在脱离入口时的行为。
