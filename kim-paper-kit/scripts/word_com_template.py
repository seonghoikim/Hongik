# -*- coding: utf-8 -*-
"""Word COM 조판 템플릿 (범용). 모든 경로는 인자로 받는다.

원천: 논문 조판기(TIIS·TKIPS)의 공통 골격을 일반화했다.
필요 조건: Windows + 정식 Microsoft Word + pywin32 (pip install pywin32).

이 모듈을 import 해도 Word 는 뜨지 않는다. open_word() 를 불러야 COM 이 시작된다.
순수 함수(word_color, next_versioned_path, visual_units, longest_token_units,
distribute_widths, plan_widths, scan_control_chars, parse_inline, figure_block_height,
estimate_balanced_bottom, fits_remaining)와 DeferredQueue(가짜 기록기로 검사)는 Word 없이 테스트한다:
    python word_com_template.py --selftest
Word COM 호출부(open_word, save_new, Typesetter 의 표·그림·수식)는 이 함수로 검사되지 않는다.
처음 쓸 때는 scratch 폴더에서 시험 조판하고 결과를 눈으로 확인한다.

핵심 규칙 (근거는 references/word-com-rules.md):
  - 덮어쓰기 금지: 산출물은 save_new() 가 next_versioned_path() 로 _vNN 새 이름에 쓴다.
  - 단락은 본문 끝(마지막 단락 기호 직전)에만 기록한다. 중간 삽입은 흡수 사고를 낸다.
  - 런은 삽입 직후 Font.Reset() 으로 이웃 서식 상속을 끊고, 요청된 속성만 준다.
  - 서식은 기록 시점에 건다. 완성된 문서에 Find 루프로 서식을 걸지 않는다.
  - 한글 표·제목: WordWrap=True. 열 폭은 plan_widths() 로 하한을 먼저 준다.
  - 그림은 표시 폭을 무조건 지정한다 (2단에서 Word 가 단 폭으로 자동 축소한다).
  - 수식은 테두리 없는 1x2 표에 넣어 BuildUp 이 단락 경계를 삼키지 못하게 한다.
"""
import re
import sys
import time
import shutil
import pathlib
import subprocess
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 한글 출력 필수

# ── Word COM 상수 (wdXxx 값) ──────────────────────────────────────
CM = 28.346457                         # 1cm = 28.35pt
ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT, ALIGN_JUSTIFY = 0, 1, 2, 3
LINE_SINGLE, LINE_EXACT = 0, 4         # wdLineSpaceSingle / wdLineSpaceExactly
SECTION_NEXT_PAGE, SECTION_CONTINUOUS = 2, 3
COLLAPSE_START, COLLAPSE_END = 1, 0
UNIT_CHARACTER, UNIT_STORY = 1, 6      # wdCharacter / wdStory
FIELD_PAGE = 33                        # wdFieldPage
EXPORT_PDF = 17                        # wdExportFormatPDF
WRAP_TOP_BOTTOM = 4                    # wdWrapTopBottom
HL_YELLOW = 7                          # wdYellow (HighlightColorIndex)
AUTOFIT_CONTENT, AUTOFIT_WINDOW = 1, 2
HDR_PRIMARY, HDR_FIRST, HDR_EVEN = 1, 2, 3
BORDER_TOP = -1                        # wdBorderTop

_HANGUL = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")


# ══════════════════════════════════════════════════════════ 순수 함수 (Word 불필요)
def word_color(r, g, b):
    """RGB → Word 색 정수. Word 는 BGR 순서다. 파랑 word_color(0, 0, 255) == 0xFF0000."""
    return int(r) | (int(g) << 8) | (int(b) << 16)


def next_versioned_path(path):
    """기존 파일을 덮어쓰지 않는다. 이름이 있으면 _v02, _v03 … 으로 빈 이름을 고른다.
    같은 이름의 .pdf 짝 파일도 비어 있어야 한다."""
    p = pathlib.Path(path)

    def taken(c):
        return c.exists() or c.with_suffix(".pdf").exists()

    if not taken(p):
        return p
    m = re.match(r"^(.*)_v(\d+)$", p.stem)
    base, n = (m.group(1), int(m.group(2))) if m else (p.stem, 1)
    while True:
        n += 1
        cand = p.with_name(f"{base}_v{n:02d}{p.suffix}")
        if not taken(cand):
            return cand


