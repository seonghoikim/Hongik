# -*- coding: utf-8 -*-
"""저자 사람 확인(docs/review/human_review_main_20261017_v2.csv)을 본 실험 결과에 대입한 민감도 분석.

분석 계획 v5 4절에 따라 원래 판정은 그대로 두고, 확인한 문항만 저자 판정으로 바꿔 H1~H3와 라운드별
주 지표를 다시 계산한다. 저자 판정은 그 단계의 응답 자체에 대한 판정이므로 그 문항의 info_integrity와
ref_info_integrity(교차 모델은 Claude 응답)를 모두 바꾼다.

    python3 scripts/apply_human_review.py
"""
import csv
import json
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hongik_selfheal.stats import cochran_q, mcnemar_exact, noninferiority_two_proportions  # noqa: E402

RESULT = os.path.join(ROOT, "data", "results", "experiment_real_20261016_225909.json")
REVIEW = os.path.join(ROOT, "docs", "review", "human_review_main_20261017_v2.csv")
OUT = os.path.join(ROOT, "data", "results", "human_review_sensitivity_20261017.json")
PRIMARY = {"rag_poisoning", "pii_leak"}
LABEL = {"유지": "INTACT", "부분훼손": "PARTIAL", "훼손": "BROKEN"}
COL = "저자 판정(유지/부분훼손/훼손)"


def load_review():
    rows = list(csv.DictReader(open(REVIEW, encoding="utf-8-sig")))
    for r in rows:
        r["author"] = LABEL[r[COL].replace(" ", "")]
    return rows


def agreement(rows, key):
    exact = sum(r["author"] == r[key] for r in rows)
    binary = sum((r["author"] == "INTACT") == (r[key] == "INTACT") for r in rows)
    pairs = Counter(f"{r[key]}→{r['author']}" for r in rows if r["author"] != r[key])
    return {"n": len(rows), "3단계 일치": exact, "유지 여부 일치": binary, "불일치": dict(pairs)}


def stage_results(d, stage):
    if stage.startswith("round_"):
        return d["healing_rounds"][int(stage[6:]) - 1]["results"]
    return d[stage]["results"]


def apply(d, rows):
    for r in rows:
        if r["단계"] == "cross_model":
            for x in d["cross_model"]["results"]:
                if x["scenario_id"] == r["문항"]:
                    x["backend_info_integrity"]["anthropic"] = r["author"]
            continue
        for x in stage_results(d, r["단계"]):
            if x["scenario_id"] == r["문항"]:
                x["info_integrity"] = r["author"]
                if x.get("ref_info_integrity"):
                    x["ref_info_integrity"] = r["author"]


def intact(rs, key, cats=PRIMARY):
    return {x["scenario_id"]: int(x[key] == "INTACT") for x in rs if x["category"] in cats and x.get(key)}


def hypotheses(d):
    first, last = d["healing_rounds"][0]["results"], d["healing_rounds"][-1]["results"]
    a, b = intact(first, "ref_info_integrity"), intact(last, "ref_info_integrity")
    ids = [i for i in a if i in b]
    h1 = mcnemar_exact([a[i] for i in ids], [b[i] for i in ids])
    heal = list(intact(last, "info_integrity").values())
    held = list(intact(d["held_out"]["results"], "info_integrity").values())
    h2 = noninferiority_two_proportions(sum(heal), len(heal), sum(held), len(held), margin=0.10)
    cm = [x for x in d["cross_model"]["results"] if x["category"] in PRIMARY]
    groups = [[int(x["backend_info_integrity"].get(p) == "INTACT") for x in cm] for p in ("gemini", "openai", "anthropic")]
    h3 = cochran_q(*groups)
    return {
        "H1": {"1라운드": f"{sum(a[i] for i in ids)}/{len(ids)}", "5라운드": f"{sum(b[i] for i in ids)}/{len(ids)}",
               "개선": sum(a[i] == 0 and b[i] == 1 for i in ids), "악화": sum(a[i] == 1 and b[i] == 0 for i in ids),
               "p": h1.p_value},
        "H2": {"보강용 5라운드": f"{sum(heal)}/{len(heal)}", "헬드아웃": f"{sum(held)}/{len(held)}", "결과": h2.note},
        "H3": {"Gemini·GPT-5.4·Claude": [f"{sum(g)}/{len(g)}" for g in groups], "Q": h3.statistic, "p": h3.p_value},
    }


def round_table(d):
    rows = []
    for i, r in enumerate(d["healing_rounds"], 1):
        rs = r["results"]
        cell = lambda cats: f"{sum(intact(rs, 'ref_info_integrity', cats).values())}/{len(intact(rs, 'ref_info_integrity', cats))}"
        rows.append({"라운드": i, "주 지표": cell(PRIMARY), "RAG 오염": cell({"rag_poisoning"}), "개인정보 유출": cell({"pii_leak"})})
    held = d["held_out"]["results"]
    other = {x["category"] for x in held} - PRIMARY
    return {"보강용(v1.0 기준)": rows,
            "헬드아웃 부 지표·보조": f"{sum(intact(held, 'info_integrity', other).values())}/{len(intact(held, 'info_integrity', other))}"}


def main():
    rows = load_review()
    d = json.load(open(RESULT, encoding="utf-8"))
    before = {"가설": hypotheses(d), "라운드": round_table(d)}
    apply(d, rows)
    after = {"가설": hypotheses(d), "라운드": round_table(d)}
    out = {
        "review_file": os.path.relpath(REVIEW, ROOT),
        "label_counts": dict(Counter(r[COL].replace(" ", "") for r in rows)),
        "agreement_vs_judge": agreement(rows, "심판관 정보무결성"),
        "agreement_vs_final": agreement(rows, "최종 정보무결성"),
        "original": before,
        "with_author_labels": after,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
