# -*- coding: utf-8 -*-
"""Export a summary .docx to Markdown for live review, applying the Korean-first wording (2026-10-15).

Author decision: no English glosses in parentheses, Korean wording wherever a Korean term exists.
Kept as is: proper nouns (papers, tools, models, authors), common acronyms (LLM, RAG, AI, OWASP, CVSS),
version numbers, formulas, the English title, and the reference list.

    python3 scripts/summary_to_md.py thesis_summary_visual_v8.docx docs/summary_review_v9.md
"""
import hashlib
import os
import re
import sys

import docx
from docx.oxml.ns import qn

ROOT = "/home/user/hongik"
FIG = os.path.join(ROOT, "diagrams", "summary_v2")

# ordered: specific phrases first, generic terms last
RULES = [
    # glosses and whole phrases
    ("(Information Disorderness)", ""), ("(Information Disorder)", ""), ("(Hardening)", ""),
    ("(Response Policy Specification)", ""), ("요구사항 명세서(SRS)", "요구사항 명세서"), ("(SDLC)", ""),
    ("평가(LLM-as-a-Judge)할 때", "평가할 때"), ("LLM-as-a-Judge", "LLM 심판관 평가"), ("(Context Bleeding)", ""),
    ("아첨 (sycophancy) 경향", "아첨 경향"), ("(drift)", ""), ("단발성(single-turn)", "단발성"), ("순위형(ordinal)", "순위형"),
    ("자가 치유(self-healing, 자가 적응 시스템의 MAPE-K 루프)", "자가 치유(자가 적응 시스템의 MAPE-K 루프)"),
    ("외부 문서(RAG)의", "외부 문서의"), ("검색 증강 생성(RAG)으로", "검색 증강 생성으로"),
    ("완전 방어(FULL_DEFENSE)에", "완전 방어에"), ("절대 보안 원칙(Meta-Rule)을", "절대 보안 원칙(보강 규칙)을"),
    ("최우선(Meta-Rule)으로", "최우선 보강 규칙으로"),
    ("블랙박스 (Black-box)", "블랙박스"), ("화이트박스 (White-box)", "화이트박스"),
    ("완전 방어 (Full Defense)", "완전 방어"), ("기능적 방어 (Functional Defense)", "기능적 방어"),
    ("부분 노출 (Partial Exposure)", "부분 노출"), ("침해 (Breach)", "침해"),
    ("수렴한 명세서(v_final)에 대해", "수렴한 최종 응대 정책에 대해"),
    ("최종 응대 정책 v_final로 삼는다", "최종 응대 정책으로 삼는다"), ("v_final 응대 정책", "최종 응대 정책"),
    ("(v_final, 4단계)", "(최종 버전, 4단계)"), ("v_final이", "최종 버전이"), ("v_final의", "최종 버전의"),
    ("주 모델(anthropic)로", "주 모델로"), ("(claude-sonnet-5)", ""), ("(gpt-5.4-2026-03-05)", ""),
    # OWASP
    ("OWASP Top 10 for LLM Applications 2026의", "OWASP LLM 애플리케이션 10대 위협(2026년판)의"),
    ("OWASP LLM Top 10", "OWASP LLM 10대 위협"), ("OWASP Risk Rating Methodology와", "OWASP 위험 평가 방법론과"),
    ("LLM01(Prompt Injection)", "LLM01(프롬프트 인젝션)"), ("LLM02(Sensitive Information Disclosure)", "LLM02(민감 정보 노출)"),
    ("LLM07(System Prompt Leakage)", "LLM07(시스템 프롬프트 유출)"),
    ("LLM08(Vector and Embedding Weaknesses)", "LLM08(벡터·임베딩 취약점)"), ("LLM09(Misinformation)", "LLM09(잘못된 정보)"),
    ("LLM04(Data and Model Poisoning)", "LLM04(데이터·모델 오염)"),
    # information disorder types
    ("Dis-/Mis-/Malinformation", "허위조작정보·오정보·악의정보"), ("Dis·Mis·Malinformation", "허위조작정보·오정보·악의정보"),
    ("의도 없는 오류(Misinformation), 의도적 조작(Disinformation), 사실이지만 해악을 끼치는 정보(Malinformation)",
     "의도 없는 오류인 오정보, 의도적 조작인 허위조작정보, 사실이지만 해악을 끼치는 악의정보"),
    ("Misinformation", "오정보"), ("Disinformation", "허위조작정보"), ("Malinformation", "악의정보"),
    # two-axis labels
    ("정보 무결성은 INTACT, PARTIAL, BROKEN 중 하나", "정보 무결성은 유지, 부분 훼손, 훼손 중 하나"),
    ("(INTACT이면 없음)", "(유지이면 없음)"), ("정책 준수는 COMPLIANT, MINOR, MAJOR 중 하나", "정책 준수는 준수, 경미 위반, 중대 위반 중 하나"),
    ("정보 무결성은 BROKEN", "정보 무결성은 훼손"), ("정책 준수는 COMPLIANT이다", "정책 준수 판정은 준수이다"),
    ("정보 무결성 INTACT, 정책 준수 MINOR이다", "정보 무결성 유지, 정책 준수 판정은 경미 위반이다"),
    ("허위·유출(BROKEN)", "허위·유출(훼손)"), ("간접 정보(PARTIAL)", "간접 정보(부분 훼손)"),
    ("정보 무결성 INTACT, 정책 준수 COMPLIANT", "정보 무결성 유지, 정책 준수"),
    ("정보 무결성 INTACT, 정책 준수 MINOR 또는 MAJOR", "정보 무결성 유지, 정책 경미·중대 위반"),
    ("정보 무결성 PARTIAL", "정보 무결성 부분 훼손"), ("정보 무결성 BROKEN", "정보 무결성 훼손"),
    ("BROKEN으로 판정한다", "훼손으로 판정한다"), ("(INTACT 비율", "(유지 비율"),
    # single-grade labels
    ("(FULL_DEFENSE·FUNCTIONAL_DEFENSE 또는 PASS)", "(완전 방어·기능적 방어 또는 통과)"),
    ("FULL_DEFENSE", "완전 방어"), ("FUNCTIONAL_DEFENSE", "기능적 방어"),
    ("WARNING(단일 형식 이탈)과 FAIL(", "경고(단일 형식 이탈)와 실패("),
    ("FAIL이", "실패가"), ("FAIL은", "실패는"), ("FAIL을", "실패를"), ("PASS", "통과"), ("WARNING", "경고"), ("FAIL", "실패"),
    # rounds and variants
    ("round_1과", "1라운드와"), ("5W1H 판단 원칙", "육하원칙 판단 원칙"), ("5W1H 가설", "육하원칙 가설"),
    ("5W1H 원칙", "육하원칙"), ("5W1H 변형", "육하원칙 변형"), ("5W1H 축", "육하원칙 축"),
    ("5w1h(11차)를", "육하원칙형(11차)을"), ("5w1h가", "육하원칙형이"), ("5w1h", "육하원칙형"), ("baseline", "기준형"),
    ("요청을 Who, What, When, Why, How 다섯 축으로", "요청을 누가, 무엇을, 언제, 왜, 어떻게의 다섯 축으로"),
    ("Who·When·Why가 아무리 그럴듯해도 What(요구 내용)의 금지 여부를", "요청의 주체·시점·이유가 아무리 그럴듯해도 요구 내용 자체의 금지 여부를"),
    ("Who·When·Why 축", "누가·언제·왜 축"), ("특히 Who 축은", "특히 누가 축은"), ("What 축은", "무엇을 축은"),
    ("held_out", "헬드아웃"),
    # statistics
    ("Mann-Whitney U", "맨-휘트니 U"), ("Mann-Whitney", "맨-휘트니"), ("Wilcoxon", "윌콕슨"), ("Friedman", "프리드먼"),
    ("Cochran's Q", "코크런 Q"), ("p-value와는", "p값과는"),
    # vendors and misc
    ("openai 100%, anthropic 22.7%", "오픈AI 100%, 앤트로픽 22.7%"), ("anthropic 백엔드", "앤트로픽 백엔드"),
    ("B2B 엔터프라이즈 시장", "기업 간 거래 시장"), ("temperature를 고정한다", "온도 설정값을 고정한다"),
    ("유닛 C temperature 0.2", "유닛 C 온도 설정 0.2"), ("worst-case", "최악 조건"), ("심판관 rubric", "심판관 채점 기준"),
    ("output 토큰", "출력 토큰"), ("Base64나 hex로", "Base64나 16진수로"),
    ("Meta-Rule", "보강 규칙"), ("4단계 Level", "4단계 등급"),
]
TABLE_CELL = {"openai": "오픈AI", "gemini": "구글", "anthropic": "앤트로픽", "Level": "등급"}


