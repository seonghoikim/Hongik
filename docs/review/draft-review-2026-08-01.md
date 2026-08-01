# 석사 논문 초안 검토 리포트 (2026-08-01)

대상: "다양한 고객 조직을 위한 LLM 커스터마이징 기반 AI 챗봇 개발 메커니즘" 초안 (제목 없는 문서.pdf)

---

## 1. 참고문헌 검증 결과 (WebSearch로 원문 대조)

| # | 초안 표기 | 검증된 실제 정보 | 문제 유형 |
|---|---|---|---|
| 1 | Liu, Y., et al. (2024). *Optimization-based Prompt Injection Attack to LLM-as-a-Judge*. arXiv:2403.17710 | Shi, J., Yuan, Z., Liu, Y., Huang, Y., Zhou, P., Sun, L., & Gong, N. Z. (2024). *Optimization-based Prompt Injection Attack to LLM-as-a-Judge*. **ACM CCS '24**. arXiv:2403.17710 | 1저자 오류 (Shi ≠ Liu, Liu는 3저자). 학회명 누락 |
| 2 | Smith, A., & Johnson, B. (2026). *PIArena*. ACL 2026. arXiv:2604.08499 | Geng, R., Yin, C., Wang, Y., Chen, Y., & Jia, J. (2026). *PIArena: A Platform for Prompt Injection Evaluation*. ACL 2026 (Penn State). arXiv:2604.08499 | 저자명 전원 오류 (가공 이름) |
| 3 | Zhang, C., et al. (2026). *SHIELD*. arXiv:2601.19174 | Sivaroopan, N., et al. (2026). *SHIELD: An Auto-Healing Agentic Defense Framework for LLM Resource Exhaustion Attacks*. (Univ. of Sydney 외). arXiv:2601.19174 | 저자명 오류 |
| 4 | Greshake, K., et al. (2023). ACM Workshop on **Wireless Security and Machine Learning (WiseML)** | 동일 저자, 단 실제 venue는 **ACM Workshop on Artificial Intelligence and Security (AISec) 2023**. arXiv:2302.12173 | 학회명 오류 (존재하지 않는 학회명) |
| 5 | OWASP Top 10 for LLM Applications (2025/2026) | OWASP Top 10 for LLM Applications **2025 (v2.0)**, 2024-11-18 공식 발간 | 표기는 대체로 문제 없음, 연도 이원 표기("2025/2026") 정리 필요 |

**조치**: 위 표의 "검증된 실제 정보" 열 내용으로 참고문헌을 전량 교체할 것. 제출 전 지도교수/논문 검색엔진(Google Scholar, arXiv)에서 직접 재확인 권장.

---

## 2. 실험 데이터 신뢰성 (최우선 확인 필요)

- 논문 본문의 정량 결과(1차 82점/54.6%, 2차 75점/50%, 3차 150점/100%)가 **실제 코드 실행 결과인지 미확인**. 현재 관련 저장소(hongik)에는 코드가 전혀 없음.
- 실제 실험으로 재현되지 않은 수치를 그대로 제출하는 것은 데이터 조작으로 간주될 수 있는 중대한 학술 윤리 리스크임.
- **조치**: 실제 파이프라인(입력 가드레일 → RAG → 추론 → 출력 가드레일, 무상태 평가 API, 자가 치유 루프)을 코드로 구현하여 동일 실험을 재현하고, 그 결과로 논문 수치를 교체해야 함.

## 3. 방법론 결함 — 테스트셋 재사용 (Train/Test 오염)

- 동일한 50개 공격 문장으로 (1) 취약점 발견 → (2) SRS 보강 → (3) 재평가를 수행. 이는 훈련에 쓴 데이터로 시험을 다시 보는 것과 동일 → 100% 달성이 일반화 증명이 되지 못함.
- **조치**: 50개는 치유용(training), 별도의 새로운 held-out 공격 시나리오셋(예: 30~50개)으로 최종 검증해야 함.

## 4. 브랜드명 노출

- 실존 기업명 "하이마트"를 그대로 사용. 익명화("A사", "가전 유통 기업 A") 권장.

## 5. 분량/구조 — 현재 실질 내용 약 7페이지 (통상 석사 논문 40~70페이지 대비 크게 부족)

누락되었거나 보강이 필요한 항목:

- [ ] 연구 방법론 챕터 (실험 설계, 반복 횟수, 통계적 검정 방법, 사용 모델/버전 명시)
- [ ] 선행연구 비교표 (본 연구 vs SHIELD vs PIArena 정량 비교)
- [ ] Action Matrix 채점 기준표(rubric) 구체화 — 현재 이름만 있고 실제 기준 서술 없음
- [ ] 50개 공격 프롬프트 전체 목록 (부록)
- [ ] SRS v1.0/v2.0/v3.0 전문 (부록)
- [ ] 그림 1·2·3 실제 도식/캡처 삽입 (현재 캡션만 존재)
- [ ] LLM-as-a-Judge 신뢰성 검증 (사람 채점과의 일치도, inter-rater reliability)
- [ ] 반복 실행에 따른 표준편차/신뢰구간 (LLM 응답의 비결정성 통제)
- [ ] 다양한 고객 조직(제목의 "Heterogeneous") 주장에 맞는 2~3개 이상 도메인 실험 (현재 가전 유통 1개뿐)
- [ ] "자동" 자가 치유의 자동화 수준 명확화 (사람 개입 여부)

## 6. 제목-내용 정합성

- 제목: "다양한(Heterogeneous) 고객 조직" vs 실험: 단일 도메인(가전 유통) → 범위 확장 또는 제목/주장 축소 필요.

---

## 다음 액션 (우선순위)

1. ✅ 참고문헌 표 교체 (완료, 위 표 사용)
2. ⬜ 실제 검증 코드 구현 (파이프라인 + held-out 테스트셋 + 실험 재실행)
3. ⬜ 목차 확장 및 누락 챕터 작성 (연구방법론, 선행연구 비교, 부록)
4. ⬜ 브랜드명 익명화
