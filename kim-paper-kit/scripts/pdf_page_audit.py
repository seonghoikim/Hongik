# -*- coding: utf-8 -*-
"""쪽별 빈칸 측정 (PyMuPDF). 시험 조판 PDF 를 넣으면 쪽마다 본문의 마지막 글·그림 하단과 빈칸(pt)을 보여 준다.
쪽수 맞춤의 첫 단계다. 빈칸이 큰 쪽의 원인(표 접힘, 그림 밀림, 묶음 속성)을 찾는 데 쓴다.

사용:
  python pdf_page_audit.py <pdf> [--bottom PT] [--top PT] [--flag PT] [--columns 1|2] [--ignore REGEX]
  python pdf_page_audit.py <pdf> --spans "문구" [--spans "문구2" ...]

옵션:
  --bottom   본문 하단 기준선(페이지 위에서부터 pt). 기본: 쪽 높이 - 72.
             여백 값을 알면 "쪽 높이 - 하단 여백"을 넣는다.
  --top      본문 상단 기준선(pt). 이보다 위 블록(머리글)은 무시. 기본: 72.
  --flag     이 값(pt) 이상 빈칸인 쪽을 표시. 기본: 120.
  --columns  2 이면 좌·우 단을 따로 잰다. 전폭 블록(그림·표)은 양 단에 모두 센다.
  --ignore   이 정규식에 맞는 글 블록은 무시한다 (예: 첫 쪽 각주 상자).
  --spans    문구가 든 글 조각의 글꼴·크기·굵기·기울임·색을 출력한다.
             제목·헤딩의 색과 볼드가 스타일대로 나왔는지 게재본 기준값과 대조할 때 쓴다.

주의: 그림이 벡터 도형이면 drawings 로, 래스터면 image 로 잡힌다. 표 테두리 선도 본문으로 센다.
"""
import argparse
import re
import sys

import fitz  # PyMuPDF (pip install pymupdf)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def body_items(page, top, bottom, ignore_re):
    """본문 항목 [(x0, y0, x1, y1, 종류, 요약)]. top 위(머리글)와 bottom 아래(바닥글)는 뺀다."""
    items = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
        if ignore_re and ignore_re.search(text):
            continue
        items.append((x0, y0, x1, y1, "글", text.strip().replace("\n", " ")[:30]))
    for im in page.get_image_info():
        x0, y0, x1, y1 = im["bbox"]
        items.append((x0, y0, x1, y1, "그림", "[image]"))
    ph = page.rect.height
    for d in page.get_drawings():
        r = d["rect"]
        if r.height > 0.9 * ph:            # 배경 사각형 등 쪽 전체를 덮는 도형은 제외
            continue
        items.append((r.x0, r.y0, r.x1, r.y1, "도형", "[vector]"))
    return [it for it in items if it[3] > top and it[1] < bottom]


def measure_page(page, top, bottom, columns, ignore_re):
    """한 쪽의 마지막 하단과 빈칸을 계산한다. 반환 dict."""
    items = body_items(page, top, bottom, ignore_re)
    W = page.rect.width
    if not items:
        return {"empty": True}
    if columns == 1:
        last = max(items, key=lambda it: it[3])
        return {"last": last[3], "blank": bottom - last[3], "what": f"[{last[4]}] {last[5]}"}
    mid = W / 2
    res = {}
    for side in ("좌", "우"):
        cand = []
        for it in items:
            x0, x1 = it[0], it[2]
            if (x1 - x0) > 0.55 * W:          # 전폭 블록은 양 단에 모두 센다
                cand.append(it)
            else:
                cx = (x0 + x1) / 2
                if (cx < mid) == (side == "좌"):
                    cand.append(it)
        if cand:
            last = max(cand, key=lambda it: it[3])
            res[side] = (last[3], bottom - last[3], f"[{last[4]}] {last[5]}")
        else:
            res[side] = None
    return {"columns": res}


