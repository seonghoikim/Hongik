"""Charts a~g (+ N11 setup table, N12 Unit-D FAIL analysis).

Panel size 8.0 x 6.5 in (= ~60% of a 13.33 in 16:9 slide). Place each PNG at 8 in wide and every
label is >= 18 pt on the slide. All numbers are read from the raw JSON; data/numbers.json is the dump.
Naming on the figures follows the outline: 7차 = "5라운드 실행", 9차 = "15라운드 실행".
"""
from __future__ import annotations

import json
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

from common import (BLACK, CATEGORIES, CAT_KO, DATA_OUT, DGRAY, FIGSIZE_PANEL, GRADE_SCORE_3,
                    LGRAY, MGRAY, RED, RELEVEL9, RUN7, RUN9, SRS7_DIR, SRS9_DIR, WHITE, XLGRAY, load, save,
                    srs_rule_counts)

plt.rcParams.update({"font.size": 20, "xtick.labelsize": 19, "ytick.labelsize": 19, "axes.labelsize": 20,
                     "legend.fontsize": 18})
MIN = 18  # minimum font size anywhere on a panel figure

d7, d9, rl = load(RUN7), load(RUN9), load(RELEVEL9)
numbers: dict = {}
R7, R9 = "5라운드 실행", "15라운드 실행"


def rounds_summary(d):
    return [dict(label=r["label"], srs=r["srs_version"], n=len(r["results"]),
                 PASS=r["pass_count"], WARNING=r["warning_count"], FAIL=r["fail_count"],
                 score=r["total_score"], max=r["max_score"], rate=r["compliance_rate"],
                 ungradable=[u["scenario_id"] for u in r["ungradable_details"]],
                 fail_by_unitD=sum(1 for x in r["results"] if x["grade"] == "FAIL" and x["blocked_by_unit"] == "D"),
                 fail_by_model=sum(1 for x in r["results"] if x["grade"] == "FAIL" and x["blocked_by_unit"] != "D"))
            for r in d["healing_rounds"]]


def stage_summary(d, key):
    s = d[key]
    out = dict(srs=s["srs_version"], n=len(s["results"]), rate=s.get("compliance_rate"))
    for k in ("pass_count", "warning_count", "fail_count", "ungradable_count",
              "per_backend_pass_rate", "cross_model_validated_count", "cross_model_validated_rate"):
        if k in s:
            out[k] = s[k]
    if s["results"] and "grade" in s["results"][0]:
        out["fail_by_unitD"] = sum(1 for x in s["results"] if x["grade"] == "FAIL" and x["blocked_by_unit"] == "D")
    out["ungradable"] = [u["scenario_id"] for u in s["ungradable_details"]]
    return out


for tag, d in (("run7", d7), ("run9", d9)):
    numbers[tag] = dict(
        rounds=rounds_summary(d), final_srs_version=d["final_srs_version"],
        held_out=stage_summary(d, "held_out"), adaptive_blackbox=stage_summary(d, "adaptive_blackbox"),
        adaptive_whitebox=stage_summary(d, "adaptive_whitebox"), cross_model=stage_summary(d, "cross_model"),
        stats={k: dict(p=v["p_value"], stat=v["statistic"]) for k, v in d["stats"].items()},
        usage={k: d["usage_summary"][k] for k in
               ("total_calls", "total_errors", "total_input_tokens", "total_output_tokens", "estimated_cost_usd")},
        usage_by_role=d["usage_summary"]["by_provider_role"], run_at_utc=d["run_at_utc"],
        primary_provider=d["primary_provider"], redteam_provider=d["redteam_provider"],
        cross_model_backends=d["cross_model_backends"], kb_version=d["kb_version"],
    )
numbers["run9"]["relevel4_summary"] = rl["summary"]
numbers["run7"]["meta_rule_counts"] = srs_rule_counts(SRS7_DIR)
numbers["run9"]["meta_rule_counts"] = srs_rule_counts(SRS9_DIR)


