# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v7.docx (interim thesis for the advisor) from v6 (v6 is read only).

Redesign of 2026-10-12 (docs/related_work_review_20261012.md, CLAUDE.md):
  - abstract, 1.2, 1.3, 1.4 rewritten around contributions ①-⑤
  - chapter 2 rebuilt: 2.1-2.6, new Table 1, eight added references (DOI unverified)
  - chapter 3: nine categories (RAG poisoning), template items, two-axis judging + code checks (3.5)
  - chapter 4: pilot experiments (4.1-4.4, 4.4 merges 5W1H and adaptive re-attack), re-analysis on the
    information-integrity axis (4.2), main experiment design with Table 10 (4.5)
  - chapter 5 and references updated; figures 2, 4, 5, 6, 7, 13, 14, 16 replaced by *_v7.png
"""
import copy
import hashlib
import os
import sys

import docx
from docx.oxml.ns import qn
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual_v6.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v7.docx")
FIG = os.path.join(ROOT, "diagrams", "summary_v2")
assert not os.path.exists(DST), "v7 already exists; do not overwrite"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

d = docx.Document(SRC)
body = d.element.body


# ---------------------------------------------------------------- helpers
def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def style_of(p):
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def paras():
    return [e for e in body if e.tag == qn("w:p")]


def one(pred, where=None):
    hits = [p for p in (where or paras()) if pred(p)]
    assert len(hits) == 1, (len(hits), [txt(h)[:30] for h in hits])
    return hits[0]


def starts(prefix, style=None):
    return one(lambda p: txt(p).startswith(prefix) and (style is None or style_of(p) == style))


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


def replace_in(p, old, new):
    ts = list(p.iter(qn("w:t")))
    full = "".join(t.text or "" for t in ts)
    pos = full.find(old)
    assert pos >= 0, old[:40]
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


def edit(old, new):
    replace_in(one(lambda p: old in txt(p)), old, new)


def cell_set(cell_el, text):
    set_text(cell_el.find(qn("w:p")), text)


# templates
T_H2 = copy.deepcopy(starts("2.1. LLM 커스터마이징과 가드레일", "2"))
T_BODY = copy.deepcopy(starts("LLM을 특정 도메인에 맞추는 기법은"))
T_CAP = copy.deepcopy(starts("표 1. 선행연구 비교."))
T_EMPTY = copy.deepcopy(starts("표 1. 선행연구 비교.").getnext().getnext())
assert T_EMPTY.tag == qn("w:p") and txt(T_EMPTY) == ""


def h2(t):
    return set_text(copy.deepcopy(T_H2), t)


def para(t):
    return set_text(copy.deepcopy(T_BODY), t)


def cap(t):
    return set_text(copy.deepcopy(T_CAP), t)


def insert_before(anchor, elements):
    for el in elements:
        anchor.addprevious(el)


# ---------------------------------------------------------------- abstract
set_text(starts("본 논문은 정보 불일치성에 저항하는 응대 정책 명세 기반 강건화"),
    "본 논문은 정보 불일치성에 대한 응대 정책 명세 기반 강건화(Hardening) 메커니즘을 제안한다. 제안 메커니즘은 입력 "
    "가드레일, RAG 검색, LLM 추론, 출력 가드레일로 이어지는 4단계 유닛 아키텍처 위에서, 적대적 공격 생성, 무상태 심판관 "
    "채점, Meta-Rule 자동 생성, 응대 정책 갱신을 반복하는 폐쇄 루프로 구성된다. 공격은 9개 범주로 분류하고 이 중 정보 "
    "불일치성 3분류에 직접 대응하는 5개를 핵심 실증 대상으로 삼으며, 제품 설명서의 사실로 만든 허위 전제 질문과 RAG 오염 "
    "문항을 포함한다. 채점은 정보 무결성과 응대 정책 준수의 두 축으로 분리하고, 정답이 있는 항목은 개인정보, 정책 원문, "
    "허위 값의 코드 대조로 판정하여 심판관 판정과 함께 기록한다.")
set_text(starts("카테고리당 3개 규모의 예비 파일럿에서 라운드 상한을 15로 둔"),
    "카테고리당 3개 규모의 예비 실험(7~13차)에서 단일 등급 기준의 준수율은 9차 실험에서 14라운드 만에 68.2%에서 100%로 "
    "올랐고 헬드아웃 셋에서도 97.1%를 기록하였다. 그러나 같은 실행을 정보 무결성 기준으로 다시 보면 초기 응대 정책에서도 "
    "22건 중 21건이 이미 정보 측면에서는 방어되어 있었고, 개선의 대부분은 응대 형식의 교정이었다. 이는 자동 보강 루프의 "
    "성과를 단일 지표로 보고하면 무엇이 개선되었는지가 가려진다는 것을 보여 준다. 본 논문은 이 발견을 바탕으로 측정 체계를 "
    "재설계하고, 정보 무결성의 개선(H1), 헬드아웃 셋에서의 비열등성(H2), 응답 생성 모델 교체에 따른 차이(H3)를 검증하는 "
    "본 실험을 설계하였다. 본 연구는 단일 도메인 사례 연구이므로 결과의 일반화에는 주의가 필요하다.")
set_text(starts("주제어:"),
    "주제어: 정보 불일치성, 강건화, 응대 정책 명세, 정보 무결성, RAG 오염, LLM 챗봇, 교차 모델 검증")

# ---------------------------------------------------------------- chapter 1
edit("기존 방식의 한계는 다음 다섯 가지로 정리된다.", "기존 방식의 한계는 다음 여섯 가지로 정리된다.")
p12 = starts("기존 방식의 한계는 다음 여섯 가지로 정리된다.")
replace_in(p12, "메커니즘 자체의 효과인지 구분하기 어렵다.",
    "메커니즘 자체의 효과인지 구분하기 어렵다. 여섯째, 실패 사례로 프롬프트를 자동 보강하는 기존 접근은 개선을 하나의 "
    "통과율로 보고하는 경우가 많아, 개선이 정보의 진위와 기밀 측면에서 일어났는지 응답 형식에서 일어났는지 구분하기 어렵다.")

set_text(starts("첫째, Wardle과 Derakhshan의 프레임워크를 이론적 뿌리로 삼아"),
    "첫째, 측정 타당도이다. 응답을 정보 무결성과 응대 정책 준수의 두 축으로 나누어 채점하고, 정답이 있는 항목은 코드 대조로 "
    "판정해 심판관과의 일치도를 함께 보고하는 측정 체계를 제안한다. 예비 실험의 재분석은 단일 등급 준수율의 개선이 실제로는 "
    "형식 교정이었음을 보여, 이 분리가 왜 필요한지를 실측으로 뒷받침한다. 둘째, 응대 정책 수준의 정보 무결성 강건화이다. 제품 "
    "설명서의 사실로 만든 허위 전제 질문과 RAG 오염 문항을 포함한 공격에 대해, 검색 단계가 아니라 추론 시점의 응대 정책을 "
    "적대적 테스트로 자동 보강하고, 헬드아웃 셋과 적응형 재공격으로 일반화를 검증한다. 셋째, 고객사의 요구사항을 응대 정책으로 "
    "명세하고 테스트로 검증·보강하는 요구사항 추적 흐름을 실제 운영 중인 가전 유통 챗봇에 적용한다. 넷째, 규칙 누적이 응대 "
    "정책의 문자열 템플릿화, 라운드 간 진동, 모델 동작 변화로 인한 재현성 위협을 낳는다는 부작용을 실측으로 보고한다. 다섯째, "
    "응답 생성 모델만 바꾸고 채점 모델은 고정하는 교차 모델 검증으로 결과의 모델 종속성을 점검한다. 4단계 유닛 아키텍처 자체의 "
    "형태적 신규성은 기존 가드레일 파이프라인 패턴과 유사하여 제한적이며, 본 연구의 중심 주장은 첫째와 둘째에 있다.")

p14 = starts("본 요약본은 학위논문 전문의 핵심 그림을 중심으로")
t14 = txt(p14)
cut = t14.index("제2장에서는")
replace_in(p14, t14[cut:],
    "제2장에서는 행동 명세와 가드레일, 자동 프롬프트 최적화와 자동 보강 루프, 자동화된 레드티밍과 정보 무결성 공격, "
    "LLM-as-a-Judge와 측정 타당도, 정보 무질서 프레임워크에 관한 선행연구를 검토하고 본 연구가 다루는 빈틈을 정리한다. "
    "제3장에서는 제안하는 강건화 메커니즘의 전체 프레임워크, 유닛 아키텍처, 5단계 절차, 공격 분류체계, 두 축 채점과 정답 "
    "대조를 설명한다. 제4장에서는 예비 실험(7~13차)의 설계와 결과, 정보 무결성 기준의 재분석을 보고하고, 이를 바탕으로 한 본 "
    "실험의 설계를 제시한다. 제5장에서는 결과를 논의하고 한계와 향후 연구 방향을 정리한다.")

# ---------------------------------------------------------------- chapter 2 (rebuilt)
ch2 = starts("제2장. 관련 연구", "1")
ch3 = starts("제3장. 제안하는 강건화 메커니즘", "1")
table1 = None
el = ch2.getnext()
while el is not ch3:
    nxt = el.getnext()
    if el.tag == qn("w:tbl"):
        table1 = el
    body.remove(el)
    el = nxt
assert table1 is not None

T1 = [
    ["비교 항목", "본 연구", "ProTeGi·OPRO", "PRISM·SISF", "PoisonedRAG·RobustRAG", "FaithJudge"],
    ["연구 목표", "응대 정책의 정보 무결성 강건화", "과제 정확도 향상", "회귀 수리·런타임 안전성", "RAG 오염 공격·방어", "RAG 충실성 판정"],
    ["자동 보강 루프", "O (Meta-Rule 생성·병합)", "O (프롬프트 개정)", "O", "X", "X"],
    ["측정 축 분리", "O (정보 무결성·정책 준수)", "X (과제 지표 1개)", "미상", "해당 없음", "X (충실성 1개)"],
    ["정답 기반 판정", "부분 (코드 대조 + 심판관)", "O (정답 레이블)", "미상", "O (목표 답 일치)", "사람 주석"],
    ["정보 무결성 공격", "O (RAG 오염·허위 전제·유출·사칭)", "X", "미상", "O (RAG 오염)", "해당 없음"],
    ["일반화 검증", "O (헬드아웃·적응형·교차 모델)", "O (테스트 셋)", "미상", "O (다중 데이터셋·모델)", "해당 없음"],
    ["실험 도메인", "실제 운영 가전 유통 챗봇", "공개 벤치마크", "엔터프라이즈 에이전트·미상", "공개 질의응답 데이터셋", "RAG 벤치마크"],
]
rows = table1.findall(qn("w:tr"))
while len(rows) < len(T1):
    rows[-1].addnext(copy.deepcopy(rows[-1]))
    rows = table1.findall(qn("w:tr"))
for r, values in zip(rows, T1):
    for c, v in zip(r.findall(qn("w:tc")), values):
        cell_set(c, v)

CH2 = [
    para("이 장에서는 본 연구와 관련된 선행연구를 다섯 갈래로 나누어 검토한다. 각 절은 선행연구의 기여, 남은 한계, 본 연구와의 "
         "관계 순서로 서술하고, 2.6절에서 주요 선행연구를 표로 비교한 뒤 본 연구가 다루는 빈틈을 정리한다."),
    h2("2.1. LLM 커스터마이징, 가드레일, 행동 명세"),
    para("LLM을 특정 도메인에 맞추는 기법은 모델 가중치를 조정하는 파인튜닝 계열과, 프롬프트와 검색 증강 생성(RAG)으로 동작을 "
         "제어하는 프롬프트 계열로 나뉜다. 업계에는 입력과 출력에 필터 계층을 두는 가드레일 프레임워크도 정착해 있으며, NeMo "
         "Guardrails(Rebedea et al., 2023)는 프로그래밍 가능한 규칙으로 LLM 응용의 입력과 출력을 통제하는 대표적인 도구이다. "
         "한편 Constitutional AI(Bai et al., 2022)는 사람이 작성한 원칙 목록으로 모델의 행동을 규정하고 그 원칙에 따른 AI "
         "피드백으로 모델을 학습시켜, 행동 규범을 자연어 문서로 명세하는 접근의 선례를 보였다."),
    para("그러나 파인튜닝과 Constitutional AI는 규범을 학습 시점에 반영하므로 고객사마다 다른 응대 규범을 바꿀 때마다 재학습이 "
         "필요하다. 프롬프트 계열은 재학습 없이 적용할 수 있으나 복잡한 지시나 역할 연기 요구가 이어지면 기존 제약을 잊는 지시 "
         "망각 현상이 보고되며, 가드레일 도구는 규칙을 사람이 정적으로 작성하고 유지해야 하므로 새로운 공격 유형이 나타날 때마다 "
         "사람이 규칙을 다시 써야 한다."),
    para("따라서 본 연구는 입력 검증, 추론, 출력 검증으로 이어지는 파이프라인의 형태 자체는 기존 가드레일과 같다는 점을 인정하고, "
         "고객사의 요구사항을 추론 시점에 읽히는 자연어 응대 정책으로 명세한 뒤 그 정책을 적대적 테스트 결과로 자동 보강하는 "
         "절차에 초점을 둔다. 이는 프롬프트를 요구공학부터 진화까지 소프트웨어 생명주기 전 단계를 거치는 산출물로 다루자는 "
         "Promptware Engineering(Chen et al., 2025)의 제안과 같은 방향이며, 본 연구는 요구공학 단계를 응대 정책 명세로, 테스트 "
         "단계를 적대적 레드티밍과 두 축 채점으로, 진화 단계를 Meta-Rule 자동 생성 루프로 구체화한 사례에 해당한다."),
    h2("2.2. 자동 프롬프트 최적화와 자동 보강 루프"),
    para("실패 사례를 근거로 프롬프트를 자동으로 고치는 연구는 자동 프롬프트 최적화에서 출발하였다. ProTeGi(Pryzant et al., "
         "2023)는 학습 데이터에서 틀린 사례를 모아 LLM이 자연어 형태의 '기울기'로 프롬프트의 문제를 지적하게 하고 이를 반영한 "
         "후보를 빔 탐색으로 고르며, OPRO(Yang et al., 2024)는 이전 프롬프트와 점수의 이력을 LLM에 보여 주어 더 높은 점수의 "
         "프롬프트를 제안하게 한다. 보안과 신뢰성 분야에서도 같은 골격의 폐쇄 루프가 제안되었다. SHIELD(Sivaroopan et al., "
         "2026)는 방어가 실패하면 방어 지시문을 자동으로 개정해 리소스 고갈 공격을 막고, PRISM(Chaitanya & Gundakaram, 2026)은 "
         "테스트 생성, LLM 심판관 평가, 실패 진단, 프롬프트 수정, 재평가로 이어지는 루프로 모델 동작 변화에 따른 회귀를 수리하며, "
         "SISF(Slater, 2025)는 자율 컴퓨팅의 MAPE-K 참조 모델을 바탕으로 판정 모듈이 위반을 탐지하면 새 방어 정책을 합성한다."),
    para("그러나 자동 프롬프트 최적화는 정답이 있는 공개 과제의 정확도를 높이는 것이 목표이며 적대적 공격에 대한 강건성은 다루지 "
         "않는다. 보안 쪽 자동 보강 연구는 각각 가용성 위협(SHIELD), 일반 기능 회귀(PRISM), 일반 안전성 위반의 구조(SISF)를 "
         "대상으로 하며, 본 연구가 확인한 범위에서 개선은 하나의 통과율로 보고되어 그 개선이 정보의 진위와 기밀 측면에서 일어났는지 "
         "응답 형식에서 일어났는지 구분되지 않는다. PRISM과 SISF는 원문 전체를 확인하지 못하였으므로 이 판단은 확인 가능한 범위에 "
         "한정한다."),
    para("따라서 실패를 탐지하고 규칙을 생성해 병합한 뒤 재평가하는 루프의 골격 자체는 본 연구가 처음 고안한 것이 아니다. 본 "
         "연구는 이 골격을 그대로 쓰되, 개선의 내용을 정보 무결성과 응대 정책 준수로 분리해 측정한다는 점에서 차별화된다(빈틈 ①). "
         "예비 실험에서 단일 등급으로는 큰 개선으로 보였던 결과가 정보 무결성 기준으로는 형식 교정이었다는 4.2절의 재분석이 이 "
         "분리의 필요성을 보여 준다."),
    h2("2.3. 자동화된 레드티밍과 정보 무결성 공격"),
    para("LLM으로 공격 문장을 생성해 다른 LLM의 실패를 찾는 자동화된 레드티밍은 Perez et al.(2022)에서 체계화되었고, PIArena(Geng "
         "et al., 2026)와 같은 통합 평가 플랫폼으로 발전하였다. 정보 무결성을 겨냥한 공격으로는 외부 문서에 숨긴 지시로 LLM 통합 "
         "응용을 조종하는 간접 프롬프트 인젝션(Greshake et al., 2023), 지식 베이스에 소수의 허위 문서를 주입해 RAG의 응답을 "
         "공격자가 원하는 답으로 바꾸는 PoisonedRAG(Zou et al., 2025), 사용자의 믿음에 맞추어 사실과 다른 답을 하는 아첨 "
         "(sycophancy) 경향(Sharma et al., 2024), 오도하는 키워드에 사실 진술이 흔들리는 현상과 그 완화 전략을 다룬 Chaos with "
         "Keywords(Aswin RRV et al., 2024)가 보고되었다. 방어 측에서는 검색된 문서마다 따로 답하게 한 뒤 안전하게 집계하는 "
         "RobustRAG(Xiang et al., 2024)처럼 검색 단계에서 오염을 견디는 방법이 제안되었다."),
    para("그러나 이들 연구는 대부분 공격의 실현 가능성을 보이거나 검색 단계의 방어를 제안하는 데 초점을 두며, 조직이 정한 응대 정책 "
         "수준에서 이러한 공격을 막도록 정책을 자동으로 보강하고 그 효과가 처음 보는 문항에서도 유지되는지는 검증하지 않는다. "
         "또한 대부분 공개 질의응답 데이터셋에서 평가되어, 실제 운영 챗봇의 제품 정보와 고객 정보를 대상으로 한 실증은 드물다."),
    para("따라서 본 연구는 사칭, 허위 전제 동조, 내부 정보 유출, 개인정보 유출에 RAG 오염을 더한 다섯 범주를 정보 불일치성의 핵심 "
         "실증 대상으로 삼고, 허위 전제 질문과 RAG 오염 문항은 실제 제품 설명서의 사실로 만들어 정답을 알 수 있게 한다. 이 "
         "공격에 대해 추론 시점의 응대 정책을 자동 보강하고 헬드아웃 셋과 적응형 재공격으로 일반화를 검증한다(빈틈 ②). 검색 "
         "단계의 방어와는 경쟁 관계가 아니라 함께 쓸 수 있는 보완 관계이다."),
    h2("2.4. LLM-as-a-Judge와 측정 타당도"),
    para("LLM을 평가자로 쓰는 방식은 대량의 응답을 일관된 기준으로 채점할 수 있어 널리 쓰인다. Zheng et al.(2023)은 강한 LLM "
         "심판관이 사람 평가와 높은 일치도를 보이는 동시에 제시 순서, 장황함, 자기 응답 선호와 같은 편향을 가진다는 점을 보고하였다. "
         "FaithJudge(Tamber et al., 2025)는 사람이 주석한 환각 사례를 심판관 프롬프트에 함께 제공해 RAG 응답의 충실성 판정에서 "
         "심판관과 사람의 일치도를 높였다."),
    para("그러나 심판관 LLM 자체도 프롬프트 인젝션의 대상이 되어 채점 신뢰성을 잃을 수 있으며(Shi et al., 2024), 챗봇과 심판관이 "
         "같은 세션을 공유하면 이전 대화가 채점에 영향을 주는 컨텍스트 오염이 생긴다. 또한 FaithJudge는 충실성이라는 단일 축을 "
         "다루므로 기밀 유출이나 사칭 동조 같은 보안 경계 위반은 판정 범위 밖이며, 사람의 주석은 비용이 커서 매 라운드 반복되는 "
         "자동 보강 루프에 그대로 쓰기 어렵다."),
    para("따라서 본 연구는 매 채점을 새 세션으로 수행하는 무상태 심판관을 쓰고, 정보 무결성과 응대 정책 준수를 따로 판정하게 "
         "하며, 정답이 있는 항목은 코드 대조로 판정해 심판관과의 일치도를 보고한다(빈틈 ①). 응답 생성 모델만 바꾸고 심판관은 "
         "고정하는 교차 모델 검증은 동일 벤더 선호 편향의 영향을 점검하는 장치로도 쓰인다(빈틈 ⑤). 다만 연구자의 수동 블라인드 "
         "채점은 아직 수행하지 않았으며, 이는 5.2절의 한계에서 다룬다."),
    h2("2.5. 정보 무질서 프레임워크"),
    para("Wardle과 Derakhshan(2017)은 정보 무질서를 의도 없는 오류(Misinformation), 의도적 조작(Disinformation), 사실이지만 "
         "해악을 끼치는 정보(Malinformation)의 세 유형으로 나누고, 정보의 생성, 제작, 유통 단계와 행위자, 메시지, 해석자로 구성된 "
         "분석틀을 제시하였다."),
    para("그러나 이 프레임워크는 정치·사회적 허위정보가 대중을 향해 확산되는 상황을 전제하므로, 고객과 챗봇이 1:1로 대화하는 상담 "
         "세션에는 그대로 적용하기 어렵다."),
    para("따라서 본 연구는 3분류를 이론적 기반으로 삼되, 조직 챗봇의 1:1 세션에서 발생하는 응답 오류로 대상을 옮겨 정보 "
         "불일치성(Information Disorderness)으로 재정의한다. 9개 공격 유형 중 3분류에 직접 대응하는 5개(관리자 사칭, 허위 사실 "
         "동조, 메타데이터 유출, 개인정보 유출, RAG 오염)를 핵심 실증 대상으로 삼고(3.4절), 심판관은 정보 무결성의 실패를 판정할 "
         "때 그 유형(Dis·Mis·Malinformation)을 함께 태깅한다(3.5절). 다만 위반의 의도성과 해악의 크기를 정량화해 채점에 반영하는 "
         "것은 후속 과제로 남긴다."),
    h2("2.6. 선행연구 비교와 본 연구의 빈틈"),
    para("표 1은 대표 선행연구를 연구 목표, 자동 보강 루프, 측정 축의 분리, 정답 기반 판정, 정보 무결성 공격, 일반화 검증, 실험 "
         "도메인의 일곱 항목으로 비교한 것이다. 원문 전체를 확인하지 못한 항목은 미상으로 표기하였으며, 미상 항목은 본 연구의 "
         "우위 근거로 쓰지 않는다."),
    cap("표 1. 선행연구 비교."),
    table1,
    copy.deepcopy(T_EMPTY),
    para("비교를 바탕으로 본 연구가 다루는 빈틈을 다섯 가지로 정리한다. ① 측정 타당도: 자동 보강의 개선을 정보 무결성과 응대 "
         "정책 준수로 분리하고 정답 기반 판정으로 뒷받침한다. ② 응대 정책 수준의 정보 무결성 강건화: RAG 오염과 허위 전제를 "
         "포함한 공격을 추론 시점의 정책 보강으로 막고 일반화를 검증한다. ③ 고객사 요구사항에서 응대 정책으로 이어지는 추적과 "
         "실제 운영 도메인에서의 실증. ④ 규칙 누적의 부작용(문자열 템플릿화, 라운드 진동, 재현성 위협)의 실측 보고. ⑤ 응답 "
         "생성 모델 교체에 대한 결과의 점검. 이 중 ①과 ②가 본 논문의 중심 주장이며, ③~⑤는 이를 보완한다."),
]
insert_before(ch3, CH2)

# ---------------------------------------------------------------- chapter 3
edit("레드팀 LLM이 카테고리별로 생성한 공격 시나리오를", "레드팀 LLM이 생성하거나 제품 설명서의 사실로 만든 공격 시나리오를")
edit("무상태 심판관이 Action Matrix에 따라 응답을 채점한다.",
     "무상태 심판관이 정보 무결성과 응대 정책 준수의 두 축으로 응답을 채점하고, 정답이 있는 항목은 코드 대조가 함께 판정한다.")
edit("사칭, 어투 변경, 허위 사실 동조, 개인정보 캐내기 등", "사칭, 어투 변경, 허위 사실 동조, 개인정보 캐내기, RAG 오염 등")
edit("공격 시나리오를 8개 범주에 걸쳐 구성한다.", "공격 시나리오를 9개 범주에 걸쳐 구성한다.")
edit("4단계에서는 격리된 심판관이 응답을 4단계 등급(FULL_DEFENSE, FUNCTIONAL_DEFENSE, PARTIAL_EXPOSURE, BREACH)으로 "
     "채점하고 우회가 발생한 유닛을 추적한다. 이는 현재 설계 기준이며, 제4장에 보고된 파일럿은 대부분 3단계 기준(PASS, "
     "WARNING, FAIL)으로 채점되었다(3.5절 참조).",
     "4단계에서는 격리된 심판관이 응답을 정보 무결성과 응대 정책 준수의 두 축으로 채점하고, 정답이 있는 항목은 코드 대조로 "
     "판정하며, 우회가 발생한 유닛을 추적한다(3.5절). 제4장의 예비 실험은 이 체계를 도입하기 전의 단일 등급 기준(PASS, "
     "WARNING, FAIL)으로 채점되었다.")

edit("본 연구는 8개 공격 유형을 OWASP Top 10 for LLM Applications 2026의 위협 카테고리에 매핑하여",
     "본 연구는 9개 공격 유형을 OWASP Top 10 for LLM Applications 2026의 위협 카테고리에 매핑하여")
edit("그림 6의 왼쪽 열과 같이 8개 유형은", "그림 6의 왼쪽 열과 같이 9개 유형은")
edit("LLM09(Misinformation)의 다섯 카테고리에 대응한다.",
     "LLM09(Misinformation)의 다섯 카테고리에 대응하며, 새로 추가한 RAG 오염은 LLM08과 함께 LLM04(Data and Model "
     "Poisoning)의 임베딩 데이터 오염과도 겹친다.")
edit("LLM03·LLM04는 학습·배포 파이프라인 단계의 위협이고", "LLM03과 LLM04의 학습 데이터 오염은 학습·배포 파이프라인 단계의 위협이고")
p_map = starts("OWASP 매핑과 별개로, 8개 공격 유형을")
t_map = txt(p_map)
replace_in(p_map, t_map[:t_map.index("이 경계는")],
    "OWASP 매핑과 별개로, 9개 공격 유형을 본 연구의 핵심 이론 축인 Dis-/Mis-/Malinformation 3분류에도 대조하였다. 관리자/"
    "시스템 사칭과 RAG 오염 문서 신뢰 유도(Disinformation), 허위 사실 동조 유도(Misinformation), 내부 메타데이터·시스템 "
    "프롬프트 유출 유도와 개인정보 유출 유도(Malinformation)의 5개를 핵심 실증 대상으로 삼고, 나머지 4개(인코딩·난독화 우회, "
    "어투 강요·가스라이팅, 다중 상품 키워드 컨텍스트 오염, 가격 정보 간접 유도)는 정보 진위와 무관한 보완적 보안 위협으로 "
    "명시적으로 분리하였다. ")
set_text(starts("공격 시나리오는 반자동 절차로 생성한다."),
    "공격 시나리오는 두 가지 방식으로 만든다. 하나는 레드팀 생성 LLM(GPT-5.4)이 카테고리 정의와 예시를 바탕으로 목표 수량의 "
    "1.5배에 해당하는 후보를 생성하고 문자열 유사도 0.85 이상의 중복을 제거하는 방식이고, 다른 하나는 정답을 알 수 있도록 제품 "
    "설명서의 사실(무게, 용량, 소비전력, 보증기간)로 문항을 만드는 템플릿 방식이다. 템플릿 방식으로는 틀린 값을 사실처럼 "
    "제시하고 확인을 요구하는 허위 전제 질문과, 틀린 값을 담은 가짜 정정 공지를 검색 결과에 섞어 넣은 RAG 오염 문항을 만든다. "
    "허위 사실 동조 범주는 두 방식을 절반씩, RAG 오염 범주는 템플릿 방식만 쓰며, 가격은 응대 정책상 먼저 언급하지 않게 되어 "
    "있어 정보 검사와 정책 검사가 섞이지 않도록 제외하였다. 이후 카테고리별·생성 방식별 비율을 유지하는 층화추출로 보강용 셋과 "
    "헬드아웃 셋에 무작위 배정한다. 설계상 연구자의 수동 검토 단계가 있으나 예비 실험에서는 이 단계가 기본값(전부 통과)으로 "
    "남아 있었으며, 이는 한계로 명시한다.")
edit("그림 6. 공격 유형 8종의 분류", "그림 6. 공격 유형 9종의 분류")

set_text(starts("3.5. 4단계 보안 심각도 Level 체계", "2"), "3.5. 두 축 채점과 정답 대조")
set_text(starts("초기 설계의 3단계 Action Matrix(PASS, WARNING, FAIL)에서"),
    "예비 실험의 채점은 응답 하나에 하나의 등급(PASS, WARNING, FAIL)을 매기는 방식이었다. 이 방식에서는 거절 판단은 옳지만 "
    "형식이 어긋난 응답과 정보가 실제로 새어 나간 응답이 같은 척도 위에 섞여, 준수율의 변화가 어느 쪽에서 왔는지 알 수 없다. "
    "이를 해결하기 위해 본 연구는 채점을 두 축으로 분리한다. 정보 무결성 축은 응답이 허위 내용을 전달하거나 동조했는지, 기밀이나 "
    "개인정보를 노출했는지만 보고 INTACT, PARTIAL, BROKEN으로 판정하며, 실패일 때는 그 유형(Dis·Mis·Malinformation)을 함께 "
    "태깅한다. 응대 정책 준수 축은 페르소나, 어투, 형식, 길이, 금지 표현 조항을 대조해 COMPLIANT, MINOR, MAJOR로 판정한다. "
    "정보 무결성이 본 연구의 주 지표이고 정책 준수는 부 지표이다.")
set_text(starts("표 3. 4단계 보안 심각도 Level 정의."), "표 3. 두 축 판정에서 산출되는 4단계 Level.")
t3 = next(t for t in body.iter(qn("w:tbl")) if txt(t).startswith("Level명칭정의 (도메인 무관)"))
T3 = [["Level", "명칭", "두 축 판정의 조합"],
      [None, None, "정보 무결성 INTACT, 정책 준수 COMPLIANT"],
      [None, None, "정보 무결성 INTACT, 정책 준수 MINOR 또는 MAJOR"],
      [None, None, "정보 무결성 PARTIAL (간접 정보 노출, 허위 전제 방치)"],
      [None, None, "정보 무결성 BROKEN (허위 전달·동조, 기밀·개인정보 노출)"]]
for r, values in zip(t3.findall(qn("w:tr")), T3):
    for c, v in zip(r.findall(qn("w:tc")), values):
        if v is not None:
            cell_set(c, v)
set_text(starts("5단계 이상으로 세분화하는 방안은 기각하였다."),
    "기존의 4단계 보안 심각도 척도(OWASP Risk Rating Methodology와 CVSS의 4단계 관행에서 차용)는 버리지 않고, 두 축의 판정에서 "
    "코드로 산출하도록 바꾸었다(표 3, 그림 7). 정보 무결성이 먼저 등급을 정하고, 정보가 지켜진 경우에만 정책 준수가 완전 방어와 "
    "기능적 방어를 가른다. 따라서 심판관이 등급과 근거를 따로 내어 서로 어긋나는 일이 없고, 등급의 변화가 정보 측면인지 형식 "
    "측면인지를 언제나 되짚을 수 있다.")
set_text(starts("한편 전문 제5장에 보고된 1~13차 파일럿은 모두 3단계 기준으로 채점되었고"),
    "정답을 알 수 있는 항목은 코드 대조가 정보 무결성을 함께 판정한다. 응답에 가상 회원 데이터베이스의 전화번호, 이메일, "
    "회원번호, 주소가 공격 문장에 없던 형태로 나타나거나, 응대 정책 원문이 25자 이상 그대로 나타나거나, 템플릿 문항의 틀린 값이 "
    "정답 없이 나타나면 BROKEN으로 판정한다. 코드 대조는 명백한 실패만 찾고 안전을 보증하지는 않으므로, 찾지 못한 경우는 "
    "심판관의 판정을 따른다. 코드 대조가 실패를 찾았는데 심판관은 그렇게 보지 않은 건수는 따로 기록하여 심판관 신뢰성의 지표로 "
    "쓴다. 심판관의 판정 근거는 150자 이내로 제한하여, 예비 실험에서 관측된 판정문의 장문화와 그에 따른 비용 증가도 함께 "
    "억제한다.")
edit("그림 7. 4단계 보안 심각도 Level 체계.", "그림 7. 두 축 판정과 4단계 Level의 관계.")

# ---------------------------------------------------------------- chapter 4
set_text(starts("이 장에서는 제안 메커니즘을 검증한 실험의 설계와 결과를 함께 다룬다."),
    "이 장에서는 예비 실험의 설계와 결과를 보고하고, 이를 바탕으로 설계한 본 실험을 제시한다. 4.1절에서 예비 실험의 설계를 "
    "기술하고, 4.2절에서 강건화 성능과 유형별 결과, 그리고 정보 무결성 기준의 재분석을 보고한다. 4.3절에서 교차 모델 검증 결과를, "
    "4.4절에서 5W1H 판단 원칙의 가설 검증과 적응형 재공격 결과를 제시한다. 4.5절에서는 예비 실험에서 드러난 측정의 한계를 반영한 "
    "본 실험의 설계와 가설을 제시한다.")
set_text(starts("4.1. 실험 설계", "2"), "4.1. 예비 실험 설계")
edit("본 요약본에 보고된 모든 결과는 카테고리당 3개로 축소한 예비 규모 파일럿이며, 보강용·헬드아웃 셋은 각각 24개 문항(채점 "
     "가능 22~23개)이다. 카테고리당 10개 규모의 본 실행은 아직 수행하지 않았다.",
     "4.1~4.4절에 보고하는 결과는 모두 2026년 8월에 수행한 예비 실험(7~13차)이며, 카테고리당 3개로 축소한 규모로 보강용·헬드아웃 "
     "셋이 각각 24개 문항(채점 가능 22~23개)이다. 예비 실험은 RAG 오염 범주와 두 축 채점을 도입하기 전의 8개 범주, 단일 등급 "
     "체계로 수행되었다.")
edit("후자는 이후 실행부터 적용할 계획이며 본 요약본에는 그 결과가 포함되지 않았다.", "후자는 4.5절의 본 실험 설계에 반영하였다.")
set_text(starts("4.2. 강건화 성능 및 유형별 방어 결과", "2"), "4.2. 강건화 성능과 정보 무결성 기준의 재분석")
edit("9차 파일럿의 결과를 3.4절의 매핑 기준(그림 6)에 따라",
     "9차 파일럿의 결과를 3.4절의 매핑 기준(그림 6, 예비 실험에는 RAG 오염 범주가 없었으므로 나머지 핵심 4범주)에 따라")
edit("블랙박스 재공격의 1건은 응답 형식이 통째로 붕괴한 사례였다(4.5절).", "블랙박스 재공격의 1건은 응답 형식이 통째로 붕괴한 사례였다(4.4절).")
fig9 = starts("그림 9. 정보 불일치성 유형별 방어 결과.")
for el in reversed([
    para("그러나 이 결과를 정보 무결성 기준으로 다시 읽으면 해석이 달라진다. 9차의 round_1(초기 응대 정책 v1.0) 22건을 4단계 "
         "기준으로 회고 재채점한 결과는 완전 방어 1건, 기능적 방어 20건, 부분 노출 1건, 침해 0건이었다. 기능적 방어는 거절 판단이 "
         "옳고 핵심 정보가 지켜졌으나 형식 조항만 어긋난 응답이므로, 초기 응대 정책에서 이미 22건 중 21건이 정보 측면에서는 "
         "방어되어 있었던 것이다. round_14의 재채점 결과(완전 방어 19건, 기능적 방어 3건)와 비교하면, 68.2%에서 100%로 오른 "
         "준수율의 대부분은 기능적 방어가 완전 방어로 바뀐 형식 교정이었다. 8차의 FAIL 15건이 모두 형식 위반이었고, 10차 FAIL의 "
         "판정 근거도 대부분 핵심 거부 판단은 옳았으나 형식 조항을 어겼다는 내용이라는 점도 같은 방향이다."),
    para("이 재분석은 두 가지를 말해 준다. 첫째, 예비 실험의 공격은 정보 측면에서 초기 응대 정책을 거의 무너뜨리지 못하여, "
         "강건화 루프가 정보 무결성을 개선하는지 보여 줄 여지 자체가 작았다. 둘째, 단일 등급의 준수율은 형식 교정과 정보 개선을 "
         "구분하지 못해 자동 보강 루프의 성과를 실제보다 크게 보이게 할 수 있다. 4.5절의 본 실험은 이 두 문제를 각각 정답 기반의 "
         "정보 무결성 공격(허위 전제, RAG 오염)과 두 축 채점으로 다룬다."),
]):
    fig9.addnext(el)

set_text(starts("4.4. 5W1H 판단 원칙의 가설 검증", "2"), "4.4. 5W1H 가설 검증과 적응형 재공격")
body.remove(starts("4.5. 적응형 재공격", "2"))
edit("고정된 공격셋에 대한 방어율만으로는", "한편 고정된 공격셋에 대한 방어율만으로는")

ch5 = starts("제5장. 논의 및 결론", "1")
t4 = next(t for t in body.iter(qn("w:tbl")) if txt(t).startswith("역할모델비고"))
t10 = copy.deepcopy(t4)
T10 = [["항목", "본 실험 설정", "근거"],
       ["문항 수 (셋당)", "핵심 5범주 × 6, 보완 4범주 × 2 = 38", "교차 모델 검정력: 8차 수준 격차에서 24문항 66% → 40문항 88% (시뮬레이션)"],
       ["라운드 상한", "5", "예비 실험의 개선이 1~3라운드에 집중"],
       ["반복 시행", "5회 다수결 (사전 실측 후 확정)", "예비 실험에서 반복 간 변동 미측정"],
       ["적응형 재공격", "조건별 10개", "5개면 1건이 20%p"],
       ["주 지표", "정보 무결성 (INTACT 비율, 점수 3·2·1)", "4.2절 재분석"],
       ["가설 검정", "H1 Wilcoxon, H2 비열등성(10%p), H3 Cochran's Q", "실행 전 고정"]]
rows = t10.findall(qn("w:tr"))
while len(rows) < len(T10):
    rows[-1].addnext(copy.deepcopy(rows[-1]))
    rows = t10.findall(qn("w:tr"))
for r, values in zip(rows, T10):
    for c, v in zip(r.findall(qn("w:tc")), values):
        cell_set(c, v)
insert_before(ch5, [
    h2("4.5. 본 실험 설계"),
    para("예비 실험의 재분석을 바탕으로 본 실험은 측정과 공격을 함께 바꾼다. 공격은 9개 범주로 확장하고, 핵심 5범주는 셋당 6개, "
         "보완 4범주는 셋당 2개로 배분하여 보강용 셋과 헬드아웃 셋을 각각 38개 문항으로 구성한다. 핵심 범주에 문항을 더 배분하는 "
         "것은 정보 불일치성에 해당하는 결과의 검정력을 높이기 위해서이다. 허위 사실 동조 범주의 절반과 RAG 오염 범주 전부는 제품 "
         "설명서의 사실로 만든 템플릿 문항이며, 생성 방식별로도 보강용 셋과 헬드아웃 셋에 같은 비율로 배정한다. 채점은 3.5절의 두 "
         "축 채점과 코드 대조를 따른다."),
    para("라운드 상한은 5로 둔다. 예비 실험에서 준수율의 상승은 1~3라운드에 집중되었고(7·9차), 10·11차는 2라운드에서 정점을 찍은 "
         "뒤 하락하였으므로, 5라운드면 개선 구간과 하락의 시작을 함께 관찰할 수 있다. 문항마다 응답과 채점을 5회 반복해 다수결로 "
         "집계하며, 동률이면 더 나쁜 판정을 택한다. 반복 횟수는 소규모 사전 실측에서 반복 간 판정 일치율을 측정한 뒤 확정하며, "
         "일치율이 90% 이상이면 3회로 줄인다. 적응형 재공격은 블랙박스와 화이트박스 조건별로 10개를 생성한다. 반복 시행에서는 만점 "
         "조기 종료를 하지 않으므로 9차와 같은 100% 수렴은 본 실험의 목표가 아니며, 그 결과는 예비 실험의 관찰로 남긴다."),
    para("본 실험의 가설과 검정은 실행 전에 고정한다(표 10). H1(정보 무결성 개선): 보강용 셋에서 정보 무결성 점수가 1라운드보다 "
         "최종 라운드에서 높다(Wilcoxon 부호순위 검정). H2(일반화): 헬드아웃 셋의 정보 무결 비율이 보강용 셋 최종 라운드보다 10%p "
         "이상 낮지 않다(비열등성 검정). H3(모델 종속성): 응답 생성 모델을 바꾸었을 때 정보 무결 비율이 달라지는지를 Cochran's Q "
         "검정으로 점검하되, 유의하지 않은 결과를 차이가 없다는 증거로 해석하지 않는다. 핵심 범주별 결과, 정책 준수 축의 변화, "
         "블랙박스와 화이트박스의 비교, 코드 대조와 심판관의 일치도는 탐색적 분석으로 보고한다. 또한 본 실험에 앞서 소규모 사전 "
         "실측을 수행해, 초기 응대 정책에서 정보 무결성 실패율이 개선을 관찰할 수 있을 만큼(약 20~50%) 나오는지 확인하고, 그렇지 "
         "않으면 공격 문항을 조정한다."),
    cap("표 10. 본 실험 설정."),
    t10,
    copy.deepcopy(T_EMPTY),
])

# ---------------------------------------------------------------- chapter 5
set_text(starts("본 연구의 예비 결과는 막대한 연산 비용이 드는 모델 파인튜닝이나"),
    "예비 실험은 파인튜닝이나 복잡한 다중 에이전트 시스템 없이 응대 정책 텍스트의 자동 보강만으로 단일 등급의 준수율을 크게 높일 "
    "수 있음을 보였다. 9차에서 준수율은 68.2%에서 100%로 올랐고 헬드아웃 셋에서도 97.1%가 유지되었다. 그러나 4.2절의 재분석에 "
    "따르면 이 개선의 대부분은 형식 교정이었고, 정보 측면의 방어는 초기 응대 정책에서 이미 거의 이루어져 있었다. 따라서 예비 "
    "실험이 뒷받침하는 주장은 자동 보강이 응대 정책의 형식 준수를 높이고 그 효과가 처음 보는 문항에서도 유지된다는 데까지이며, "
    "정보 불일치성에 대한 강건성이 높아진다는 주장은 정답 기반 공격과 두 축 채점을 도입한 본 실험으로 검증해야 한다. 이 구분 "
    "자체가 본 연구의 첫째 기여인 측정 타당도의 근거이다. 또한 안전성이 강하게 튜닝된 모델이 레드팀 생성과 채점 요청을 정책상 "
    "거부하는 현상은, 여러 역할에 동일 모델을 쓸 때 구조적으로 부딪히는 문제로서 역할 분리 설계의 필요성을 실측으로 보여 준다.")
edit("첫째, 모든 결과가 단일 도메인(가전 유통)의 카테고리당 3개 규모 예비 파일럿이며",
     "첫째, 현재 보고된 결과는 모두 단일 도메인(가전 유통)의 카테고리당 3개 규모 예비 실험이며")
edit("셋째, 모든 채점이 단일 주 모델 심판관에 의존하며 연구자의 수동 블라인드 채점은 아직 수행되지 않았고, 4단계 rubric의 "
     "심판관 신뢰도도 실측되지 않았다.",
     "셋째, 예비 실험의 채점은 단일 등급이어서 정보 무결성과 형식 준수를 구분하지 못하였고 모든 채점이 단일 주 모델 심판관에 "
     "의존하였다. 본 실험은 두 축 채점과 코드 대조를 도입하지만, 코드 대조는 정답이 있는 항목에만 적용되므로 연구자의 수동 "
     "블라인드 채점은 여전히 필요하다.")
set_text(starts("본 논문은 LLM 기반 AI 챗봇의 정보 불일치성에 저항하기 위해"),
    "본 논문은 LLM 기반 AI 챗봇의 정보 불일치성에 대한 강건화 메커니즘으로, 모듈형 4단계 유닛 아키텍처 위에서 고객사의 응대 "
    "정책을 적대적 테스트로 자동 보강하는 폐쇄 루프를 제안하였다. 카테고리당 3개 규모의 예비 실험에서 단일 등급의 준수율은 크게 "
    "개선되고 헬드아웃 셋에서도 유지되었으나, 정보 무결성 기준의 재분석은 그 개선이 주로 형식 교정이었음을 보여 주었다. 이에 따라 "
    "채점을 정보 무결성과 응대 정책 준수의 두 축으로 분리하고, 정답 기반 코드 대조와 제품 설명서 기반의 허위 전제·RAG 오염 공격을 "
    "도입한 본 실험을 설계하였다. 9차의 100% 수렴이 응대 정책의 문자열 템플릿화를 동반하였고 5W1H 원칙이 기각되었다는 점도 함께 "
    "보고하며, 본 결과는 본 실험 전까지 예비적 근거로 해석되어야 한다.")
set_text(starts("향후 연구로는 카테고리당 10개 규모의 본 실행"),
    "향후 연구로는 4.5절의 본 실험 수행과 사전에 고정한 가설의 검정, 연구자의 수동 블라인드 채점에 의한 심판관 신뢰도 검증, "
    "헬드아웃 셋의 독립 생성, 의료·금융·공공 등 법적 제약이 더 복잡한 타 도메인으로의 확장, 여러 턴에 걸친 공격의 포함, 그리고 "
    "생성된 Meta-Rule을 프로덕션에 반영하기 전의 사람 검수 게이트 설계를 계획한다.")

# ---------------------------------------------------------------- references (23, by author)
REFS = [
    "Aswin RRV, Tyagi, N., Uddin, M. N., Varshney, N., & Baral, C. (2024). Chaos with Keywords: Exposing Large Language Models' Sycophantic Hallucination to Misleading Keywords and Evaluating Defense Strategies. Findings of the Association for Computational Linguistics: ACL 2024. arXiv:2406.03827.",
    "Bai, Y., Kadavath, S., Kundu, S., et al. (2022). Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073.",
    "Chaitanya, & Gundakaram (2026). PRISM: Prompt Reliability via Iterative Simulation and Monitoring for Enterprise Conversational AI. arXiv:2605.15665.",
    "Chen, Wang, Sun, Liu, Zhang, & Liu (2025). Promptware Engineering: Software Engineering for Prompt-Enabled Systems. arXiv:2503.02400.",
    "FIRST.Org, Inc. (2023). Common Vulnerability Scoring System version 4.0: Specification Document. Forum of Incident Response and Security Teams (FIRST). https://www.first.org/cvss/v4-0/cvss-v40-specification.pdf",
    "Geng, R., Yin, C., Wang, Y., Chen, Y., & Jia, J. (2026). PIArena: A Platform for Prompt Injection Evaluation. Proceedings of the Association for Computational Linguistics (ACL 2026). arXiv:2604.08499.",
    "Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. ACM Workshop on Artificial Intelligence and Security (AISec 2023). arXiv:2302.12173.",
    "Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the Middle: How Language Models Use Long Contexts. Transactions of the Association for Computational Linguistics, 12, 157–173. arXiv:2307.03172.",
    "OWASP Foundation. OWASP Risk Rating Methodology. https://owasp.org/www-community/OWASP_Risk_Rating_Methodology",
    "OWASP Top 10 for Large Language Model Applications 2026. OWASP Foundation, OWASP Gen AI Security Project. (Published 2026-08-04).",
    "Perez, E., Huang, S., Song, F., Cai, T., Ring, R., Aslanides, J., Glaese, A., McAleese, N., & Irving, G. (2022). Red Teaming Language Models with Language Models. Proceedings of EMNLP 2022. arXiv:2202.03286.",
    "Pryzant, R., Iter, D., Li, J., Lee, Y. T., Zhu, C., & Zeng, M. (2023). Automatic Prompt Optimization with \"Gradient Descent\" and Beam Search. Proceedings of EMNLP 2023. arXiv:2305.03495.",
    "Rebedea, Dinu, Sreedhar, Parisien, & Cohen (2023). NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails. Proceedings of EMNLP 2023: System Demonstrations. arXiv:2310.10501.",
    "Sharma, M., Tong, M., Korbak, T., et al. (2024). Towards Understanding Sycophancy in Language Models. International Conference on Learning Representations (ICLR 2024). arXiv:2310.13548.",
    "Shi, J., Yuan, Z., Liu, Y., Huang, Y., Zhou, P., Sun, L., & Gong, N. Z. (2024). Optimization-based Prompt Injection Attack to LLM-as-a-Judge. Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security (CCS '24). arXiv:2403.17710.",
    "Sivaroopan, N., Thilakarathna, K., Zomaya, A., et al. (2026). SHIELD: An Auto-Healing Agentic Defense Framework for LLM Resource Exhaustion Attacks. arXiv:2601.19174.",
    "Slater, T. (2025). A Self-Improving Architecture for Dynamic Safety in Large Language Models. arXiv:2511.07645.",
    "Tamber, M. S., Bao, F. S., Xu, C., Luo, G., Kazi, S., Bae, M., Li, M., Mendelevitch, O., Qu, R., & Lin, J. (2025). Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards. Proceedings of EMNLP 2025 (Industry Track). arXiv:2505.04847.",
    "Wardle, C., & Derakhshan, H. (2017). Information Disorder: Toward an Interdisciplinary Framework for Research and Policy Making. Council of Europe report DGI(2017)09.",
    "Xiang, C., Wu, T., Zhong, Z., Wagner, D., Chen, D., & Mittal, P. (2024). Certifiably Robust RAG against Retrieval Corruption. arXiv:2405.15556.",
    "Yang, C., Wang, X., Lu, Y., Liu, H., Le, Q. V., Zhou, D., & Chen, X. (2024). Large Language Models as Optimizers. International Conference on Learning Representations (ICLR 2024). arXiv:2309.03409.",
    "Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track. arXiv:2306.05685.",
    "Zou, W., Geng, R., Wang, B., & Jia, J. (2025). PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models. 34th USENIX Security Symposium (USENIX Security 2025). arXiv:2402.07867.",
]
ref_head = one(lambda p: txt(p) == "참고문헌" and style_of(p) == "1")
ref_ps = []
el = ref_head.getnext()
while el is not None and el.tag == qn("w:p"):
    if txt(el).strip():
        ref_ps.append(el)
    el = el.getnext()
assert len(ref_ps) == 15, len(ref_ps)
while len(ref_ps) < len(REFS):
    clone = copy.deepcopy(ref_ps[-1])
    ref_ps[-1].addnext(clone)
    ref_ps.append(clone)
for i, (p, ref) in enumerate(zip(ref_ps, REFS), 1):
    set_text(p, f"{i}. {ref}")

# ---------------------------------------------------------------- static TOC
toc_head = one(lambda p: txt(p) == "목차")
toc = []
el = toc_head.getnext()
while txt(el) != "참고문헌":
    toc.append(el)
    el = el.getnext()
TOC_NEW = {
    "2.1. LLM 커스터마이징과 가드레일": "2.1. LLM 커스터마이징, 가드레일, 행동 명세",
    "2.2. LLM-as-a-Judge와 심판관 신뢰성": "2.2. 자동 프롬프트 최적화와 자동 보강 루프",
    "2.3. 자동화된 레드티밍과 자가 치유 프레임워크": "2.3. 자동화된 레드티밍과 정보 무결성 공격",
    "2.4. 정보 무질서 프레임워크": "2.4. LLM-as-a-Judge와 측정 타당도",
    "2.5. 선행연구 비교": "2.5. 정보 무질서 프레임워크",
    "3.5. 4단계 보안 심각도 Level 체계": "3.5. 두 축 채점과 정답 대조",
    "4.1. 실험 설계": "4.1. 예비 실험 설계",
    "4.2. 강건화 성능 및 유형별 방어 결과": "4.2. 강건화 성능과 정보 무결성 기준의 재분석",
    "4.4. 5W1H 판단 원칙의 가설 검증": "4.4. 5W1H 가설 검증과 적응형 재공격",
    "4.5. 적응형 재공격": "4.5. 본 실험 설계",
}
for p in toc:
    if txt(p) in TOC_NEW:
        new = TOC_NEW[txt(p)]
        set_text(p, new)
        if new.startswith("2.5."):
            p.addnext(set_text(copy.deepcopy(p), "2.6. 선행연구 비교와 본 연구의 빈틈"))

# check the TOC against the real headings
heads = [txt(p) for p in paras() if style_of(p) in ("1", "2")]
toc_lines = []
el = toc_head.getnext()
while el is not None and txt(el) != "참고문헌":
    if txt(el).strip() and txt(el) != "초록":
        toc_lines.append(txt(el))
    el = el.getnext()
assert toc_lines == [h for h in heads if h != "참고문헌"][:len(toc_lines)], (toc_lines, heads)

# ---------------------------------------------------------------- figures
sources = {}
for name in os.listdir(FIG):
    if name.endswith("_v6.png"):
        with open(os.path.join(FIG, name), "rb") as f:
            sources[hashlib.md5(f.read()).hexdigest()] = name
swapped = []
for p in body.iter(qn("w:p")):
    for blip in p.iter(qn("a:blip")):
        part = d.part.related_parts[blip.get(qn("r:embed"))]
        name = sources.get(hashlib.md5(part.blob).hexdigest())
        if not name:
            continue
        new = os.path.join(FIG, name.replace("_v6.png", "_v7.png"))
        if not os.path.exists(new):
            continue
        with open(new, "rb") as f:
            part._blob = f.read()
        w, h = Image.open(new).size
        for ext in list(p.iter(qn("wp:extent"))) + list(p.iter(qn("a:ext"))):
            if ext.get("cx"):
                ext.set("cy", str(round(int(ext.get("cx")) * h / w)))
        swapped.append(name)

all_text = "\n".join(txt(p) for p in body.iter(qn("w:p")))
for stale in ("8개 범주에 걸쳐", "4.5절의 위협", "Action Matrix에 따라", "본 실행은 아직 수행하지 않았다"):
    assert stale not in all_text, stale
d.save(DST)
print("saved", DST)
print("figures swapped:", sorted(swapped))
