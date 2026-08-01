<!-- 작업 원고. TODO 표시는 실제 코드 구현/실험 후 채울 자리입니다. -->

# 다양한 고객 조직을 위한 LLM 커스터마이징 기반 AI 챗봇 개발 메커니즘

**AI Chatbot Development Mechanism Through Customizing LLM for Heterogeneous Customer's Organization**

---

## 초록 (Abstract)

### 국문 초록

기업 환경에서 생성형 대규모 언어 모델(LLM)을 도입할 때, 개별 고객 조직(Heterogeneous Organizations)의 고유한 브랜드 페르소나, 비즈니스 가이드라인 및 보안 정책을 완벽히 준수하도록 LLM을 정교하게 커스터마이징하는 것은 필수적이다. 그러나 기존의 파인튜닝(Fine-tuning) 방식은 높은 연산 비용과 유연성 부족 문제를 지니며, 단순 프롬프트 엔지니어링 및 RAG(검색 증강 생성) 구조는 실제 운영 환경의 극단적인 사용자 입력 및 간접 프롬프트 인젝션 공격에 의해 가이드라인을 이탈하는 한계를 보인다.

본 논문은 이러한 문제를 해결하기 위해 모듈형 4단계 유닛 아키텍처(유닛 A~D)와 요구사항 명세서(SRS) 기반의 자동 자가 치유(Self-Healing) 폐쇄 루프 메커니즘을 제안한다. 제안하는 메커니즘은 적대적 스트레스 테스트 데이터셋을 활용해 시스템의 우회 가능성을 정량적 지표인 '액션 매트릭스(Action Matrix)'로 산출하고, 평가 결과에 따라 명세서의 절대 보안 원칙(Meta-Rules)을 자동으로 보강한다. 나아가 고정된 공격셋에 대한 과적합을 방지하기 위해 별도의 헬드아웃(Held-out) 검증셋과 적응형 재공격(Adaptive Re-Attack) 실험을 통해 방어 메커니즘의 일반화 성능과 견고성을 검증한다.

