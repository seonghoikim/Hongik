# -*- coding: utf-8 -*-
"""본 실험(2026-10-16 실행) 결과 그림 2종. 결과 파일에서 직접 계산한다. 색·글자는 make_figs_v10.py와 같다.

  plot_main_rounds_v1.png  라운드별 정보 무결성 유지율(주 지표, RAG 오염, 개인정보)과 v1.0 기준 정책 준수율
  plot_main_cross_v1.png   교차 모델 검증 — 응답 모델별 주 지표 정보 무결성 유지(헬드아웃, 5회 다수결)

    python3 diagrams/summary_v2/make_main_figs.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figs_v10 as V  # noqa: E402

plt, BLACK, RED, G_LIGHT, G_MID, W, FS = V.plt, V.BLACK, V.RED, V.G_LIGHT, V.G_MID, V.W, V.FS
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULT = os.path.join(ROOT, "data", "results", "experiment_real_20261016_225909.json")
PRIMARY = {"rag_poisoning", "pii_leak"}


def pct(rs, cats, key):
    sel = [r for r in rs if r["category"] in cats and r.get(key)]
    return 100 * sum(r[key] == "INTACT" for r in sel) / len(sel)


def main():
    d = json.load(open(RESULT, encoding="utf-8"))
    rounds = d["healing_rounds"]
    x = list(range(1, len(rounds) + 1))
    prim = [pct(r["results"], PRIMARY, "ref_info_integrity") for r in rounds]
    rag = [pct(r["results"], {"rag_poisoning"}, "ref_info_integrity") for r in rounds]
    pii = [pct(r["results"], {"pii_leak"}, "ref_info_integrity") for r in rounds]
    pol = []
    for r in rounds:
        sel = [x_ for x_ in r["results"] if x_.get("ref_policy_compliance")]
        pol.append(100 * sum(x_["ref_policy_compliance"] == "COMPLIANT" for x_ in sel) / len(sel))

    fig, ax = plt.subplots(figsize=(W, 2.9))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    ax.plot(x, prim, color=RED, marker="o", lw=2.0, label="주 지표")
    ax.plot(x, rag, color=BLACK, ls="--", marker="s", label="RAG 오염")
    ax.plot(x, pii, color=G_MID, ls=":", marker="^", label="개인정보 유출")
    ax.plot(x, pol, color=G_MID, ls="-", marker="D", ms=4, label="정책 준수")
    ax.set_xticks(x); ax.set_xticklabels([f"{i}\n{r['srs_version']}" for i, r in zip(x, rounds)])
    ax.set_ylim(-3, 105); ax.set_xlabel("라운드"); ax.set_ylabel("비율 (%)")
    ax.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.15))
    V.save(fig, "plot_main_rounds_v1.png")

    cm = [r for r in d["cross_model"]["results"] if r["category"] in PRIMARY]
    names = [("gemini", "Gemini\n(운영 모델)"), ("openai", "GPT-5.4"), ("anthropic", "Claude")]
    vals = [sum(r["backend_info_integrity"].get(k) == "INTACT" for r in cm) for k, _ in names]
    fig, ax = plt.subplots(figsize=(4.6, 2.6))
    ax.grid(axis="y", alpha=0.3, lw=0.6)
    bars = ax.bar(range(3), vals, 0.55, color=[RED, G_MID, G_LIGHT], edgecolor=BLACK)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v}/{len(cm)}", ha="center", fontsize=FS)
    ax.set_xticks(range(3)); ax.set_xticklabels([n for _, n in names])
    ax.set_ylim(0, len(cm) + 3); ax.set_ylabel("유지 문항 수")
    V.save(fig, "plot_main_cross_v1.png")


if __name__ == "__main__":
    main()
