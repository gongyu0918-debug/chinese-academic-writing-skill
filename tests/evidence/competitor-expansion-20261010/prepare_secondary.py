from pathlib import Path
import json, shutil

HERE = Path(__file__).parent
ROOT = Path('F:/Workspaces/chinese-academic-writing-skill')
target = HERE / 'candidates/secondary'
shutil.copytree(ROOT/'chinese-academic-writing-assistant', target, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
p = target/'references/academic-literature-review.md'
old = '- 综合证据时回溯原始研究：对同一结果的多次转述不增加独立证据，准确转述仍可按其来源使用；采用相同方法但基于独立材料或样本的新研究分别判断，不因方法相同合并。'
new = old + '使用转引时，正文明确转引关系并就近绑定实际读到的二手来源，不把未读原文写成已核验；文后著录服从用户或模板，并清楚区分实际使用来源与未读原作。'
text = p.read_text(encoding='utf-8-sig')
assert text.count(old) == 1
p.write_bytes(text.replace(old,new).encode())
(HERE/'secondary-rule.txt').write_bytes(new.encode())
material = '''本轮实际可读的二手材料为AR12：Artino, A. R., Jr. (2012). Academic self-efficacy: from educational theory to instructional practice. Perspectives on Medical Education, 1, 76–85. https://doi.org/10.1007/s40037-012-0012-5 。取自出版方页面“The nature and structure of self-efficacy”中的“Self-efficacy defined”：Artino借Bandura的定义讨论，自我效能是对自身执行有关任务能力的信念，这种信念不必等同于实际能力。这里只提供中文内容摘编，不是原文引语。该节把定义标到文后第10条：Bandura, A. (1986). Social foundations of thought and action: A social cognitive theory. Prentice Hall. 书目信息来自AR12的文后清单，Bandura原书正文未取得、未阅读、未核验；没有原书页码。AR12不是新的效应测量或系统综述。'''
spec = {
 'G_secondary_apa': {'leaf':'academic-literature-review','style':False,'requests':['据下面给定材料写一小段概念综述，说明“自我效能信念与实际能力为何不能直接等同”，正文后附APA实际使用参考文献。离线，不联网，保留AR12来源ID。'+material+' 不使用直接引语，不补原书页码，不增加其他来源。']},
 'H_secondary_body_only': {'leaf':'academic-literature-review','style':False,'requests':['依据材料修改独立综述中的两句，只交正文，不联网，保留AR12来源ID；不另附说明、参考文献清单或材料账本。'+material+' 目标底稿：“本综述已阅读并核验Bandura（1986）原著，证实自我效能与实际能力完全相同[AR12]。Artino（2012）也完成了新的能力干预实验，进一步证明这一结论[AR12]。”']}
}
(HERE/'secondary-cases.json').write_bytes((json.dumps(spec,ensure_ascii=False,indent=2)+'\n').encode())
(HERE/'SECONDARY-PREREGISTRATION.md').write_text('''# 真实文献转引候选首轮（北京时间2026-10-10）

来源由竞品转引规则发现，并用APA官方二手来源页面核对APA场景；不是把APA作为中文论文统一格式。两题为主审据Artino(2012)出版方可读小节制作的中文内容摘编，加构造任务/错误底稿；不是客户原稿。仅一篇二手文章的该小节与书目定位，不声称原书阅读或全篇来源审计。PMC打开仅返回浏览器检查，未计为原文阅读；出版方HTML实际可读。

候选只消歧实际读到的来源与未读原作，不自动触发联网、不强制全部任务列书目、不统一APA。基线仍c60c589产品0.1.8；两模型/provider/max effort与其他R1相同，共8次新会话。独立冷审看原材料与匿名稿，主审回读。首轮不构成三轮准入，产品保持不变，后续才考虑证据充分时细化。

竞品出处：https://github.com/comeonvictor/claude-code-deep-research/blob/ad0ad690f2b47a21fdf10c191c8be0b63df77033/references/citation_rules.md
官方APA：https://apastyle.apa.org/style-grammar-guidelines/citations/secondary-sources
实际文章：https://link.springer.com/article/10.1007/s40037-012-0012-5
''',encoding='utf-8')
print('Secondary candidate and two source-derived tasks frozen.')