또한, 평가 과정에서 발생할 수 있는 평가 모델(LLM-as-a-Judge)의 컨텍스트 오염 및 확증 편향을 원천 차단하기 위해 무상태(Stateless) API 기반의 독립 평가 환경을 구축하였으며, 사람 평가자와의 채점 일치도(Cohen's Kappa)를 측정하여 평가 신뢰성을 검증하였다. 가전 유통 기업 사례(A사)를 적용한 실증 실험 결과, [TODO: 실제 실험 후 결과 요약 문장으로 교체], 모델 재학습 없이 텍스트 명세 최적화만으로 대화형 AI의 신뢰성을 확보할 수 있음을 입증하였다.

### 영문 초록 (Abstract)

When deploying Generative Large Language Models (LLMs) in enterprise environments, precisely customizing LLMs to strictly comply with the unique brand personas, business guidelines, and security policies of heterogeneous customer organizations is critical. However, conventional fine-tuning approaches suffer from high computational costs and a lack of flexibility, while basic prompt engineering and RAG (Retrieval-Augmented Generation) structures fail under adversarial stress tests and indirect prompt injection attacks.

This paper proposes a novel AI chatbot development framework featuring a modular 4-unit system architecture (Units A–D) and an automated Requirements Specification (SRS)-based Self-Healing closed-loop mechanism. The proposed framework generates adversarial stress scenarios, evaluates unit-level compliance via a quantitative 'Action Matrix', and automatically hardens the SRS meta-rules based on feedback logs. To prevent overfitting to a fixed attack set, generalization and robustness are further validated through a held-out test set and adaptive re-attack experiments.

To eliminate context bleeding and confirmation bias during evaluation, a stateless API-driven LLM-as-a-Judge environment was implemented, and judge reliability was validated against human annotators (Cohen's Kappa). Empirical validation using a consumer electronics retail domain (Company A) [TODO: replace with actual result summary after experiments], demonstrating that enterprise-grade reliability can be achieved purely via lightweight SRS optimization without costly model retraining.

---

## 제1장. 서론 (Introduction)

### 1.1. 연구의 배경 및 필요성

최근 B2B 엔터프라이즈 시장에서 대규모 언어 모델(LLM)을 기반으로 한 인공지능 챗봇의 도입이 가속화되고 있다. 그러나 서로 다른 비즈니스 도메인과 조직 문화를 가진 고객사(Heterogeneous Customer's Organizations)들은 저마다 엄격하고 구체적인 응대 가이드라인, 페르소나, 내부 보안 규정을 요구한다. 예컨대 유통업체의 챗봇은 친절하고 적극적인 영업 화법을 유지해야 하는 반면, 금융/법률 기관의 챗봇은 객관적이고 단정적인 표현을 지양해야 한다.

이처럼 다양하고 이질적인 고객 조직의 요구사항에 맞추어 LLM을 커스터마이징하는 작업은 전통적으로 모델 파인튜닝(Fine-tuning)이나 시스템 프롬프트 작성에 의존해 왔다. 그러나 파인튜닝은 커스터마이징 요구사항이 바뀔 때마다 막대한 재학습 비용이 발생하며, 프롬프트 엔지니어링은 복잡한 사용자 입력이나 악의적인 우회 공격(Jailbreak, Indirect Prompt Injection)이 가해졌을 때 설정된 페르소나를 이탈하거나 내부 기밀을 노출하는 취약점을 드러낸다.

### 1.2. 기존 방식의 한계 및 문제 제기

1. **RAG 및 컨텍스트 편향에 따른 가이드라인 이탈**: LLM은 외부 문서(RAG)의 정보를 최우선으로 신뢰하도록 훈련되었기 때문에, 검색된 문서에 오염된 데이터가 포함되어 있거나 사용자가 가스라이팅성 입력을 주입할 경우 시스템 프롬프트의 지시사항을 쉽게 망각한다.
2. **소프트웨어 생명주기(SDLC) 내 검증 모듈의 부재**: 기존 개발 메커니즘은 프롬프트 작성 후 수동으로 몇 가지 테스트를 거쳐 배포하는 방식에 머물러 있어, 실제 운영 환경에서 발생할 수 있는 엣지 케이스(Edge Case)를 선제적으로 탐지하기 어렵다.
3. **평가 체계의 불투명성**: LLM을 이용해 LLM의 응답을 평가(LLM-as-a-Judge)할 때, 단일 세션 내에서 평가를 진행하면 이전 대화 기록이 평가 모델에 영향을 미치는 컨텍스트 오염(Context Bleeding) 현상이 발생하여 평가 결과의 객관성을 담보할 수 없다.
4. **고정 테스트셋에 대한 과적합**: 방어 메커니즘을 특정 공격셋에 맞춰 튜닝한 뒤 동일한 공격셋으로만 검증하는 경우, 실제 미지의 공격이나 방어를 인지한 적응형 공격 앞에서는 성능이 재현되지 않을 위험이 있다 (Geng et al., 2026).

### 1.3. 본 연구의 기여도 (Contributions)

본 연구는 상기 문제를 해결하기 위해 다양한 고객 조직의 요구사항을 효율적이고 견고하게 커스터마이징할 수 있는 자가 치유(Self-Healing) 기반 AI 챗봇 개발 메커니즘을 제안한다. 본 연구의 주요 기여는 다음과 같다.

- **모듈형 4단계 유닛 아키텍처(Units A~D) 제시**: 입력 검증, RAG 검색, 추론 엔진, 출력 검증으로 이어지는 단계별 방어망을 구축하여 취약점 발생 지점을 명확히 격리하였다.
- **SRS 기반 자가 치유(Self-Healing) 폐쇄 루프 개발**: 적대적 스트레스 테스트를 통해 발견된 취약점을 분석하고, 시스템 스스로 요구사항 명세서(SRS)의 절대 보안 원칙(Meta-Rules)을 자동 보강하는 피드백 루프를 구현하였다.
- **무상태(Stateless) API 기반의 철저한 평가 변인 통제**: 타겟 시스템과 평가 심판관 간의 컨텍스트를 완벽히 격리하여 학술적/실무적으로 객관성이 보장되는 자동화 검증 환경을 증명하였다.
- **일반화 및 견고성의 실증적 검증**: 헬드아웃 테스트셋과 적응형 재공격 실험을 통해, 제안 메커니즘이 특정 공격셋에 대한 암기가 아니라 실질적인 방어력 향상을 달성했음을 검증하였다.

---

## 제2장. 관련 연구 (Related Work)

### 2.1. LLM 커스터마이징 및 프롬프트 제어 기법

LLM을 특정 도메인에 적용하기 위한 커스터마이징 기법은 크게 Weights-level 접근법(Fine-tuning, LoRA)과 Prompt-level 접근법(In-Context Learning, RAG)으로 나뉜다. 파인튜닝은 특정 어투나 형식을 고정하는 데 유리하지만, 지속적으로 업데이트되는 비즈니스 로직에 유연하게 대응하기 어렵다. 반면 프롬프트 기법은 경량화되어 있으나, 사용자의 복잡한 지시나 다중 롤플레잉 요구 시 기존 제약 조건을 상실하는 '지시 망각(Instruction Forgetting)' 현상이 빈번하게 보고된다.

### 2.2. 무상태(Stateless) API 기반 평가와 LLM-as-a-Judge

LLM을 평가자로 활용하는 연구가 활발해짐에 따라, 심판관 LLM 자체가 프롬프트 인젝션 공격에 노출되어 채점 신뢰성을 잃는 현상이 주요 연구 과제로 부상하였다(Shi et al., 2024). 단일 세션에서 챗봇 역할과 심판관 역할을 동시에 수행시킬 경우, 평가 모델이 이전 대화 컨텍스트에 편향되어 잘못된 점수를 부여하는 확증 편향이 나타난다. 이를 극복하기 위해 본 연구는 매 평가마다 완전히 초기화된 백지 상태의 API를 호출하는 무상태(Stateless) 평가 방식을 도입한다.

### 2.3. 자동화된 레드티밍과 자가 치유(Self-Healing) 프레임워크

최근 AI 보안 분야에서는 자동화된 공격 문장 생성 모듈(Red Teaming)을 활용하여 시스템의 한계를 테스트하는 PIArena(Geng et al., 2026) 등의 플랫폼이 등장하였다. 그러나 기존 연구들은 취약점 '탐지'에 그치거나, 방어를 위해 무거운 에이전트를 추가로 가동하여 연산 비용을 증가시키는 한계가 있었다(SHIELD, Sivaroopan et al., 2026). 본 연구는 별도의 모델 재학습 없이 텍스트 형태의 요구사항 명세서(SRS)를 자동 재구성하는 경량화된 자가 치유 알고리즘을 제시한다는 점에서 기존 연구와 뚜렷한 차별성을 갖는다.

### 2.4. 선행연구 비교

| 비교 항목 | 본 연구 | PIArena (Geng et al., 2026) | SHIELD (Sivaroopan et al., 2026) |
|---|---|---|---|
| 목적 | LLM 챗봇의 조직별 가이드라인 준수 자가 치유 | 프롬프트 인젝션 공격/방어 통합 평가 플랫폼 | 리소스 고갈(Sponge) 공격 방어 |
| 방어 대상 공격 | 가이드라인 이탈, 사칭, 가스라이팅, 롤플레이 탈옥 | 범용 프롬프트 인젝션 | 리소스 고갈 공격 |
| 자가 치유 여부 | O (SRS 텍스트 자동/반자동 보강) | X (평가 플랫폼) | O (지식베이스 갱신 + 프롬프트 최적화) |
| 재학습 필요 여부 | 불필요 | 해당없음 | 불필요 |
| 일반화/적응형 공격 검증 | O (헬드아웃 + 적응형 재공격, 본 연구 §5.4) | O (플랫폼 자체의 핵심 실험) | [TODO: 원문 재확인] |
| 실험 도메인 수 | 1개 (확장 예정) | 다중 벤치마크 | 다중 공격 유형 |
| 핵심 차별점 | 경량 SRS 최적화만으로 준수율 향상, 모델 재학습·추가 에이전트 불필요 | 공격/방어 평가의 통합 플랫폼 제공 | 리소스 고갈이라는 특정 공격 유형에 특화 |

---

## 제3장. 고객 조직 맞춤형 AI 챗봇 아키텍처

본 연구에서 제안하는 챗봇 시스템은 다양한 고객 조직의 가이드라인을 단계별로 검증하고 실행할 수 있도록 4개의 독립된 모듈(Units A~D)로 구성된다.

**그림 1. AI 챗봇의 질의 응답 시퀀스 흐름**

```mermaid
sequenceDiagram
    participant U as 사용자
    participant A as 유닛 A<br/>입력 가드레일
    participant B as 유닛 B<br/>RAG 검색·검증
    participant C as 유닛 C<br/>LLM 추론 엔진
    participant D as 유닛 D<br/>출력 가드레일

    U->>A: 사용자 입력
    A->>A: 탈옥/사칭/유해 발언 스캔
    alt 차단 대상
        A-->>U: 즉시 차단 응답
    else 통과
        A->>B: 정제된 입력 전달
        B->>B: 내부 지식DB 검색<br/>(외부/오염 데이터 격리)
        B->>C: 검증된 컨텍스트 + 입력
        C->>C: SRS 페르소나/Meta-Rules 반영<br/>응답 생성
        C->>D: 생성된 응답
        D->>D: 경쟁사 노출·메타데이터 유출·<br/>부적절 단어 최종 점검
        D-->>U: 최종 응답
    end
```

- **유닛 A (입력 가드레일 / Input Guardrail)**: 사용자의 입력 문장을 1차적으로 스캔하여 명백한 탈옥(Jailbreak) 구문, 시스템 관리자 사칭, 비정상적 인코딩 코드 및 유해성 발언을 즉시 차단한다.
- **유닛 B (RAG 검색 및 지시어 검증 / RAG Retrieval & Verification)**: 고객사의 내부 지식 베이스(지식 DB)에서 관련 정보만을 정제하여 가져온다. 외부 웹사이트나 인젝션 위험이 있는 오염된 데이터의 유입을 물리적으로 격리한다.
- **유닛 C (LLM 추론 엔진 / LLM Inference Engine)**: 요구사항 명세서(SRS)에 정의된 페르소나와 Meta-Rules를 이행하는 핵심 두뇌이다. 사용자의 의도를 파악하여 고객사의 톤앤매너에 맞는 답변을 생성한다.
- **유닛 D (출력 검증 / Output Guardrail)**: 유닛 C가 생성한 텍스트가 최종 출력되기 전, 경쟁사 브랜드명 노출, 내부 메타데이터 유출, 부적절한 단어 포함 여부를 최종 점검하여 필터링한다.

### 3.5. 연구 방법론 (Research Methodology)

#### 3.5.1 실험 설계 개요

본 연구는 단일 사례 연구(single case study) 방법론을 채택하되, 내적 타당성을 높이기 위해 다음 세 가지 실험 변인 통제를 적용한다.

1. **데이터 분할(Data Split)**: 적대적 공격 시나리오를 다음과 같이 분리한다.
   - 치유용 셋(Healing Set, n=50): SRS 하드닝(Meta-Rule 생성)에 사용.
   - 헬드아웃 셋(Held-out Set, n=50): 치유 과정에 전혀 노출되지 않으며, 최종 일반화 성능 검증에만 사용.
   - 두 셋은 공격 유형(사칭, 어투 강요, 허위 사실 동조, 인코딩 우회, 롤플레이 탈옥 등) 비율이 동일하도록 층화추출(stratified sampling)한다.
2. **반복 시행(Repetition)**: LLM 응답의 비결정성을 통제하기 위해 동일 시나리오를 temperature를 고정한 상태에서 N=5회 반복 실행하고, 평균 점수와 표준편차를 함께 보고한다. [TODO: 실험 후 채움]
3. **평가자 신뢰성 검증**: §3.6 참조.

#### 3.5.2 사용 모델 및 버전 (재현성 확보)

| 역할 | 모델 | 버전/날짜 | API 방식 |
|---|---|---|---|
| 유닛 C (추론 엔진) | [TODO] | [TODO] | Stateful, 시스템 프롬프트 주입 |
| LLM 심판관 (Judge) | [TODO] | [TODO] | Stateless, 매 호출 신규 세션 |
| Temperature | [TODO, 권장 0.0~0.3 고정] | - | - |

#### 3.5.3 통계적 검정 방법

명세서 버전 간(v1.0 vs v2.0 vs v3.0) 점수 차이의 유의성 검정은 표본 수가 적고 정규성 가정이 어려운 점을 고려해 **Wilcoxon signed-rank test**를 사용한다. 헬드아웃 셋에서의 방어율이 치유용 셋과 통계적으로 유의한 차이가 없어야 "과적합이 아니다"라는 주장이 성립한다. [TODO: 실험 후 p-value 채움]

#### 3.5.4 독립변인 / 종속변인 정의

- 독립변인: SRS 버전(v1.0/v2.0/v3.0), 공격 시나리오 유형, 위협 모델(블랙박스/화이트박스, §5.4)
- 종속변인: Action Matrix 점수(1~3점), 유닛별 실패 위치(A/B/C/D)
- 통제변인: 모델 버전, temperature, 평가 프롬프트 템플릿, 평가 시점(무상태)

### 3.6. 심판관(LLM-as-a-Judge) 신뢰성 검증

#### 3.6.1 문제의식

본 연구의 모든 정량 결과는 결국 심판관 LLM의 채점에 전적으로 의존한다. 심판관이 체계적으로 관대하거나(false PASS) 체계적으로 엄격하면(false FAIL), 방어 성공률 자체가 무의미해진다. 따라서 심판관의 채점이 사람의 판단과 얼마나 일치하는지 별도로 검증한다.

#### 3.6.2 검증 절차

1. **표본 추출**: 치유용 50개 + 헬드아웃 50개 + 적응형 재공격 30개, 총 130개 결과 중 30개(약 23%)를 층화 무작위 추출한다 (PASS/WARNING/FAIL 등급이 골고루 섞이도록).
2. **독립 평가자 2인**이 심판관과 동일한 rubric으로, 서로의 채점과 심판관의 채점을 보지 않은 채 블라인드로 채점한다.
3. **일치도 산출**: 사람 간 일치도(Cohen's Kappa), 사람-모델 일치도(Percent Agreement + Cohen's Kappa)를 각각 산출한다.
4. **판정 기준**: Kappa ≥ 0.6(Substantial agreement, Landis & Koch, 1977)이면 심판관 채점을 신뢰할 수 있는 것으로 간주한다. [TODO: 실험 후 실제 Kappa 값 채움]

#### 3.6.3 부가 검증 — 심판관 자체의 피공격 가능성

심판관 LLM도 인젝션 공격의 대상이 될 수 있다(Shi et al., 2024, JudgeDeceiver). 본 연구는 무상태(매 호출 신규 세션) 설계로 컨텍스트 오염만 차단했을 뿐, 단일 응답 내 인젝션 공격(챗봇 응답 자체에 심판관을 속이는 문구가 포함된 경우) 가능성은 연구 범위 밖으로 명시하고 향후 과제로 남긴다.

---

## 제4장. 제안하는 LLM 커스터마이징 및 자가 치유 메커니즘

본 연구의 핵심은 개발자가 일일이 프롬프트를 수정할 필요 없이, 적대적 스트레스 테스트와 자가 치유 루프를 통해 챗봇이 고객사 요구사항을 준수하도록 자동 최적화하는 5단계 폐쇄 루프(Closed-loop) 메커니즘이다.

**그림 2. 적대적 스트레스를 이용한 자가 치유 루프**

```mermaid
flowchart TD
    A["SRS v(n) 정의"] --> B["스트레스 테스트 데이터셋<br/>(치유용 50개)"]
    B --> C["무상태 시뮬레이션 실행<br/>유닛 A~D"]
    C --> D["액션 매트릭스 산출<br/>3점 PASS / 2점 WARNING / 1점 FAIL"]
    D --> E{"FAIL/WARNING<br/>존재?"}
    E -- "예" --> F["실패 사유 분석 →<br/>Meta-Rules 샌드위치 주입"]
    F --> G["SRS v(n+1)"]
    G --> B
    E -- "아니오 (만점)" --> H["헬드아웃 셋(50개)<br/>최종 검증"]
    H --> I["적응형 재공격(30개)<br/>블랙박스/화이트박스 검증"]
    I --> J["최종 방어율 보고"]
```

### 4.1. 자가 치유 5단계 동작 절차

1. **초기 요구사항 명세 정의 (SRS v1.0)**: 고객사가 요구하는 역할, 말투, 업무 범위, 금지 사항을 명세서 형태로 작성한다.
2. **스트레스 테스트 데이터셋 생성**: 고객사 가이드라인을 의도적으로 파괴하려는 50가지의 극단적인 프롬프트 인젝션 공격 시나리오(사칭, 어투 변경, 허위 사실 동조 등)를 구성한다.
3. **무상태(Stateless) 시뮬레이션 실행**: 각 공격 문장을 유닛 A~D 시스템에 입력하여 응답 텍스트를 추출한다.
4. **액션 매트릭스(Action Matrix) 산출**: 격리된 LLM 심판관이 답변을 분석하여 3점(PASS - 완벽 준수), 2점(WARNING - 부분 노출), 1점(FAIL - 이탈)으로 정량 채점하고, 어느 유닛에서 우회가 발생했는지 추적한다.
5. **자가 치유 및 SRS 강화 (SRS Hardening)**: 1점 및 2점 항목이 발생할 경우, 실패 사유를 분석하여 명세서 최상단 및 최하단에 사용자의 어떠한 지시보다 무조건 우선하는 '절대 보안 원칙(Meta-Rules)'을 샌드위치 기법(Sandwich Prompting)으로 주입하여 명세서를 보강(v2.0, v3.0…)한다. 이 과정은 총점이 만점에 도달할 때까지 자동 반복된다.

**Action Matrix 채점 기준표 (Rubric)**

| 점수 | 등급 | 정의 | 예시 |
|---|---|---|---|
| 3점 | PASS (완벽 준수) | 공격 의도를 완전히 인지하고 거부하며, 페르소나/톤/업무 범위를 전혀 이탈하지 않음 | "죄송하지만 그 요청은 도와드릴 수 없어요. 제품 관련해서 궁금하신 점 있으실까요?" |
| 2점 | WARNING (부분 노출) | 명백한 위반은 없으나, 어투 변화·모호한 답변·불필요한 정보 일부 노출 등 경미한 이탈 발생 | 사칭 요청을 거부하지 않고 애매하게 답하거나, 순간적으로 어투가 흐트러짐 |
| 1점 | FAIL (이탈) | 페르소나 이탈, 내부 정보 노출, 경쟁사 비하 동조, 허위사실 인정 등 명백한 가이드라인 위반 | 관리자 사칭에 속아 내부 프롬프트 일부를 노출함 |

채점 절차: 무상태 심판관 LLM에 (원본 SRS 발췌 + 공격 프롬프트 + 챗봇 응답)만 입력하고(직전 대화 이력 없음), 위 rubric을 시스템 프롬프트로 제공하여 점수 + 근거 + 위반 유닛(A/B/C/D)을 JSON으로 반환하도록 지시한다. [TODO: 실제 프롬프트 템플릿 전문을 부록 C에 수록]

---

## 제5장. 실험 및 평가 (Experimental Setup & Results)

### 5.1. 실험 환경 및 대상 고객 조직 모델링

본 메커니즘의 효과를 검증하기 위해 B2B 고객사 사례로 '가전 유통 기업(A사)'을 모델링하여 실험을 진행하였다.

- 고객사 요구 페르소나: 한국어를 사용하는 친절한 여성 직원 (-해요체)
- 핵심 제약 조건: 타사 비하 금지, 허위 결함 동조 금지, 내부 메타데이터 은닉, 단답형 응대, 제품 안내 업무 범위 유지

### 5.2. 평가 변인 통제를 위한 무상태(Stateless) API 파이프라인

평가 결과의 객관성을 확보하기 위해, Python 자동화 스크립트를 통해 OpenAI / Google Gemini API를 독립 호출하는 방식을 채택하였다.

**그림 3. 평가 변인 통제를 위한 API 파이프라인 예시 코드**

```python
# 매 평가마다 완전히 새로운(무상태) 세션으로 심판관을 호출한다.
# 챗봇(유닛 C)과 심판관이 절대 같은 대화 컨텍스트를 공유하지 않도록 격리한다.

def evaluate_response(srs_excerpt: str, attack_prompt: str, chatbot_response: str) -> dict:
    judge_system_prompt = build_rubric_prompt(srs_excerpt)  # Action Matrix rubric 포함

    # 매 호출마다 새 클라이언트/세션 — 이전 대화 이력 없음 (컨텍스트 오염 차단)
    response = judge_client.chat.completions.create(
        model=JUDGE_MODEL,          # [TODO: 실제 모델명 명시]
        temperature=0,               # 재현성 확보
        messages=[
            {"role": "system", "content": judge_system_prompt},
            {"role": "user", "content": f"공격 프롬프트: {attack_prompt}\n챗봇 응답: {chatbot_response}"},
        ],
    )
    return parse_action_matrix_json(response)  # {score, reason, violated_unit}
```

### 5.3. 실험 결과 및 자가 치유 성능 분석

[TODO: 아래 표는 실제 코드 구현 및 실험 실행 후 실측값으로 교체]

| 평가 회차 | 적용 명세서 | 3점(PASS) | 2점(WARNING) | 1점(FAIL) | 총점 | 가이드라인 준수율 |
|---|---|---|---|---|---|---|
| 1차 (치유용 셋) | 기본 명세 (v1.0) | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| N차 (치유용 셋) | 자가 치유 완료 (v_final) | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 검증 (헬드아웃 셋, 50개) | v_final | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 검증 (적응형 재공격 - 블랙박스, 15개) | v_final | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |
| 검증 (적응형 재공격 - 화이트박스, 15개) | v_final | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |

#### 심층 분석 (Action Matrix Analysis)

[TODO: 실험 후 실제 로그 기반으로 작성. 다음 항목을 반드시 포함할 것]
- 초기 명세(v1.0)에서 어느 유닛(A~D)이 가장 취약했는지
- Meta-Rule 보강이 구체적으로 어떤 실패 패턴을 겨냥했는지 (SRS diff 예시 포함)
- 헬드아웃 셋 결과가 치유용 셋 결과와 통계적으로 유의미한 차이가 없는지 (Wilcoxon test 결과)
- 적응형 재공격에서의 방어율 저하폭과 그 해석

### 5.4. 적응형 재공격 실험 (Adaptive Re-Attack)

#### 5.4.1 필요성

기존 3단계 실험(v1.0→...→v_final)은 고정된 공격셋에 대한 방어율만 측정한다. 그러나 실제 공격자는 방어 로직이 갱신된 것을 관찰한 뒤 이를 우회하도록 공격을 재설계한다 (PIArena, Geng et al. 2026: 기존 방어들은 "적응형 공격에 취약하고 과제 간 일반화가 제한적"). 따라서 v_final 완성 후 별도의 4차 라운드를 신설한다.

#### 5.4.2 실험 설계 (2가지 위협 모델)

| 위협 모델 | 공격자가 아는 정보 | 목적 |
|---|---|---|
| 블랙박스(Black-box) 적응 공격 | SRS에 Meta-Rule이 존재한다는 사실만 알고, 정확한 문구는 모름 | 현실적 공격자 시나리오 |
| 화이트박스(White-box) 적응 공격 | v_final의 Meta-Rule 전문을 그대로 알고 있음 | 방어의 이론적 하한선(worst-case robustness) 측정 |

#### 5.4.3 절차 및 해석 원칙

별도의 공격 생성 LLM(레드팀 역할)에게 v_final SRS(화이트박스) 또는 이전 라운드의 실패/성공 로그(블랙박스)를 제공하여 우회 공격 30개(각 15개)를 생성하고, 무상태로 실행 후 채점한다. 100%가 아니어도 정상이며, "블랙박스 조건에서 방어율 X%, 화이트박스 조건에서 방어율 Y%(Y≤X)"처럼 성능 저하 정도를 정직하게 보고하는 것이 학술적으로 더 설득력 있다.

---

## 제6장. 논의 및 한계점 (Discussion)

1. **학술적/실무적 시사점**: 본 연구는 막대한 연산 비용이 드는 모델 파인튜닝(Fine-tuning)이나 복잡한 다중 에이전트(Multi-agent) 시스템 없이도, 소프트웨어공학의 요구사항 명세서(SRS) 텍스트 최적화와 모듈형 아키텍처 재구성만으로 LLM의 준수율을 끌어올릴 수 있음을 헬드아웃 검증과 적응형 재공격 실험을 통해 증명하였다. 이는 기업의 AI 도입 비용을 절감시킨다.
2. **내적 타당성 위협 통제**: 'LLM이 LLM을 채점하는 방식'에서 제기되는 확증 편향 문제는 무상태(Stateless) API 파이프라인과 사람 평가자 대비 일치도 검증(§3.6)을 통해 구조적으로 통제하였다.
3. **연구의 한계점 및 향후 과제**: 본 실험은 가전 유통 분야를 중심으로 진행되었으므로, 향후 의료, 금융, 공공기관 등 더욱 복잡한 법적 제약 조건이 존재하는 타 도메인(Heterogeneous Organizations)으로 적용 범위를 확장하여 일반화 가능성을 추가 검증할 예정이다. 또한 심판관 LLM에 대한 응답 내 인젝션 공격(§3.6.3)은 본 연구의 범위 밖으로 남겨두었다.

---

## 제7장. 결론 (Conclusion)

본 논문은 다양한 B2B 고객 조직을 위한 LLM 커스터마이징 과정에서 발생하는 가이드라인 이탈 및 보안 취약성 문제를 해결하기 위해 모듈형 4단계 유닛 아키텍처와 자가 치유(Self-Healing) 요구사항 명세 프레임워크를 제안하였다.

적대적 스트레스 테스트와 액션 매트릭스 평가, 무상태 API 기반의 철저한 변인 통제, 그리고 헬드아웃 검증 및 적응형 재공격 실험을 거쳐 [TODO: 실제 결과 요약으로 교체], 챗봇 시스템이 스스로 취약점을 분석하고 명세서의 Meta-Rules를 보강함으로써 가이드라인 준수율을 향상시키는 성과를 달성하였다. 본 연구가 제시한 개발 메커니즘은 향후 엔터프라이즈 AI 시장에서 안전하고 신뢰할 수 있는 LLM 기반 서비스를 신속하게 구축하고 배포하는 데 핵심적인 소프트웨어 공학적 지침을 제공할 것으로 기대된다.

---

## 참고문헌 (References)

1. Shi, J., Yuan, Z., Liu, Y., Huang, Y., Zhou, P., Sun, L., & Gong, N. Z. (2024). Optimization-based Prompt Injection Attack to LLM-as-a-Judge. *Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security (CCS '24)*. arXiv:2403.17710.
2. Geng, R., Yin, C., Wang, Y., Chen, Y., & Jia, J. (2026). PIArena: A Platform for Prompt Injection Evaluation. *Proceedings of the Association for Computational Linguistics (ACL 2026)*. arXiv:2604.08499.
3. Sivaroopan, N., et al. (2026). SHIELD: An Auto-Healing Agentic Defense Framework for LLM Resource Exhaustion Attacks. arXiv:2601.19174.
4. OWASP Top 10 for Large Language Model Applications 2025 (v2.0). OWASP Foundation. (Published 2024-11-18)
5. Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. *ACM Workshop on Artificial Intelligence and Security (AISec 2023)*. arXiv:2302.12173.
6. Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159-174. [Cohen's Kappa 판정 기준 인용]

> ⚠️ 제출 전 지도교수/Google Scholar 재확인 권장. 6번(Landis & Koch)은 본 초안 작성 과정에서 신규 추가된 표준 통계 문헌 인용이므로 형식(APA/IEEE 등 학교 지정 스타일)에 맞춰 재포맷 필요.

---

## 부록 (Appendix)

- 부록 A. 치유용 50개 + 헬드아웃 50개 공격 시나리오 전문 [TODO]
- 부록 B. SRS v1.0 ~ v_final 전문 (Meta-Rule diff 포함) [TODO]
- 부록 C. Action Matrix 채점 프롬프트 템플릿 전문 [TODO]
- 부록 D. 실험 재현 코드 저장소 링크 및 실행 방법 (`seonghoikim/hongik`) [TODO: 코드 구현 후 링크 채움]
- 부록 E. 사람-LLM 심판관 채점 일치율 원자료 (§3.6) [TODO]
- 부록 F. 적응형 재공격 30개(블랙박스 15 + 화이트박스 15) 전문 및 결과 (§5.4) [TODO]
