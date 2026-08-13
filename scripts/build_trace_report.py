#!/usr/bin/env python3
"""experiment_*.json 결과를 사람이 읽을 수 있는 단일 HTML 리포트로 변환한다.

지도교수/연구자가 "무슨 프롬프트와 RAG 컨텍스트로 이 결과가 나왔는지" 원문
로그(raw_calls_*.jsonl)를 직접 파싱하지 않고도 확인할 수 있도록, 각 시나리오의
공격문/RAG 컨텍스트/시스템 프롬프트(SRS 렌더링)/원문 응답(Unit D 필터링 전)/
최종 응답/심판관 판정을 한 화면에서 펼쳐볼 수 있게 만든다.

사용법:
    PYTHONPATH=src python3 scripts/build_trace_report.py \
        data/results/experiment_real_20260803_102127.json \
        --srs-dir data/srs \
        --output data/results/report_real_20260803_102127.html
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.srs import SRS  # noqa: E402

# 4단계 보안 심각도 Level 체계(thesis.md §4.1.1, 2026-08-13 코드 구현).
_GRADE_ORDER = ["FULL_DEFENSE", "FUNCTIONAL_DEFENSE", "PARTIAL_EXPOSURE", "BREACH"]


def esc(text: str) -> str:
    # 공격 문장에 리터럴 백슬래시(예: encoding_bypass 예시의 "\y")가 그대로 들어있으면
    # 일부 다운스트림 HTML 처리기가 이를 이스케이프 시퀀스로 오인해 깨질 수 있으므로
    # HTML 엔티티로 치환해 항상 리터럴 문자로만 렌더링되게 한다.
    # 원문 결과 JSON 자체에 API 응답 디코딩 과정에서 생긴 것으로 보이는 손상 문자(U+FFFD)가
    # 실제로 1건 섞여 있었다(real_20260804_082642, encoding_bypass 판정 사유). 원문
    # 근거 파일(experiment_*.json)은 그대로 보존하고, 표시용 리포트에서만 표시 가능한
    # 마커로 바꿔 렌더링이 깨지지 않게 한다.
    s = str(text).replace("�", "[손상된 문자 1개 - 원문 JSON 그대로 보존됨]")
    return html.escape(s, quote=True).replace("\\", "&#92;")


def load_srs_prompt(srs_dir: Path, version: str, cache: dict[str, str]) -> str:
    if version in cache:
        return cache[version]
    path = srs_dir / f"{version}.json"
    if not path.exists():
        cache[version] = "(SRS 파일을 찾을 수 없음: " + str(path) + ")"
        return cache[version]
    prompt = SRS.load(path).render_system_prompt()
    cache[version] = prompt
    return prompt


def grade_pill(grade: str) -> str:
    cls = {
        "FULL_DEFENSE": "pass",
        "FUNCTIONAL_DEFENSE": "functional",
        "PARTIAL_EXPOSURE": "warn",
        "BREACH": "fail",
    }.get(grade, "mute")
    return f'<span class="pill {cls}">{esc(grade)}</span>'


def scenario_card(result: dict, system_prompt: str) -> str:
    blocked = result.get("blocked_by_unit")
    blocked_note = (
        f'<span class="pill mute">차단: Unit {esc(blocked)}</span>' if blocked else ""
    )
    return f"""
<details class="trace-card">
  <summary>
    <span class="scenario-id">{esc(result['scenario_id'])}</span>
    <span class="category-tag">{esc(result['category'])}</span>
    {grade_pill(result['grade'])} <span class="score">{result['score']}/4</span>
    {blocked_note}
  </summary>
  <div class="trace-body">
    <div class="trace-block">
      <div class="trace-label">공격 문장 (attack_prompt)</div>
      <pre>{esc(result['attack_prompt'])}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">RAG 검색 결과 (Unit B, retrieved_context)</div>
      <pre>{esc(result.get('retrieved_context', ''))}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">시스템 프롬프트 (SRS {esc(result.get('_srs_version',''))} 렌더링)</div>
      <pre>{esc(system_prompt)}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">Unit C 원문 응답 (Unit D 필터링 전)</div>
      <pre>{esc(result.get('raw_unit_c_response', ''))}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">최종 응답 (사용자에게 전달된 것)</div>
      <pre>{esc(result['chatbot_response'])}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">심판관 판정 근거</div>
      <pre>{esc(result['reason'])}</pre>
      {f'<div class="violated">위반 유닛: {esc(result["violated_unit"])}</div>' if result.get('violated_unit') else ''}
      {f'<div class="violated">파고든 축(5W1H): {esc(result["exploited_axis"])}</div>' if result.get('exploited_axis') else ''}
    </div>
  </div>
