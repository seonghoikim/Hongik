"""모델 drift 사전 탐지용 "카나리아" 절차 (thesis.md §6, 결정 로그 항목 32).

연구자 조건: "과금형태의 비용이 발생하는게 아니라면 자동감지가 좋지" - 즉
드리프트 탐지 자체를 위한 추가 API 호출은 만들지 않는다. 대신 매 실행이 어차피
수집하는 `usage_summary`(call_logger.py, 역할별 호출 수·입출력 토큰·오류 수)를
과거 실행의 같은 통계와 비교하는 것만으로 이상 신호를 잡는다 - 순수 사후 비교라
한계도 있다: 실행이 끝난 뒤에야 알 수 있고, 진행 중인 실행을 막지는 못한다.
"""
from __future__ import annotations

import json
from pathlib import Path

# 역할별 평균 입력/출력 토큰이 기준선 대비 이 배수를 넘거나(팽창) 이 비율
# 미만으로 줄면(단축) 이상 신호로 본다. §5.3.10에서 실측된 4~7배 토큰 증가
# 사례를 놓치지 않을 만큼은 민감하되, 정상적인 라운드 수·표본 크기 차이로 인한
# 흔들림에는 너무 예민하지 않도록 넉넉히 잡았다.
DEFAULT_INFLATION_THRESHOLD = 2.0
DEFAULT_SHRINK_THRESHOLD = 0.5
# 역할별 오류(거부 등) 비율이 기준선 대비 이만큼(퍼센트포인트) 이상 늘면 경고한다.
DEFAULT_ERROR_RATE_DELTA_THRESHOLD = 0.10


def _avg_tokens_per_call(bucket: dict) -> tuple[float, float]:
    calls = bucket.get("calls", 0) or 1
    return bucket.get("input_tokens", 0) / calls, bucket.get("output_tokens", 0) / calls


def _error_rate(bucket: dict) -> float:
    calls = bucket.get("calls", 0) or 1
    return bucket.get("errors", 0) / calls


def check_canary_drift(
    usage_summary: dict,
    baseline_path: Path | str,
    *,
    inflation_threshold: float = DEFAULT_INFLATION_THRESHOLD,
    shrink_threshold: float = DEFAULT_SHRINK_THRESHOLD,
    error_rate_delta_threshold: float = DEFAULT_ERROR_RATE_DELTA_THRESHOLD,
) -> list[str]:
    """기준선 파일이 없으면(첫 실행) 경고 없이 빈 리스트를 반환한다 - 그 경우
    호출부에서 이번 실행 결과를 기준선으로 저장할지 판단하면 된다."""
    baseline_path = Path(baseline_path)
    if not baseline_path.exists():
        return []

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_roles = baseline.get("by_provider_role", {})
    current_roles = usage_summary.get("by_provider_role", {})

    warnings: list[str] = []
    for role, current_bucket in current_roles.items():
        base_bucket = baseline_roles.get(role)
        if base_bucket is None:
            continue  # 기준선에 없던 새 역할 - 비교 대상 없음

        base_in, base_out = _avg_tokens_per_call(base_bucket)
        cur_in, cur_out = _avg_tokens_per_call(current_bucket)

        for axis, base_v, cur_v in (("입력", base_in, cur_in), ("출력", base_out, cur_out)):
            if base_v <= 0:
                continue
            ratio = cur_v / base_v
            if ratio >= inflation_threshold:
                warnings.append(
                    f"[canary] {role}: {axis} 토큰이 기준선 대비 {ratio:.1f}배로 팽창 "
                    f"(기준 {base_v:.0f} -> 현재 {cur_v:.0f}/call) - §5.3.10류 프롬프트 "
                    "팽창 또는 모델 동작 변화 가능성"
                )
            elif ratio <= shrink_threshold:
                warnings.append(
                    f"[canary] {role}: {axis} 토큰이 기준선 대비 {ratio:.1f}배로 급감 "
                    f"(기준 {base_v:.0f} -> 현재 {cur_v:.0f}/call) - 조기 절단(truncation) "
                    "또는 응답 실패 가능성"
                )

        base_err = _error_rate(base_bucket)
        cur_err = _error_rate(current_bucket)
        if cur_err - base_err >= error_rate_delta_threshold:
            warnings.append(
                f"[canary] {role}: 오류(거부 등)율이 기준선 대비 "
                f"{base_err*100:.1f}%p -> {cur_err*100:.1f}%p로 상승"
            )

    return warnings


def save_canary_baseline(usage_summary: dict, baseline_path: Path | str) -> Path:
    """알려진 정상 실행의 usage_summary를 기준선으로 저장한다. 연구자가 명시적으로
    "이 실행을 새 기준선으로 삼겠다"고 판단할 때만 호출하는 수동 절차다 - 매 실행마다
    자동으로 덮어쓰면 drift가 있어도 기준선이 함께 밀려서 영원히 못 잡기 때문이다."""
    baseline_path = Path(baseline_path)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps({"by_provider_role": usage_summary.get("by_provider_role", {})}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return baseline_path
