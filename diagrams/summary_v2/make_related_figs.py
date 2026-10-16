# -*- coding: utf-8 -*-
"""2장 관련 연구 설명용 그림 3종 (2026-10-16). 원 논문 그림을 캡처하지 않고, 각 연구가 제시한 구조를
요약본 그림 기준(검정 선·글자, 회색 두 단계, 빨강 하나)으로 다시 그린다.

  related_guard_apo_loop_v1.png   2.1 가드레일, 자동 프롬프트 최적화, 자동 보강 루프
  related_disorder_attack_v1.png  2.2 정보 무질서 3분류, 간접 인젝션·RAG 오염, 검색 단계 방어
  related_judge_v1.png            2.3 LLM 심판관과 편향, 사례 제공형 심판관, 본 연구의 판정

    python3 diagrams/summary_v2/make_related_figs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figs_v9 as F  # noqa: E402  (helpers and style only; its main does not run on import)
from matplotlib.patches import Circle  # noqa: E402

BLACK, RED, G_LIGHT, G_MID, W, FS = F.BLACK, F.RED, F.G_LIGHT, F.G_MID, F.W, F.FS
box, arrow, container, canvas = F.box, F.arrow, F.container, F.canvas


def save(fig, name):
    p = os.path.join(F.OUT, name)
    fig.savefig(p, dpi=F.DPI, facecolor="white", bbox_inches="tight", pad_inches=0.04)
    F.plt.close(fig)
    print("saved", p)


def panel_title(ax, x, y, t):
    ax.text(x, y, t, ha="left", va="center", fontsize=F.FS_T, fontweight="bold")


def row(ax, y, labels, x0=0.0, w=1.05, gap=0.17, h=0.55, kinds=None):
    xs = []
    for i, t in enumerate(labels):
        x = x0 + i * (w + gap)
        box(ax, x, y, w, h, t, kind=(kinds or {}).get(i, "plain"), bold_first=False)
        xs.append(x)
        if i:
            arrow(ax, [(x - gap, y + h / 2), (x, y + h / 2)])
    return xs


def fig_guard_apo_loop():
    fig, ax = canvas(4.35)
    # (가) guardrail framework
    panel_title(ax, 0, 4.20, "(가) 가드레일 프레임워크 — 규칙을 사람이 작성 (Rebedea 등, 2023)")
    row(ax, 3.45, ["사용자\n입력", "입력 레일\n(차단·정제)", "대화·검색\n레일", "LLM", "출력 레일\n(검사·수정)"], w=1.0, gap=0.24,
        kinds={1: "light", 2: "light", 4: "light"})
    ax.text(W / 2, 3.28, "회색: 개발자가 미리 작성한 규칙(예: Colang 스크립트)으로 동작하는 단계", ha="center", va="center",
            fontsize=FS, color=G_MID)
    # (나) automatic prompt optimisation
    panel_title(ax, 0, 2.98, "(나) 자동 프롬프트 최적화 — 정답이 있는 과제의 정확도 향상 (Pryzant 등, 2023; Yang 등, 2024)")
    xs = row(ax, 2.20, ["현재\n프롬프트", "과제 데이터로\n정확도 평가", "오답 사례로\n문제 지적", "수정 후보\n생성", "탐색으로\n후보 선택"],
             w=1.0, gap=0.24)
    arrow(ax, [(xs[4] + 0.5, 2.20), (xs[4] + 0.5, 2.06), (xs[0] + 0.5, 2.06), (xs[0] + 0.5, 2.20)])
    ax.text(W / 2, 1.96, "OPRO는 지금까지의 (프롬프트, 점수) 이력을 LLM에 보여 주고 더 높은 점수의 프롬프트를 제안받는다",
            ha="center", va="center", fontsize=FS, color=G_MID)
    # (다) self-repair loop
    panel_title(ax, 0, 1.66, "(다) 자동 보강 루프 — 실패를 찾아 프롬프트·정책을 고침 (Chaitanya & Gundakaram, 2026; Slater, 2025)")
    xs = row(ax, 0.85, ["테스트\n생성·실행", "LLM 심판관\n평가", "실패\n진단", "프롬프트·정책\n수정", "재평가"], w=1.0, gap=0.24,
             kinds={3: "red"})
    arrow(ax, [(xs[4] + 0.5, 0.85), (xs[4] + 0.5, 0.71), (xs[0] + 0.5, 0.71), (xs[0] + 0.5, 0.85)])
    ax.text(W / 2, 0.52, "SISF는 자율 컴퓨팅의 MAPE-K(감시·분석·계획·실행 + 지식) 구조로 위반을 찾아 방어 정책을 합성한다",
            ha="center", va="center", fontsize=FS, color=G_MID)
    ax.text(W / 2, 0.30, "본 연구도 이 골격을 쓰되, 빨간 단계에서 보강 규칙을 응대 정책에 병합하고 개선을 두 축으로 나누어 잰다",
            ha="center", va="center", fontsize=FS, color=RED)
    save(fig, "related_guard_apo_loop_v1.png")


def fig_disorder_attack():
    fig, ax = canvas(4.2)
    # (가) information disorder Venn
    panel_title(ax, 0, 4.05, "(가) 정보 무질서 3분류")
    ax.text(1.55, 2.02, "(Wardle & Derakhshan, 2017)", ha="center", fontsize=FS - 0.5, color=G_MID)
    ax.add_patch(Circle((1.05, 2.95), 0.78, fc="none", ec=BLACK, lw=1.1))
    ax.add_patch(Circle((2.05, 2.95), 0.78, fc="none", ec=BLACK, lw=1.1))
    ax.text(0.62, 3.80, "거짓 정보", ha="center", fontsize=FS, fontweight="bold")
    ax.text(2.48, 3.80, "해를 끼칠 의도", ha="center", fontsize=FS, fontweight="bold")
    ax.text(0.70, 2.95, "오정보\n(의도 없는\n오류)", ha="center", va="center", fontsize=FS)
    ax.text(1.55, 2.95, "허위\n조작\n정보", ha="center", va="center", fontsize=FS, color=RED, fontweight="bold")
    ax.text(2.42, 2.95, "악의정보\n(사실이지만\n해악)", ha="center", va="center", fontsize=FS)
    # (나) attack paths
    panel_title(ax, 3.15, 4.05, "(나) 검색 경로를 노리는 공격")
    box(ax, 3.15, 3.15, 1.15, 0.72, "간접 프롬프트 인젝션\n웹 문서에 숨긴 지시\n(Greshake 등, 2023)", kind="red", bold_first=False)
    box(ax, 3.15, 2.30, 1.15, 0.72, "RAG 오염\n허위 문서 주입\n(Zou 등, 2025)", kind="red", bold_first=False)
    box(ax, 4.65, 2.85, 0.65, 0.55, "RAG\n검색", bold_first=False)
    box(ax, 5.45, 2.85, 0.62, 0.55, "LLM\n응답", bold_first=False)
    arrow(ax, [(4.30, 3.51), (4.47, 3.51), (4.47, 3.25), (4.65, 3.25)])
    arrow(ax, [(4.30, 2.66), (4.47, 2.66), (4.47, 3.0), (4.65, 3.0)])
    arrow(ax, [(5.30, 3.12), (5.45, 3.12)])
    ax.text(4.60, 1.98, "사용자 믿음에 맞춘 동조(아첨)로도 허위 정보가 전달된다\n(Sharma 등, 2024; Aswin RRV 등, 2024)",
            ha="center", va="center", fontsize=FS - 0.5, color=G_MID)
    # (다) retrieval-stage defence
    panel_title(ax, 0, 1.60, "(다) 검색 단계 방어 — 문서별로 따로 답한 뒤 안전하게 집계 (Xiang 등, 2026)")
    ys = [1.08, 0.66, 0.24]
    for i, y in enumerate(ys):
        box(ax, 0.0, y, 1.10, 0.34, f"검색 문서 {i + 1}" if i < 2 else "검색 문서 k (오염)", kind="red" if i == 2 else "plain",
            bold_first=False)
        box(ax, 1.45, y, 1.30, 0.34, f"문서 {i + 1}만 보고 응답" if i < 2 else "문서 k만 보고 응답", bold_first=False)
        arrow(ax, [(1.10, y + 0.17), (1.45, y + 0.17)])
        arrow(ax, [(2.75, y + 0.17), (3.15, 0.75)])
    box(ax, 3.15, 0.48, 1.30, 0.55, "안전한 집계\n(키워드·디코딩)", bold_first=False, kind="light")
    box(ax, 4.80, 0.48, 1.27, 0.55, "최종 응답\n(오염 문서 영향 제한)", bold_first=False)
    arrow(ax, [(4.45, 0.75), (4.80, 0.75)])
    save(fig, "related_disorder_attack_v1.png")


def fig_judge():
    fig, ax = canvas(3.05)
    panel_title(ax, 0, 2.90, "(가) LLM 심판관 (Zheng 등, 2023)")
    box(ax, 0.0, 1.95, 1.20, 0.55, "질문 +\n챗봇 응답", bold_first=False)
    box(ax, 1.50, 1.95, 1.00, 0.55, "심판 LLM", kind="mid", bold_first=False)
    box(ax, 2.80, 1.95, 0.90, 0.55, "점수·판정", bold_first=False)
    arrow(ax, [(1.20, 2.22), (1.50, 2.22)]); arrow(ax, [(2.50, 2.22), (2.80, 2.22)])
    ax.text(1.85, 1.68, "알려진 편향: 제시 순서 · 장황함 · 자기 응답 선호", ha="center", fontsize=FS, color=G_MID)
    ax.text(1.85, 1.45, "심판관 자체도 프롬프트 인젝션 대상 (Shi 등, 2024)", ha="center", fontsize=FS, color=G_MID)
    panel_title(ax, 3.95, 2.90, "(나) 사례 제공형 심판관 (Tamber 등, 2025)")
    box(ax, 3.95, 1.95, 2.12, 0.55, "사람이 주석한 환각 사례를\n심판관 프롬프트에 함께 제공", bold_first=False, kind="light")
    ax.text(5.01, 1.68, "RAG 응답의 충실성 한 축을 판정", ha="center", fontsize=FS, color=G_MID)
    panel_title(ax, 0, 1.12, "(다) 본 연구의 판정")
    box(ax, 0.0, 0.18, 1.85, 0.70, "무상태 호출\n매 채점 새 세션, 이전 대화 없음", bold_first=True)
    box(ax, 2.11, 0.18, 1.85, 0.70, "두 축 판정\n정보 무결성 · 정책 준수", kind="red", bold_first=True)
    box(ax, 4.22, 0.18, 1.85, 0.70, "정답 대조\n정답이 있는 문항은 코드로", bold_first=True)
    save(fig, "related_judge_v1.png")


if __name__ == "__main__":
    fig_guard_apo_loop()
    fig_disorder_attack()
    fig_judge()
