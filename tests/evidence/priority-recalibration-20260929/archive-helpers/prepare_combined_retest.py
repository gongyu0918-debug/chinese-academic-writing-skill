from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parent.parent
local=root/'.release/priority-recalibration'
candidate=local/'PQ2-combined'
shutil.copytree(local/'P-priority',candidate)
line='- 综合证据时回溯原始研究：对同一结果的多次转述不增加独立证据，准确转述仍可按其来源使用；采用相同方法但基于独立材料或样本的新研究分别判断，不因方法相同合并。'
p=candidate/'references/academic-literature-review.md'
anchor='- 每项观点回到正确来源，不把不同作者的对象、方法、数据或结论相互移接。'
s=p.read_text(encoding='utf-8');assert anchor in s
p.write_text(s.replace(anchor,anchor+'\n'+line,1),encoding='utf-8',newline='\n')
cases={
'J_new_samples': '只用以下已读材料写独立文献综述“检索提示与引文定位”的小节，约400字，只交正文，保留所用来源ID。R1：非随机两组各16人，同一任务中提示组11人正确定位引文，无提示组8人正确。R2：沿用R1的提示格式与题目，在另一所学校另招40人，非随机两组各20人，提示组14人正确，无提示组10人正确；原文说明没有使用R1的任何参与者或答题记录。R3：一篇综述引用R1、R2后写“这两项观察中提示组定位正确人数均较多”，没有新做测试。R4：提示格式的设计文献只说明页码、作者、引文起始词三个栏目的安排，没有用户表现数据。R5：另一项访谈的8人中5人认为提示便于查找、3人觉得信息拥挤，未测定位表现。请围绕提示是否有助于定位，比较来源之间的关系、主要结果及结论范围，不逐篇平均介绍，不检索文献。',
'K_shared_result': '依据下面已读材料写独立文献综述“栏边编号与来源核对”的研究述评，约380字，只交正文，保留来源ID。T1：观察24名读者使用带栏边编号的文章，15人核对来源；没有无编号对照，未记录核对原因。T2：一篇方法说明引用T1，并准确转述“24名使用编号文章的读者中15人核对来源”，随后介绍编号制作步骤，没有另招参与者或提供新观察。T3：一篇综述同时引用T1、T2，陈述“T1观察到部分读者使用编号文章时核对来源”，没有新增数据。T4：另一任务记录30名读者阅读不带编号的不同文章，其中19人核对来源；未与T1使用相同文章或同一招募方式。T5：访谈T1中的6人，4人说编号帮助找到来源位置、2人说习惯自己核对；该访谈使用T1参与者，不是新一轮行为观察。请比较这些材料对研究问题的支持与限制，可以作材料内有限综合，不做总体效果或因果判断。'
}
src=(root/'.release/run_citation_retest.py').read_text(encoding='utf-8')
start=src.index('CASES = ');end=src.index('\n\n\ndef fingerprint',start)
src=src[:start]+'CASES = '+repr(cases)+src[end:]
# Keep this round's temporary profile inside the disposable managed worktree.
src=src.replace("tempfile.mkdtemp(prefix='cow-native-'+out.name+'-')","tempfile.mkdtemp(prefix='cow-native-'+out.name+'-', dir=out.parent)")
(root/'.release/run_combined_retest.py').write_text(src,encoding='utf-8',newline='\n')
ev=root/'tests/evidence/priority-recalibration-20260929'
(ev/'Q2-candidate.md').write_text(line+'\n',encoding='utf-8',newline='\n')
(ev/'Q2-cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
with (ev/'agent.md').open('a',encoding='utf-8',newline='\n') as f:
    f.write('''
Q第一版的Qwen控制稿错误地因复用方法否定独立新样本，并把准确二手转述泛称越界。主审据此作一次最小修订Q2：明确准确转述仍能使用，只是不增加独立结果；同方法的新材料/新样本不因方法相同合并。原Q全部结果仍保存，不替换坏稿。两道全新材料题J/K保留准确转引、独立新样本和同批样本访谈三种区别。Q2用P-only作两臂共同基线，候选为P+Q2，冻结后不改；同模型同题比较只归因Q2，也观察合并后交付。新临时profile放worktree内以便完成后统一归档回收。
''')
print(json.dumps({'candidate':str(candidate),'baseline':str(local/'P-priority'),'cases':list(cases)},ensure_ascii=False))
