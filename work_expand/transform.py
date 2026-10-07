#!/usr/bin/env python3
"""在 original.docx 上做文字级就地编辑，生成保留原版式的扩写稿（不处理批注）。"""
import copy
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

TXT = '感知内化迁移_扩写6000字.txt'
SRC = 'original.docx'
OUT = 'build_6000字版.docx'

lines = [l.strip() for l in Path(TXT).read_text(encoding='utf-8').splitlines() if l.strip()]
def get(prefix):
    for l in lines:
        if l.startswith(prefix): return l
    raise KeyError(prefix)

d = Document(SRC)
P = d.paragraphs

def set_text(p, new_text, abstract_prefix=None):
    el = p._p
    runs = el.findall(qn('w:r'))
    text_rpr = None
    for r in runs:
        if r.find(qn('w:t')) is not None:
            rpr = r.find(qn('w:rPr'))
            if rpr is not None: text_rpr = rpr
            break
    keep = [r for r in runs if r.find(qn('w:drawing')) is not None or r.find(qn('w:pict')) is not None or r.find(qn('w:commentReference')) is not None]
    for r in runs:
        if r not in keep: el.remove(r)
    def mk(text):
        r = el.makeelement(qn('w:r'), {})
        if text_rpr is not None: r.append(copy.deepcopy(text_rpr))
        t = el.makeelement(qn('w:t'), {}); t.text = text; t.set(qn('xml:space'), 'preserve')
        r.append(t); return r
    for k in keep: el.append(k)
    first_keep = keep[0] if keep else None
    if abstract_prefix:
        n1 = mk(abstract_prefix); n2 = mk(new_text)
        if first_keep is not None: first_keep.addprevious(n1)
        else: el.append(n1)
        n1.addnext(n2)
    else:
        n1 = mk(new_text)
        if first_keep is not None: first_keep.addprevious(n1)
        else: el.append(n1)

def clone_para(template_p, text, anchor_el, after=True):
    new_el = copy.deepcopy(template_p._p)
    for r in new_el.findall(qn('w:r')): new_el.remove(r)
    rpr_src = None
    for r in template_p._p.findall(qn('w:r')):
        if r.find(qn('w:t')) is not None:
            rp = r.find(qn('w:rPr'))
            if rp is not None: rpr_src = rp
            break
    r = new_el.makeelement(qn('w:r'), {})
    if rpr_src is not None: r.append(copy.deepcopy(rpr_src))
    t = new_el.makeelement(qn('w:t'), {}); t.text = text; t.set(qn('xml:space'), 'preserve')
    r.append(t); new_el.append(r)
    if after: anchor_el.addnext(new_el)
    else: anchor_el.addprevious(new_el)
    return new_el

# 标题/摘要/关键词
set_text(P[0], get('感知·内化·迁移'))
set_text(P[1], get('摘要：在幼小衔接的关键期')[3:], abstract_prefix='【摘  要】')

# 一、问题审视
set_text(P[5], get('大班幼儿即将步入小学'))
set_text(P[6], get('1.规则传递偏抽象'))
set_text(P[7], get('大班幼儿以具体形象思维为主'))
set_text(P[8], get('2.自控能力较欠缺'))
set_text(P[9], get('大班幼儿虽已具备初步的规则认知'))
set_text(P[10], get('3.集体观念较薄弱'))
set_text(P[11], get('许多幼儿尚未建立起'))

# 二、策略探寻
set_text(P[14], get('幼小衔接：'))
set_text(P[15], get('体育游戏：'))
set_text(P[16], get('规则意识：'))
set_text(P[18], get('根据皮亚杰的认知理论'))
adv = clone_para(P[5], get('体育游戏之所以适于承载'), P[18]._p, after=True)
clone_para(P[13], get('（三）框架建构'), adv, after=True)
set_text(P[19], get('基于以上思考'))

# 三、策略实施
set_text(P[30], get('本研究依托《3—6岁儿童学习与发展指南》'))
set_text(P[34], get('（一）规则感知'))
set_text(P[35], get('大班幼儿注意力持续时间短'))
set_text(P[41], get('教师思考：幼儿仅仅听到规则'))
set_text(P[53], get('教师思考：“宝石”'))
set_text(P[55], get('规则内化是从被动遵守走向主动遵守'))
set_text(P[57], get('回看案例1：有经验'))
set_text(P[59], get('教师思考：规则的价值必须通过'))
set_text(P[60], get('2.螺旋递进：让规则要求'))
set_text(P[61], get('将规则意识的培养分解为不同层次'))
set_text(P[63], get('教师思考：复杂的规则'))
set_text(P[66], get('1.举一反三：从“单个游戏”'))
set_text(P[67], get('在游戏中，很多游戏在形式组织上'))
set_text(P[70], get('教师思考：当适应了一类规则'))
set_text(P[71], get('2.规则共建：从“教师制定”'))
set_text(P[72], get('“勇敢的小猎人”游戏中'))
set_text(P[76], get('通过倾听孩子们的想法'))
set_text(P[77], get('教师思考：当规则出自幼儿自己的提议'))

# 四、成效与反思 + 参考文献
cur = P[77]._p
for text in [get('四、成效与反思'), get('（一）成效'), get('1.规则认知由模糊走向清晰'),
             get('2.规则执行由他律走向自律'), get('3.规则运用由守规走向创规'),
             get('（二）反思与展望'), get('其一，发展的不均衡'),
             '参考文献', get('[1] 皮亚杰'), get('[2] 中华人民共和国教育部'), get('[3] 中华人民共和国教育部')]:
    tmpl = P[3] if text in ('四、成效与反思', '参考文献') else (P[13] if text.startswith('（') else P[5])
    cur = clone_para(tmpl, text, cur, after=True)

d.save(OUT)
print('已生成', OUT)
