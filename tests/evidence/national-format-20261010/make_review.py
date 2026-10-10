from pathlib import Path
import json, hashlib
root=Path(__file__).parent
def build(name):
    folder=root/name
    binding=json.loads((folder/'binding.json').read_text(encoding='utf-8'))
    rows=json.loads((folder/'results.json').read_text(encoding='utf-8'))
    pack=['本包是匿名实写评审。逐题对照用户请求和原材料，判定事实/状态/范围/格式及交付问题；不因输出长度、审稿表完整或执行成功判定质量。仅审，不重写。只依据给定条款要点，不自行填补国标细则。\n国标要点：GB/T 7713.1-2025第5.2.9条，中文学位论文摘要一般300—1000字（不是统一绝对下限），每篇应选3—8个关键词；英文摘要为宜有，英文关键词对应中文。第4.3条，首次出现外文专业术语或缩略词在译文后括注原词语全称。GB/T 7714-2025第9章允许顺序编码制与著者—出版年制；前者按引用先后排，后者年份放责任者后、按文种/责任者字顺/年排序，文后不加顺序号。开题不是已完成学位论文，不能套成稿的结果、结论和声明。只审任务不可替换原文；只交正文不能附过程说明。']
    mapping=[]
    for model in sorted({r['model'] for r in rows}):
      for case in binding['spec']:
        pair=[r for r in rows if r['case']==case and r['model']==model]
        if len(pair)!=2 or any(r['invalid'] for r in pair): continue
        key=model+'-'+case
        pair.sort(key=lambda r:hashlib.sha256((key+r['arm']).encode()).hexdigest())
        pack.append('\n任务 '+key+'\n'+binding['spec'][case]['requests'][0])
        for label,r in zip(['X','Y'],pair):
          index=0 if 'alibaba' in model else 1
          stem=f"m{index}-{case}-{r['arm']}-s1"
          draft=(folder/(stem+'.final.txt')).read_text(encoding='utf-8-sig')
          pack.append('\n稿件 '+label+'\n'+draft)
          mapping.append({'task':key,'label':label,'arm':r['arm'],'stem':stem})
    (folder/'blind-review.txt').write_text('\n'.join(pack),encoding='utf-8')
    (folder/'blind-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    print(name,len(mapping)//2,'valid pairs')
if __name__=='__main__':
 import sys
 for name in sys.argv[1:]: build(name)
