# -*- coding: utf-8 -*-
"""조건 1·4 결과의 코드 판정만 현재 oracle.py로 다시 한다 (모델 호출 없음).

저장된 응답·검색 결과·심판관 판정을 그대로 두고 정답 대조·전화번호 검사만 다시 돌려,
기존 결과 파일은 그대로 두고 <원래 이름>_rescored_<시각>.json으로 새로 저장한다.
심판관 기준 변경(judge.py)은 반영되지 않는다: 심판관을 다시 부르지 않기 때문이다.

    python3 scripts/rescore_c1_c4.py data/results/c1_c4_real_20261016_133535.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hongik_selfheal.attack_generator import load_pool  # noqa: E402
from hongik_selfheal.experiment import _policy_lines  # noqa: E402
from hongik_selfheal.oracle import check_response  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from hongik_selfheal.stats import mcnemar_exact  # noqa: E402
from probe_difficulty import FAILED  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("result_file", type=Path)
    args = ap.parse_args()

    src = args.result_file.resolve()
    report = json.loads(src.read_text(encoding="utf-8"))
    pool = {s.id: s for s in load_pool(ROOT / report["attack_pool_file"])}
    policy_lines = _policy_lines(initial_srs_v1())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    report["rescored"] = {"from": str(src.relative_to(ROOT)), "commit": commit,
                          "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "note": "code oracle re-run on saved responses; judge not re-run"}

    for cond, out in report["conditions"].items():
        intact: dict[str, list[int]] = {}
        for arm in ("attack", "control"):
            items = out[arm]["items"]
            for it in items:
                sc = pool[it["id"]]
                o = check_response(it["response"], it["attack"], policy_lines, sc.oracle,
                                   context=it["retrieved_context"] or "")
                it["prev_info_integrity"], it["prev_oracle_verdict"] = it["info_integrity"], it["oracle_verdict"]
                it["oracle_verdict"], it["oracle_evidence"] = o.verdict, o.evidence
                # same rule as experiment._apply_oracle: code BROKEN overrides, otherwise the judge's call stands
                it["info_integrity"] = "BROKEN" if o.verdict == "BROKEN" else it["judge_info_integrity"]
                if o.verdict == "BROKEN":
                    it["info_type"] = it["info_type"] or o.info_type
            intact[arm] = [int(i["info_integrity"] not in FAILED) for i in items]
            out[arm]["info_failed"] = sum(1 - x for x in intact[arm])
            out[arm]["oracle_broken"] = sum(i["oracle_verdict"] == "BROKEN" for i in items)
            out[arm]["review_notes"] = sum(any(e.startswith("review:") for e in i["oracle_evidence"]) for i in items)
            print(f"{cond} {arm:7s} 정보 무결성 실패 {out[arm]['info_failed']}/{len(items)}  "
                  f"코드 판정 훼손 {out[arm]['oracle_broken']}  사람 확인 표시 {out[arm]['review_notes']}")
        t = mcnemar_exact(intact["control"], intact["attack"])
        out["mcnemar_control_vs_attack"] = {"statistic": t.statistic, "p_value": t.p_value}
        print(f"{cond} 맥니마 정확검정(대조군 대 공격) p={t.p_value:.4g}")

    dest = src.with_name(f"{src.stem}_rescored_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", dest)


if __name__ == "__main__":
    main()
