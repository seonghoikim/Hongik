# 영문 문체 (문형 재사용, AI 문체 제거, 교정 기준)

## 1. 핵심 원칙: 창작하지 않는다

교수님 영문 문체의 실체는 자기 문형의 재사용이다. 교정본을 비교해 보니, 새로 교정하신 문장들이 교수님의 과거 논문 문장 틀과 같았다. 매끈하게 새로 쓴 문장일수록 AI가 쓴 것처럼 읽힌다.

따라서 영문을 쓸 때의 절차는 다음과 같다.
1. 문형 은행(phrase bank)에서 맞는 틀을 고른다.
2. 틀의 빈칸(X, Y)에 내 내용만 넣는다.
3. 틀에 맞지 않는 문장은 평이한 공학 서술로 쓴다. 수사를 더하지 않는다.

문형 은행 만드는 법:
- 저자나 교수님의 기존 논문(본인이 가진 것)에서 초록, 서론, 정의, 결론의 문장 구조를 뽑는다.
- 뽑은 문장을 X, Y, Z 같은 빈칸이 있는 틀로 바꾼다.
- 틀을 `kim_phrase_bank.md` 같은 파일 하나에 모으고, 영문 작성 때마다 먼저 연다.
- 남의 논문 문장을 그대로 옮기지 않는다. 틀(구조)만 옮긴다. 출판물의 문장을 복제하면 저작권 문제가 생긴다.

Why: 교수님이 2003년 국제 학회 논문과 2026년 교정본의 문장을 대조했을 때, 교정에서 새로 들어온 문장이 과거 논문의 문장을 재사용한 것이었다.
How: 새 문장을 쓰기 전에 은행에서 같은 기능의 틀이 있는지 먼저 찾는다. 있으면 그 틀을 쓴다.

## 2. 문형 틀 (설명용 일반형)

아래는 교수님 영문 교정 패턴에서 추출한 구조다. 빈칸은 내 내용으로 채운다.

문장 층위:
- 초록 첫 문장: `This paper describes a part of an extended {method} for {domain}.`
- 구조 설명: `{Method} is based on {foundation}, which partitions {object} into {parts}.`
- 무관사 제안 주어: `Proposed {method} and {method2} measure and produce {output} to enhance {goal}.`
- 사례 도입: `To illustrate, the proposed approach uses an example of {case}.`
- 절 도입: `In this section, we present what we propose.`
- 범위 한정: `We claim no uniqueness across {scope}.`
- 기대 표현: `We expect to {verb} {object}.`
- 선행 인정(능동): `{Author} et al. proposed {X} for {Y}.`
- 용어 재정의: `We refine {Author}'s notion of {concept} with {extension}.`
- 분사구 선행: `Therefore, focused on {X}, we deal with {Y}.`
- 대칭 구조: `{Method} combines them` (X is the role of Y 대신)
- 사례 소개: `In the case study, {statement}.` (쉼표 필수)
- 결과 확인: `The results confirm that {claim}.`
- 신중한 주장: `We believe that this method can lead to {effect}.`
- 수치 비교: `{metric} = {value}, outperforming {baseline} ({baseline value}).`

단락 층위:
- 개념마다 네 단: 정의(튜플) → 예시(그림·표) → 논의 → 적용(definitions-and-gap.md 참조)
- 방법론 접점마다 자기 계보 인용: `Kim [1][2]`. 문구 자체도 자기 논문에서 가져온다.

## 3. AI 문체 장치 걷어내기

교수님이 교정에서 삭제하거나 다시 쓰신 장치들이다. 아래 장치가 보이면 평이한 공학 서술로 바꾼다.

| 장치 | 예 (일반형) | 교정 방향 |
|---|---|---|
| 은유 | "the check is blind to whether ..." | "the check does not verify whether ..." |
| 의인화 | "The procedure tells us how many scenarios ..." | 문장 삭제 또는 "We compute ..." |
| 질문-답 수사 | "We ask how ... and answer with ..." | 질문만 남기거나 평서문으로: "How can a test agent cover ...?" 그 뒤에 바로 방법을 쓴다 |
| 정교한 3항 병렬 | "slow, costly, and blind" | 평서 문장 둘 |
| 강조 부사 | actually, at all, precisely, truly | 삭제 |
| 우아한 무생물 주어 | "The method yields ..." | "We obtain ..." (we 주어로) |
| 선언 수사 | "The core problem of this paper is therefore a single sentence:" | "The problem is ..." 로 바로 쓴다 |
| 도입 대구 | "Two of the six deserve a word on why they are separate." | "Two are described separately, because ..." |