def grid(ax):
    ax.yaxis.grid(True, color=XLGRAY, lw=1)
    ax.set_axisbelow(True)


# =================================================================== a. 5-round curve
def chart_a():
    rs, ho = numbers["run7"]["rounds"], numbers["run7"]["held_out"]
    x = np.arange(1, len(rs) + 1)
    y = [r["rate"] for r in rs]
    fig, ax = plt.subplots(figsize=FIGSIZE_PANEL)
    ax.plot(x, y, color=BLACK, lw=3, marker="o", ms=12, zorder=3)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points",
                    xytext=(0, -40) if xi in (2, 4) else (0, 14), ha="center", fontsize=21,
                    fontweight="bold" if xi in (1, 5) else "normal")
    hx = len(rs) + 1.4
    ax.axvline(len(rs) + 0.7, color=LGRAY, lw=1.5, ls="--")
    ax.plot([hx], [ho["rate"]], marker="D", ms=15, color=RED, zorder=3)
    ax.annotate(f"{ho['rate']:.1f}", (hx, ho["rate"]), textcoords="offset points", xytext=(0, 14), ha="center",
                fontsize=21, fontweight="bold", color=RED)
    ax.set_xticks(list(x) + [hx])
    ax.set_xticklabels([str(i) for i in x] + ["헬드\n아웃"])
    ax.set_xlabel("라운드")
    ax.set_ylim(60, 100)
    ax.set_xlim(0.5, hx + 0.6)
    ax.set_ylabel("준수율 (%)")
    grid(ax)
    p = numbers["run7"]["stats"]["wilcoxon_v1_vs_final_healing_set"]["p"]
    ax.text(3, 63, f"R1→R5 Wilcoxon p = {p:.5f}", ha="center", fontsize=MIN, color=DGRAY)
    save(fig, "chart_a_run7_rounds.png")


# =================================================================== b. 15-round curve
def chart_b():
    rs, ho, cm = numbers["run9"]["rounds"], numbers["run9"]["held_out"], numbers["run9"]["cross_model"]
    x = np.arange(1, len(rs) + 1)
    y = np.array([r["rate"] for r in rs])
    fig, ax = plt.subplots(figsize=FIGSIZE_PANEL)
    osc = y[2:13]
    ax.axhspan(osc.min(), osc.max(), color=XLGRAY, zorder=0)
    ax.text(8, osc.min() - 1.2, f"진동 구간 {osc.min():.1f}~{osc.max():.1f}%", ha="center", va="top",
            fontsize=MIN, color=DGRAY)
    ax.plot(x[:-1], y[:-1], color=BLACK, lw=2.5, marker="o", ms=8, zorder=3)
    ax.plot(x[-2:], y[-2:], color=RED, lw=3, zorder=3)
    ax.plot([x[-1]], [y[-1]], marker="o", ms=14, color=RED, zorder=4)
    ax.annotate("100", (x[-1], y[-1]), textcoords="offset points", xytext=(-14, 6), ha="right", va="bottom",
                fontsize=21, fontweight="bold", color=RED)
    ax.annotate(f"{y[0]:.1f}", (x[0], y[0]), textcoords="offset points", xytext=(4, -34), ha="center", fontsize=MIN)
    hx, cx = len(rs) + 1.7, len(rs) + 3.3
    ax.axvline(len(rs) + 0.85, color=LGRAY, lw=1.5, ls="--")
    ax.plot([hx], [ho["rate"]], marker="D", ms=13, color=BLACK)
    ax.plot([cx], [cm["cross_model_validated_rate"]], marker="s", ms=13, color=BLACK)
    ax.annotate(f"{ho['rate']:.1f}", (hx, ho["rate"]), textcoords="offset points", xytext=(0, 12), ha="center",
                fontsize=20, fontweight="bold")
    ax.annotate(f"{cm['cross_model_validated_rate']:.1f}", (cx, cm["cross_model_validated_rate"]),
                textcoords="offset points", xytext=(0, -34), ha="center", fontsize=20, fontweight="bold")
    ax.set_xticks([1, 3, 5, 7, 9, 11, 14, hx, cx])
    ax.set_xticklabels(["1", "3", "5", "7", "9", "11", "14", "헬드\n아웃", "교차\n모델"])
    ax.set_xlabel("라운드", labelpad=-4)
    ax.set_ylim(60, 104)
    ax.set_xlim(0.4, cx + 0.8)
    ax.set_ylabel("준수율 (%)")
    grid(ax)
    save(fig, "chart_b_run9_rounds.png")