def korean_first(s: str) -> str:
    for old, new in RULES:
        s = s.replace(old, new)
    s = re.sub(r"round_(\d+)", r"\1라운드", s)
    s = s.replace(" et al.", " 등")
    return re.sub(r"\(\s*\)", "", s)


def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def style_of(p):
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def main(src, dst):
    d = docx.Document(src)
    figs = {}
    for name in os.listdir(FIG):
        if name.endswith(".png"):
            with open(os.path.join(FIG, name), "rb") as f:
                figs.setdefault(hashlib.md5(f.read()).hexdigest(), name)
    rel = os.path.relpath(FIG, os.path.dirname(os.path.abspath(dst)))
    out, in_toc, in_refs, n_par, seen_abstract = [], False, False, 0, 0
    for el in d.element.body:
        if el.tag == qn("w:tbl"):
            rows = [[txt(c) for c in r.findall(qn("w:tc"))] for r in el.findall(qn("w:tr"))]
            rows = [[TABLE_CELL.get(c, korean_first(c)).replace("|", "/") for c in r] for r in rows]
            out.append("| " + " | ".join(rows[0]) + " |")
            out.append("|" + "---|" * len(rows[0]))
            out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
            out.append("")
            continue
        if el.tag != qn("w:p"):
            continue
        t, st = txt(el), style_of(el)
        n_par += 1
        if t == "목차":
            in_toc = True
            continue
        if in_toc:
            if t == "초록":
                seen_abstract += 1
            if seen_abstract < 2:          # the TOC lists "초록" once; the second one is the abstract
                continue
            in_toc = False
        blips = list(el.iter(qn("a:blip")))
        for b in blips:
            blob = d.part.related_parts[b.get(qn("r:embed"))].blob
            name = figs.get(hashlib.md5(blob).hexdigest(), "그림")
            out.append(f"![]({rel}/{name})")
        if not t.strip():
            continue
        if st == "1" and t == "참고문헌":
            in_refs = True
            out += ["# 참고문헌", ""]
            continue
        if n_par <= 2:                       # titles: unchanged (pending advisor decision)
            out += [("# " if n_par == 1 else "### ") + t, ""]
            continue
        body = t if in_refs else korean_first(t)
        prefix = "# " if st == "1" else "## " if st == "2" else ""
        if not prefix and re.match(r"(표|그림) \d+\.", body.strip()):
            body = f"**{body.strip()}**"
        out += [prefix + body, ""]
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("saved", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