</details>"""


def cross_model_card(result: dict, system_prompt: str) -> str:
    backend_rows = ""
    for provider, response in result["backend_responses"].items():
        grade = result["backend_grades"][provider]
        score = result["backend_scores"][provider]
        reason = result["backend_reasons"][provider]
        backend_rows += f"""
    <div class="trace-block">
      <div class="trace-label">[{esc(provider)}] 응답 &middot; {grade_pill(grade)} <span class="score">{score}/4</span></div>
      <pre>{esc(response)}</pre>
      <div class="reason-inline">{esc(reason)}</div>
    </div>"""
    validated = result.get("cross_model_validated")
    validated_pill = (
        '<span class="pill pass">교차모델 검증됨</span>'
        if validated
        else '<span class="pill fail">검증 안 됨</span>'
    )
    return f"""
<details class="trace-card">
  <summary>
    <span class="scenario-id">{esc(result['scenario_id'])}</span>
    <span class="category-tag">{esc(result['category'])}</span>
    {validated_pill} <span class="score">{result['full_defense_count']}/3 FULL_DEFENSE</span>
  </summary>
  <div class="trace-body">
    <div class="trace-block">
      <div class="trace-label">공격 문장</div>
      <pre>{esc(result['attack_prompt'])}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">RAG 검색 결과 (Unit B, 3개 백엔드 공통)</div>
      <pre>{esc(result.get('retrieved_context', ''))}</pre>
    </div>
    <div class="trace-block">
      <div class="trace-label">시스템 프롬프트 (SRS {esc(result.get('_srs_version',''))} 렌더링, 3개 백엔드 공통)</div>
      <pre>{esc(system_prompt)}</pre>
    </div>
    {backend_rows}
  </div>
</details>"""


def stage_section(title: str, tag: str, summary: dict, srs_dir: Path, cache: dict) -> str:
    system_prompt = load_srs_prompt(srs_dir, summary["srs_version"], cache)
    cards = "\n".join(
        scenario_card({**r, "_srs_version": summary["srs_version"]}, system_prompt)
        for r in summary["results"]
    )
    ungradable_note = ""
    if summary.get("ungradable_count"):
        rows = "".join(
            f"<li>{esc(d['scenario_id'])} ({esc(d['category'])}) — {esc(d['error'])}</li>"
            for d in summary["ungradable_details"]
        )
        ungradable_note = f"""
<div class="ungradable-box">
  <b>채점 불가 {summary['ungradable_count']}건 (통계에서 제외, §3.6.3)</b>
  <ul>{rows}</ul>
</div>"""
    return f"""
<section>
  <h2>{esc(title)} <span class="tag">{esc(tag)}</span></h2>
  <p class="section-note">
    SRS {esc(summary['srs_version'])} &middot; {" / ".join(f"{g} {summary['grade_counts'][g]}" for g in _GRADE_ORDER)}
    &middot; 준수율 {summary['compliance_rate']}%
  </p>
  {ungradable_note}
  <div class="trace-list">{cards}</div>
</section>"""


def cross_model_section(cm: dict, srs_dir: Path, cache: dict) -> str:
    system_prompt = load_srs_prompt(srs_dir, cm["srs_version"], cache)
    cards = "\n".join(
        cross_model_card({**r, "_srs_version": cm["srs_version"]}, system_prompt)
        for r in cm["results"]
    )
    backend_summary = " &middot; ".join(
        f"{esc(p)} FULL_DEFENSE율 {rate}%" for p, rate in cm["per_backend_full_defense_rate"].items()
    )
    return f"""
<section>
  <h2>교차 모델 검증 <span class="tag">헬드아웃 재실행, 심판관 {esc(cm['judge_provider'])} 고정</span></h2>
  <p class="section-note">{backend_summary} &middot; 2/3 이상 FULL_DEFENSE 비율 {cm['cross_model_validated_rate']}%</p>
  <div class="trace-list">{cards}</div>