# =================================================================== c. per-category heatmap
def cat_rates(results):
    agg = defaultdict(list)
    for r in results:
        agg[r["category"]].append(GRADE_SCORE_3[r["grade"]])
    return {k: (sum(v) / (3 * len(v)) * 100, len(v)) for k, v in agg.items()}


def chart_c():
    cols = [("5R\nR1", d7["healing_rounds"][0]["results"]), ("5R\nR5", d7["healing_rounds"][-1]["results"]),
            ("15R\nR1", d9["healing_rounds"][0]["results"]), ("15R\nR14", d9["healing_rounds"][-1]["results"]),
            ("15R\n헬드\n아웃", d9["held_out"]["results"])]
    rates = [cat_rates(res) for _, res in cols]
    numbers["per_category"] = {lab.replace("\n", " "): {k: dict(rate=round(v[0], 1), n=v[1]) for k, v in r.items()}
                               for (lab, _), r in zip(cols, rates)}
    keys = [k for k, *_ in CATEGORIES]
    M = np.array([[rates[j][k][0] for j in range(len(cols))] for k in keys])
    fig, ax = plt.subplots(figsize=(8.0, 7.2))
    cmap = LinearSegmentedColormap.from_list("g", ["#ffffff", "#bdbdbd", "#3a3a3a"])
    ax.imshow(M, cmap=cmap, vmin=60, vmax=100, aspect="auto")
    for i, k in enumerate(keys):
        for j in range(len(cols)):
            v = rates[j][k][0]
            color = WHITE if v >= 88 else BLACK
            if v < 100 and j >= 3:
                color = RED
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=21, fontweight="bold", color=color)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c for c, _ in cols], fontsize=MIN, linespacing=1.1)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([CAT_KO[k] + ("*" if k == "encoding_bypass" else "") for k in keys], fontsize=MIN)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-.5, len(keys)), minor=True)
    ax.grid(which="minor", color=WHITE, lw=3)
    ax.tick_params(which="minor", length=0)
    ax.axvline(1.5, color=WHITE, lw=10)
    fig.text(0.02, 0.0, "범주별 준수율(%). 5R = 5라운드 실행, 15R = 15라운드 실행\n* 인코딩 우회는 채점 가능 1~2건",
             fontsize=MIN, color=DGRAY, va="top")
    save(fig, "chart_c_category_heatmap.png")


# =================================================================== d. grade stacks (3-tier, all rounds)
def chart_d():
    rs = numbers["run9"]["rounds"]
    x = np.arange(1, len(rs) + 1)
    P, W, F = (np.array([r[k] for r in rs]) for k in ("PASS", "WARNING", "FAIL"))
    fig, ax = plt.subplots(figsize=FIGSIZE_PANEL)
    w = 0.74
    ax.bar(x, P, w, color=BLACK, edgecolor=WHITE, lw=1.5, label="PASS")
    ax.bar(x, W, w, bottom=P, color=LGRAY, edgecolor=WHITE, lw=1.5, label="WARNING")
    ax.bar(x, F, w, bottom=P + W, color=RED, edgecolor=WHITE, lw=1.5, label="FAIL")
    for xi, p, wv, f in zip(x, P, W, F):
        if f:
            ax.text(xi, p + wv + f + 0.3, str(f), ha="center", va="bottom", color=RED, fontsize=MIN, fontweight="bold")
    ax.text(14, 11, "22", ha="center", va="center", color=WHITE, fontsize=20, fontweight="bold")
    ax.text(1, 11, str(W[0]), ha="center", va="center", color=BLACK, fontsize=MIN)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 14])
    ax.set_xlabel("라운드")
    ax.set_ylabel("시나리오 수 (채점 22건)")
    ax.set_ylim(0, 25.5)
    ax.legend(loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.13))
    save(fig, "chart_d_run9_grade_stack.png")


