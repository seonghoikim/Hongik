# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v6.docx from v5 (v5 is read only).

Terminology change (2026-10-12, author decision):
  요구사항 명세서(SRS) -> 응대 정책 명세 / 응대 정책,  자가 치유 -> 강건화,  치유용 -> 보강용
Prior work that calls itself self-healing (§2.3 title, chapter overview) keeps the word.
Figures whose labels used the old terms are replaced by the *_v6.png renders (make_figs_v6.py).
"""
import hashlib
import os
import sys

import docx
from docx.oxml.ns import qn
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual_v5.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v6.docx")
FIG = os.path.join(ROOT, "diagrams", "summary_v2")
assert not os.path.exists(DST), "v6 already exists; do not overwrite"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

d = docx.Document(SRC)
body = d.element.body


def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


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


WHOLE = {
    "AI 챗봇의 정보 불일치성(Information Disorderness): SRS 기반 자가 치유 저항 메커니즘 — 가전 유통 사례를 중심으로":
        "AI 챗봇의 정보 불일치성(Information Disorderness)에 대한 강건화: 적대적 테스트 기반 응대 정책 자동 보강 — 가전 유통 사례를 중심으로",
    "Information Disorderness in AI Chatbots: An SRS-based Self-Healing Resistance Mechanism — A Consumer Electronics Retail Case Study":
        "Hardening AI Chatbots against Information Disorderness: Adversarial Test-Driven Response Policy Reinforcement — A Consumer Electronics Retail Case Study",
}
PROTECT = "자동화된 레드티밍과 자가 치유 프레임워크"
RULES = [
    ("자가 치유 루프를 갖는 주요 선행연구", "자동 보강 루프를 갖는 주요 선행연구"),
    ("자가 치유 여부", "자동 보강 루프 여부"),
    ("요구사항 명세서(SRS)", "응대 정책 명세"),
    ("요구사항 명세서", "응대 정책 명세"),
    ("SRS라는", "응대 정책이라는"), ("SRS가", "응대 정책이"), ("SRS를", "응대 정책을"),
    ("SRS는", "응대 정책은"), ("SRS와", "응대 정책과"), ("SRS로", "응대 정책으로"),
    ("SRS", "응대 정책"),
    ("자가 치유(Self-Healing)", "강건화(Hardening)"),
    ("Self-Healing", "Hardening"),
    ("자가 치유", "강건화"),
    ("치유용", "보강용"),
    ("치유", "보강"),
]
DEFINITION = (" 본 요약본에서 응대 정책 명세(Response Policy Specification, 이하 응대 정책)는 고객사의 요구사항을 LLM이 실행 "
              "시점에 읽는 자연어 지시문으로 명세한 문서를 가리키며, 소프트웨어공학의 요구사항 명세서(SRS)와 구분한다. 강건화는 "
              "적대적 테스트로 찾은 결함을 응대 정책에 보강 규칙(Meta-Rule)으로 자동 반영하고 재검증하는 설계 시점의 반복 절차를 "
              "뜻하며, 운영 중 스스로 복구하는 자가 치유와 구분한다.")

paras = list(body.iter(qn("w:p")))
for p in paras:
    t = txt(p)
    if t == "자가 치유":                                   # table 1 row label (whether a work has the loop)
        replace_in(p, t, "자동 보강 루프")
        continue
    if t in WHOLE:
        replace_in(p, t, WHOLE[t])
        continue
    hold = PROTECT in t
    if hold:
        replace_in(p, PROTECT, "⟦P⟧")
    for old, new in RULES:
        while old in txt(p):
            replace_in(p, old, new)
    if hold:
        replace_in(p, "⟦P⟧", PROTECT)

overview = next(p for p in paras if txt(p).startswith("본 요약본은 학위논문 전문의 핵심 그림을 중심으로"))
first_sentence_end = "이하 '전문'은 학위논문 전체 원고를 가리킨다."
replace_in(overview, first_sentence_end, first_sentence_end + DEFINITION)

# figures: match embedded images to their source files and swap in the v6 render
sources = {}
for name in os.listdir(FIG):
    if name.endswith(".png") and not name.endswith("_v6.png"):
        with open(os.path.join(FIG, name), "rb") as f:
            sources[hashlib.md5(f.read()).hexdigest()] = name
swapped = []
for p in paras:
    for blip in p.iter(qn("a:blip")):
        part = d.part.related_parts[blip.get(qn("r:embed"))]
        name = sources.get(hashlib.md5(part.blob).hexdigest())
        if not name:
            continue
        stem = name[:-4].replace("plot_cross_v5", "plot_cross")
        new = os.path.join(FIG, stem + "_v6.png")
        if not os.path.exists(new):
            continue
        with open(new, "rb") as f:
            part._blob = f.read()
        w, h = Image.open(new).size
        for ext in list(p.iter(qn("wp:extent"))) + list(p.iter(qn("a:ext"))):
            if ext.get("cx"):
                ext.set("cy", str(round(int(ext.get("cx")) * h / w)))
        swapped.append(name)

all_text = "".join(txt(p) for p in body.iter(qn("w:p")))
left = [k for k in ("SRS", "자가 치유", "치유") if all_text.replace(PROTECT, "").replace("요구사항 명세서(SRS)와", "")
        .replace("자가 치유와 구분", "").count(k)]
assert not left, left
d.save(DST)
print("saved", DST, "| figures swapped:", sorted(swapped))
