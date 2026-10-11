#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""김영철 교수님 기준 원고 린트 (kim-paper-writing 스킬).

사용법:
  python style_lint.py 원고.md [원고2.md ...] [--ban 단어1,단어2] [--json]

검사 항목과 근거는 스킬의 references/ 문서를 따른다.
  - 국문 번역체, 금칙 제목('소결', '본 연구의 위치'), 트리 비유어   korean-style.md
  - 본문 질문형 문장, 구어체                                    korean-style.md
  - 영문 1인칭 I, AI 문체 어휘, 수동태, 미국식 철자, em-dash       english-style.md
  - 쉼표 인용 [1,2], 번호 주어 '[23]은'                          numbers-and-citations.md
  - 정의·알고리즘 번호 체계                                       definitions-and-gap.md
  - '정확'과 '몬테카를로'의 동시 사용, p-값 표기                   numbers-and-citations.md
  - maximum/maximal 혼동                                       terminology.md
  - 표 행의 열 수 불일치 (셀 안 리터럴 '|' 의심)                  workflow.md

심각도: error(반드시 고친다), warn(문맥 확인), info(참고).
종료 코드: error가 하나라도 있으면 1, 아니면 0.
표준 라이브러리만 사용한다. 코드 블록(``` 구간) 안은 검사하지 않는다.
"""

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# (규칙 ID, 심각도, 정규식, 정규식 플래그, 메시지)
RULES = [
    # --- 국문 번역체 (korean-style.md §2) ---
    ("ko-translationese", "error", r"덮었|덮는다|덮고|덮인", 0,
     "번역체 '덮다'(cover). '포함하다', '모두 실행하다'로 바꾼다"),
    ("ko-translationese", "error", r"몫이다|몫이며|의 몫", 0,
     "번역체 '~의 몫'. '~가 수행한다'로 바꾼다"),
    ("ko-translationese", "error", r"낳는다|낳고|낳아|낳으", 0,
     "번역체 '낳다'(yield). '얻다', '산출한다'로 바꾼다"),
    ("ko-translationese", "error", r"동반 연구", 0,
     "'동반 연구'(companion) → '선행 연구'"),
    ("ko-translationese", "warn", r"세운다|세우고|세워|세우는", 0,
     "번역체 '세우다'(establish, prioritize) 의심. '정한다', '먼저 실행한다'로 (계획을 세운다는 허용)"),
    ("ko-translationese", "warn", r"메운다|메우|메워", 0,
     "번역체 '메우다'(fill the gap) 의심. '해결한다', '보완한다'로 (빈칸을 메운다는 허용)"),
    ("ko-translationese", "warn", r"갭", 0,
     "'갭'(gap) → '문제', '한계', '공백'"),
    ("ko-translationese", "warn", r"짚어\s?내|짚어\s?냅", 0,
     "'짚어 낸다' → '특정한다', '지적한다'"),
    ("ko-translationese", "warn", r"책임을 묻", 0,
     "'책임을 묻는다' → '결함을 귀속한다'"),
    ("ko-translationese", "warn", r"운영 준비가 된", 0,
     "'운영 준비가 된' → '실제 운영에 적용할 수 있는'"),
    ("ko-translationese", "warn", r"돌려준다", 0,
     "'돌려준다'(return) 의심. '반환한다'로 (문맥 확인)"),

    # --- 금칙 제목, 용어, 구어 (korean-style.md §2, structure.md §9) ---
    ("ko-banned-heading", "error", r"소결", 0,
     "'소결' 절 금지. 절 맺음은 본문 단락으로 쓴다"),
    ("ko-banned-heading", "error", r"본 연구의 위치|본 위치", 0,
     "'본 연구의 위치' 제목 금지. 예: '연구 격차와 제안 접근'"),
    ("ko-term", "warn", r"뿌리|잎|가지치기", 0,
     "트리 비유어 → '루트 노드', '단말 노드', '경로 제거(pruning)'"),
    ("ko-term", "warn", r"선택자", 0,
     "'선택자' → '요소 식별자(selector)'"),
    ("ko-term", "warn", r"행태", 0,
     "'행태'는 부정적 함의. '행동', '행위', '동작' 중 뜻에 맞는 것으로"),
    ("ko-colloquial", "warn", r"거든|하는 거다|하는 겁니다", 0,
     "구어체. 평서문으로 바꾼다"),

    # --- 영문 (english-style.md) ---
    ("en-first-person", "warn", r"(?<![A-Za-z])I(?![A-Za-z])", 0,
     "1인칭 I 대신 we를 쓴다"),
    ("en-ai-style", "warn",
     r"\b(blind to|tells us|delve|tapestry|crucial|pivotal|landscape|showcase|"
     r"at all|actually|precisely because|we ask|we answer|it is worth noting|in today's)\b",
     re.IGNORECASE,
     "AI 문체 장치 의심(은유, 의인화, 질문-답, 강조 부사). 평이한 공학 서술로 바꾼다"),
    ("en-passive", "warn", r"\bwas (proposed|developed|introduced) by\b", re.IGNORECASE,
     "수동 대신 능동. 'X et al. proposed Y'"),
    ("en-british", "warn",
     r"\b(colour|behaviour|catalogue|analys(?:e|ing)|optimis(?:e|ing|ation)|"
     r"recognis(?:e|ing)|minimis(?:e|ing))\b",
     re.IGNORECASE,
     "미국식 철자로 (color, behavior, catalog, optimize)"),

    # --- 정의, 인용 (definitions-and-gap.md §1, numbers-and-citations.md §8) ---
    ("en-definition-number", "warn", r"\bDefinition \d+\b|\bAlgorithm \d+\.", 0,
     "정의·알고리즘 번호 체계 대신 소절 + 네 항목(1) Definition: ...)을 쓴다"),
    ("cite-comma", "error", r"\[\d+\s*,\s*\d+", 0,
     "쉼표 인용 → 연속 대괄호 [1][2]"),
    ("cite-bare-subject", "warn", r"(?<![A-Za-z가-힣])\[\d+\]\s*(?:은|는|이|가)(?![가-힣])", 0,
     "번호가 주어 → 'Qi 등[23]은', '선행 연구[3]는'"),
    ("cite-bare-subject", "warn",
     r"^\s*\[\d+\]\s+(?:proposed|suggests|showed|shows|presents|provides|describes|developed)\b",
     re.IGNORECASE,
     "번호가 주어 → 저자명 + 번호"),

    # --- 수치, 용어 정확성 (numbers-and-citations.md §3, terminology.md §8) ---
    ("stat-pvalue", "info", r"p\s*<\s*0?\.0", 0,
     "p-값 정밀 표기: 정확값이나 분수(k/N) 병기를 검토"),
    ("term-max-tree", "warn", r"\bmaximum spanning tree\b", re.IGNORECASE,
     "maximum(가중치 최대)과 maximal(가지를 치지 않음)은 다르다. 의도를 확인"),
]

MAX_HITS_PER_RULE = 5  # 한 줄에서 같은 규칙으로 보고할 최대 매치 수

EM_DASH_SPACED = re.compile(r"\s—\s")
HANGUL = re.compile(r"[가-힣]")
MONTE_CARLO = re.compile(r"monte\s*carlo|몬테카를로", re.IGNORECASE)
EXACT_WORD = re.compile(r"\bexact\b|정확", re.IGNORECASE)


def make_finding(path, lineno, sev, rule, msg, snippet):
    return {
        "file": path,
        "line": lineno,
        "severity": sev,
        "rule": rule,
        "message": msg,
        "snippet": snippet.strip()[:80],
    }


def ascii_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) < 128) / len(letters)


def is_table_line(line):
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def cell_count(line):
    """마크다운 표 한 행의 셀 개수. 이스케이프된 \\| 는 구분자가 아니다."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return len(re.split(r"(?<!\\)\|", s))


def check_file(path, ban_words):
    findings = []
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        return [make_finding(path, 0, "error", "io", "파일을 읽을 수 없다", str(exc))]

    # 코드 블록 표시 (``` 구간은 검사에서 제외)
    fenced = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            fenced.append(True)
        else:
            fenced.append(in_fence)

    compiled = [(rid, sev, re.compile(pat, flags), msg) for rid, sev, pat, flags, msg in RULES]

    for idx, line in enumerate(lines):
        if fenced[idx] or not line.strip():
            continue
        lineno = idx + 1

        for rid, sev, rx, msg in compiled:
            for count, m in enumerate(rx.finditer(line)):
                if count >= MAX_HITS_PER_RULE:
                    break
                findings.append(make_finding(path, lineno, sev, rid, msg, m.group(0)))

        if HANGUL.search(line) and line.rstrip().endswith("?") and not is_table_line(line):
            findings.append(make_finding(path, lineno, "warn", "ko-question",
                                         "본문 질문형 문장. 평서문으로 바꾼다", line))

        if MONTE_CARLO.search(line) and EXACT_WORD.search(line):
            findings.append(make_finding(path, lineno, "warn", "stat-exact-sampling",
                                         "정확(exact)과 몬테카를로(샘플링)를 같은 문장에 씀. 열거가 가능하면 전수 열거로",
                                         line))

        if EM_DASH_SPACED.search(line) and ascii_ratio(line) >= 0.6:
            findings.append(make_finding(path, lineno, "info", "en-em-dash",
                                         "em-dash는 앞뒤 공백 없이 붙인다 (chain—use case)", "—"))

        for word in ban_words:
            if word in line:
                findings.append(make_finding(path, lineno, "error", "project-ban",
                                             f"프로젝트 금칙어 '{word}'", word))

    # 표: 행마다 열 수가 헤더와 같은지 (셀 안 리터럴 '|' 검출)
    i = 0
    n = len(lines)
    while i < n:
        if not fenced[i] and is_table_line(lines[i]):
            start = i
            while i < n and not fenced[i] and is_table_line(lines[i]):
                i += 1
            head = cell_count(lines[start])
            for k in range(start + 1, i):
                cols = cell_count(lines[k])
                if cols != head:
                    findings.append(make_finding(
                        path, k + 1, "error", "table-cols",
                        f"표 열 수 불일치(헤더 {head}개, 이 행 {cols}개). "
                        "셀 안의 리터럴 '|'(절댓값 등)를 \\mid로 바꾼다",
                        lines[k]))
        else:
            i += 1

    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="김영철 교수님 기준 원고 린트")
    ap.add_argument("files", nargs="+", help="검사할 원고 파일 (.md, .txt)")
    ap.add_argument("--ban", default="", help="프로젝트 금칙어, 쉼표로 구분")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args(argv)

    ban_words = [w.strip() for w in args.ban.split(",") if w.strip()]

    all_findings = []
    for path in args.files:
        all_findings.extend(check_file(path, ban_words))

    if args.json:
        print(json.dumps(all_findings, ensure_ascii=False, indent=2))
    else:
        for f in all_findings:
            print(f"{f['file']}:{f['line']}: [{f['severity']}] {f['rule']}: "
                  f"{f['message']} | {f['snippet']}")
        counts = {s: sum(1 for f in all_findings if f["severity"] == s)
                  for s in ("error", "warn", "info")}
        print(f"합계: error {counts['error']} · warn {counts['warn']} · info {counts['info']}")

    return 1 if any(f["severity"] == "error" for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
