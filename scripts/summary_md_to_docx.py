# -*- coding: utf-8 -*-
"""검토용 요약본 md를 교수님 제출용 docx로 만든다 (2026-10-16).

서식은 thesis_summary_visual_v8.docx를 틀로 쓴다: 제목 두 줄과 쪽 설정, 장·절 제목 스타일, 본문·캡션·
참고문헌 문단의 서식을 그대로 복사하고, 본문 내용은 md에서 새로 채운다. 목차는 md의 장·절 제목으로 만든다.
2026-10-16 수정: 그림은 원래 크기로 넣고(글자 축소 방지), 표 칸은 상하·좌우 가운데 정렬.

    python3 scripts/summary_md_to_docx.py docs/summary_review_v19.md thesis_summary_visual_v14.docx
"""
import copy
import os
import re
import sys

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Inches, Pt

ROOT = "/home/user/hongik"
TEMPLATE = os.path.join(ROOT, "thesis_summary_visual_v8.docx")
FONT = "맑은 고딕"


def main(md_path: str, out_name: str) -> None:
    dst = os.path.join(ROOT, out_name)
    assert not os.path.exists(dst), "exists; save as a new version"
    d = docx.Document(TEMPLATE)
    ps = d.paragraphs
    body_proto = next(p for p in ps if p.style.name == "Normal" and len(p.text) > 150)
    cap_proto = next(p for p in ps if p.text.startswith("표 2."))
    ref_proto = next(p for p in ps if re.match(r"^1\. [A-Z]", p.text))
    img_proto = next(p for p in ps if p._p.xpath(".//a:blip"))
    protos = {k: (copy.deepcopy(v._p.pPr), copy.deepcopy(v.runs[0]._r.rPr) if v.runs else None)
              for k, v in (("body", body_proto), ("cap", cap_proto), ("ref", ref_proto), ("img", img_proto))}
    h1_proto, h2_proto = next(p for p in ps if p.style.name == "Heading 1"), next(p for p in ps if p.style.name == "Heading 2")
    protos["h1"] = (copy.deepcopy(h1_proto._p.pPr), copy.deepcopy(h1_proto.runs[0]._r.rPr) if h1_proto.runs else None)
    protos["h2"] = (copy.deepcopy(h2_proto._p.pPr), copy.deepcopy(h2_proto.runs[0]._r.rPr) if h2_proto.runs else None)
    text_width = d.sections[0].page_width - d.sections[0].left_margin - d.sections[0].right_margin

    body = d.element.body
    keep = 2                                   # title lines (Korean, English)
    for el in list(body)[keep:]:
        if el.tag != qn("w:sectPr"):
            body.remove(el)

    def para(text_runs, kind="body", align=None, size=None, bold=None, indent=None):
        p = d.add_paragraph()
        pPr, rPr = protos.get(kind, (None, None))
        if pPr is not None:
            p._p.insert(0, copy.deepcopy(pPr))
        for t, opt in text_runs:
            r = p.add_run(t)
            if rPr is not None:
                r._r.insert(0, copy.deepcopy(rPr))
            if opt.get("bold") is not None:
                r.font.bold = opt["bold"]
            if size:
                r.font.size = size
            if bold is not None:
                r.font.bold = bold
        if align is not None:
            p.alignment = align
        if indent is not None:
            p.paragraph_format.left_indent = indent
        return p

    def runs_of(s: str):
        out, pos = [], 0
        for m in re.finditer(r"\*\*(.+?)\*\*", s):
            if m.start() > pos:
                out.append((s[pos:m.start()], {}))
            out.append((m.group(1), {"bold": True}))
            pos = m.end()
        if pos < len(s):
            out.append((s[pos:], {}))
        return out or [("", {})]

    def table(rows):
        t = d.add_table(rows=len(rows), cols=len(rows[0]))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{edge}")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "000000")
            borders.append(e)
        t._tbl.tblPr.append(borders)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = t.cell(i, j)
                cell.text = ""
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                p = cell.paragraphs[0]
                # 표는 상하·좌우 가운데 정렬. 긴 문장(40자 초과) 칸만 좌우는 왼쪽 정렬로 둔다
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if len(val) > 40 else WD_ALIGN_PARAGRAPH.CENTER
                for tx, opt in runs_of(val):
                    r = p.add_run(tx)
                    r.font.size = Pt(9)
                    r.font.bold = True if i == 0 else opt.get("bold")
                    r.font.name = FONT
                    r._r.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
                if i == 0:
                    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "E7E6E6")
                    cell._tc.get_or_add_tcPr().append(shd)
        return t

    lines = open(md_path, encoding="utf-8").read().split("\n")
    # skip md title lines (# title, ### English title)
    start = next(i for i, l in enumerate(lines) if l.strip() == "초록")
    heads = [(l[2:], 1) if l.startswith("# ") else (l[3:], 2) for l in lines[start:] if l.startswith(("# ", "## "))]

    para([("", {})])
    para([("목차", {})], size=Pt(15), bold=True)
    para([("초록", {})], bold=True)
    for t, lvl in heads:
        para([(t, {})], bold=(lvl == 1), size=Pt(10.5) if lvl == 2 else None, indent=Emu(317500) if lvl == 2 else None)
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    md_dir = os.path.dirname(os.path.abspath(md_path))
    in_refs = False
    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.strip() == "초록":
            para([("초록", {})], size=Pt(15), bold=True); i += 1; continue
        if ln.strip() == "국문 초록":
            para([("국문 초록", {})], size=Pt(12), bold=True); i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|(-+\|)+$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split(" | ")])
                i += 1
            table(rows)
            continue
        m = re.match(r"!\[\]\((.+)\)", ln)
        if m:
            p = para([], kind="img", align=WD_ALIGN_PARAGRAPH.CENTER)
            path = os.path.normpath(os.path.join(md_dir, m.group(1)))
            from PIL import Image
            im = Image.open(path)
            w, h = im.size
            # 그림은 그린 크기(PNG의 dpi 정보) 그대로 넣어 글자 크기가 줄지 않게 한다.
            # 본문 폭보다 크면 본문 폭에 맞추고, 높이는 7.5인치를 넘지 않게 한다.
            dpi = (im.info.get("dpi") or (160, 160))[0]
            native = Inches(w / dpi)
            if dpi < 200:                  # 발표 그림(160dpi, 슬라이드 글자 크기)은 0.55배로 넣어 본문 글자와 맞춘다
                native = int(native * 0.55)
            width = min(int(text_width), int(native), int(Inches(7.5) * w / h))
            p.add_run().add_picture(path, width=width)
            i += 1
            continue
        if ln.startswith("# "):
            in_refs = ln[2:].strip() == "참고문헌"
            if ln[2:].startswith("제") or in_refs:
                d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            p = para([(ln[2:], {})], kind="h1"); p.style = d.styles["Heading 1"]
            i += 1
            continue
        if ln.startswith("## "):
            p = para([(ln[3:], {})], kind="h2"); p.style = d.styles["Heading 2"]
            i += 1
            continue
        if re.match(r"\*\*(표|그림) \d+\.", ln):
            para(runs_of(ln.strip()), kind="cap", align=WD_ALIGN_PARAGRAPH.CENTER)
            i += 1
            continue
        para(runs_of(ln), kind="ref" if in_refs else "body")
        i += 1
    d.save(dst)
    print("saved", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