def chart_d2():
    order = ["FULL_DEFENSE", "FUNCTIONAL_DEFENSE", "PARTIAL_EXPOSURE", "BREACH"]
    colors = [BLACK, MGRAY, LGRAY, RED]
    s = rl["summary"]
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    for yi, key in ((1, "1"), (0, "14")):
        left = 0
        for g, c in zip(order, colors):
            v = s[key][g]
            if v:
                ax.barh(yi, v, left=left, color=c, edgecolor=WHITE, lw=2, height=0.6)
                ax.text(left + v / 2, yi, str(v), ha="center", va="center", fontsize=22, fontweight="bold",
                        color=BLACK if c == LGRAY else WHITE)
                left += v
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["라운드 1", "라운드 14"], fontsize=20)
    ax.set_xlim(0, 22)
    ax.set_xticks([0, 5, 10, 15, 22])
    ax.set_xlabel("시나리오 수")
    ax.legend(handles=[Patch(color=c, label=f"L{i} {g}") for i, (g, c) in zip((4, 3, 2, 1), zip(order, colors))],
              loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.45, -0.24), fontsize=MIN)
    ax.set_title("4단계 사후 재채점(라운드 1·14)", loc="left", fontsize=22, pad=12)
    save(fig, "chart_d2_run9_level4_relevel.png")


# =================================================================== e. meta-rule cumulative
def chart_e():
    c9, c7 = numbers["run9"]["meta_rule_counts"], numbers["run7"]["meta_rule_counts"]
    rs = numbers["run9"]["rounds"]
    x = np.arange(1, len(rs) + 1)
    y9 = [c9[r["srs"]] for r in rs]
    y7 = [c7[r["srs"]] for r in numbers["run7"]["rounds"]]
    fig, ax = plt.subplots(figsize=FIGSIZE_PANEL)
    ax.bar(x, y9, 0.7, color=[LGRAY] * (len(x) - 1) + [RED], edgecolor=WHITE, lw=1.5)
    for xi, yi in zip(x, y9):
        if xi in (2, 5, 8, 11, 14):
            ax.text(xi, yi + 0.5, str(yi), ha="center", fontsize=20 if xi == 14 else MIN,
                    color=RED if xi == 14 else BLACK, fontweight="bold" if xi == 14 else "normal")
    ax.plot(x[:5], y7, color=BLACK, lw=2.2, ls="--", marker="o", ms=8)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 14])
    ax.set_xlabel("라운드 (라운드 n은 SRS v1.(n-1) 적용)")
    ax.set_ylabel("적용된 Meta-Rule 수")
    ax.set_ylim(0, 32)
    grid(ax)
    ax.legend(handles=[Patch(color=LGRAY, label=f"{R9} (최종 v1.13 = {c9['v1.13']}개)"),
                       plt.Line2D([], [], color=BLACK, ls="--", marker="o", label=f"{R7} (최종 v1.5 = {c7['v1.5']}개)")],
              loc="upper left", frameon=False, fontsize=MIN)
    save(fig, "chart_e_metarule_cumulative.png")


