# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v3.docx from v2 (v2 is read only).

1. Insert a new Chapter 2 (related work) and shift chapter numbers.
2. Merge "실험 설계" and "실험 결과" into one chapter, "제4장. 실험 설계 및 결과",
   with 4.1 (design) and 4.2 (results) as sections and the old sections as 4.x.y.
3. Update in-text section and table references, section 1.4, the static TOC,
   and the reference list (sorted by first author for author-year citation).
Kit rules applied to the new text: chapter overview paragraph, prior work written as
acknowledgement -> limitation -> this study, comparison table at the end of related work,
caption ends with a period, no translationese verbs.
"""
import sys
import re
import os
import copy
import docx
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual_v2.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v3.docx")
assert not os.path.exists(DST), "v3 already exists; do not overwrite"

d = docx.Document(SRC)
body = d.element.body
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def style_of(p):
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def set_text(p, new):
    """Put all text in the first run, drop the other runs (keeps pPr and first rPr)."""
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


def find_para(pred):
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


# ---------------------------------------------------------------- templates
heads = [p for p in paras() if style_of(p) in ("1", "2")]
T_H1 = copy.deepcopy(next(p for p in heads if txt(p).startswith("제5장")))
T_H2 = copy.deepcopy(next(p for p in heads if txt(p).startswith("5.1.")))
T_BODY = copy.deepcopy(find_para(lambda p: txt(p).startswith("고객 조직의 가이드라인을 단계별로")))
T_TCAP = copy.deepcopy(find_para(lambda p: txt(p).startswith("표 1. 유닛 A~D의 역할")))
T_TABLE = copy.deepcopy(body.findall(qn("w:tbl"))[0])


def h1(t):
    return set_text(copy.deepcopy(T_H1), t)


def h2(t):
    return set_text(copy.deepcopy(T_H2), t)


def h3(t):
    p = set_text(copy.deepcopy(T_H2), t)
    p.find(qn("w:pPr") + "/" + qn("w:pStyle")).set(qn("w:val"), "3")
    run = p.find(qn("w:r"))
    rpr = run.find(qn("w:rPr"))
    if rpr is None:
        rpr = run.makeelement(qn("w:rPr"), {}); run.insert(0, rpr)
    for ch in list(rpr):
        rpr.remove(ch)
    rpr.append(rpr.makeelement(qn("w:rFonts"), {qn("w:ascii"): "돋움체", qn("w:eastAsia"): "돋움체",
                                                qn("w:hAnsi"): "돋움체", qn("w:cs"): "돋움체"}))
    rpr.append(rpr.makeelement(qn("w:b"), {}))
    rpr.append(rpr.makeelement(qn("w:bCs"), {}))
    rpr.append(rpr.makeelement(qn("w:color"), {qn("w:val"): "000000"}))
    rpr.append(rpr.makeelement(qn("w:sz"), {qn("w:val"): "23"}))
    rpr.append(rpr.makeelement(qn("w:szCs"), {qn("w:val"): "23"}))
    return p


def h2_from_h1(p_h1, t):
    """Turn a chapter heading into a section heading (no page break)."""
    new = h2(t)
    p_h1.addprevious(new)
    body.remove(p_h1)
    return new


def bodyp(t):
    return set_text(copy.deepcopy(T_BODY), t)


def table(header, rows, widths):
    tbl = copy.deepcopy(T_TABLE)
    grid = tbl.find(qn("w:tblGrid"))
    for g in list(grid):
        grid.remove(g)
    for w in widths:
        gc = grid.makeelement(qn("w:gridCol"), {qn("w:w"): str(w)})
        grid.append(gc)
    trs = tbl.findall(qn("w:tr"))
    head_tr, body_tr = trs[0], trs[1]
    for tr in trs:
        tbl.remove(tr)

    def make_row(tpl_tr, cells):
        tr = copy.deepcopy(tpl_tr)
        tcs = tr.findall(qn("w:tc"))
        for tc in tcs[1:]:
            tr.remove(tc)
        tc0 = tcs[0]
        tr.remove(tc0)
        for text, w in zip(cells, widths):
            tc = copy.deepcopy(tc0)
            tc.find(qn("w:tcPr") + "/" + qn("w:tcW")).set(qn("w:w"), str(w))
            p = tc.find(qn("w:p"))
            set_text(p, text)
            tr.append(tc)
        return tr

    tbl.append(make_row(head_tr, header))
    for r in rows:
        tbl.append(make_row(body_tr, r))
    return tbl


# ---------------------------------------------------------------- 1) renumber existing headings
moved = {}  # old section number -> new
for p in heads:
    t = txt(p)
    if t.startswith("제2장."):
        set_text(p, t.replace("제2장.", "제3장.", 1))
    elif style_of(p) == "2" and re.match(r"2\.\d+\. ", t):
        n = re.match(r"2\.(\d+)\. ", t).group(1)
        set_text(p, re.sub(r"^2\.", "3.", t)); moved[f"2.{n}"] = f"3.{n}"
    elif t.startswith("제3장. 실험 설계"):
        set_text(p, "제4장. 실험 설계 및 결과")
        ch4 = p
    elif style_of(p) == "2" and re.match(r"3\.\d+\. ", t):
        n = re.match(r"3\.(\d+)\. ", t).group(1)
        new = h3(f"4.1.{n}. " + t.split(". ", 1)[1]); p.addprevious(new); body.remove(p)
        moved[f"3.{n}"] = f"4.1.{n}"
    elif t.startswith("제4장. 실험 결과"):
        res = h2_from_h1(p, "4.2. 실험 결과")
    elif style_of(p) == "2" and re.match(r"4\.\d+\. ", t):
        n = re.match(r"4\.(\d+)\. ", t).group(1)
        new = h3(f"4.2.{n}. " + t.split(". ", 1)[1]); p.addprevious(new); body.remove(p)
        moved[f"4.{n}"] = f"4.2.{n}"
print("section map:", moved)

# chapter 4 overview + 4.1 heading
ov4 = bodyp("이 장에서는 제안 메커니즘을 검증한 실험의 설계와 결과를 함께 다룬다. 먼저 4.1절에서 실험 환경과 데이터 구성, "
            "사용 모델과 평가 절차, 통계 검정 방법, 심판관 신뢰성과 교차 모델 검증의 설계를 기술한다. 이어서 4.2절에서 "
            "자가 치유 성능, 정보 불일치성 유형별 방어 결과, 교차 모델 검증, 5W1H 판단 원칙의 가설 검증, 적응형 재공격의 "
            "결과를 차례로 제시한다.")
ch4.addnext(ov4)
ov4.addnext(h2("4.1. 실험 설계"))

# ---------------------------------------------------------------- 2) old in-text references
SEC = {"2.5절": "3.5절", "4.5절": "4.2.5절", "2.4절": "3.4절", "2.1절": "3.1절"}
for p in paras():
    if style_of(p) in ("1", "2", "3"):
        continue
    t = txt(p)
    for old, new in SEC.items():
        if old in t:
            replace_in(p, old, new)
            t = txt(p)
# table numbers shift by one (new 표 1 is inserted in chapter 2)
for t in body.iter(qn("w:t")):
    if t.text and re.search(r"표 \d+", t.text):
        t.text = re.sub(r"표 (\d+)", lambda m: f"표 {int(m.group(1)) + 1}", t.text)

# Korean particles after "표/그림 N" must follow the final sound of the number
JONG = set("013678")   # 영 일 삼 육 칠 팔 end in a consonant
PAIRS = [("과", "와"), ("은", "는"), ("이", "가"), ("을", "를")]


def fix_particle(m):
    num, part = m.group(2), m.group(3)
    has_final = num[-1] in JONG
    for with_final, without in PAIRS:
        if part in (with_final, without):
            part = with_final if has_final else without
    return f"{m.group(1)} {num}{part}"


for t in body.iter(qn("w:t")):
    if t.text:
        t.text = re.sub(r"(표|그림) (\d+)(과|와|은|는|이|가|을|를)(?=[ ,.)])", fix_particle, t.text)

# section 1.4
p14 = find_para(lambda p: txt(p).startswith("본 요약본은 학위논문 전문의 핵심 그림을"))
set_text(p14, "본 요약본은 학위논문 전문의 핵심 그림을 중심으로 내용을 재구성한 것이며, 상세한 근거와 수치는 전문의 해당 절을 "
         "참조한다. 이하 '전문'은 학위논문 전체 원고를 가리킨다. 제2장에서는 LLM 커스터마이징과 가드레일, LLM-as-a-Judge, "
         "자동화된 레드티밍과 자가 치유 프레임워크, 정보 무질서 프레임워크에 관한 선행연구를 검토하고 본 연구와 비교한다. "
         "제3장에서는 제안하는 자가 치유 메커니즘의 전체 프레임워크, 유닛 아키텍처, 5단계 절차, 공격 분류체계, 4단계 보안 "
         "심각도 체계를 설명한다. 제4장에서는 실험 설계(실험 환경, 사용 모델, 평가 지표와 통계 검정, 심판관 신뢰성과 교차 "
         "모델 검증)와 실험 결과(자가 치유 성능, 유형별 방어 결과, 교차 모델 검증, 5W1H 가설 검증, 적응형 재공격)를 함께 "
         "제시한다. 제5장에서는 결과를 논의하고 한계와 향후 연구 방향을 정리하며 결론을 맺는다.")

# ---------------------------------------------------------------- 3) new chapter 2
anchor = find_para(lambda p: style_of(p) == "1" and txt(p).startswith("제3장."))
new = [
    h1("제2장. 관련 연구"),
    bodyp("이 장에서는 본 연구와 관련된 선행연구를 네 갈래로 나누어 검토한다. 먼저 LLM 커스터마이징과 가드레일 기법을, "
          "다음으로 LLM을 평가자로 쓰는 LLM-as-a-Judge와 심판관의 신뢰성 문제를 살펴본다. 이어서 자동화된 레드티밍과 "
          "자가 치유 프레임워크를, 마지막으로 본 연구의 이론적 기반인 정보 무질서 프레임워크를 다룬다. 각 절은 선행연구의 "
          "기여, 남은 한계, 본 연구와의 관계 순서로 서술하며, 장의 끝에서 주요 선행연구를 표로 비교한다."),
    h2("2.1. LLM 커스터마이징과 가드레일"),
    bodyp("LLM을 특정 도메인에 맞추는 기법은 모델 가중치를 조정하는 파인튜닝 계열과, 프롬프트와 검색 증강 생성(RAG)으로 "
          "동작을 제어하는 프롬프트 계열로 나뉜다. 파인튜닝은 어투와 형식을 안정적으로 고정할 수 있고, 프롬프트 계열은 "
          "재학습 없이 가볍게 적용할 수 있다. 업계에는 입력과 출력에 필터 계층을 두는 가드레일 프레임워크도 정착해 있으며, "
          "NeMo Guardrails(Rebedea et al., 2023)는 프로그래밍 가능한 규칙으로 LLM 응용의 입력과 출력을 통제하는 대표적인 "
          "도구이다."),
    bodyp("그러나 파인튜닝은 요구사항이 바뀔 때마다 재학습 비용이 들고, 프롬프트 계열은 복잡한 지시나 역할 연기 요구가 "
          "이어지면 기존 제약을 잊는 지시 망각 현상이 보고된다. 가드레일 도구 역시 규칙을 사람이 정적으로 작성하고 유지해야 "
          "하므로, 새로운 공격 유형이 나타날 때마다 사람이 규칙을 다시 써야 한다."),
    bodyp("따라서 본 연구는 입력 검증, 추론, 출력 검증으로 이어지는 파이프라인의 형태 자체는 기존 가드레일과 같다는 점을 "
          "인정하고, 그 규칙을 적대적 시나리오의 실행 결과로부터 자동으로 생성해 명세서에 삽입하는 절차에 기여의 초점을 "
          "둔다. 이는 프롬프트를 요구공학부터 진화까지 소프트웨어 생명주기 전 단계를 거치는 산출물로 다루자는 Promptware "
          "Engineering(Chen et al., 2025)의 제안과 같은 방향이다. 본 연구는 요구공학 단계를 SRS로, 테스트 단계를 적대적 "
          "레드티밍과 Action Matrix로, 진화 단계를 Meta-Rule 자동 생성 루프로 구체화한 사례에 해당한다."),
    h2("2.2. LLM-as-a-Judge와 심판관 신뢰성"),
    bodyp("LLM을 평가자로 쓰는 방식은 대량의 응답을 일관된 기준으로 채점할 수 있어 널리 쓰인다. FaithJudge(Tamber et al., "
          "2025)는 사람이 주석한 환각 사례를 심판관 프롬프트에 함께 제공해, RAG 응답의 충실성 판정에서 심판관과 사람의 "
          "일치도를 높였다. 응답의 정보 무결성을 LLM 심판관으로 판정한다는 점에서 본 연구와 가장 가까운 선행연구이다."),
    bodyp("그러나 심판관 LLM 자체도 프롬프트 인젝션의 대상이 되어 채점 신뢰성을 잃을 수 있으며(Shi et al., 2024), 챗봇과 "
          "심판관이 같은 세션을 공유하면 이전 대화가 채점에 영향을 주는 컨텍스트 오염이 생긴다. 또한 FaithJudge는 RAG "
          "충실성이라는 단일 축을 다루므로 페르소나 이탈이나 정보 유출 같은 보안 경계 위반은 판정 범위 밖이다."),
    bodyp("따라서 본 연구는 매 채점을 새 세션으로 수행하는 무상태 심판관을 쓰고, 정보 무결성과 보안 경계를 함께 판정하는 "
          "Action Matrix를 채점 기준으로 둔다. 다만 FaithJudge와 달리 본 연구의 심판관은 사람의 주석으로 신뢰도를 검증받지 "
          "않았으며, 이 점은 4.1.4절의 교차 심판관 재검증과 5.2절의 한계에서 다룬다."),
    h2("2.3. 자동화된 레드티밍과 자가 치유 프레임워크"),
    bodyp("공격 문장을 자동으로 생성해 시스템의 한계를 시험하는 자동화된 레드티밍은 PIArena(Geng et al., 2026)와 같은 "
          "통합 평가 플랫폼으로 발전하였다. 방어 측에서도 실패를 탐지하면 방어 규칙이나 프롬프트를 자동으로 고치는 폐쇄 "
          "루프가 여러 연구에서 제안되었다. SHIELD(Sivaroopan et al., 2026)는 방어가 실패하면 방어 지시문을 자동으로 개정하는 "
          "루프로 리소스 고갈 공격을 막고, PRISM(Chaitanya & Gundakaram, 2026)은 테스트 생성, LLM 심판관 평가, 실패 진단, "
          "프롬프트 수정, 재평가로 이어지는 루프로 모델 동작 변화에 따른 회귀를 수리한다. SISF(Slater, 2025)는 자율 컴퓨팅의 "
          "MAPE-K 참조 모델을 바탕으로, 판정 모듈이 위반을 탐지하면 새 방어 정책을 합성하는 구조를 제시한다. 공격과 방어를 "
          "함께 다룬 연구로는 오도하는 키워드가 LLM의 사실 진술을 얼마나 흔드는지 측정하고 네 가지 완화 전략을 평가한 Chaos "
          "with Keywords(Aswin RRV et al., 2024)가 있다."),
    bodyp("그러나 이들 연구는 각각 가용성 위협(SHIELD), 일반 기능 회귀(PRISM), 일반 안전성 위반의 이론적 구조(SISF), 단일 "
          "실패 모드(Chaos with Keywords)를 다루며, 조직별 가이드라인 준수라는 보안 도메인의 공격 분류체계와 실제 운영 "
          "도메인에서의 실증은 제시하지 않았다. PIArena는 공격과 방어를 평가하는 플랫폼이며, 방어를 스스로 고치는 절차는 "
          "포함하지 않는다."),
    bodyp("따라서 실패를 탐지하고 방어 규칙을 생성해 병합한 뒤 재평가하는 루프의 골격 자체는 본 연구가 처음 고안한 것이 "
          "아니다. 본 연구의 기여는 그 골격을 구성하는 구체적인 설계의 조합, 즉 자연어 Meta-Rule을 헤더와 푸터에 이중 "
          "삽입하는 형식, OWASP LLM Top 10에 매핑한 8개 공격 분류체계, 응답 생성 모델만 바꾸고 채점 모델은 고정하는 교차 "
          "모델 검증, 5W1H 축 태깅에 있다. 또한 이를 실제 운영 도메인에 적용해 선행연구가 보고하지 않은 실패 양상, 즉 "
          "명세서의 문자열 템플릿화, 라운드 진동, 모델 동작 변화로 인한 재현성 위협을 함께 보고한다."),
    h2("2.4. 정보 무질서 프레임워크"),
    bodyp("Wardle과 Derakhshan(2017)은 정보 무질서를 의도 없는 오류(Misinformation), 의도적 조작(Disinformation), 사실이지만 "
          "해악을 끼치는 정보(Malinformation)의 세 유형으로 나누고, 정보의 생성, 제작, 유통 단계와 행위자, 메시지, 해석자로 "
          "구성된 분석틀을 제시하였다."),
    bodyp("그러나 이 프레임워크는 정치·사회적 허위정보가 대중을 향해 확산되는 상황을 전제하므로, 고객과 챗봇이 1:1로 대화하는 "
          "상담 세션에는 그대로 적용하기 어렵다."),
    bodyp("따라서 본 연구는 3분류를 이론적 기반으로 삼되, 조직 챗봇의 1:1 세션에서 발생하는 응답 오류로 대상을 옮겨 정보 "
          "불일치성(Information Disorderness)으로 재정의한다. 또한 8개 공격 유형 전부를 3분류에 대응시키지 않고, 직접 대응하는 "
          "4개(관리자 사칭, 허위 사실 동조, 메타데이터 유출, 개인정보 유출)만 핵심 실증 대상으로 삼는다(3.4절). 다만 3분류는 "
          "채점의 축이 아니라 공격 유형을 묶어 해석하는 틀로 쓰이며, 위반의 의도성과 해악성을 채점에 반영하는 것은 후속 "
          "과제로 남긴다."),
    h2("2.5. 선행연구 비교"),
    bodyp("표 1은 본 연구와 자가 치유 루프를 갖는 주요 선행연구를 목적, 방어 대상, 자가 치유 여부, 재학습 필요 여부, 일반화 "
          "검증, 실험 도메인을 기준으로 비교한 것이다. PRISM과 SISF는 원문 전체를 확인하지 못해 일부 항목을 미상으로 "
          "표기하였으며, 미상 항목은 본 연구의 우위 근거로 쓰지 않는다."),
    set_text(copy.deepcopy(T_TCAP), "표 1. 선행연구 비교."),
    table(["비교 항목", "본 연구", "PIArena", "SHIELD", "PRISM", "SISF"],
          [["목적", "조직 가이드라인 준수 자가 치유", "프롬프트 인젝션 공격·방어 평가", "리소스 고갈 공격 방어",
            "프롬프트 신뢰성 유지", "런타임 안전성 자기 개선"],
           ["방어 대상", "사칭, 정보 유출 등 8개 공격 유형", "범용 프롬프트 인젝션", "리소스 고갈(Sponge) 공격",
            "기능 회귀", "일반 안전성 위반"],
           ["자가 치유", "O (Meta-Rule 생성·병합)", "X", "O (방어 지시문 개정)", "O (프롬프트 수정)", "O (정책 합성)"],
           ["재학습", "불필요", "해당 없음", "불필요", "불필요", "불필요"],
           ["일반화·적응형 공격 검증", "O (헬드아웃, 적응형 재공격)", "O", "미확인", "미상", "미상"],
           ["실험 도메인", "실제 운영 가전 유통 챗봇 1개", "다중 벤치마크", "다중 공격 유형", "엔터프라이즈 대화형 에이전트",
            "미상"]],
          [1300, 1650, 1450, 1450, 1450, 1400]),
]
for el in new:
    anchor.addprevious(el)
# keep the spacing paragraph that follows tables elsewhere
anchor.addprevious(copy.deepcopy(body.findall(qn("w:tbl"))[1].getnext()))

# ---------------------------------------------------------------- 4) references (author-year, sorted by first author)
ref_head = find_para(lambda p: style_of(p) == "1" and txt(p) == "참고문헌")
old_refs, p = [], ref_head.getnext()
while p is not None and p.tag == qn("w:p") and re.match(r"\d+\. ", txt(p)):
    old_refs.append(p); p = p.getnext()
entries = [re.sub(r"^\d+\. ", "", txt(r)) for r in old_refs]
entries += [
    "Rebedea, Dinu, Sreedhar, Parisien, & Cohen (2023). NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails. Proceedings of EMNLP 2023: System Demonstrations. arXiv:2310.10501.",
    "Chen, Wang, Sun, Liu, Zhang, & Liu (2025). Promptware Engineering: Software Engineering for Prompt-Enabled Systems. arXiv:2503.02400.",
    "Tamber, M. S., Bao, F. S., Xu, C., Luo, G., Kazi, S., Bae, M., Li, M., Mendelevitch, O., Qu, R., & Lin, J. (2025). Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards. Proceedings of EMNLP 2025 (Industry Track). arXiv:2505.04847.",
    "Sivaroopan, N., Thilakarathna, K., Zomaya, A., et al. (2026). SHIELD: An Auto-Healing Agentic Defense Framework for LLM Resource Exhaustion Attacks. arXiv:2601.19174.",
    "Chaitanya, & Gundakaram (2026). PRISM: Prompt Reliability via Iterative Simulation and Monitoring for Enterprise Conversational AI. arXiv:2605.15665.",
    "Slater, T. (2025). A Self-Improving Architecture for Dynamic Safety in Large Language Models. arXiv:2511.07645.",
    "Aswin RRV, Tyagi, N., Uddin, M. N., Varshney, N., & Baral, C. (2024). Chaos with Keywords: Exposing Large Language Models' Sycophantic Hallucination to Misleading Keywords and Evaluating Defense Strategies. Findings of the Association for Computational Linguistics: ACL 2024. arXiv:2406.03827.",
]
entries.sort(key=lambda s: s.lower())
tpl_ref = old_refs[0]
for r in old_refs:
    body.remove(r)
prev = ref_head
for i, e in enumerate(entries, 1):
    np_ = set_text(copy.deepcopy(tpl_ref), f"{i}. {e}")
    prev.addnext(np_); prev = np_
print("references:", len(entries))

# ---------------------------------------------------------------- 5) static TOC
toc_head = find_para(lambda p: txt(p) == "목차")
toc_items, p = [], toc_head.getnext()
while p is not None and not (style_of(p) == "1" or txt(p) == "초록" and p is not toc_head.getnext()):
    if txt(p).strip():
        toc_items.append(p)
    p = p.getnext()
first = toc_items[0]                               # "초록"
lvl1 = next(x for x in toc_items if txt(x).startswith("제1장"))
lvl2 = next(x for x in toc_items if txt(x).startswith("1.1."))
T1, T2 = copy.deepcopy(lvl1), copy.deepcopy(lvl2)
for x in toc_items[1:]:
    body.remove(x)
prev = first
for p in paras():
    s, t = style_of(p), txt(p)
    if s == "1" and (t.startswith("제") or t == "참고문헌"):
        e = set_text(copy.deepcopy(T1), t)
    elif s == "2" and re.match(r"\d+\.\d+\. ", t):
        e = set_text(copy.deepcopy(T2), t)
    elif s == "3":
        e = set_text(copy.deepcopy(T2), t)
        ppr = e.find(qn("w:pPr"))
        ind = ppr.find(qn("w:ind"))
        if ind is None:
            ind = ppr.makeelement(qn("w:ind"), {}); ppr.append(ind)
        ind.set(qn("w:left"), "1000")
        for sz in e.iter(qn("w:sz")):
            sz.set(qn("w:val"), "20")
    else:
        continue
    prev.addnext(e); prev = e

d.save(DST)
print("saved", DST)