def print_report(doc, top, bottom, columns, flag, ignore_re):
    flagged = []
    if columns == 1:
        print(f"{'쪽':>3}  {'마지막 y':>9}  {'빈칸':>7}  마지막 블록")
    else:
        print(f"{'쪽':>3}  {'좌 마지막':>9} {'좌 빈칸':>7}  {'우 마지막':>9} {'우 빈칸':>7}  좌/우 마지막 블록")
    for pno, page in enumerate(doc, 1):
        m = measure_page(page, top, bottom, columns, ignore_re)
        if m.get("empty"):
            print(f"{pno:>3}  (본문 없음)")
            continue
        if columns == 1:
            flagged_now = m["blank"] >= flag
            mark = " <-" if flagged_now else ""
            print(f"{pno:>3}  {m['last']:>9.1f}  {m['blank']:>7.1f}  {m['what']}{mark}")
            if flagged_now:
                flagged.append((pno, m["blank"]))
        else:
            L, R = m["columns"]["좌"], m["columns"]["우"]
            lb = L[1] if L else float("nan")
            rb = R[1] if R else float("nan")
            ll = f"{L[0]:>9.1f} {L[1]:>7.1f}" if L else f"{'-':>9} {'-':>7}"
            rr = f"{R[0]:>9.1f} {R[1]:>7.1f}" if R else f"{'-':>9} {'-':>7}"
            what = (L[2] if L else "-") + "  |  " + (R[2] if R else "-")
            mark = " <-" if max(lb if lb == lb else 0, rb if rb == rb else 0) >= flag else ""
            print(f"{pno:>3}  {ll}  {rr}  {what}{mark}")
            if mark:
                flagged.append((pno, max(lb, rb)))
    if flagged:
        pages = ", ".join(str(p) for p, _ in flagged)
        print(f"\n빈칸 {flag:.0f}pt 이상인 쪽: {len(flagged)}개 ({pages})")
    else:
        print(f"\n빈칸 {flag:.0f}pt 이상인 쪽 없음")


def print_spans(doc, needles):
    """문구가 든 글 조각의 글꼴·크기·굵기·기울임·색(#RRGGBB)을 쪽별로 출력한다."""
    for pno, page in enumerate(doc, 1):
        for blk in page.get_text("dict")["blocks"]:
            if blk.get("type") != 0:
                continue
            for line in blk["lines"]:
                for sp in line["spans"]:
                    for nd in needles:
                        if nd in sp["text"]:
                            flags = sp["flags"]
                            bold = bool(flags & 16) or "Bold" in sp["font"]
                            ital = bool(flags & 2) or "Italic" in sp["font"]
                            color = "#%06x" % sp["color"]
                            print(f"쪽 {pno:>3} | {sp['font'][:24]:<24} {sp['size']:>5.1f}pt "
                                  f"{'굵게 ' if bold else '     '}{'기울임 ' if ital else '       '}"
                                  f"{color} | {sp['text'][:50]}")


def main():
    ap = argparse.ArgumentParser(description="쪽별 빈칸 측정 / 글꼴 실측")
    ap.add_argument("pdf")
    ap.add_argument("--bottom", type=float)
    ap.add_argument("--top", type=float, default=72.0)
    ap.add_argument("--flag", type=float, default=120.0)
    ap.add_argument("--columns", type=int, choices=(1, 2), default=1)
    ap.add_argument("--ignore")
    ap.add_argument("--spans", action="append", default=[])
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    if a.spans:
        print_spans(doc, a.spans)
        return
    bottom = a.bottom if a.bottom is not None else doc[0].rect.height - 72.0
    ignore_re = re.compile(a.ignore) if a.ignore else None
    print(f"파일: {a.pdf} · 쪽 {doc.page_count} · 본문 상단 {a.top:.0f}pt · 하단 기준 {bottom:.0f}pt · 단 {a.columns}")
    print_report(doc, a.top, bottom, a.columns, a.flag, ignore_re)


if __name__ == "__main__":
    main()