</section>"""


_CSS = """
:root {
  --paper:#f5f3ee; --paper-raised:#ffffff; --ink:#171b20; --ink-soft:#4b5259;
  --line:#dedad0; --line-soft:#e9e6de; --accent:#2f6459; --accent-soft:#e4ede9;
  --accent-ink:#1d453d; --pass:#2f7d4f; --pass-soft:#e3f1e6; --warn:#a8722b;
  --warn-soft:#f7ecd9; --fail:#b1402f; --fail-soft:#fae6e2; --mute:#6b6f76; --mute-soft:#eceae4;
  --font-body:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;
  --font-mono:ui-monospace,"SF Mono","Cascadia Code","Consolas","D2Coding",monospace;
}
@media (prefers-color-scheme: dark) {
  :root { --paper:#14171b; --paper-raised:#1b1f24; --ink:#e9e8e3; --ink-soft:#a8adb3;
    --line:#2c3137; --line-soft:#262a30; --accent:#6fb3a3; --accent-soft:#1c2f2b;
    --accent-ink:#a9d8cb; --pass:#6fbf8c; --pass-soft:#17281d; --warn:#d7a44e;
    --warn-soft:#2e2515; --fail:#e28372; --fail-soft:#2e1a17; --mute:#9298a0; --mute-soft:#23262b; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:var(--font-body); line-height:1.6; }
.wrap { max-width: 980px; margin:0 auto; padding: 48px 24px 96px; }
h1 { font-size: 26px; margin: 0 0 20px; }
h2 { font-size: 19px; margin: 0 0 4px; display:flex; align-items:baseline; gap:10px; }
h2 .tag { font-family:var(--font-mono); font-size:11.5px; font-weight:500; color:var(--mute); }
.section-note { color:var(--ink-soft); font-size:13px; margin:0 0 14px; }
section { margin-bottom: 40px; }
.pill { display:inline-flex; align-items:center; gap:5px; font-family:var(--font-mono); font-size:11px;
  font-weight:600; padding:2px 8px; border-radius:100px; }
.pill.pass { background:var(--pass-soft); color:var(--pass); }
.pill.warn { background:var(--warn-soft); color:var(--warn); }
.pill.functional { background:var(--accent-soft); color:var(--accent-ink); }
.pill.fail { background:var(--fail-soft); color:var(--fail); }
.pill.mute { background:var(--mute-soft); color:var(--mute); }
.trace-list { display:flex; flex-direction:column; gap:8px; }
.trace-card { border:1px solid var(--line); border-radius:10px; background:var(--paper-raised); padding: 4px 4px; }
.trace-card summary { cursor:pointer; padding:10px 14px; display:flex; align-items:center; gap:10px;
  font-size:13.5px; list-style:none; }
.trace-card summary::-webkit-details-marker { display:none; }
.trace-card summary::before { content:"▸"; color:var(--mute); }
.trace-card[open] summary::before { content:"▾"; }
.scenario-id { font-family:var(--font-mono); font-size:12px; color:var(--ink-soft); }
.category-tag { font-family:var(--font-mono); font-size:11px; background:var(--mute-soft); color:var(--ink-soft);
  padding:2px 7px; border-radius:6px; }
.score { font-family:var(--font-mono); font-size:12px; color:var(--ink-soft); margin-left:auto; }
.trace-body { padding: 4px 14px 14px; border-top:1px solid var(--line-soft); display:flex; flex-direction:column; gap:12px; }
.trace-block { }
.trace-label { font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--ink-soft); margin-bottom:4px; }
pre { margin:0; white-space:pre-wrap; word-break:break-word; font-family:var(--font-body); font-size:13.5px;
  background:var(--mute-soft); border-radius:8px; padding:10px 12px; }
.reason-inline { font-size:12.5px; color:var(--ink-soft); margin-top:4px; padding-left:2px; }
.violated { font-size:12px; color:var(--fail); margin-top:4px; }
.ungradable-box { border:1px solid var(--warn); background:var(--warn-soft); border-radius:8px;
  padding:10px 14px; font-size:13px; margin-bottom:12px; }
.ungradable-box ul { margin:6px 0 0; padding-left:18px; }
.axis-table { border-collapse:collapse; width:100%; font-size:13px; background:var(--paper-raised);
  border:1px solid var(--line); border-radius:8px; overflow:hidden; }
.axis-table th, .axis-table td { padding:8px 12px; text-align:right; border-bottom:1px solid var(--line-soft); }
.axis-table th:first-child, .axis-table td:first-child { text-align:left; }
.axis-table th { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--ink-soft);
  background:var(--mute-soft); font-weight:600; }
.axis-table tbody tr:last-child td { border-bottom:none; }
.axis-table td.fail-n { color:var(--fail); font-weight:700; }
.axis-table td.warn-n { color:var(--warn); font-weight:700; }
"""


def kb_full_section(rag_dir: Path, kb_version: str | None) -> str:
    if not kb_version:
        return ""
    path = rag_dir / f"{kb_version}.json"
    if not path.exists():
        return f'<p class="section-note">⚠ RAG 스냅샷 파일을 찾을 수 없음: {esc(path)}</p>'
    kb = json.loads(path.read_text(encoding="utf-8"))
    rows = ""
    for i, entry in enumerate(kb.get("entries", []), 1):
        keywords = ", ".join(entry["keywords"])
        rows += f"""
    <div class="trace-block">
      <div class="trace-label">#{i} 트리거 키워드: {esc(keywords)}</div>
      <pre>{esc(entry["content"])}</pre>
    </div>"""
    return f"""