# =================================================================== f. cross-model (two groups by SRS)
def chart_f():
    vend = [("openai", "GPT"), ("gemini", "Gemini"), ("anthropic", "Claude")]
    groups = [(f"{R7}\nSRS v1.5", numbers["run7"]["cross_model"]), (f"{R9}\nSRS v1.13", numbers["run9"]["cross_model"])]
    shades = [BLACK, DGRAY, MGRAY]
    fig, ax = plt.subplots(figsize=FIGSIZE_PANEL)
    w, xs, labels = 0.8, [], []
    for gi, (gname, cm) in enumerate(groups):
        base = gi * 5.0
        vals = [cm["per_backend_pass_rate"][k] for k, _ in vend] + [cm["cross_model_validated_rate"]]
        for bi, (v, c) in enumerate(zip(vals, shades + [RED])):
            xb = base + bi + (0.35 if bi == 3 else 0)
            ax.bar(xb, v, w, color=c, edgecolor=WHITE)
            ax.text(xb, v + 1.5, f"{v:.0f}" if v == 100 else f"{v:.1f}", ha="center", fontsize=MIN,
                    color=RED if bi == 3 else BLACK, fontweight="bold" if bi == 3 else "normal")
            xs.append(xb)
        ax.text(base + 1.6, -4, gname, ha="center", va="top", fontsize=MIN, fontweight="bold")
    ax.set_xticks([])
    ax.legend(handles=[Patch(color=c, label=l) for c, l in zip(shades + [RED],
              ["GPT-5.4", "Gemini 3.6 Flash", "Claude Sonnet 5", "2/3 이상 통과"])],
              loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=2, frameon=False, fontsize=MIN)
    ax.set_ylim(0, 108)
    ax.set_ylabel("헬드아웃 PASS 비율 (%)")
    grid(ax)
    fig.subplots_adjust(bottom=0.18, top=0.83)
    save(fig, "chart_f_cross_model.png")


# =================================================================== g. cost table
def chart_g():
    rows = []
    for tag, name in (("run7", R7), ("run9", R9)):
        u = numbers[tag]["usage"]
        rows.append([name, f"{u['total_calls']:,}회",
                     f"{(u['total_input_tokens'] + u['total_output_tokens']) / 1e6:.1f}M",
                     f"${u['estimated_cost_usd']:.2f}"])
    header = ["실행", "API 호출", "토큰", "추정 비용"]
    fig, ax = plt.subplots(figsize=(8.0, 2.6))
    ax.axis("off")
    tb = ax.table(cellText=rows, colLabels=header, loc="center", cellLoc="center", colWidths=[0.36, 0.22, 0.18, 0.24])
    tb.auto_set_font_size(False)
    tb.set_fontsize(20)
    tb.scale(1, 3.0)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor(WHITE)
        cell.set_linewidth(2)
        if r == 0:
            cell.set_text_props(fontweight="bold", color=WHITE)
            cell.set_facecolor(BLACK)
        else:
            cell.set_facecolor(XLGRAY if r % 2 == 0 else WHITE)
            if c == len(header) - 1:
                cell.set_text_props(color=RED, fontweight="bold")
    fig.text(0.02, 0.0, "가격표 기반 추정치(실제 청구액 아님)", fontsize=MIN, color=DGRAY)
    save(fig, "chart_g_cost_table.png")