def visual_units(text, hangul=2):
    """글자 폭 계산용 단위 수. 한글 1글자 = hangul 단위(기본 2), 그 밖의 글자 = 1단위."""
    t = re.sub(r"\*\*", "", text)
    return sum(hangul if _HANGUL.match(c) else 1 for c in t)


def longest_token_units(texts, hangul=2):
    """열 하한 계산용: 셀 문자열들에서 가장 긴 낱말(공백 기준)의 단위 수.
    Word 는 낱말이 한 줄에 못 들어가면 쪼갠다. 하한은 이 낱말이 들어갈 폭이다."""
    best = 1
    for t in texts:
        for w in re.sub(r"\*\*|\{\+|\+\}|\$", "", t).split():
            best = max(best, visual_units(w, hangul))
    return best


def distribute_widths(mins, wants, total):
    """표 열 폭 배분 (pt). 하한을 먼저 주고, 남는 폭은 추가 수요에 비례해 나눈다.
    mins : 열별 하한 (가장 긴 낱말이 쪼개지지 않는 최소 폭)
    wants: 열별 원하는 폭 (wants < mins 이면 mins 로 올린다)
    total: 표 전체 폭 (pt)
    반환: (열 폭 목록, ok). ok=False 면 하한 합이 전체 폭을 넘어 글자가 쪼개질 수 있다.
          이때는 글자 크기를 줄이거나 본문 문장을 줄이는 쪽으로 해결한다 (열 폭만 늘리면 다른 열이 깨진다)."""
    mins = list(mins)
    wants = [max(w, m) for w, m in zip(wants, mins)]
    total = float(total)
    if sum(mins) > total:
        return [total * m / sum(mins) for m in mins], False
    rest = total - sum(mins)
    extra = [w - m for w, m in zip(wants, mins)]
    if sum(extra) <= rest:
        sw = sum(wants)
        return [w + (rest - sum(extra)) * w / sw for w in wants], True
    se = sum(extra)
    return [m + rest * e / se for m, e in zip(mins, extra)], True


def plan_widths(grid, total_pt, body_unit_pt=5.2, head_unit_pt=5.8, pad=14.0, cap=38, hangul=2):
    """grid(머리 행 포함 [[str]])에서 열 폭을 계산한다.
    body_unit_pt / head_unit_pt: 글자 1단위당 pt. TIIS 실측값(영문 본문 8pt 기준 5.2, 머리글 5.8).
        글꼴·크기가 다르면 반드시 재측정한다. 한글 조판은 hangul=2, TKIPS 실측 U=4.1 같은 별도 상수를 쓴다.
    pad: 셀 여백 보정 (pt). cap: 희망 폭을 잴 때 본문 셀 길이 상한(단위).
    참고: 원천 TIIS 조판기는 희망 폭에도 머리글 길이 × 1.15 항을 넣었다. 여기서는 머리글을 하한에만 반영한다.
    원천과 결과가 다를 수 있으므로 표 한 개를 시험 조판해 비교한다."""
    nc = max(len(r) for r in grid)
    mins, wants = [], []
    for j in range(nc):
        col = [r[j] if j < len(r) else "" for r in grid]
        head, body = col[0], (col[1:] or [""])
        m_body = longest_token_units(body, hangul) * body_unit_pt
        m_head = longest_token_units([head], hangul) * head_unit_pt
        lo = max(m_body, m_head) + pad
        longest = max(min(visual_units(c, hangul), cap) for c in body)
        mins.append(lo)
        wants.append(max(longest * body_unit_pt + pad, lo))
    return distribute_widths(mins, wants, total_pt)


def scan_control_chars(text):
    """제어문자(탭·폼피드·수직탭·백스페이스) 위치 [(줄번호, 코드)].
    heredoc 의 \\t \\f 가 실제 제어문자로 저장된 흔적을 찾는다 (원고 수식과 조판 스크립트 손상 사고)."""
    bad = []
    # splitlines() 는 \f \v 를 줄 경계로 써서 검사에서 빠진다. "\n" 으로만 나눈다.
    for ln, line in enumerate(text.split("\n"), 1):
        for ch in re.findall(r"[\t\f\v\b]", line):
            bad.append((ln, ord(ch)))
    return bad


