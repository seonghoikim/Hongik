# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v4.docx from v3 (v3 is read only).

Chapter 4 is flattened to five sections with no third-level headings:
  4.1 실험 설계 (old 4.1.1-4.1.4 as running text)
  4.2 자가 치유 성능 및 유형별 방어 결과 (old 4.2.1 + 4.2.2)
  4.3 교차 모델 검증 / 4.4 5W1H 판단 원칙의 가설 검증 / 4.5 적응형 재공격
Section references, the chapter overview paragraph and the static TOC follow the change.
"""
import sys
import re
import os
import copy
import docx
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual_v3.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v4.docx")
assert not os.path.exists(DST), "v4 already exists; do not overwrite"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

d = docx.Document(SRC)
body = d.element.body


def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def style_of(p):
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def set_text(p, new):
    runs = p.findall(qn("w:r"))
    for r in runs[1:]:
        p.remove(r)
    ts = runs[0].findall(qn("w:t"))
    for t in ts[1:]:
        runs[0].remove(t)
    ts[0].text = new
    ts[0].set(XML_SPACE, "preserve")
    return p


def paras():
    return [e for e in body if e.tag == qn("w:p")]


def one(pred):
    hits = [p for p in paras() if pred(p)]
    assert len(hits) == 1, (len(hits), [txt(h)[:30] for h in hits])
    return hits[0]


def replace_in(p, old, new):
    ts = list(p.iter(qn("w:t")))
    full = "".join(t.text or "" for t in ts)
    pos = full.find(old)
    assert pos >= 0, old[:30]
    end, cur, placed = pos + len(old), 0, False
    for t in ts:
        s, e = cur, cur + len(t.text or "")
        cur = e
        if e <= pos or s >= end:
            continue
        a, b = max(pos - s, 0), min(end - s, len(t.text))
        t.text = t.text[:a] + ("" if placed else new) + t.text[b:]
        t.set(XML_SPACE, "preserve")
        placed = True


T_H2 = copy.deepcopy(one(lambda p: style_of(p) == "2" and txt(p).startswith("5.1.")))


def h2(t):
    return set_text(copy.deepcopy(T_H2), t)


# 1) headings in chapter 4
for p in [p for p in paras() if style_of(p) == "3"]:
    t = txt(p)
    if re.match(r"4\.1\.\d\. |4\.2\.[12]\. ", t):
        body.remove(p)                                   # merged into the parent section
    elif t.startswith("4.2.3. "):
        p.addprevious(h2("4.3. 교차 모델 검증")); body.remove(p)
    elif t.startswith("4.2.4. "):
        p.addprevious(h2("4.4. 5W1H 판단 원칙의 가설 검증")); body.remove(p)
    elif t.startswith("4.2.5. "):
        p.addprevious(h2("4.5. 적응형 재공격")); body.remove(p)
set_text(one(lambda p: style_of(p) == "2" and txt(p) == "4.2. 실험 결과"), "4.2. 자가 치유 성능 및 유형별 방어 결과")
assert not [p for p in paras() if style_of(p) == "3"]

# 2) chapter overview and section references
ov = one(lambda p: txt(p).startswith("이 장에서는 제안 메커니즘을 검증한 실험의 설계와 결과를 함께 다룬다."))
set_text(ov, "이 장에서는 제안 메커니즘을 검증한 실험의 설계와 결과를 함께 다룬다. 먼저 4.1절에서 실험 환경과 데이터 구성, "
             "사용 모델과 평가 절차, 통계 검정 방법, 심판관 신뢰성과 교차 모델 검증의 설계를 기술한다. 이어서 4.2절에서 "
             "자가 치유 성능과 정보 불일치성 유형별 방어 결과를, 4.3절에서 교차 모델 검증 결과를 제시한다. 4.4절에서는 "
             "5W1H 판단 원칙의 가설 검증 결과를, 4.5절에서는 적응형 재공격 결과를 보고한다.")
REF = {"4.1.4절": "4.1절", "4.2.5절": "4.5절"}
for p in paras():
    if style_of(p) in ("1", "2"):
        continue
    for old, new in REF.items():
        while old in txt(p):
            replace_in(p, old, new)
left = [m for p in paras() for m in re.findall(r"\d\.\d\.\d절", txt(p))]
assert not left, left

# 3) static TOC: drop third-level entries, rename changed sections
toc_head = one(lambda p: txt(p) == "목차")
p = toc_head.getnext()
while p is not None and not (txt(p) == "초록" and p is not toc_head.getnext()):
    nxt = p.getnext()
    t = txt(p)
    if re.match(r"4\.[12]\.\d\. ", t):
        if t.startswith("4.2.3. "):
            set_text(p, "4.3. 교차 모델 검증")
        elif t.startswith("4.2.4. "):
            set_text(p, "4.4. 5W1H 판단 원칙의 가설 검증")
        elif t.startswith("4.2.5. "):
            set_text(p, "4.5. 적응형 재공격")
        else:
            body.remove(p); p = nxt; continue
        ind = p.find(qn("w:pPr") + "/" + qn("w:ind"))
        ind.set(qn("w:left"), "500")                      # second-level indent
        for sz in p.iter(qn("w:sz")):
            sz.set(qn("w:val"), "21")
    elif t == "4.2. 실험 결과":
        set_text(p, "4.2. 자가 치유 성능 및 유형별 방어 결과")
    p = nxt

d.save(DST)
print("saved", DST)
