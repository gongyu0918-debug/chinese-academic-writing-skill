"""Prepare complete blind review packets; do not score text or imply review completion."""
from pathlib import Path
import json

HERE = Path(__file__).parent
OUT = HERE/'review-packets'
OUT.mkdir(exist_ok=True)
for group in ['review','reports','statistics','secondary']:
    if (OUT/(group+'.md')).exists():
        continue
    batch = HERE/(group+'-R1')
    if not (batch/'results.json').exists():
        print('PENDING '+group)
        continue
    spec = json.loads((HERE/(group+'-cases.json')).read_text(encoding='utf-8-sig'))
    request = '''独立语义审阅以下封闭材料与已完成稿件。只依据原任务判断，不联网、不委派、不重写稿件、不修改文件。你未参与起草。X/Y规则标签隐藏；不按文风喜好推断优胜，不看其他证据。逐对定位实际事实、研究状态、作者/材料对象、来源归属、就近ID、交付范围与审稿误报问题；能成立的稿件不为凑意见报缺。不把格式标号存在当语义支持，也不把字数/调用完成当通过。任务未要求正文外清单时不额外要求。有限作者分析、纯给定材料转述均不是自动造假。单次差别不是规则因果证据。若某稿标技术无效，可以列观察，但排除其受控胜负；无需解释执行环境。最后说明逐对哪些可用、哪些有实际问题，以及你所看范围。'''
    mapping = {}
    results = json.loads((batch/'results.json').read_text(encoding='utf-8-sig'))
    for ci,(name,case) in enumerate(spec.items()):
        request += '\n\n任务 '+name+'\n'+'\n'.join(case['requests'])
        for mi in [0,1]:
            mapping[name+'-m'+str(mi)] = {}
            arms = ['main','candidate'] if (mi+ci)%2 == 0 else ['candidate','main']
            request += '\n作者路线'+str(mi)
            for label,arm in zip(['X','Y'],arms):
                mapping[name+'-m'+str(mi)][label]=arm
                row = next(r for r in results if r['model']==['alibaba-token-plan-responses/qwen3.8-flash','ollama-cloud/glm-5.3-flash'][mi] and r['case']==name and r['arm']==arm)
                request += '\n稿 '+label+'\n'+('[本稿技术无效，排除受控判定。]\n' if row['invalid'] else '')+(batch/f'm{mi}-{name}-{arm}-s1.final.txt').read_text(encoding='utf-8-sig')
    (OUT/(group+'.md')).write_bytes(request.encode())
    (OUT/(group+'.mapping.json')).write_bytes((json.dumps(mapping,ensure_ascii=False,indent=2)+'\n').encode())
    print('COMPLETE '+group)