def parse_inline(text):
    """**굵게** 와 *기울임* → [(text, bold, italic)]. 굵게 안의 기울임 중첩을 지원한다.
    LaTeX 수식·리비전 표시·그림 토큰은 이 함수가 아니라 원고 파서 계층에서 처리한다."""
    out = []

    def emit(seg, bold):
        pos = 0
        for m in re.finditer(r"\*([^*]+)\*", seg):
            if m.start() > pos:
                out.append((seg[pos:m.start()], bold, False))
            out.append((m.group(1), bold, True))
            pos = m.end()
        if pos < len(seg):
            out.append((seg[pos:], bold, False))

    pos = 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text, re.S):
        if m.start() > pos:
            emit(text[pos:m.start()], False)
        emit(m.group(1), True)
        pos = m.end()
    if pos < len(text):
        emit(text[pos:], False)
    return [r for r in out if r[0]]


def figure_block_height(width_pt, img_w, img_h, caption_lines=1, caption_line_pt=11.5, slack_pt=30.0):
    """그림 블록(그림 + 캡션 + 여유)의 높이 추정 (pt). 폭은 표시 폭이다.
    상수는 글꼴·줄 간격에 따라 다르다. 원천 값: TKIPS 는 폭×비율+30, TIIS 는 캡션 11.5pt 줄 + 여유 46pt.
    바꾸면 시험 조판으로 다시 잰다 (references/page-fitting.md §4-2)."""
    return width_pt * img_h / img_w + caption_lines * caption_line_pt + slack_pt


def estimate_balanced_bottom(section_top, current_y, body_bottom, right_column=False, line_pt=14.2):
    """연속 구역 나누기를 넣을 때 현재 쪽 2단이 균형 잡혀 끝나는 세로 위치(추정, pt).
    Word 는 연속 구역 나누기 앞의 2단을 균형 맞춰 끝낸다. 좌측 단 기준 채움은 (현재 y − 구역 시작) 이고,
    우측 단이면 좌측 단은 가득 찬 것으로 본다 (references/word-com-rules.md §8, page-fitting.md §4-4)."""
    top = float(section_top)
    if right_column:
        fill = max(0.0, body_bottom - top) + max(0.0, current_y - top)
    else:
        fill = max(0.0, current_y - top)
    return top + fill / 2.0 + line_pt


def fits_remaining(body_bottom, y_bottom, need_pt, margin_pt=6.0):
    """남은 높이 ≥ 필요 높이 + 여유 이면 True. 2단 전폭 그림은 estimate_balanced_bottom() 결과를 y_bottom 으로 넘긴다."""
    return (body_bottom - y_bottom) >= (need_pt + margin_pt)