흔한 AI 어휘(피한다. 원천 밖의 일반 지침이며 린트의 en-ai-style 규칙과 같다): delve, tapestry, landscape(비유), crucial, pivotal, showcase, "It is worth noting", "In today's".

공통점: 긴장을 만드는 수사를 모두 걷어내고, 문장이 밋밋해도 공학 서술로 남긴다. 2026-08-31 교정 분석에서 교수님은 수사를 덧붙이지 않고 평이한 서술로 직접 고치셨다.

## 4. 지킬 것 (교수님 교정 패턴)

- 주어는 we. 능동태를 쓴다. 예: "Kim et al. proposed X" (수동 "was proposed by" 금지).
- 강한 주장 앞에는 "We expect to", "We claim"을 붙여 주장의 주체를 밝힌다.
- 소유격 압축: "the graph's execution order" (the execution order of the graph 대신).
- 동사 압축: "their combination is the role of M5" → "M5 combines them".
- 하이픈 복합어: sub-path, path-occurrence probability, test-priority score, test-case reusability.
- em-dash는 앞뒤 공백 없이 붙인다: "chain—use case".
- 미국식 철자: color, behavior, catalog, optimize.
- 도입 쉼표: "In the case study, ...", "For the fashion store, ...".
- 1인칭은 we. I를 쓰지 않는다.
- 전환어: Further, (세부 추가), Thus, (논리적 귀결), In addition, (추가), However, (대조), As a result, (결과), In other words, (바꿔 말하기).

## 4-1. 시제

- 확립된 사실과 방법 설명: 현재형. "{Method} is ..."
- 이 절에서 다룰 내용 예고: 미래형. "Section {n} will describe ..."
- 선행 연구 소개: 과거형. "{Author} proposed {X}."
- 빈 곳(gap) 지적: 현재완료. "Until now, no {approach} has addressed {problem}."

## 5. 흉내 내지 말아야 할 것

과거 논문에는 비원어민의 오류(관사 누락, 동사 선택 오류 등)가 있다. 문형과 어휘 선택은 따르되, 문법 오류는 재현하지 않는다. 문법 기준은 가장 최근 교정본이다.

## 6. 교정 절차

교수님이나 동료가 교정한 원고가 있으면 다음 순서로 패턴을 뽑는다.
1. 직전본과 교정본을 문장 단위로 비교한다(diff). 교정 건수를 센다.
2. 교정 유형을 분류한다: 수사 제거, 주어 변경, 복합어 표기, 쉼표, 철자, 문형 교체.
3. 같은 유형이 새 원고에도 있는지 검색해 같은 방식으로 고친다.
4. 교정자가 직접 고친 문장은 건드리지 않는다.

## 7. 정의와 예시의 영문 표기

- `1) Definition:` `2) Example:` `3) Discussion:` `4) Application:`
- 정의 번호 체계(Definition 1 …)와 Algorithm 번호는 쓰지 않는다.
- 예시 문장에는 그림이나 표 번호를 붙인다: "as shown in Figure 4" / "as listed in the left column of Table 2".
- 캡션 형식: "Figure N. Title.", "Table N. Title."(번호 뒤와 제목 끝에 마침표). 본문에서는 "Figure N shows ...", "Table N illustrates ..."로 가리킨다. 그림 캡션은 아래, 표 캡션은 위에 둔다.

## 8. 제목 패턴

제목은 교수님이 승인한 형식을 따른다. 구조 예: `<Method> Based <Task> & <Metric> Based on a <Approach> for <Domain>`. 어순은 승인본을 기준으로 하고, 임의로 바꾸지 않는다.

## 9. 신중한 주장과 수치 문장

- 주장은 데이터가 뒷받침하는 만큼만 쓴다. 강한 주장은 "The results confirm that"처럼 데이터 뒤에 둔다.
- 보수적 추정은 라벨을 붙인다: "This estimate is conservative; actual savings are likely higher."
- 위협 요인은 논의 절에 명시한다.

## 10. 영문 작성 체크리스트

- [ ] 문형 은행에서 고른 틀인가, 창작한 문장인가
- [ ] 은유, 의인화, 질문-답, 강조 부사가 없는가
- [ ] 주어가 we이고 능동태인가
- [ ] "was proposed by"가 없는가
- [ ] em-dash에 공백이 없는가
- [ ] 미국식 철자인가
- [ ] 도입 쉼표가 있는가
- [ ] 인용이 [1][2] 형식이고 번호만 주어로 쓰지 않았는가
- [ ] 수치 문장에 기준선이 있는가
