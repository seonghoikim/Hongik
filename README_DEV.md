# 개발용 실행 가이드 (Self-Healing AI Chatbot 실험 코드)

thesis.md / thesis-draft.md에서 설계한 유닛 A~D 파이프라인, 무상태 심판관,
Meta-Rule 자가 치유 루프, 헬드아웃 검증, 적응형 재공격 실험을 코드로 구현한
것입니다. `src/hongik_selfheal/` 아래 모듈로 구성되어 있습니다.

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env   # 실제 API로 돌릴 때만 필요, 값 채워 넣기
```

## 모드

- `LLM_PROVIDER=mock` (기본값): API 키 없이 파이프라인 배선만 검증한다.
  가짜 응답이며 **논문에 쓸 결과가 아니다.**
- `LLM_PROVIDER=openai` 또는 `gemini`: 실제 API 호출. `.env`에 키를 넣어야 한다.

## 실행

```bash
# 전체 실험 (자가 치유 → 헬드아웃 → 적응형 재공격 → 통계 검정까지 한 번에)
PYTHONPATH=src python3 scripts/run_experiment.py --mode mock
PYTHONPATH=src python3 scripts/run_experiment.py --mode openai --n-per-category 10

# 테스트
PYTHONPATH=src python3 -m pytest tests/ -v
```

결과는 `data/results/experiment_<provider>_<timestamp>.json`에 저장된다.
`data/results/mock_demo_run.json`은 mock 모드로 코드가 정상 동작함을 보여주는
데모 결과물이며 실험 데이터가 아니다.

## 모듈 구조

| 파일 | 논문 대응 절 | 역할 |
|---|---|---|
| `srs.py` | §4.1, §4.3 | SRS 버전 관리, Meta-Rule 샌드위치 삽입 |
| `units.py` | §3 (유닛 A~D) | 입력 가드레일 → RAG → LLM 추론 → 출력 가드레일 |
| `knowledge_base.py` | §3 유닛 B | 초소형 키워드 기반 지식 베이스 (A사 제품 정보) |
| `judge.py` | §3.6, §4.1 | 무상태 Action Matrix 채점 |
| `meta_rule_generator.py` | §4.3 | 실패 로그 → Meta-Rule 자동 생성 |
| `attack_taxonomy.py` | §4.2.1 | OWASP LLM Top 10 매핑 5개 카테고리 |
| `attack_generator.py` | §4.2.2, §5.4 | 공격 시나리오 생성/중복제거/분할, 적응형 재공격 |
| `experiment.py` | §4.1, §5.4 | 전체 오케스트레이션 |
| `stats.py` | §3.5.3 | Wilcoxon / Mann-Whitney U / 카이제곱 |

## 아직 수동 개입이 필요한 부분

- `attack_generator.generate_category_scenarios(..., manual_review_hook=...)`:
  기본값은 전부 통과. 실제 실험 시 연구자가 도메인 적합성을 검토하는 함수로
  교체해야 한다 (§4.2.2의 "연구자 수동 검토" 단계).
- 심판관 채점 경량 표본 검토(§3.6.2)는 아직 별도 스크립트가 없다. 실험 결과
  JSON에서 무작위 15~20건을 뽑아 수기로 채점 후 비교하면 된다.
