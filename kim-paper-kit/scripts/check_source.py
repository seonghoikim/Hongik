# -*- coding: utf-8 -*-
"""원고 소스(Markdown) 정합성 점검. 조판기를 돌리기 전에 실행한다. 원고 파일은 읽기만 한다.

사용: python check_source.py <sec1.md> [<sec2.md> ...]

점검 항목
  오류(E)
    - 제어문자(탭·폼피드·수직탭·백스페이스): heredoc 백슬래시 손상 흔적
    - 표 행의 파이프 개수 불일치 (유령 열 위험)
    - 표 셀 안 $...$ 수식의 리터럴 '|' (\\mid 로 바꿀 것. 셀이 쪼개진다)
    - {+ 와 +} 개수 불일치 (리비전 표시 짝)
    - $$ 개수 홀수 (수식 블록 짝)
    - [[FIGURE n]] 다음 글줄에 캡션(**Fig. n.**, **Figure n.**, **그림 n.** 중 하나)이 없거나 번호가 다름
    - [[FIGURE n]] 번호 중복
  경고(W)
    - ‹TBD: …› 자리표시가 남아 있음 (제출 전 확정 또는 제거)
    - 캡션 접두 형식이 조판기 규칙과 달라 보임 (저널 규칙에 맞는지 확인)
    - 그림 토큰 뒤 캡션이 없음 (조판기 규칙에 따라 캡션이 빠지거나 기본 캡션이 붙는다)

종료 코드: 오류가 있으면 1, 없으면 0.
"""
import pathlib
import re
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIG_TOKEN = re.compile(r"^\[\[FIGURE (\d+)\]\]$")
# 캡션 접두: TIIS 식 "Fig. n.", IJIBC 식 "Figure n.", 한글 "그림 n."
CAP_FIG = re.compile(r"^\*\*(Fig\.|Figure|그림) (\d+)\.\*\*")
CAP_TBL = re.compile(r"^\*\*(Table|표) \d+\.\*\*")
CAP_ALG = re.compile(r"^\*\*Algorithm \d+\.\*\*")
SEP_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
MATH_IN_LINE = re.compile(r"\$([^$]+)\$")
CTRL = re.compile(r"[\t\f\v\b]")


def check_file(path):
    text = path.read_text(encoding="utf-8")
    # splitlines() 는 \f \v 도 줄 경계로 취급해 제어문자가 검사에서 사라진다. "\n" 으로만 나눈다.
    lines = text.split("\n")
    errs, warns = [], []

    # 1. 제어문자
    for ln, line in enumerate(lines, 1):
        if CTRL.search(line):
            errs.append(f"{ln}행: 제어문자(탭·폼피드 등) 포함 — heredoc 백슬래시 손상 의심")

    # 2. 표 블록: 행별 파이프 수, 셀 수식 안의 리터럴 |
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append((i + 1, lines[i]))
                i += 1
            rows = [(ln, row) for ln, row in block if not SEP_ROW.match(row)]
            if rows:
                base_ln, base_row = rows[0]
                base_n = base_row.strip().count("|")
                for ln, row in rows:
                    n = row.strip().count("|")
                    if n != base_n:
                        errs.append(f"{ln}행: 표 열 수 불일치 (파이프 {n}개, 표 첫 행 {base_n}개) — 유령 열 위험")
                    for m in MATH_IN_LINE.finditer(row):
                        if "|" in m.group(1):
                            errs.append(f"{ln}행: 셀 수식 안 리터럴 '|' — \\mid 로 바꿀 것 (셀이 쪼개진다)")
        else:
            i += 1

    # 3. 리비전 표시 짝, $$ 짝
    n_open = len(re.findall(r"\{\+", text))
    n_close = len(re.findall(r"\+\}", text))
    if n_open != n_close:
        errs.append(f"리비전 표시 짝 불일치: {{+ {n_open}개, +}} {n_close}개")
    if len(re.findall(r"\$\$", text)) % 2:
        errs.append("$$ 개수가 홀수 — 수식 블록 짝이 맞지 않는다")

    # 4. 그림 토큰과 캡션
    seen = Counter()
    for k, line in enumerate(lines):
        m = FIG_TOKEN.match(line.strip())
        if not m:
            continue
        n = int(m.group(1))
        seen[n] += 1
        nxt = next((x.strip() for x in lines[k + 1:] if x.strip()), "")
        mc = CAP_FIG.match(nxt)
        if not mc:
            warns.append(f"{k + 1}행: [[FIGURE {n}]] 다음 글줄에 캡션 없음 — 조판기 규칙에 따라 캡션이 빠지거나 기본 캡션이 붙는다")
        elif int(mc.group(2)) != n:
            errs.append(f"{k + 1}행: [[FIGURE {n}]] 다음 캡션 번호가 {mc.group(2)} — 번호 불일치")
    for n, c in sorted(seen.items()):
        if c > 1:
            errs.append(f"그림 {n} 토큰 {c}회 — 중복")

    # 5. TBD 자리표시
    t = text.count("‹TBD:")
    if t:
        warns.append(f"TBD 자리표시 {t}개 남음 — 제출 전 확정 또는 제거")

    # 6. 캡션 접두 형식
    for k, line in enumerate(lines, 1):
        s = line.strip()
        if re.match(r"^\*\*(Table|Fig\.|Figure|Algorithm)\b", s) and not (
                CAP_FIG.match(s) or CAP_TBL.match(s) or CAP_ALG.match(s)):
            warns.append(f"{k}행: 캡션 접두 형식 확인 필요 — {s[:30]}")
    return errs, warns


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for name in argv:
        path = pathlib.Path(name)
        errs, warns = check_file(path)
        print(f"== {path.name}: 오류 {len(errs)} · 경고 {len(warns)}")
        for e in errs:
            print("  E", e)
        for w in warns:
            print("  W", w)
        failed = failed or bool(errs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
