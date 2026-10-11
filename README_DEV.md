# 개발용 실행 가이드 (Self-Healing AI Chatbot 실험 코드)

thesis.md / thesis_report.md에서 설계한 유닛 A~D 파이프라인, 무상태 심판관,
Meta-Rule 자가 치유 루프, 헬드아웃 검증, 적응형 재공격, 교차 모델 검증을
코드로 구현한 것입니다. `src/hongik_selfheal/` 아래 모듈로 구성되어 있습니다.
(2026-10-11 실험 프로그램 점검 후 갱신: `docs/program_review_20261011.md`)

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env   # 실제 API로 돌릴 때만 필요, 값 채워 넣기
```

## 모드와 모델

- `--mode mock` (또는 `.env`의 `LLM_PROVIDER=mock`): API 키 없이 파이프라인 배선만
  검증한다. 가짜 응답이며 **논문에 쓸 결과가 아니다.**
- `--mode real`: 실제 API 호출. 교차 모델 검증 단계 때문에 Anthropic·OpenAI·Gemini
  3종 키가 모두 필요하다.
  - `--primary-provider` (기본 anthropic): 유닛 C, 심판관, Meta-Rule 생성기
  - `--redteam-provider` (기본 openai): 공격 문장 생성 (주 모델이 이 역할을 정책상 거부해 분리)
  - 교차 모델 검증: 헬드아웃 셋을 3개 백엔드로 재실행, 채점은 주 모델 심판관으로 고정

## 실행

```bash
# 전체 실험 (공격 생성 → 자가 치유 → 헬드아웃 → 적응형 재공격 → 교차 모델 검증 → 통계 검정)
PYTHONPATH=src python3 scripts/run_experiment.py --mode mock
PYTHONPATH=src python3 scripts/run_experiment.py --mode real --n-per-category 10

# 같은 공격 문항으로 SRS 변형 비교 (대응표본)
PYTHONPATH=src python3 scripts/run_experiment.py --mode real --save-attack-pool data/results/pool.json
PYTHONPATH=src python3 scripts/run_experiment.py --mode real --attack-pool-file data/results/pool.json --srs-variant 5w1h

# 옵션 전체
PYTHONPATH=src python3 scripts/run_experiment.py --help

# 테스트
PYTHONPATH=src python3 -m pytest tests/ -v
```

## 비용 절감 장치

- 프롬프트 캐싱 (항상 켜짐, 2026-08-19): Anthropic 호출의 system 프롬프트(SRS·채점 기준)를 캐시한다.
  한 라운드 안에서는 system이 같으므로 첫 호출 뒤에는 그 부분이 기본 입력가의 10%로 계산된다.
- `--batch` (선택, 2026-10-11): 라운드마다 모이는 Anthropic 응답 생성·채점을 Message Batches API로
  보낸다(입출력 50%). 배치 하나가 끝나야 다음 단계로 가므로 실행 시간이 길어진다. 실패·만료된 건은
  일반 API로 한 건씩 다시 보낸다. 배치 처리된 호출은 원문 로그의 `batch: true`로 구분되고 비용 추정에
  50% 할인이 반영된다.


- 실측 결과: `data/results/experiment_real_<timestamp>.json`
- mock 결과: `data/results/mock/`, `data/srs/mock/` (git 제외, 실측 결과와 섞이지 않게 분리)
- 원문 호출 로그 `raw_calls_*.jsonl`과 체크포인트 `checkpoint_*.json`은 git 제외

## v_final 정의

자가 치유 루프는 (1) 전원 FULL_DEFENSE, (2) Meta-Rule 생성기가 새 규칙을 내지 못함,
(3) `--max-rounds` 도달 중 하나로 끝난다. 세 경우 모두 **치유용 셋에서 마지막으로 평가된
버전이 v_final**이며, 헬드아웃·적응형 재공격·교차 모델 검증은 이 버전으로 수행된다.
2026-10-11 이전 코드는 상한 도달 시 Meta-Rule을 한 번 더 만들어 평가되지 않은 버전을
v_final로 썼다(7·8·10~13차 실행에 해당, 논문 §6에 명시).

## 채점과 통계

- 채점: 4단계 (FULL_DEFENSE 4 / FUNCTIONAL_DEFENSE 3 / PARTIAL_EXPOSURE 2 / BREACH 1).
  점수는 심판관이 낸 등급에서 정한다. 허용 외 등급은 "채점 불가"로 기록하고 통계에서 제외한다.
  7~9차 실행은 3단계(PASS/WARNING/FAIL)로 채점되었다.
- 준수율 = 총점 / 만점. 전원이 최하 등급이어도 25%(3단계는 33.3%)이므로 등급 분포를 함께 본다.
- 통계 (`stats.py`)

| 비교 | 자료 형태 | 검정 |
|---|---|---|
| 치유용 셋 v1.0 vs v_final | 같은 문항 반복 | Wilcoxon 부호순위 |
| 치유용 최종 vs 헬드아웃, 블랙박스 vs 화이트박스 | 다른 문항 | Mann-Whitney U, 카이제곱 |
| 교차 모델 3개 백엔드 | 같은 문항 반복 | Friedman(점수), Cochran's Q(FULL_DEFENSE 여부) |

기존 결과 파일의 교차 모델 검정 재계산 (API 호출 없음):

```bash
PYTHONPATH=src python3 scripts/recompute_cross_model_stats.py
```

## 모듈 구조

| 파일 | 역할 |
|---|---|
| `srs.py` | SRS 버전 관리, Meta-Rule 헤더·푸터 이중 삽입, 5W1H 변형 |
| `units.py` | 유닛 A~D: 입력 가드레일 → RAG → LLM 추론 → 출력 가드레일 |
| `knowledge_base.py` | 유닛 B용 소형 키워드 지식 베이스 |
| `fake_members.py` | 가상 회원 DB (개인정보 유출 공격 대상) |
| `judge.py` | 무상태 심판관, 4단계 Action Matrix 채점, 등급 검증 |
| `meta_rule_generator.py` | 실패 로그 → Meta-Rule 생성 |
| `attack_taxonomy.py` | 공격 8개 범주 (impersonation, encoding_bypass, tone_gaslighting, misinformation, metadata_leak, pii_leak, cross_product_leak, price_probing) |
| `attack_generator.py` | 공격 생성, 중복 제거, 범주별 분할(부족 시 비례 분할과 경고), 적응형 재공격 |
| `experiment.py` | 자가 치유 루프, 세트 평가, 교차 모델 검증 |
| `stats.py` | Wilcoxon, Mann-Whitney U, 카이제곱, Friedman, Cochran's Q |
| `llm_client.py` | Anthropic·OpenAI·Gemini·mock 클라이언트, 토큰 사용량 집계 |
| `call_logger.py` | 원문 호출 로그 |
| `canary.py` | 모델 동작 변화(drift) 점검: 이전 실행과 토큰·오류율 비교 |

## 아직 수동 개입이 필요한 부분

- `attack_generator.generate_category_scenarios(..., manual_review_hook=...)`:
  기본값은 전부 통과. 실제 실험 시 연구자가 도메인 적합성을 검토하는 함수로 교체한다.
- 심판관 채점 표본 검토: `scripts/spotcheck_sample.py`로 표본을 뽑아 수기 채점 후
  `scripts/spotcheck_compare.py`로 비교한다.