# ══════════════════════════════════════════════════════════ Word COM 입출력
def kill_word():
    """WINWORD.EXE 를 모두 종료한다 (COM 인스턴스 충돌 방지).
    주의: 사용자가 열어 둔 Word 창의 저장되지 않은 내용도 함께 사라진다. 실행 전에 확인할 것."""
    subprocess.run(["taskkill", "/f", "/im", "WINWORD.EXE"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)


def open_word(template, scratch_dir):
    """템플릿을 작업 사본으로 복사해 열고 본문만 비운다 (스타일·머리글/바닥글은 유지).
    반환: (word, doc, work). 원본 템플릿과 기존 산출물은 건드리지 않는다.
    work 는 임시 사본이므로 끝나면 지워도 된다."""
    import win32com.client                       # Windows + pywin32 전용, 지연 import
    scratch_dir = pathlib.Path(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    work = next_versioned_path(scratch_dir / "_work_copy.docx")
    shutil.copy2(template, work)
    # DispatchEx: 새 Word 인스턴스를 띄운다. Dispatch 는 사용자가 열어 둔 Word 에 붙어서
    # close_word() 의 Quit() 가 사용자의 다른 문서까지 닫는다.
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = word.Documents.Open(str(work))
    doc.Content.Delete()
    return word, doc, work


def save_new(doc, out_path, pdf=True):
    """새 이름으로 저장하고 (옵션) PDF 를 내보낸다. 기존 파일은 덮어쓰지 않는다. 실제 저장 경로를 돌려준다."""
    out = next_versioned_path(out_path)
    doc.SaveAs2(str(out))
    if pdf:
        doc.ExportAsFixedFormat(str(out.with_suffix(".pdf")), EXPORT_PDF)
    return out


def close_word(word, doc):
    """문서를 저장하지 않고 닫은 뒤 Word 를 종료한다. 저장은 save_new() 로만 한다."""
    try:
        doc.Close(False)
    finally:
        word.Quit()


def selection_to_end(word):
    """Selection 기반 조립을 쓸 때의 가드: 기록 전마다 본문 끝으로 옮긴다.
    Selection 이 문서 머리로 튄 사고가 있었다(비결정적). Selection 을 쓰면 항상 호출한다."""
    word.Selection.EndKey(UNIT_STORY)


def find_para(doc, prefix):
    """텍스트 접두어로 단락을 다시 찾는다. 인덱스를 캐시하지 않는다 (삽입 뒤 참조가 밀린다).
    같은 접두어가 여럿이면 첫 매치를 쓰므로 호출부가 의도한 섹션인지 확인한다."""
    for k in range(1, doc.Paragraphs.Count + 1):
        if doc.Paragraphs(k).Range.Text.startswith(prefix):
            return doc.Paragraphs(k)
    raise KeyError(prefix)


def replace_para_text(para, new_text):
    """단락 본문만 바꾼다. para.Range.Text = ... 로 바꾸면 단락 기호까지 지워 다음 단락과 합쳐진다.
    글자 수 제한(Find.Replacement 255자)을 피하는 방법이기도 하다."""
    r = para.Range
    r.MoveEnd(UNIT_CHARACTER, -1)
    r.Text = new_text


def add_page_field(doc, rng):
    """쪽 번호 PAGE 필드를 범위 위치에 넣는다."""
    return doc.Fields.Add(rng, FIELD_PAGE)


def add_caption_list_field(doc, rng, style_name, level=1):
    """캡션 스타일 목록(<표 목차> 등)용 원시 TOC 필드.
    TablesOfFigures.Add 에 키워드 인자를 주면 오바인딩되어 헤딩 기반 목차가 들어간다. 원시 필드를 쓴다.
    style_name: 캡션 전용 단락 스타일 이름(예: 표 캡션 스타일)."""
    code = 'TOC \\h \\z \\t "%s,%d"' % (style_name, level)
    return doc.Fields.Add(rng, -1, code, False)


def header_with_page(sec, which, text, page_first=False):
    """머리말 한 줄에 텍스트와 PAGE 필드를 넣는다.
    page_first=True 면 쪽 번호가 앞(짝수 쪽 방식), False 면 뒤(홀수 쪽 방식).
    Range.Text 를 통째로 바꾸면 PAGE 필드가 사라지므로, 텍스트를 쓴 뒤 필드를 따로 넣는다."""
    h = sec.Headers(which)
    h.Range.Text = text
    fr = h.Range
    if page_first:
        fr.Collapse(COLLAPSE_START)
    else:
        fr.MoveEnd(UNIT_CHARACTER, -1)
        fr.Collapse(COLLAPSE_END)
    h.Range.Fields.Add(fr, FIELD_PAGE)
    return h


# ══════════════════════════════════════════════════════════ 본문 기록기
class Typesetter:
    """본문 끝에 단락·그림·표·수식을 차례로 기록한다.

    규칙:
      - 항상 마지막 단락 기호 직전(= Content.End - 1)에 쓴다. 중간 삽입은 하지 않는다.
      - 런은 삽입 직후 Font.Reset() 으로 이웃 직접 서식을 끊고, 요청된 속성만 준다.
      - 스타일은 텍스트를 넣은 뒤 적용하고, 직접 서식은 그 뒤에 준다.
        (미요청 속성은 건드리지 않는다. Bold=0 같은 명시 할당은 스타일의 색·볼드를 죽인다.)
    """

    def __init__(self, word, doc):
        self.word = word
        self.doc = doc

    def end(self):
        return self.doc.Content.End - 1

    def where(self):
        """(쪽 번호, 쪽 위 세로 위치 pt). 지연 배치(그림을 나중에 밀어 넣기) 판단에 쓴다."""
        e = self.end()
        r = self.doc.Range(e, e)
        return int(r.Information(3)), float(r.Information(6))

    def para(self, runs, style=None, align=None, first_indent=None, left_indent=None,
             keep_next=False, keep_together=False, space_before=None, space_after=None,
             line_rule=None, line_spacing=None, font=None, size=None):
        """단락 하나를 본문 끝에 쓴다.
        runs: str(굵게·기울임 마크업 허용) 또는 [(text, bold, italic, color)] 목록. color 는 Word 정수 또는 None.
        반환: (단락 시작, 텍스트 끝) 절대 위치."""
        doc = self.doc
        if isinstance(runs, str):
            runs = [(t, b, i, None) for t, b, i in parse_inline(runs)] or [(" ", False, False, None)]
        else:
            runs = [tuple(r) + (None,) * (4 - len(r)) for r in runs]
        runs = [(unicodedata.normalize("NFC", t), b, i, c) for t, b, i, c in runs if t]
        if not runs:
            runs = [(" ", False, False, None)]
        start = self.end()
        cur = start
        recs = []
        for t, b, i, c in runs:
            r = doc.Range(cur, cur)
            r.Text = t                           # 삽입 후 r 은 새 텍스트를 덮는다
            r.Font.Reset()                       # 이웃 런의 직접 서식 상속 차단
            recs.append((r.Start, r.End, b, i, c))
            cur = r.End
        doc.Range(cur, cur).Text = "\r"
        rng = doc.Range(start, cur + 1)
        if style:
            try:
                rng.Style = doc.Styles(style)
            except Exception:
                print(f"  [경고] 스타일 없음: {style!r} — 기본 단락으로 남김")
        p = rng.Paragraphs(1)
        pf = p.Format
        if align is not None:
            p.Alignment = align
        if first_indent is not None:
            pf.FirstLineIndent = first_indent
        if left_indent is not None:
            pf.LeftIndent = left_indent
        if keep_next:
            p.KeepWithNext = True
        if keep_together:
            p.KeepTogether = True
        if space_before is not None:
            pf.SpaceBefore = space_before
        if space_after is not None:
            pf.SpaceAfter = space_after
        if line_rule is not None:
            pf.LineSpacingRule = line_rule
            if line_rule == LINE_EXACT and line_spacing is not None:
                pf.LineSpacing = line_spacing
        if font or size:
            f = rng.Font
            if font:
                f.Name = font
            if size:
                f.Size = size
        for s, e, b, i, c in recs:               # 요청된 속성만 직접 서식으로
            fr = doc.Range(s, e).Font
            if b:
                fr.Bold = -1
            if i:
                fr.Italic = -1
            if c is not None:
                fr.Color = c
        return start, cur

    def picture(self, path, width_pt, align=ALIGN_CENTER, keep_next=True):
        """그림 단락. 표시 폭을 무조건 지정하고 높이는 가로세로 비율로 맞춘다.
        그림 단락에는 '정확히' 줄 간격을 주지 않는다 (그림이 잘린다). 반환: (shape, 표시 높이 pt)."""
        from PIL import Image
        with Image.open(path) as im:
            iw, ih = im.size
        start, _ = self.para(" ", align=align, first_indent=0, line_rule=LINE_SINGLE,
                             keep_next=keep_next)
        shp = self.doc.InlineShapes.AddPicture(str(path), False, True, self.doc.Range(start, start))
        shp.LockAspectRatio = -1
        shp.Width = width_pt
        h = width_pt * ih / iw
        shp.Height = h
        return shp, h

    def table(self, grid, widths_pt, style_header=None, style_cell=None, header_bold=True,
              keep_rows=1, borders=True, font=None, size=None):
        """표. grid 의 첫 행은 머리글. 셀의 **굵게** 표기는 굵은 글자로 바꾼다.
        widths_pt 는 plan_widths() 로 계산해 넘긴다 (표 직후 자동 맞춤 값은 읽을 수 없다).
        keep_rows: 다음 행과 묶을 앞쪽 행 수 (머리글+첫 행 권장, 짧은 표만 전체를 묶는다).
        행은 쪼개지지 않게 하고, 쪽을 넘으면 머리 행을 반복한다."""
        doc = self.doc
        nr, nc = len(grid), max(len(r) for r in grid)
        end = self.end()
        tbl = doc.Tables.Add(doc.Range(end, end), nr, nc)
        tbl.Borders.Enable = bool(borders)
        tbl.Rows.Alignment = ALIGN_CENTER
        tbl.AllowAutoFit = False
        for j, w in enumerate(widths_pt):
            tbl.Columns(j + 1).Width = w
        for i, row in enumerate(grid):
            for j in range(nc):
                raw = row[j] if j < len(row) else ""
                bold = len(raw) > 4 and raw.startswith("**") and raw.endswith("**")
                txt = re.sub(r"\*\*([^*]*)\*\*", r"\1", raw)
                cr = tbl.Cell(i + 1, j + 1).Range
                cr.Text = unicodedata.normalize("NFC", txt)
                st = style_header if i == 0 else style_cell
                if st:
                    try:
                        cr.Style = doc.Styles(st)
                    except Exception:
                        print(f"  [경고] 표 스타일 없음: {st!r}")
                if (i == 0 and header_bold) or bold:
                    cr.Font.Bold = -1            # 요청된 경우에만 굵게
                if font:
                    cr.Font.Name = font
                if size:
                    cr.Font.Size = size
                pf = cr.ParagraphFormat
                pf.WordWrap = True               # 한글 낱말이 셀 안에서 쪼개지지 않게
                pf.Alignment = ALIGN_CENTER if i == 0 else ALIGN_LEFT
                pf.KeepWithNext = i < keep_rows
        tbl.Rows.AllowBreakAcrossPages = False
        tbl.Rows(1).HeadingFormat = True         # 쪽을 넘으면 머리 행 반복
        return tbl

    def equation(self, linear, tag, text_w_pt, tag_w_pt=1.6 * CM, rev=False, color=None):
        """수식을 테두리 없는 1x2 표로 격리한다. 셀1 = 수식(가운데), 셀2 = (tag)(오른쪽).
        셀 경계는 BuildUp 이 넘지 못하므로 단락 경계 삼킴 사고를 막는다.
        linear: 유니코드 선형 표기(UnicodeMath 근사). LaTeX 변환은 원고 파서 계층에서 한다.
        BuildUp 이 실패하면 이탤릭 텍스트로 남긴다. rev=True 면 파랑 볼드(리비전 표시)."""
        doc = self.doc
        end = self.end()
        tbl = doc.Tables.Add(doc.Range(end, end), 1, 2)
        tbl.Borders.Enable = False
        tbl.AllowAutoFit = False
        tbl.Columns(1).Width = text_w_pt - tag_w_pt
        tbl.Columns(2).Width = tag_w_pt
        tbl.Rows.AllowBreakAcrossPages = False
        c1 = tbl.Cell(1, 1).Range
        c1.End = c1.End - 1                      # 셀 끝 마커 제외
        c1.Text = linear
        c1.Font.Name = "Times New Roman"
        c1.Font.Size = 11
        c1.ParagraphFormat.Alignment = ALIGN_CENTER
        c1.ParagraphFormat.FirstLineIndent = 0
        tbl.Cell(1, 1).VerticalAlignment = 1
        try:
            om = tbl.Cell(1, 1).Range
            om.End = om.End - 1
            doc.OMaths.Add(om)
            doc.OMaths(doc.OMaths.Count).BuildUp()
        except Exception:
            r = tbl.Cell(1, 1).Range
            r.End = r.End - 1
            r.Font.Italic = -1
            print("  [경고] BuildUp 실패 — 이탤릭 텍스트로 남김:", linear[:40])
        if tag:
            c2 = tbl.Cell(1, 2).Range
            c2.End = c2.End - 1
            c2.Text = "(" + tag + ")"
            c2.Font.Name = "Times New Roman"
            c2.Font.Size = 11
            c2.ParagraphFormat.Alignment = ALIGN_RIGHT
            c2.ParagraphFormat.FirstLineIndent = 0
            tbl.Cell(1, 2).VerticalAlignment = 1
        if rev or color is not None:
            for cc in (tbl.Cell(1, 1), tbl.Cell(1, 2)):
                cc.Range.Font.Color = color if color is not None else word_color(0, 0, 255)
                if rev:
                    cc.Range.Font.Bold = -1
        return tbl

    def section_break(self, kind=SECTION_CONTINUOUS):
        """구역 나누기. 연속(CONTINUOUS)은 앞 구역의 단을 Word 가 균형 맞춰 끝낸다."""
        e = self.end()
        self.doc.Range(e, e).InsertBreak(kind)
        return self.doc.Sections(self.doc.Sections.Count)

    def set_columns(self, n, gap_pt=20.0):
        """연속 구역 나누기 뒤 새 구역의 단 수를 정한다 (n=1 전폭 구역, n=2 2단 본문)."""
        sec = self.section_break(SECTION_CONTINUOUS)
        tc = sec.PageSetup.TextColumns
        tc.SetCount(n)
        if n > 1:
            tc.EvenlySpaced = True
            tc.Spacing = gap_pt
        return sec

    def dump_tail(self, n=6):
        """검증용: 끝 n 개 단락의 스타일·그림 수·앞부분 텍스트를 출력한다. 인접 단락 흡수 여부를 본다."""
        doc = self.doc
        total = doc.Paragraphs.Count
        for k in range(max(1, total - n + 1), total + 1):
            p = doc.Paragraphs(k)
            txt = p.Range.Text.replace("\r", "").replace("\x07", "")[:40]
            print(f"  [{k}] style={p.Style.NameLocal} shapes={p.Range.InlineShapes.Count} :: {txt}")


class DeferredQueue:
    """그림 지연 배치 큐 (references/page-fitting.md §4). Word 없이 가짜 ts 로도 검사할 수 있다.

    그림을 바로 넣을 수 없으면 큐에 보류하고 본문을 계속 흘린다.
    큐가 비기 전에는 새 그림도 뒤에 세운다 (그림 순서를 지킨다. 원천 TIIS 조판기 방식).
    호출 규칙:
      - offer(): 그림 토큰을 만났을 때 호출한다. placer 는 인자 없는 삽입 함수다.
      - flush(): 완결 문단이 끝난 경계에서 호출한다. 소문자로 시작하는 줄, 표, 수식 앞에서는 호출하지 않는다.
      - flush(force=True): 참고문헌, 약력 등 블록 시작 전에 강제로 배출한다.
    bottom_fn: 현재 쪽의 기준 세로 위치를 돌려 준다. 2단 본문의 전폭 그림이면
      estimate_balanced_bottom() 결과를 돌려 주는 함수를 넣는다. 생략하면 ts.where() 의 y 를 쓴다.
    """

    def __init__(self, ts, body_bottom, margin_pt=6.0, bottom_fn=None, log=print):
        self.ts = ts
        self.body_bottom = float(body_bottom)
        self.margin_pt = margin_pt
        self.bottom_fn = bottom_fn
        self.log = log
        self.q = []                                  # [(높이 pt, placer, 라벨)]

    def _y(self):
        return self.bottom_fn() if self.bottom_fn else self.ts.where()[1]

    def _room_for(self, need_pt):
        return fits_remaining(self.body_bottom, self._y(), need_pt, self.margin_pt)

    def offer(self, height_pt, placer, label=""):
        """넣었으면 True, 보류했으면 False."""
        if not self.q and self._room_for(height_pt):
            placer()
            self.log(f"  [즉시] {label}")
            return True
        self.q.append((height_pt, placer, label))
        self.log(f"  [보류] {label}: 필요 {height_pt:.0f}pt")
        return False

    def flush(self, force=False):
        """큐 앞에서부터 들어갈 만큼 넣는다. force=True 면 조건을 보지 않고 모두 넣는다."""
        while self.q:
            h, placer, label = self.q[0]
            if not force and not self._room_for(h):
                break
            self.q.pop(0)
            placer()
            self.log(f"  [배치] {label}")

    def pending(self):
        return len(self.q)


# ══════════════════════════════════════════════════════════ 자체 검사 (Word 불필요)
def _selftest():
    import tempfile
    assert word_color(0, 0, 255) == 0xFF0000, "파랑 BGR"
    assert word_color(255, 0, 0) == 0x0000FF, "빨강 BGR"

    w, ok = distribute_widths([50, 60, 40], [80, 60, 120], 300)
    assert ok and abs(sum(w) - 300) < 1e-6, "하한 여유 있는 배분은 합계를 보존해야 한다"
    w2, ok2 = distribute_widths([120, 120, 120], [150, 150, 150], 300)
    assert (not ok2) and abs(sum(w2) - 300) < 1e-6, "하한 초과 시 False 와 비례 축소"
    w3, ok3 = distribute_widths([50, 50], [50, 200], 300)
    assert ok3 and abs(sum(w3) - 300) < 1e-6 and w3[1] > w3[0], "남는 폭은 추가 수요에 비례"

    grid = [["Name", "Description"], ["LW", "Independent (Alg. 1) text"], ["**Total**", "가나다라 마바사"]]
    pw, pok = plan_widths(grid, 400)
    assert abs(sum(pw) - 400) < 1e-6 and pok, "plan_widths 합계 보존"

    assert visual_units("가a") == 3 and visual_units("**굵게**") == 4, "한글 2단위"
    assert longest_token_units(["가나 다라마"]) == 6, "공백 기준 가장 긴 낱말 '다라마' = 6단위"

    assert scan_control_chars("a\tb") == [(1, 9)], "탭 탐지"
    assert scan_control_chars("a  b\nc") == [], "정상 공백은 통과"
    assert scan_control_chars("a\fb\nc") == [(1, 12)], "폼피드도 탐지 (splitlines 회귀 방지)"
    assert scan_control_chars("x\nab\vc") == [(2, 11)], "수직탭도 줄 번호와 함께 탐지"

    assert parse_inline("a **b *c* d** e") == [
        ("a ", False, False), ("b ", True, False), ("c", True, True),
        (" d", True, False), (" e", False, False)], "굵게 안 기울임 중첩"

    assert abs(figure_block_height(411, 1000, 1000) - 452.5) < 1e-9, "그림 블록 = 폭 + 캡션 1줄 + 여유 30"
    assert abs(estimate_balanced_bottom(100, 400, 765.9) - 264.2) < 1e-9, "좌측 단: 구역 시작 + 채움/2 + 한 줄"
    assert abs(estimate_balanced_bottom(100, 400, 765.9, right_column=True) - 597.15) < 1e-6, \
        "우측 단: 좌측 단 가득 + 우측 일부의 절반"
    assert fits_remaining(765.9, 600, 100) and not fits_remaining(765.9, 700, 100), "필요 높이 + 여유 6pt"

    class _FakeTS:                                   # Word 없이 큐 동작만 검사하는 가짜 기록기
        def __init__(self):
            self.y = 100.0

        def where(self):
            return (1, self.y)

    fts, placed = _FakeTS(), []
    quiet = lambda *a, **k: None
    dq = DeferredQueue(fts, 765.9, log=quiet)
    assert dq.offer(100, lambda: placed.append("A"), "A") and placed == ["A"], "남는 높이가 있으면 즉시 삽입"
    fts.y = 700.0
    assert not dq.offer(100, lambda: placed.append("B"), "B"), "남는 높이가 없으면 보류"
    assert not dq.offer(10, lambda: placed.append("C"), "C"), "큐가 남아 있으면 뒤에 세운다 (순서 유지)"
    dq.flush()
    assert placed == ["A"] and dq.pending() == 2, "들어갈 공간이 없으면 배출하지 않는다"
    fts.y = 200.0
    dq.flush()
    assert placed == ["A", "B", "C"] and dq.pending() == 0, "공간이 생기면 FIFO 로 배출"
    fts.y = 700.0
    dq.offer(100, lambda: placed.append("D"), "D")
    dq.flush(force=True)
    assert placed[-1] == "D" and dq.pending() == 0, "force 는 조건을 보지 않고 배출"
    fts2 = _FakeTS()
    dq2 = DeferredQueue(fts2, 765.9, bottom_fn=lambda: 700.0, log=quiet)
    assert not dq2.offer(100, lambda: None, "E"), "bottom_fn 이 주는 기준 위치로 판정 (2단 전폭 그림)"

    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "paper.docx"
        assert next_versioned_path(p) == p, "없으면 그대로"
        p.write_text("x", encoding="utf-8")
        assert next_versioned_path(p).name == "paper_v02.docx", "있으면 _v02"
        (pathlib.Path(d) / "paper_v02.docx").write_text("y", encoding="utf-8")
        assert next_versioned_path(p).name == "paper_v03.docx", "_v02 도 있으면 _v03"
        (pathlib.Path(d) / "paper_v03.pdf").write_text("z", encoding="utf-8")
        assert next_versioned_path(p).name == "paper_v04.docx", "짝 PDF 가 있어도 건너뜀"
    print("selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print(__doc__)