# =================================================================== N11 setup table
def n11():
    n_rounds9 = len(numbers["run9"]["rounds"])
    rows = [
        ["대상", "실제 운영 중인 상품 상담 챗봇\n(단일 도메인 파일럿, 업체명 비공개)"],
        ["SRS v1.0", "실제 운영 지침: 페르소나 + 제약 조건 17개"],
        ["RAG", "실제 상품 설명 자료 6종"],
        ["시나리오", "8범주 × 3 = 치유용 24 / 헬드아웃 24"],
        ["응답·심판관·\nMeta-Rule", "Claude Sonnet 5"],
        ["레드팀 생성", "GPT-5.4 (타 벤더)"],
        ["교차 모델", "GPT-5.4 · Gemini 3.6 Flash ·\nClaude Sonnet 5"],
        ["실행", f"라운드 상한 5 / 상한 15\n(상한 15는 라운드 {n_rounds9}에서 종료)"],
        ["준수율", "점수 합 ÷ 만점\n(PASS 3 · WARNING 2 · FAIL 1)"],
    ]
    fig, ax = plt.subplots(figsize=(8.0, 7.6))
    ax.axis("off")
    tb = ax.table(cellText=rows, loc="center", cellLoc="left", colWidths=[0.3, 0.7])
    tb.auto_set_font_size(False)
    tb.set_fontsize(MIN)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor(WHITE)
        cell.set_linewidth(2)
        two = "\n" in rows[r][0] or "\n" in rows[r][1]
        cell.set_height(0.135 if two else 0.085)
        cell.PAD = 0.04
        if c == 0:
            cell.set_facecolor(BLACK)
            cell.set_text_props(color=WHITE, fontweight="bold")
        else:
            cell.set_facecolor(XLGRAY if r % 2 else WHITE)
    save(fig, "N11_experiment_setup.png")


# =================================================================== N12 Unit D FAIL analysis
def n12():
    rs = numbers["run9"]["rounds"]
    ho = numbers["run9"]["held_out"]
    labels = [str(i) for i in range(1, len(rs) + 1)] + ["헬드\n아웃"]
    D = [r["fail_by_unitD"] for r in rs] + [ho["fail_by_unitD"]]
    M = [r["fail_by_model"] for r in rs] + [ho["fail_count"] - ho["fail_by_unitD"]]
    x = np.arange(len(labels), dtype=float)
    x[-1] += 0.6
    fig = plt.figure(figsize=(8.0, 7.0))
    ax = fig.add_axes([0.11, 0.42, 0.86, 0.5])
    ax.bar(x, D, 0.72, color=RED, edgecolor=WHITE, label=f"유닛 D 고정 문구 ({sum(D)}건)")
    ax.bar(x, M, 0.72, bottom=D, color=MGRAY, edgecolor=WHITE, label=f"모델 응답 ({sum(M)}건)")
    ax.set_xticks(x)
    show = {0, 2, 4, 6, 8, 10, 13, len(labels) - 1}
    ax.set_xticklabels([lab if i in show else "" for i, lab in enumerate(labels)])
    ax.set_ylabel("라운드별 FAIL 건수")
    ax.set_yticks([0, 1, 2])
    ax.set_ylim(0, 2.9)
    grid(ax)
    ax.legend(loc="upper left", frameon=False, ncol=1, fontsize=MIN)
    fallback = next(r["chatbot_response"] for r in d9["held_out"]["results"]
                    if r["blocked_by_unit"] == "D" and r["grade"] == "FAIL")
    first, second = fallback.split(". ", 1)
    fig.text(0.04, 0.24, "유닛 D 고정 거절 문구(15라운드 실행 당시 원문)", fontsize=MIN, fontweight="bold")
    fig.text(0.04, 0.17, f"“{first}.", fontsize=MIN)
    fig.text(0.04, 0.10, f" {second}”", fontsize=MIN, color=RED)
    fig.text(0.04, 0.03, "→ 문구 자체가 SRS 제약 9번(추가 질문 권유 금지) 위반", fontsize=MIN, color=DGRAY)
    numbers["run9"]["fallback_message"] = fallback
    save(fig, "N12_unitD_fail_analysis.png")


if __name__ == "__main__":
    chart_a(); chart_b(); chart_c(); chart_d(); chart_d2(); chart_e(); chart_f(); chart_g(); n11(); n12()
    with open(DATA_OUT / "numbers.json", "w", encoding="utf-8") as f:
        json.dump(numbers, f, ensure_ascii=False, indent=1)
    print("wrote", DATA_OUT / "numbers.json")
