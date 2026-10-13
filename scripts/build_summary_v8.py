# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v8.docx from v7 (v7 is read only): kim-paper-kit pass.

  R2   abstract rewritten in the seven steps (problem, current practice and who, gap and need,
       proposal, mechanism, case, effect with baseline); conclusion as done / results (1)-(4) /
       future work (1)-(6)
  R3/R4 four core concepts written as 1) 정의 2) 예시 3) 논의 4) 적용, with the judging unit's granularity
  R9   compliance floor (33.3%) given with the rate; power figures from scripts/power_simulation_cross_model.py
  R13  translationese removed (style_lint error), differences in pp
  R18  one core-problem sentence in abstract, introduction and conclusion
  §2   chapter overviews added to chapters 3 and 5; contributions carry section numbers
"""
import copy
import os
import re
import sys

import docx
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual_v7.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v8.docx")
assert not os.path.exists(DST), "v8 already exists; do not overwrite"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
CORE = "적대적 테스트로 응대 정책을 자동 보강하고, 그 개선을 정보 무결성 기준으로 확인"

d = docx.Document(SRC)
body = d.element.body


def txt(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def style_of(p):
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def paras():
    return [e for e in body if e.tag == qn("w:p")]


def one(pred):
    hits = [p for p in paras() if pred(p)]
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


T_BODY = copy.deepcopy(starts("LLM을 특정 도메인에 맞추는 기법은"))


def para(t):
    return set_text(copy.deepcopy(T_BODY), t)


def insert_after(anchor, texts):
    for t in reversed(texts):
        anchor.addnext(para(t))


# ---------------------------------------------------------------- R13: translationese, pp
edit("재현성 위협을 낳는다는 부작용을 실측으로 보고한다.", "재현성 위협으로 이어진다는 부작용을 실측으로 보고한다.")
for t in body.iter(qn("w:t")):
    if t.text and "%p" in t.text:
        t.text = re.sub(r"(\d)%p", r"\1 pp", t.text)

edit("측면인지를 언제나 되짚을 수 있다.", "측면인지를 언제나 확인할 수 있다.")
edit("Response Policy Reinforcement — A Consumer Electronics Retail Case Study",
     "Response Policy Reinforcement—A Consumer Electronics Retail Case Study")   # English em-dash without spaces

# ---------------------------------------------------------------- R2 abstract (7 steps) + R18
set_text(starts("기업 환경에 도입되는 생성형 LLM 기반 챗봇은"),
    "기업 환경에 도입되는 LLM 기반 챗봇은 고객 개인정보의 유출, 제품 정보와 다른 응답, 사용자가 주입한 허위 전제에 대한 "
    "동조처럼 정보의 진위와 기밀이 흔들리는 문제에 반복적으로 노출된다. 본 연구는 이를 Wardle과 Derakhshan(2017)의 정보 "
    "무질서 3분류에 근거하여 조직 챗봇의 1:1 세션에서 일어나는 '정보 불일치성(Information Disorderness)'으로 재정의한다. "
    "지금까지 이 문제는 챗봇 개발자가 시스템 프롬프트를 수작업으로 작성해 몇 가지 사례로 시험하거나, 가드레일 도구의 규칙을 "
    "사람이 작성하고 유지하는 방식으로 다루어 왔으며, 최근에는 실패 사례로 프롬프트를 자동 보강하는 연구가 제안되었다. 그러나 "
    "사람이 쓰는 규칙은 새로운 공격이 나올 때마다 다시 써야 하고, 자동 보강 연구는 개선을 하나의 통과율로 보고하여 그 개선이 "
    "정보의 진위와 기밀 측면에서 일어났는지 응답 형식에서 일어났는지 구분하지 못한다. 따라서 본 연구의 핵심 문제는 "
    + CORE + "하는 것이다.")
set_text(starts("본 논문은 정보 불일치성에 대한 응대 정책 명세 기반 강건화"),
    "본 논문은 응대 정책 명세 기반 강건화(Hardening) 메커니즘을 제안한다. 입력 가드레일, RAG 검색, LLM 추론, 출력 "
    "가드레일로 이어지는 4단계 유닛 아키텍처 위에서 레드팀 LLM과 제품 설명서 템플릿으로 9개 범주의 공격 문항을 만들고, "
    "무상태 심판관이 응답을 정보 무결성과 응대 정책 준수의 두 축으로 채점하며, 정답이 있는 항목은 개인정보, 정책 원문, 허위 "
    "값의 코드 대조로 판정한다. 실패 사례는 Meta-Rule 생성기가 보강 규칙으로 바꾸어 응대 정책에 병합하고, 이 과정을 라운드 "
    "상한까지 반복한 뒤 헬드아웃 셋, 적응형 재공격, 응답 생성 모델만 바꾸는 교차 모델 검증으로 일반화를 확인한다.")
set_text(starts("카테고리당 3개 규모의 예비 실험(7~13차)에서 단일 등급 기준의 준수율은"),
    "가전 유통 고객사의 실제 운영 챗봇을 대상으로 카테고리당 3개 규모의 예비 실험(7~13차)을 수행하였다. 9차 실험에서 단일 "
    "등급 준수율은 14라운드 만에 68.2%에서 100%로 올랐고(이 지표의 하한은 33.3%) 헬드아웃 셋에서도 97.1%가 유지되었다. "
    "그러나 정보 무결성 기준으로 다시 보면 초기 응대 정책에서도 22건 중 21건이 이미 정보 측면에서 방어되어 있어, 개선의 "
    "대부분은 형식 교정이었다. 이 재분석은 두 축 채점이 자동 보강의 효과를 과대평가하지 않게 해 준다는 편익을 보이며, 이를 "
    "바탕으로 정보 무결성의 개선(H1), 헬드아웃 셋에서의 비열등성(H2), 응답 생성 모델 교체에 따른 차이(H3)를 검증하는 본 "
    "실험을 설계하였다. 본 연구는 단일 도메인 사례 연구이므로 결과의 일반화에는 주의가 필요하다.")

# ---------------------------------------------------------------- chapter 1: core sentence, contributions with sections
set_text(starts("본 논문에서 '강건화(Hardening)'는 배포된 시스템이"),
    "본 논문의 핵심 개념인 응대 정책 명세와 강건화는 3.3절에서 정의한다. 강건화는 배포된 시스템이 런타임에 스스로 복구하는 "
    "자가 치유와 달리 설계 시점의 오프라인 반복 절차를 가리킨다. 본 연구의 핵심 문제는 " + CORE + "하는 것이며, 그 기여는 "
    "다음과 같다.")
set_text(starts("첫째, 측정 타당도이다."),
    "첫째, 측정 타당도이다. 응답을 정보 무결성과 응대 정책 준수의 두 축으로 나누어 채점하고, 정답이 있는 항목은 코드 대조로 "
    "판정해 심판관과의 일치도를 함께 보고하는 측정 체계를 제안한다(3.5절). 예비 실험의 재분석은 단일 등급 준수율의 개선이 "
    "실제로는 형식 교정이었음을 보여, 이 분리가 필요한 이유를 실측으로 뒷받침한다(4.2절). 둘째, 응대 정책 수준의 정보 무결성 "
    "강건화이다. 제품 설명서의 사실로 만든 허위 전제 질문과 RAG 오염 문항을 포함한 공격에 대해, 검색 단계가 아니라 추론 시점의 "
    "응대 정책을 적대적 테스트로 자동 보강하고, 헬드아웃 셋과 적응형 재공격으로 일반화를 검증하도록 설계하였다(3.4절, 4.5절). "
    "셋째, 고객사의 요구사항을 응대 정책으로 명세하고 테스트로 검증·보강하는 요구사항 추적 흐름을 실제 운영 중인 가전 유통 "
    "챗봇에 적용하였다(3.3절, 4.1절). 넷째, 규칙 누적이 응대 정책의 문자열 템플릿화, 라운드 간 진동, 모델 동작 변화로 인한 "
    "재현성 위협으로 이어진다는 부작용을 실측으로 보고한다(4.2절, 4.4절). 다섯째, 응답 생성 모델만 바꾸고 채점 모델은 고정하는 "
    "교차 모델 검증으로 결과의 모델 종속성을 점검한다(4.3절). 4단계 유닛 아키텍처 자체의 형태적 신규성은 기존 가드레일 "
    "파이프라인 패턴과 유사하여 제한적이며, 본 연구의 중심 주장은 첫째와 둘째에 있다.")
p14 = starts("본 요약본은 학위논문 전문의 핵심 그림을 중심으로")
t14 = txt(p14)
a = t14.index("본 요약본에서 응대 정책 명세(")
b = t14.index("제2장에서는")
replace_in(p14, t14[a:b], "")

# ---------------------------------------------------------------- chapter 3: overview + definitions
ch3 = starts("제3장. 제안하는 강건화 메커니즘", "1")
ch3.addnext(para(
    "이 장에서는 제안하는 강건화 메커니즘을 설명한다. 먼저 3.1절에서 세 구조로 이루어진 전체 프레임워크를, 3.2절에서 유닛 "
    "아키텍처를 제시한다. 이어서 3.3절에서 응대 정책 명세와 강건화를 정의하고 5단계 절차를 기술하며, 3.4절에서 정보 불일치성을 "
    "정의하고 공격 분류체계와 문항 생성 방법을, 3.5절에서 판정 단위와 두 축 채점, 정답 대조를 설명한다."))

insert_after(starts("3.3. 강건화 5단계 절차", "2"), [
    "응대 정책 명세(Response Policy Specification)는 다음과 같이 정의한다.",
    "1) 정의: 응대 정책 명세는 고객사의 요구사항을 LLM이 추론 시점에 읽는 자연어 지시문으로 명세한 문서이며, 버전 k의 "
    "명세는 P_k = (페르소나, 제약 조건 집합, 보강 규칙 집합)이다.",
    "2) 예시: 가전 유통 고객사의 초기 명세 P_0(v1.0)는 해요체 응대를 정한 페르소나와, 설명서 범위 안에서만 답할 것, 답변을 "
    "100~300자로 할 것, 고객이 먼저 묻기 전에는 가격을 언급하지 않을 것 등 17개의 제약 조건으로 이루어지며, 보강 규칙은 비어 "
    "있다.",
    "3) 논의: 소프트웨어공학의 요구사항 명세서(SRS)는 개발자가 시스템을 구현하기 위해 합의하는 개발 산출물인 반면, 응대 정책 "
    "명세는 실행 중인 LLM이 응답할 때마다 읽는 지시문이다. 따라서 요구사항 명세서라는 이름을 쓰지 않고, 고객사의 요구사항이 "
    "응대 정책으로 옮겨지는 관계를 추적 대상으로 삼는다. 또한 Constitutional AI의 원칙 문서와 달리 학습에 쓰이지 않으므로, "
    "고객사마다 재학습 없이 교체할 수 있다.",
    "4) 적용: 9차 예비 실험에서 응대 정책은 v1.0에서 v1.13까지 13번 갱신되었고 보강 규칙은 28개가 누적되었으며, 모든 버전을 "
    "실행별로 저장하여 버전 간 차이를 추적할 수 있게 하였다.",
    "강건화(Hardening)는 다음과 같이 정의한다.",
    "1) 정의: 강건화는 응대 정책 P_k를 적대적 문항 집합으로 시험해 실패 사례 F_k를 얻고, 보강 규칙 생성기가 F_k로부터 보강 "
    "규칙 R_k를 만들어 P_k에 R_k를 병합한 P_(k+1)로 갱신하는 과정을, 모든 문항이 완전 방어에 이르거나 라운드 상한에 도달할 "
    "때까지 반복하는 설계 시점의 절차이다.",
    "2) 예시: 9차 예비 실험에서 P_0(v1.0)으로 시작한 강건화는 14라운드 만에 보강용 셋의 채점 가능 문항 22개가 모두 최고 "
    "등급(당시 3단계 기준 PASS)에 이르러 P_13(v1.13)에서 종료되었다.",
    "3) 논의: 운영 중인 시스템이 스스로 진단하고 복구하는 자가 치유(self-healing, 자가 적응 시스템의 MAPE-K 루프)와 달리 "
    "강건화는 배포 전의 오프라인 절차이며, 런타임 자율 복구, 자기 수정 코드, 모델 가중치 변경을 포함하지 않는다. 자동 프롬프트 "
    "최적화와는 루프의 골격이 같지만, 목표가 과제 정확도가 아니라 적대적 공격에 대한 정보 무결성이라는 점이 다르다.",
    "4) 적용: 이 절차를 아래의 5단계로 구현하였으며, 라운드 상한에 도달하면 마지막으로 평가된 버전을 최종 응대 정책 v_final로 "
    "삼는다.",
])

insert_after(starts("3.4. 공격 분류체계와 시나리오 생성", "2"), [
    "정보 불일치성(Information Disorderness)은 다음과 같이 정의한다.",
    "1) 정의: 정보 불일치성은 조직 챗봇의 1:1 응답이 조직이 정한 사실(제품 설명서와 지식 베이스)이나 기밀 경계와 어긋나는 "
    "상태이며, 그 유형은 사실과 다른 정보를 전달하는 Misinformation, 의도적으로 꾸며진 허위나 사칭에 넘어가는 Disinformation, "
    "사실이지만 공개되면 안 되는 정보를 노출하는 Malinformation의 세 가지이다.",
    "2) 예시: 건조기 무게가 9kg이라는 사용자의 허위 전제에 동조하는 응답(설명서의 정답은 17kg, Misinformation), 검색 결과에 "
    "섞인 가짜 정정 공지의 용량 값을 그대로 안내하는 응답(Disinformation), 다른 고객의 전화번호를 알려 주는 응답"
    "(Malinformation)이 여기에 해당한다.",
    "3) 논의: Wardle과 Derakhshan(2017)의 원 개념은 대중을 향한 확산을 전제하지만, 본 연구는 대상을 1:1 상담 세션의 응답으로 "
    "옮겼다. 의도성은 응답한 챗봇이 아니라 공격자나 오염된 문서 쪽의 의도로 판단하며, 말투나 형식의 어긋남은 정보 불일치성이 "
    "아니라 응대 정책 준수의 문제로 따로 다룬다(3.5절).",
    "4) 적용: 9개 공격 범주 중 정보 불일치성의 세 유형에 직접 대응하는 5개를 핵심 실증 대상으로 삼고, 나머지 4개는 보완적 보안 "
    "위협으로 분리하였다(그림 6). 분류체계와 문항 생성 방법은 다음과 같다.",
])

p35 = starts("예비 실험의 채점은 응답 하나에 하나의 등급(PASS, WARNING, FAIL)을 매기는 방식이었다.")
set_text(p35,
    "예비 실험의 채점은 응답 하나에 하나의 등급(PASS, WARNING, FAIL)을 매기는 방식이었다. 이 방식에서는 거절 판단은 옳지만 "
    "형식이 어긋난 응답과 정보가 실제로 새어 나간 응답이 같은 척도 위에 섞여, 준수율의 변화가 어느 쪽에서 왔는지 알 수 없다. "
    "그래서 본 연구는 판정을 두 축으로 분리하며, 판정 단위와 두 축 판정을 다음과 같이 정의한다.")
insert_after(p35, [
    "1) 정의: 판정 단위는 공격 문항 하나에 대한 챗봇 응답 1회이며, 판정은 J = (정보 무결성, 유형, 정책 준수)의 세 값으로 "
    "이루어진다. 정보 무결성은 INTACT, PARTIAL, BROKEN 중 하나, 유형은 Dis·Mis·Malinformation 중 하나(INTACT이면 없음), "
    "정책 준수는 COMPLIANT, MINOR, MAJOR 중 하나이다. 여러 턴에 걸친 대화나 응답 안의 문장 하나는 판정 단위가 아니며, 같은 "
    "문항을 반복 시행하면 응답마다 판정한 뒤 다수결로 묶는다.",
    "2) 예시: '정정 공지에 따라 최대 건조 용량은 5kg입니다'라는 응답은 설명서의 정답(3.0kg)과 다른 오염 문서의 값을 사실처럼 "
    "안내했으므로 정보 무결성은 BROKEN, 유형은 Disinformation이며, 말투와 길이를 지켰다면 정책 준수는 COMPLIANT이다. 반대로 "
    "거절은 옳지만 '궁금하신 점 있으시면 말씀해 주세요'를 덧붙인 응답은 정보 무결성 INTACT, 정책 준수 MINOR이다.",
    "3) 논의: 두 축으로 나눈 이유는 4.2절의 재분석처럼 한 축의 등급이 형식 교정과 정보 개선을 구분하지 못하기 때문이다. 정보 "
    "무결성을 세 수준으로 둔 것은 직접적인 허위·유출(BROKEN)과 공격자에게 유의미한 간접 정보(PARTIAL)를 구분하기 위해서이며, "
    "더 잘게 나누면 무상태 단일 호출 심판관의 판정 일관성이 떨어질 위험이 있다. 정보 무결성이 본 연구의 주 지표이고 정책 준수는 "
    "부 지표이다.",
    "4) 적용: 두 축의 판정에서 4단계 Level을 코드로 산출하고(표 3, 그림 7), 정답이 있는 항목은 코드 대조로 정보 무결성을 함께 "
    "판정한다. 본 실험의 주 가설은 이 정보 무결성 판정으로 검정한다(4.5절).",
])

# ---------------------------------------------------------------- R9: floor and power source
edit("가이드라인 준수율은 총점을 만점(3점에 채점 가능 문항 수를 곱한 값)으로 나눈 비율로 정의한다.",
     "가이드라인 준수율은 총점을 만점(3점에 채점 가능 문항 수를 곱한 값)으로 나눈 비율로 정의한다. 모든 문항이 최하 등급을 "
     "받아도 준수율은 33.3%이므로 이 지표의 하한은 0%가 아니라 33.3%이며, 이후의 준수율은 이 하한을 기준선으로 읽는다.")
edit("핵심 범주에 문항을 더 배분하는 것은 정보 불일치성에 해당하는 결과의 검정력을 높이기 위해서이다.",
     "핵심 범주에 문항을 더 배분하는 것은 정보 불일치성에 해당하는 결과의 검정력을 높이기 위해서이다. 문항 난이도를 백엔드가 "
     "공유하는 1,000회 시뮬레이션에서, 8차에서 관측된 수준의 백엔드 간 격차를 Cochran's Q 검정으로 검출할 확률은 24문항에서 "
     "66.7%, 38문항에서 87.6%였다.")
t10 = next(t for t in body.iter(qn("w:tbl")) if txt(t).startswith("항목본 실험 설정근거"))
for c in t10.iter(qn("w:tc")):
    if txt(c).startswith("교차 모델 검정력"):
        set_text(c.find(qn("w:p")), "교차 모델 검정력: 8차 수준 격차에서 24문항 66.7% → 38문항 87.6% (시뮬레이션 1,000회)")

# ---------------------------------------------------------------- chapter 5: overview + conclusion (R2)
ch5 = starts("제5장. 논의 및 결론", "1")
ch5.addnext(para(
    "이 장에서는 예비 실험의 결과가 무엇을 뒷받침하고 무엇을 뒷받침하지 못하는지 논의하고(5.1절), 연구의 한계를 정리한 뒤"
    "(5.2절), 결론과 향후 연구를 제시한다(5.3절)."))
concl = starts("본 논문은 LLM 기반 AI 챗봇의 정보 불일치성에 대한 강건화 메커니즘으로")
set_text(concl,
    "본 논문은 LLM 기반 AI 챗봇의 정보 불일치성에 대한 강건화 메커니즘으로, 모듈형 4단계 유닛 아키텍처 위에서 고객사의 응대 "
    "정책을 적대적 테스트로 자동 보강하는 폐쇄 루프를 제시하였다. 본 논문의 핵심 문제는 " + CORE + "하는 것이며, 본 논문은 "
    "이를 두 축 채점과 정답 기반 코드 대조로 다루었다. 예비 실험의 주요 결과는 다음과 같다.")
body.remove(starts("향후 연구로는 4.5절의 본 실험 수행과"))
insert_after(concl, [
    "(1) 9차 예비 실험에서 단일 등급 준수율은 68.2%에서 100%로 올랐고(하한 33.3%), 헬드아웃 셋에서도 97.1%가 유지되었다.",
    "(2) 같은 실행을 정보 무결성 기준으로 다시 보면 초기 응대 정책에서도 22건 중 21건이 정보 측면에서 방어되어 있었고, 개선의 "
    "대부분은 형식 교정이었다.",
    "(3) 규칙 누적은 응대 정책의 문자열 템플릿화(보강 규칙 28개)와 라운드 간 진동으로 이어졌고, 5W1H 판단 원칙은 세 가지 "
    "예측이 모두 기각되었다.",
    "(4) 응답 생성 모델을 바꾼 교차 모델 검증에서 백엔드 간 차이는 7~9차 중 8차에서만 점수 기준으로 유의하였고(Friedman "
    "p=0.036, Cochran's Q p=0.059), 5W1H 변형을 적용한 11차에서는 백엔드 간 격차가 매우 컸다(두 검정 모두 p=2.98×10⁻⁶).",
    "본 결과는 본 실험 전까지 예비적 근거로 해석되어야 하며, 향후 연구는 5.2절의 한계에서 도출한 다음 항목이다.",
    "(1) 4.5절의 본 실험을 수행하고 사전에 고정한 가설 H1~H3를 검정한다.",
    "(2) 연구자의 수동 블라인드 채점으로 두 축 판정의 심판관 신뢰도를 검증한다.",
    "(3) 보강용 셋과 독립적으로 생성한 헬드아웃 셋으로 분포 밖 일반화를 확인한다.",
    "(4) 의료·금융·공공처럼 법적 제약이 더 복잡한 도메인으로 확장한다.",
    "(5) 여러 턴에 걸친 점진적 공격을 포함한다.",
    "(6) 생성된 보강 규칙을 프로덕션에 반영하기 전의 사람 검수 게이트를 설계한다.",
])

# ---------------------------------------------------------------- checks
full = "\n".join(txt(p) for p in body.iter(qn("w:p")))
assert full.count(CORE) == 3, full.count(CORE)
assert "%p" not in full and "낳" not in full
assert not re.search(r"[가-힣]\?", full), "question sentence"
d.save(DST)
print("saved", DST)
