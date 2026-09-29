from pathlib import Path
import json, subprocess
root=Path(__file__).resolve().parent.parent
base='297d458d3d6c1b38c140aa75d9529631a02dfe49'
candidate=root/'.release/priority-recalibration/Q-independent-evidence'
candidate.mkdir(parents=True,exist_ok=False)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',base,'chinese-academic-writing-assistant'],cwd=root,text=True).splitlines():
    p=candidate/Path(name).relative_to('chinese-academic-writing-assistant')
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(subprocess.check_output(['git','show',base+':'+name],cwd=root))
p=candidate/'references/academic-literature-review.md'
line='- 综合多来源证据时，区分独立研究结果与对同一结果的转述；多篇转述不能当作多次独立验证，方法或背景引用仍按实际作用保留。'
anchor='- 每项观点回到正确来源，不把不同作者的对象、方法、数据或结论相互移接。'
s=p.read_text(encoding='utf-8');assert anchor in s
p.write_text(s.replace(anchor,anchor+'\n'+line,1),encoding='utf-8',newline='\n')
cases={
'Q1_secondary': '只依据以下已读材料，为独立文献综述写“索引页与原文回查”的研究述评，约400字，只交正文，保留使用来源ID。问题是索引页是否有助于读者回查原文。A：一项课堂研究的80名读者非随机分为两组各40人，带索引页材料组16人回查原文，无索引页组10人回查；研究未记录回查原因。B：后来的综述写道“已有研究发现索引页组回查人数较多”，该句引用A的80人研究，没有另报回查数据。C：一篇评论据B概括“索引页可能有利于原文回查”，没有实施用户研究。D：另一研究对60名读者分组，各30人，在不同文章任务中有索引页组15人回查、无索引页组16人回查，分组方式未交代。E：方法说明介绍如何制作索引页与记录点击，只给操作步骤，无用户效果数据。请综合比较证据及其允许的结论，不逐篇摘要，不做文献检索。',
'Q2_independent': '只依据以下已读来源，为独立文献综述写“检索清单与来源辨认”的小节，约400字，只交正文，保留来源ID。A：48名读者分两组各24人，同一辨认任务中清单组18人正确辨认来源、无清单组13人正确，非随机分组。B：另一研究使用A同样的任务设计和清单模板，重新招募54名读者，清单组与无清单组各27人，分别20人与16人正确；作者明确报告这54人来自另一课程，未与A共用样本，亦非随机分组。C：方法文献介绍清单模板中的作者、年份与出版机构三个栏目；A、B均说明采用该模板，C本身未测读者表现。D：访谈12人，8人觉得清单查找方便，4人认为栏目繁琐，没有测试辨认正确性。综述问题是清单对来源辨认是否有帮助，需要结合研究之间的关系作有限综合，正文可以交代方法引用的作用，不要求逐篇列述。'
}
src=(root/'tests/evidence/argument-priority-20260929/priority-r2/runner-source.py').read_text(encoding='utf-8')
start=src.index('CASES = ');end=src.index('\n\n\ndef fingerprint',start)
src=src[:start]+'CASES = '+repr(cases)+src[end:]
src=src.replace('ThreadPoolExecutor(max_workers=4)','ThreadPoolExecutor(max_workers=2)')
(root/'.release/run_citation_retest.py').write_text(src,encoding='utf-8',newline='\n')
ev=root/'tests/evidence/priority-recalibration-20260929'
(ev/'Q-candidate.md').write_text(line+'\n',encoding='utf-8',newline='\n')
(ev/'Q-cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
with (ev/'agent.md').open('a',encoding='utf-8',newline='\n') as f:
    f.write('''
Q候选由Scite引用角色机制适配为“独立结果与二手转述分开”，只落在独立综述叶一条，不建立分类器，不将方法引用判无效。基线只有来源身份去重和逐观点支持核对，没有明确多篇转述不等于多次独立验证。正向题为原始研究—综述—评论转引链，反控题为同方法但新样本的两项独立研究及方法来源；两模型独立配对。用户题面不说明待测规则或预期赢家。

竞品提案中的“摘要先筛，只读直接相关全文”不直接试入：它可能提前排除摘要未交代的关键材料，也不是本库当前已证缺口；是否有更窄职责由主审另记。已有证据账本、先证据后文风和最小加载不重复添加。
''')
print(json.dumps({'candidate':str(candidate),'cases':list(cases)},ensure_ascii=False))