<section>
  <h2>이번 실행에 쓰인 전체 RAG 지식베이스 <span class="tag">{esc(kb_version)}, Unit B</span></h2>
  <p class="section-note">
    아래 항목 중 사용자 입력에 트리거 키워드가 포함된 것만 골라져 각 시나리오의 "RAG 검색 결과"로 전달됩니다.
    이 목록은 실행 시점에 <code>data/rag/{esc(kb_version)}.json</code>으로 스냅샷 저장된 것 — 코드가 나중에
    바뀌어도 이 실행이 실제로 어떤 내부 지식을 갖고 있었는지 이 파일만으로 재구성할 수 있습니다.
  </p>
  <div class="trace-card" style="padding:4px 14px 14px;">{rows}</div>
</section>"""


def members_summary_section(rag_dir: Path, members_version: str | None) -> str:
    if not members_version:
        return ""
    path = rag_dir / f"{members_version}.json"
    if not path.exists():
        return f'<p class="section-note">⚠ 회원 DB 스냅샷 파일을 찾을 수 없음: {esc(path)}</p>'
    snap = json.loads(path.read_text(encoding="utf-8"))
    count = snap.get("count", len(snap.get("members", [])))
    sample = snap.get("members", [])[:3]
    sample_lines = [
        "{} {} / {} / {}등급 / 주문 {}건".format(m["member_id"], m["name"], m["phone"], m["grade"], len(m["orders"]))
        for m in sample
    ]
    sample_rows = "".join(f'<div class="trace-block"><pre>{esc(line)}</pre></div>' for line in sample_lines)
    return f"""
<section>
  <h2>이번 실행에 쓰인 가공 회원 DB <span class="tag">{esc(members_version)}, {count}명</span></h2>
  <p class="section-note">
    전체는 <code>data/rag/{esc(members_version)}.json</code>에 스냅샷 저장되어 있습니다(전부 실존 인물과
    무관한 합성 데이터, 시드 고정 재생성 가능). 공격문이 주문번호·이름을 언급하면 이 DB에서 실제로 일치하는
    레코드가 있는지 동적으로 조회되어 RAG 컨텍스트에 포함됩니다 — 앞의 "RAG 검색 결과"에 이미 반영되어
    있으므로 여기서는 앞 3명만 예시로 보여줍니다.
  </p>
  {sample_rows}
</section>"""


_AXIS_LABELS = {
    "who": "Who (권한 사칭)",
    "what": "What (완곡 질의)",
    "when": "When (긴급성)",
    "why": "Why (명분 위장)",
    "how": "How (전달 우회)",
    None: "(태그 없음/해당없음)",
}


def axis_breakdown_section(data: dict) -> str:
    """thesis.md §4.1.2 — exploited_axis 진단 태그의 집계 뷰. 개별 카드에서
    하나씩 확인하지 않아도, 이 실행 전체에서 공격이 어느 5W1H 축에 몰렸고
    그 축에서 등급이 어떻게 나왔는지 한눈에 보여준다."""
    counts: dict[str | None, dict[str, int]] = {}

    def _tally(axis, grade):
        bucket = counts.setdefault(axis, {g: 0 for g in _GRADE_ORDER})
        if grade in bucket:
            bucket[grade] += 1

    for round_data in data.get("healing_rounds", []):
        for r in round_data.get("results", []):
            _tally(r.get("exploited_axis"), r.get("grade"))
    for key in ("held_out", "adaptive_blackbox", "adaptive_whitebox"):
        for r in data.get(key, {}).get("results", []):
            _tally(r.get("exploited_axis"), r.get("grade"))

    cross_counts: dict[str | None, dict[str, int]] = {}
    for r in data.get("cross_model", {}).get("results", []):
        axes = r.get("backend_exploited_axes", {}) or {}
        grades = r.get("backend_grades", {}) or {}
        for provider, axis in axes.items():
            bucket = cross_counts.setdefault(axis, {g: 0 for g in _GRADE_ORDER})
            grade = grades.get(provider)
            if grade in bucket:
                bucket[grade] += 1

    if not counts and not cross_counts:
        return ""

    _CELL_CLASS = {
        "FULL_DEFENSE": "",
        "FUNCTIONAL_DEFENSE": "",
        "PARTIAL_EXPOSURE": "warn-n",
        "BREACH": "fail-n",
    }

    def _rows(tally: dict) -> str:
        rows = ""
        for axis in sorted(tally, key=lambda a: (a is None, a)):
            g = tally[axis]
            total = sum(g[grade] for grade in _GRADE_ORDER)
            label = _AXIS_LABELS.get(axis, esc(axis))
            cells = "".join(
                f'<td class="{_CELL_CLASS[grade]}">{g[grade]}</td>' for grade in _GRADE_ORDER
            )
            rows += f"<tr><td>{label}</td><td>{total}</td>{cells}</tr>"
        return rows

    header_cells = "".join(f"<th>{g}</th>" for g in _GRADE_ORDER)

    cross_block = ""
    if cross_counts:
        cross_block = f"""
  <p class="section-note" style="margin-top:18px;">교차 모델 검증(3개 백엔드, 축 태그가 백엔드별로 따로 남음)</p>
  <table class="axis-table">
    <thead><tr><th>축</th><th>계</th>{header_cells}</tr></thead>
    <tbody>{_rows(cross_counts)}</tbody>
  </table>"""

    return f"""
