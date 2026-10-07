#!/usr/bin/env python3
"""彻底移除 docx 中的批注：删正文标记 + 删 comments 相关部件/关系/内容类型声明。"""
import re, shutil, sys, zipfile

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
items = {n: zin.read(n) for n in zin.namelist()}
zin.close()

# 1) 删除批注部件
for name in list(items):
    if re.search(r'word/(comments|commentsExtended|commentsIds|people)\.xml$', name):
        del items[name]

# 2) 清理 document.xml 中的批注标记与引用 run
doc = items['word/document.xml'].decode('utf-8')
doc = re.sub(r'<w:commentRangeStart[^>]*/>', '', doc)
doc = re.sub(r'<w:commentRangeEnd[^>]*/>', '', doc)
doc = re.sub(r'<w:r(?:\s[^>]*)?>(?:(?!</w:r>).)*?<w:commentReference[^>]*/>(?:(?!</w:r>).)*?</w:r>',
             '', doc, flags=re.S)
assert 'commentReference' not in doc and 'commentRange' not in doc, '正文批注标记未清干净'
items['word/document.xml'] = doc.encode('utf-8')

# 3) 清理关系
rels = items['word/_rels/document.xml.rels'].decode('utf-8')
rels = re.sub(r'<Relationship\b[^>]*?/>',
              lambda m: '' if (re.search(r'Target="[^"]*(comments|people)\.xml', m.group(0))
                              or 'comments' in m.group(0)) else m.group(0), rels)
items['word/_rels/document.xml.rels'] = rels.encode('utf-8')

# 4) 清理内容类型声明
ct = items['[Content_Types].xml'].decode('utf-8')
ct = re.sub(r'<Override PartName="/word/(comments|commentsExtended|commentsIds|people)\.xml"[^>]*/>', '', ct)
items['[Content_Types].xml'] = ct.encode('utf-8')

with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, data in items.items():
        z.writestr(n, data)
print('批注已移除 →', dst)
