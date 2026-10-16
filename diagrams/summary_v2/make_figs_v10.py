# -*- coding: utf-8 -*-
"""v10 (2026-10-16): 그림 속 글자를 줄이고 설명은 본문으로 옮긴 판. make_figs_v9.py에서 파생.

- 상자에는 단계 이름만 남기고 부연 설명(두 번째 줄)은 지운다.
- 주석 화살표, p값, 범례 설명 줄은 본문으로 옮긴다.
- 관련 연구 그림(make_related_figs.py의 3종, 각 3패널)은 패널마다 별도 그림으로 나눈다.
- 글자 크기 9.5pt(상자 제목 10pt). 그림은 이 캔버스 크기 그대로 인쇄된다는 전제로 그린다
  (scripts/summary_md_to_docx.py가 PNG의 dpi 정보로 원래 크기를 계산해 넣는다).
색은 v9와 같다: 검정, 회색 두 단계, 빨강 하나.

    python3 diagrams/summary_v2/make_figs_v10.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figs_v9 as F  # noqa: E402  (font setup and helpers; its main does not run on import)
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402

plt = F.plt
BLACK, RED, G_LIGHT, G_MID, W = F.BLACK, F.RED, F.G_LIGHT, F.G_MID, F.W
FS, FS_T, LH = 9.5, 10.0, 0.185
F.FS, F.FS_T = FS, FS_T                       # container() and strip() read these at call time
plt.rcParams.update({"font.size": 9.5, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
                     "axes.labelsize": 10, "legend.fontsize": 9.5})
arrow, container, strip = F.arrow, F.container, F.strip
OUT = F.OUT


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-0.04, w + 0.04); ax.set_ylim(-0.04, h + 0.04); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, kind="plain", bold=True, fs=None):
    """bold: True = every line bold (names only), False = none."""
    ec, fc, lw, ls, tc = BLACK, "white", 1.0, "-", BLACK
    if kind == "red":
        ec, lw = RED, 2.0
    elif kind == "light":
        fc = G_LIGHT
    elif kind == "mid":
        fc, tc = G_MID, "white"
    elif kind == "dash":
        ec, ls = G_MID, (0, (3, 2))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                fc=fc, ec=ec, lw=lw, ls=ls))
    lines = text.split("\n")
    top = y + h / 2 + (len(lines) - 1) * LH / 2
    for i, s in enumerate(lines):
        ax.text(x + w / 2, top - i * LH, s, ha="center", va="center", fontsize=fs or (FS_T if bold else FS),
                fontweight="bold" if bold else "normal", color=tc)


def label(ax, x, y, s, **kw):
    ax.text(x, y, s, ha=kw.pop("ha", "center"), va=kw.pop("va", "center"), fontsize=kw.pop("fs", FS), **kw)


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=F.DPI if not name.startswith("plot_") else 380, facecolor="white",
                bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print("saved", p)


def row(ax, y, labels, w, gap, h=0.62, kinds=None, x0=0.0):
    xs = []
    for i, t in enumerate(labels):
        x = x0 + i * (w + gap)
        box(ax, x, y, w, h, t, kind=(kinds or {}).get(i, "plain"))
        if i:
            arrow(ax, [(x - gap, y + h / 2), (x, y + h / 2)])
        xs.append(x)
    return xs


# ================================================================ chapter 3 diagrams
def fig_overview():
    fig, ax = canvas(W, 1.35)
    y, h = 0.10, 0.62
    box(ax, 0.00, y, 1.20, h, "사전 점검")
    box(ax, 1.45, y, 1.20, h, "공격 생성")
    box(ax, 2.90, y, 1.45, h, "강건화 루프", kind="red")
    box(ax, 4.85, y, 1.20, h, "사후 검증")
    m = y + h / 2
    arrow(ax, [(1.20, m), (1.45, m)]); arrow(ax, [(2.65, m), (2.90, m)]); arrow(ax, [(4.35, m), (4.85, m)])
    label(ax, 4.60, m + 0.10, "수렴 시", va="bottom")
    arrow(ax, [(4.00, y + h), (4.00, 1.02), (3.25, 1.02), (3.25, y + h)])
    label(ax, 3.62, 1.10, "미수렴 시 반복", va="bottom")
    save(fig, "fig_overview_v10.png")


def fig_prep():
    fig, ax = canvas(W, 2.30)
    strip(ax, [0, 1], 1.98)
    container(ax, 0.00, 0.05, 2.55, 1.65, "사전 점검")
    for i, t in enumerate(["① 차단 문구 검증", "② 모델 동작 변화 감시", "③ 대화형 검토 도구"]):
        box(ax, 0.12, 1.05 - i * 0.47, 2.31, 0.36, t, bold=False)
    box(ax, 2.85, 0.62, 1.45, 0.55, "공격 생성")
    box(ax, 4.62, 0.62, 1.43, 0.55, "강건화 루프", kind="dash", bold=False)
    arrow(ax, [(2.55, 0.895), (2.85, 0.895)]); arrow(ax, [(4.30, 0.895), (4.62, 0.895)])
    save(fig, "fig_prep_v10.png")


def fig_struct1():
    fig, ax = canvas(W, 1.95)
    strip(ax, [2], 1.63)
    container(ax, 0.00, 0.05, W, 1.33, "구조 1 — 유닛 A~D")
    units = [("유닛 A\n입력 가드레일", "plain"), ("유닛 B\nRAG 검색", "plain"),
             ("유닛 C\nLLM 추론", "red"), ("유닛 D\n출력 가드레일", "plain")]
    xs = [0.10, 1.60, 3.10, 4.60]
    for i, (x, (t, k)) in enumerate(zip(xs, units)):
        box(ax, x, 0.17, 1.37, 0.80, t, kind=k)
        if i < 3:
            arrow(ax, [(x + 1.37, 0.57), (xs[i + 1], 0.57)])
    save(fig, "fig_struct1_v10.png")


def fig_struct2():
    fig, ax = canvas(W, 3.05)
    strip(ax, [2], 2.73)
    container(ax, 0.00, 0.55, W, 1.90, "구조 2 — 강건화 폐쇄 루프")
    cx = [0.12, 2.18, 4.24]; bw, bh = 1.70, 0.52
    ytop, ybot = 1.62, 0.70
    box(ax, cx[0], ytop, bw, bh, "① 응대 정책 정의")
    box(ax, cx[1], ytop, bw, bh, "⑤ 응대 정책 병합")
    box(ax, cx[2], ytop, bw, bh, "④ 보강 규칙 생성", kind="red")
    box(ax, cx[0], ybot, bw, bh, "② 적대적 실행")
    box(ax, cx[1], ybot, bw, bh, "구조 1 (유닛 A~D)", kind="dash", bold=False)
    box(ax, cx[2], ybot, bw, bh, "③ 두 축 채점")
    arrow(ax, [(0.97, ytop), (0.97, ybot + bh)])
    arrow(ax, [(cx[0] + bw, ybot + bh / 2), (cx[1], ybot + bh / 2)])
    arrow(ax, [(cx[1] + bw, ybot + bh / 2), (cx[2], ybot + bh / 2)])
    arrow(ax, [(5.09, ybot + bh), (5.09, ytop)])
    label(ax, 5.16, (ybot + bh + ytop) / 2, "미수렴 시", ha="left")
    arrow(ax, [(cx[2], ytop + bh / 2), (cx[1] + bw, ytop + bh / 2)])
    arrow(ax, [(cx[1], ytop + bh / 2), (cx[0] + bw, ytop + bh / 2)])
    arrow(ax, [(5.09, ybot), (5.09, 0.40)])
    box(ax, 3.70, 0.02, 2.37, 0.38, "수렴 시 사후 검증으로", bold=False)
    save(fig, "fig_struct2_v10.png")


def fig_struct3():
    fig, ax = canvas(W, 1.95)
    strip(ax, [3], 1.63)
    box(ax, 0.00, 0.45, 0.85, 0.55, "수렴", bold=False)
    container(ax, 1.08, 0.05, 4.99, 1.33, "구조 3 — 사후 검증")
    steps = ["③ 헬드아웃\n검증", "④ 적응형\n재공격", "⑤ 교차 모델\n검증", "⑥ 통계\n검정"]
    xs = [1.18, 2.40, 3.62, 4.84]
    for i, (x, t) in enumerate(zip(xs, steps)):
        box(ax, x, 0.17, 1.13, 0.80, t)
        if i < 3:
            arrow(ax, [(x + 1.13, 0.57), (xs[i + 1], 0.57)])
    arrow(ax, [(0.85, 0.725), (1.18, 0.725)])
    save(fig, "fig_struct3_v10.png")


def fig_integrated():
    fig, ax = canvas(W, 6.10)
    # pre-check and attack generation (left)
    container(ax, 0.00, 4.55, 1.55, 1.50, "사전 점검")
    for i, t in enumerate(["① 차단 문구", "② 동작 변화", "③ 검토 도구"]):
        box(ax, 0.10, 5.43 - i * 0.40, 1.35, 0.32, t, bold=False)
    box(ax, 0.10, 3.55, 1.35, 0.55, "공격 생성")
    arrow(ax, [(0.775, 4.55), (0.775, 4.10)])
    # structure 1 (top right)
    container(ax, 1.70, 4.55, 4.37, 1.50, "구조 1 — 유닛 A~D")
    units = ["A\n입력 가드레일", "B\nRAG 검색", "C\nLLM 추론", "D\n출력 가드레일"]
    ux = [1.78, 2.86, 3.94, 5.02]
    for i, (x, t) in enumerate(zip(ux, units)):
        box(ax, x, 4.65, 0.98, 0.95, t)
        if i < 3:
            arrow(ax, [(x + 0.98, 5.125), (ux[i + 1], 5.125)])
    # structure 2 (middle)
    container(ax, 1.70, 0.85, 2.85, 3.50, "구조 2 — 강건화 폐쇄 루프", title_at_bottom=True)
    c1, c2, bw, bh = 1.78, 3.20, 1.27, 0.52
    yr = [3.55, 2.55, 1.55]
    box(ax, c1, yr[0], bw, bh, "② 적대적 실행")
    box(ax, c2, yr[0], bw, bh, "③ 두 축 채점")
    box(ax, c1, yr[1], bw, bh, "① 응대 정책 정의")
    box(ax, c2, yr[1], bw, bh, "④ 보강 규칙 생성", kind="red")
    box(ax, c2, yr[2], bw, bh, "⑤ 응대 정책 병합")
    m1, m2 = c1 + bw / 2, c2 + bw / 2
    arrow(ax, [(m1, yr[1] + bh), (m1, yr[0])])                                   # 1 -> 2
    arrow(ax, [(m1, yr[0] + bh), (m1, 4.65)])                                    # 2 -> unit A
    arrow(ax, [(5.51, 4.65), (5.51, 4.42), (m2, 4.42), (m2, yr[0] + bh)])        # D -> 3
    arrow(ax, [(m2, yr[0]), (m2, yr[1] + bh)])                                   # 3 -> 4
    label(ax, m2 - 0.06, 3.31, "미수렴 시", ha="right")
    arrow(ax, [(m2, yr[1]), (m2, yr[2] + bh)])                                   # 4 -> 5
    arrow(ax, [(c2, yr[2] + bh / 2), (m1, yr[2] + bh / 2), (m1, yr[1])])         # 5 -> 1
    arrow(ax, [(0.775, 3.55), (0.775, 2.81), (c1, 2.81)])                        # attack gen -> 1
    # structure 3 (right column)
    label(ax, 5.36, 4.25, "수렴 시")
    steps = ["③ 헬드아웃 검증", "④ 적응형 재공격", "⑤ 교차 모델 검증", "⑥ 통계 검정"]
    ys = [3.55, 2.55, 1.55, 0.55]
    for i, (y, t) in enumerate(zip(ys, steps)):
        box(ax, 4.65, y, 1.42, 0.52, t)
        if i < 3:
            arrow(ax, [(5.36, y), (5.36, ys[i + 1] + 0.52)])
    arrow(ax, [(c2 + bw, 3.81), (4.65, 3.81)])
    save(fig, "fig_integrated_v10.png")


def fig_taxonomy():
    rows = [("관리자·시스템 사칭", "LLM01 프롬프트 인젝션", "허위조작정보", True),
            ("허위 사실 동조 유도", "LLM09 잘못된 정보", "오정보", True),
            ("메타데이터 유출 유도", "LLM07 / LLM02", "악의정보", True),
            ("개인정보 유출 유도", "LLM02 민감 정보 노출", "악의정보", True),
            ("RAG 오염 문서 신뢰 유도", "LLM08 / LLM04", "허위조작정보", True),
            ("인코딩·난독화 우회", "LLM01 (변형)", "범위 밖", False),
            ("어투 강요·가스라이팅", "LLM01 (지시 재정의)", "범위 밖", False),
            ("다중 상품 키워드 오염", "LLM08 (벡터·임베딩)", "범위 밖", False),
            ("가격 정보 간접 유도", "LLM02 (변형)", "범위 밖", False)]
    rh, gap = 0.32, 0.09
    h = 0.30 + len(rows) * (rh + gap)
    fig, ax = canvas(W, h)
    top = h - 0.14
    for x, t in ((0.85, "OWASP LLM 10대 위협"), (3.05, "공격 유형"), (5.25, "정보 불일치성")):
        label(ax, x, top, t, fs=FS_T, fontweight="bold")
    for i, (t, ow, dis, core) in enumerate(rows):
        y = top - 0.22 - (i + 1) * (rh + gap) + gap
        box(ax, 0.00, y, 1.70, rh, ow, kind="plain" if core else "dash", bold=False)
        box(ax, 2.00, y, 2.10, rh, t, kind="light" if core else "plain", bold=False)
        box(ax, 4.45, y, 1.60, rh, dis, kind="red" if core else "dash", bold=False)
        style = dict(color=BLACK, ls="-") if core else dict(color=G_MID, ls=(0, (3, 2)))
        arrow(ax, [(2.00, y + rh / 2), (1.70, y + rh / 2)], **style)
        arrow(ax, [(4.10, y + rh / 2), (4.45, y + rh / 2)], **style)
    save(fig, "fig_taxonomy_v10.png")


def fig_levels():
    levels = [("4등급 완전 방어", "정보 유지 · 정책 준수", "red"),
              ("3등급 기능적 방어", "정보 유지 · 정책 위반", "plain"),
              ("2등급 부분 노출", "정보 부분 훼손", "light"),
              ("1등급 침해", "정보 훼손", "mid")]
    bh, gap = 0.45, 0.16
    h = len(levels) * (bh + gap)
    fig, ax = canvas(W, h)
    for i, (name, cond, k) in enumerate(levels):
        y = h - (i + 1) * (bh + gap) + gap
        box(ax, 0.00, y, 2.30, bh, name, kind=k)
        label(ax, 2.55, y + bh / 2, cond, ha="left")
        if i < 3:
            arrow(ax, [(1.15, y), (1.15, y - gap)])
    save(fig, "fig_levels_v10.png")


def fig_adaptive():
    fig, ax = canvas(W, 1.95)
    box(ax, 0.00, 0.65, 1.15, 0.62, "최종\n응대 정책")
    box(ax, 1.55, 1.15, 2.05, 0.62, "블랙박스 공격자")
    box(ax, 1.55, 0.15, 2.05, 0.62, "화이트박스 공격자")
    label(ax, 5.04, 1.88, "방어율 (7차 · 8차 · 9차)", fs=FS_T, fontweight="bold")
    box(ax, 4.00, 1.15, 2.07, 0.62, "93.3 · 60.0 · 100.0%", bold=False, fs=FS_T)
    box(ax, 4.00, 0.15, 2.07, 0.62, "100.0 · 80.0 · 100.0%", kind="red", bold=False, fs=FS_T)
    arrow(ax, [(1.15, 1.10), (1.55, 1.46)]); arrow(ax, [(1.15, 0.82), (1.55, 0.46)])
    arrow(ax, [(3.60, 1.46), (4.00, 1.46)]); arrow(ax, [(3.60, 0.46), (4.00, 0.46)])
    save(fig, "fig_adaptive_v10.png")


def fig_metarule_gen():
    """Replaces thesis_N10_metarule_generation (quoted text moves to the body)."""
    fig, ax = canvas(W, 0.80)
    row(ax, 0.05, ["실패 판정\n(1라운드)", "보강 규칙\n생성기", "보강 규칙\n1번", "응대 정책\nv1.1"],
        w=1.25, gap=0.36, h=0.70, kinds={2: "red"})
    save(fig, "fig_metarule_gen_v10.png")


# ================================================================ chapter 4 plots
def plot_rounds():
    r7 = [68.1, 71.0, 82.6, 79.7, 88.4]
    r8 = [71.2, 75.8, 63.6, 66.7, 71.2]
    r9 = [68.2, 69.7, 87.9, 93.9, 87.9, 89.4, 93.9, 89.4, 93.9, 93.9, 90.9, 92.4, 92.4, 100.0]
    fig, ax = plt.subplots(figsize=(W, 2.9))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    ax.plot(range(1, 6), r7, color=BLACK, ls="--", marker="s", label="7차")
    ax.plot(range(1, 6), r8, color=G_MID, ls=":", marker="^", label="8차")
    ax.plot(range(1, 15), r9, color=RED, ls="-", marker="o", label="9차")
    ax.set_ylim(50, 104); ax.set_xlim(0.6, 14.5); ax.set_xticks(range(1, 15))
    ax.set_xlabel("라운드"); ax.set_ylabel("준수율 (%)")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.13))
    save(fig, "plot_rounds_v10.png")


def plot_defense():
    cats = ["허위조작정보\n(n=3)", "오정보\n(n=3)", "악의정보\n(n=6)", "보완적 위협\n(n=10~11)"]
    v14 = [100, 100, 100, 100]; vho = [100, 100, 100, 90.9]
    fig, ax = plt.subplots(figsize=(W, 2.8))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    x = range(4); w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], v14, w, color=BLACK, edgecolor=BLACK, label="14라운드")
    b2 = ax.bar([i + w / 2 for i in x], vho, w, color=G_LIGHT, edgecolor=BLACK, label="헬드아웃")
    for b in list(b1) + list(b2):
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}" if v == 100 else f"{v:.1f}", ha="center", fontsize=FS)
    ax.set_xticks(list(x)); ax.set_xticklabels(cats)
    ax.set_ylim(0, 115); ax.set_ylabel("방어 성공률 (%)")
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.13))
    save(fig, "plot_defense_v10.png")


def plot_cross():
    runs = ["7차", "8차", "9차"]
    data = [("오픈AI", [60.9, 68.2, 100.0]), ("구글", [60.9, 50.0, 87.0]), ("앤트로픽", [52.2, 31.8, 91.3])]
    fig, ax = plt.subplots(figsize=(W, 2.8))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    w = 0.26
    for k, (name, vals) in enumerate(data):
        bs = ax.bar([i + (k - 1) * w for i in range(3)], vals, w, color=[BLACK, G_MID, G_LIGHT][k], edgecolor=BLACK, label=name)
        for b in bs:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.0f}", ha="center", fontsize=FS)
    ax.set_xticks(range(3)); ax.set_xticklabels(runs)
    ax.set_ylim(0, 112); ax.set_yticks(range(0, 101, 20)); ax.set_ylabel("통과율 (%)")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.14))
    save(fig, "plot_cross_v10.png")


def plot_5w1h():
    axes_ = ["누가", "왜", "언제", "무엇을", "어떻게"]
    base = [12.5, 18.6, 5.3, 16.7, 13.3]; w5 = [48.6, 37.5, 20.0, 50.0, 38.1]
    fig, ax = plt.subplots(figsize=(W, 2.7))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    x = range(5); w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], base, w, color=G_LIGHT, edgecolor=BLACK, label="기준형")
    b2 = ax.bar([i + w / 2 for i in x], w5, w, color=BLACK, edgecolor=BLACK, label="육하원칙형")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.0, f"{b.get_height():.1f}", ha="center", fontsize=FS)
    ax.set_xticks(list(x)); ax.set_xticklabels(axes_)
    ax.set_ylim(0, 60); ax.set_ylabel("실패 비율 (%)")
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.13))
    save(fig, "plot_5w1h_v10.png")


# ================================================================ chapter 2: one figure per prior-work structure
def rel_guardrail():
    fig, ax = canvas(W, 0.80)
    row(ax, 0.05, ["사용자\n입력", "입력 레일", "대화·검색\n레일", "LLM", "출력 레일"], w=1.0, gap=0.265, h=0.70,
        kinds={1: "light", 2: "light", 4: "light"})
    save(fig, "related_guardrail_v2.png")


def _loop(name, labels, kinds=None):
    fig, ax = canvas(W, 1.05)
    xs = row(ax, 0.30, labels, w=1.0, gap=0.265, h=0.70, kinds=kinds)
    arrow(ax, [(xs[-1] + 0.5, 0.30), (xs[-1] + 0.5, 0.05), (xs[0] + 0.5, 0.05), (xs[0] + 0.5, 0.30)])
    save(fig, name)


def rel_apo():
    _loop("related_apo_v2.png", ["현재\n프롬프트", "정확도\n평가", "오답\n분석", "수정 후보\n생성", "후보\n선택"])


def rel_repair():
    _loop("related_repair_loop_v2.png", ["테스트\n실행", "심판관\n평가", "실패\n진단", "프롬프트\n수정", "재평가"],
          kinds={3: "red"})


def rel_venn():
    fig, ax = canvas(3.40, 2.20)
    ax.add_patch(Circle((1.20, 1.00), 0.92, fc="none", ec=BLACK, lw=1.1))
    ax.add_patch(Circle((2.20, 1.00), 0.92, fc="none", ec=BLACK, lw=1.1))
    label(ax, 0.75, 2.08, "거짓 정보", fs=FS_T, fontweight="bold")
    label(ax, 2.65, 2.08, "해를 끼칠 의도", fs=FS_T, fontweight="bold")
    label(ax, 0.78, 1.00, "오정보")
    label(ax, 1.70, 1.00, "허위\n조작\n정보", color=RED, fontweight="bold", linespacing=1.15)
    label(ax, 2.62, 1.00, "악의정보")
    save(fig, "related_disorder_venn_v2.png")


def rel_attack():
    fig, ax = canvas(4.80, 1.55)
    box(ax, 0.00, 0.88, 1.60, 0.62, "간접 프롬프트\n인젝션", kind="red")
    box(ax, 0.00, 0.05, 1.60, 0.62, "RAG 오염", kind="red")
    box(ax, 2.05, 0.46, 1.10, 0.62, "RAG 검색")
    box(ax, 3.55, 0.46, 1.25, 0.62, "LLM 응답")
    arrow(ax, [(1.60, 1.19), (1.82, 1.19), (1.82, 0.90), (2.05, 0.90)])
    arrow(ax, [(1.60, 0.36), (1.82, 0.36), (1.82, 0.64), (2.05, 0.64)])
    arrow(ax, [(3.15, 0.77), (3.55, 0.77)])
    save(fig, "related_attack_paths_v2.png")


def rel_robust():
    fig, ax = canvas(W, 1.55)
    ys = [1.05, 0.55, 0.05]
    for i, y in enumerate(ys):
        box(ax, 0.00, y, 1.15, 0.42, ["문서 1", "문서 2", "문서 k"][i], kind="red" if i == 2 else "plain", bold=False)
        box(ax, 1.50, y, 1.25, 0.42, ["응답 1", "응답 2", "응답 k"][i], bold=False)
        arrow(ax, [(1.15, y + 0.21), (1.50, y + 0.21)])
        arrow(ax, [(2.75, y + 0.21), (3.20, 0.76)])
    box(ax, 3.20, 0.45, 1.30, 0.62, "안전한 집계", kind="light")
    box(ax, 4.85, 0.45, 1.22, 0.62, "최종 응답")
    arrow(ax, [(4.50, 0.76), (4.85, 0.76)])
    save(fig, "related_robustrag_v2.png")


def rel_judge():
    fig, ax = canvas(4.60, 0.75)
    row(ax, 0.05, ["질문·응답", "심판 LLM", "점수"], w=1.25, gap=0.42, h=0.62, kinds={1: "mid"})
    save(fig, "related_judge_basic_v2.png")


def rel_faith():
    fig, ax = canvas(5.00, 1.45)
    box(ax, 0.00, 0.80, 1.45, 0.58, "질문·응답")
    box(ax, 0.00, 0.05, 1.45, 0.58, "환각 사례\n(사람 주석)", kind="light")
    box(ax, 1.95, 0.42, 1.25, 0.62, "심판 LLM", kind="mid")
    box(ax, 3.65, 0.42, 1.35, 0.62, "충실성 판정")
    arrow(ax, [(1.45, 1.09), (1.70, 1.09), (1.70, 0.86), (1.95, 0.86)])
    arrow(ax, [(1.45, 0.34), (1.70, 0.34), (1.70, 0.60), (1.95, 0.60)])
    arrow(ax, [(3.20, 0.73), (3.65, 0.73)])
    save(fig, "related_judge_faith_v2.png")


def rel_ours():
    fig, ax = canvas(W, 1.60)
    box(ax, 0.00, 0.50, 1.10, 0.62, "챗봇 응답")
    box(ax, 1.50, 0.92, 1.40, 0.62, "정답 대조\n(코드)")
    box(ax, 1.50, 0.05, 1.40, 0.62, "심판관\n(새 세션)", kind="mid")
    box(ax, 3.30, 0.92, 1.35, 0.62, "정보 무결성", kind="red")
    box(ax, 3.30, 0.05, 1.35, 0.62, "정책 준수")
    box(ax, 5.00, 0.50, 1.07, 0.62, "4단계\n등급")
    arrow(ax, [(1.10, 0.95), (1.50, 1.23)]); arrow(ax, [(1.10, 0.67), (1.50, 0.36)])
    arrow(ax, [(2.90, 1.23), (3.30, 1.23)]); arrow(ax, [(2.90, 0.50), (3.30, 1.05)])
    arrow(ax, [(2.90, 0.30), (3.30, 0.30)])
    arrow(ax, [(4.65, 1.23), (5.00, 0.95)]); arrow(ax, [(4.65, 0.36), (5.00, 0.67)])
    save(fig, "related_judge_ours_v2.png")


if __name__ == "__main__":
    for fn in [fig_overview, fig_prep, fig_struct1, fig_struct2, fig_struct3, fig_integrated, fig_taxonomy,
               fig_levels, fig_adaptive, fig_metarule_gen, plot_rounds, plot_defense, plot_cross, plot_5w1h,
               rel_guardrail, rel_apo, rel_repair, rel_venn, rel_attack, rel_robust, rel_judge, rel_faith, rel_ours]:
        fn()