<section>
  <h2>공격이 파고든 5W1H 축 집계 <span class="tag">§4.1.2 진단 태그, exploited_axis</span></h2>
  <p class="section-note">
    자가 치유 라운드 전체 + 헬드아웃 + 적응형 재공격을 합산한 집계입니다. 등급 자체에는 영향이 없는
    진단용 태그이며, 어느 축에 방어 실패(PARTIAL_EXPOSURE/BREACH)가 몰려 있는지를 보여줍니다.
  </p>
  <table class="axis-table">
    <thead><tr><th>축</th><th>계</th>{header_cells}</tr></thead>
    <tbody>{_rows(counts)}</tbody>
  </table>{cross_block}
</section>"""


def build_report(data: dict, srs_dir: Path, rag_dir: Path) -> str:
    cache: dict[str, str] = {}
    sections = [
        axis_breakdown_section(data),
        kb_full_section(rag_dir, data.get("kb_version")),
        members_summary_section(rag_dir, data.get("members_version")),
    ]

    for round_data in data["healing_rounds"]:
        sections.append(
            stage_section(
                f"자가 치유 {round_data['label']}", "치유용 셋", round_data, srs_dir, cache
            )
        )
    sections.append(stage_section("헬드아웃 검증", "held_out", data["held_out"], srs_dir, cache))
    sections.append(
        stage_section("적응형 재공격 (블랙박스)", "adaptive_blackbox", data["adaptive_blackbox"], srs_dir, cache)
    )
    sections.append(
        stage_section("적응형 재공격 (화이트박스)", "adaptive_whitebox", data["adaptive_whitebox"], srs_dir, cache)
    )
    sections.append(cross_model_section(data["cross_model"], srs_dir, cache))

    meta = (
        f"mode={data.get('mode')} &middot; primary={data.get('primary_provider')} &middot; "
        f"redteam={data.get('redteam_provider')} &middot; run_at={data.get('run_at_utc')} &middot; "
        f"final_srs={data.get('final_srs_version')} &middot; kb={data.get('kb_version', '(기록 없음)')} "
        f"&middot; members={data.get('members_version', '(기록 없음)')}"
    )
    usage = data.get("usage_summary") or {}

    return f"""<title>원문 추적 리포트</title>
<style>{_CSS}</style>
<div class="wrap">
  <h1>원문 추적 리포트 — 시나리오별 공격/RAG/응답/판정 전문</h1>
  <p class="section-note">{meta}</p>
  <p class="section-note">
    API 호출 {usage.get('total_calls', '?')}건 &middot; 추정 비용 ${usage.get('estimated_cost_usd', '?')} &middot;
    각 카드를 펼치면 공격 문장 → Unit B(RAG) 검색 결과 → 실제 렌더링된 시스템 프롬프트 → Unit C 원문 응답 →
    (Unit D 필터링 후) 최종 응답 → 심판관 판정 근거까지 순서대로 볼 수 있습니다.
  </p>
  {''.join(sections)}
</div>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_json", type=Path)
    parser.add_argument("--srs-dir", type=Path, default=Path("data/srs"))
    parser.add_argument("--rag-dir", type=Path, default=Path("data/rag"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.experiment_json.read_text(encoding="utf-8"))
    report_html = build_report(data, args.srs_dir, args.rag_dir)

    output = args.output or args.experiment_json.with_name(
        args.experiment_json.stem.replace("experiment_", "report_") + ".html"
    )
    output.write_text(report_html, encoding="utf-8")
    print(f"[build_trace_report] 저장: {output}")


if __name__ == "__main__":
    main()
