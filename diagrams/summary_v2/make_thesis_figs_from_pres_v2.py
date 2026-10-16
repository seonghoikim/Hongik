# -*- coding: utf-8 -*-
"""v2 (2026-10-16): 그림 속 보조 글자(표 각주, 차트 제목, 긴 축 이름·범례 설명)를 지우고 thesis_v2_*.png로 저장.
본문 설명으로 옮긴 그림만 다시 그린다(n01, n02, chart_d2, chart_e).

강릉 발표용 그림(실험 원자료로 생성)을 학위논문 용어로 다시 그린다 (2026-10-16).

발표 그림은 학회 논문 용어(SRS, Meta-Rule, 자가 치유, Action Matrix, 영문 등급명)를 쓴다. 여기서는 같은 그림
함수를 그대로 부르되, matplotlib 글자 설정 단계에서 용어만 학위논문 표기로 바꾸고 결과를
diagrams/summary_v2/thesis_*.png로 저장한다(2026-10-16 이전 판은 pres_*.png). 숫자와 인용문은 발표 스크립트가 원자료에서 읽은 그대로이다.

    python3 diagrams/summary_v2/make_thesis_figs_from_pres.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRES = Path("/home/user/hongik/papers/gangneung_2026/presentation/scripts")
sys.path.insert(0, str(PRES))

import matplotlib.text as mtext  # noqa: E402

import common  # noqa: E402

TERMS = [
    ("SRS 자가 치유", "응대 정책 강건화"), ("자가 치유 폐쇄 루프", "강건화 폐쇄 루프"), ("자가 치유", "강건화"),
    ("Meta-Rule 생성기", "보강 규칙 생성기"), ("META-RULE", "보강 규칙"), ("Meta-Rule", "보강 규칙"),
    ("SRS v_final", "최종 응대 정책"), ("v_final", "최종 버전"), ("SRS 제약", "응대 정책 조항"), ("SRS", "응대 정책"),
    ("치유용 셋", "보강용 셋"), ("Action Matrix", "4단계 등급"),
    ("FULL_DEFENSE", "완전 방어"), ("FUNCTIONAL_DEFENSE", "기능적 방어"), ("FUNCTIONAL_\nDEFENSE", "기능적 방어"),
    ("PARTIAL_EXPOSURE", "부분 노출"), ("PARTIAL_\nEXPOSURE", "부분 노출"), ("BREACH", "침해"),
    ("PASS", "통과"), ("WARNING", "경고"), ("FAIL", "실패"),
    ("15라운드 실행", "9차 실행"), ("5라운드 실행", "7차 실행"),
]


DROP = {"정적 가드레일 = NeMo Guardrails 등", "4단계 사후 재채점(라운드 1·14)"}


def to_thesis(s):
    if not isinstance(s, str):
        return s
    if s in DROP:
        return ""
    s = re.sub(r" \(최종 v1\.\d+ = \d+개\)", "", s)
    s = re.sub(r"^라운드 \(라운드 n은 SRS v1\.\(n-1\) 적용\)$", "라운드", s)
    for a, b in TERMS:
        s = s.replace(a, b)
    s = re.sub(r"\bL([1-4])\b", r"\1등급", s)
    return s


_orig = mtext.Text.set_text
mtext.Text.set_text = lambda self, s: _orig(self, to_thesis(s) if isinstance(s, str) else s)
common.FIGS = HERE
# 논문 그림 색 기준(2026-10-16): 검정·회색 두 단계·빨강 하나. 빨강은 요약본 그림(make_figs_v9.py)과 같은 색.
common.RED = "#B03A2E"
_save = common.save


def save(fig, name):
    _save(fig, "thesis_v2_" + name)


common.save = save

import make_cards  # noqa: E402
import make_charts  # noqa: E402
import make_diagrams  # noqa: E402

for mod in (make_cards, make_charts, make_diagrams):
    mod.save = save
# 발표 그림의 초록 강조는 검정으로, 빨강은 요약본과 같은 색으로 바꾼다
for mod in (make_cards, make_charts, make_diagrams):
    if hasattr(mod, "RED"):
        mod.RED = common.RED
make_diagrams.GREEN = common.BLACK

make_diagrams.n01()
make_diagrams.n02()
make_charts.chart_d2()
make_charts.chart_e()
