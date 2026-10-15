# -*- coding: utf-8 -*-
"""Turn the review markdown (summary_to_md.py output) into a reading page for the claude.ai viewer.

Each paragraph gets a label like "3.5 ¶2" so review questions can point at it. Figures are copied
next to the page under fig/ and published with it.

    python3 scripts/summary_md_to_html.py docs/summary_review_v9.md <out_dir>
"""
import html
import os
import re
import shutil
import sys

ROOT = "/home/user/hongik"

CSS = """
<title>논문 요약본 검토</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600&display=swap">
<style>
/* layout: left contents rail + one reading column (~40em), paragraph labels in the margin */
:root {
  --paper: #fbfbf8; --ink: #1d2124; --muted: #5d6670; --rule: #dcdfe0;
  --accent: #9b2c2c; --mark: #eef1ee; --tablehead: #f1f2ef;
  --body: "Noto Serif KR", "Nanum Myeongjo", "Batang", serif;
  --ui: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #16191b; --ink: #e4e6e3; --muted: #9aa3aa; --rule: #31373b;
  --accent: #e08a80; --mark: #1f2427; --tablehead: #22282b; color-scheme: dark } }
:root[data-theme="dark"] {
  --paper: #16191b; --ink: #e4e6e3; --muted: #9aa3aa; --rule: #31373b;
  --accent: #e08a80; --mark: #1f2427; --tablehead: #22282b; color-scheme: dark }
body { background: var(--paper); color: var(--ink); font-family: var(--body); font-size: 16px; line-height: 1.85; }
.wrap { display: grid; grid-template-columns: 15rem minmax(0, 1fr); gap: 3rem; max-width: 72rem; margin: 0 auto;
  padding-block: 2rem 4rem; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
nav { position: sticky; top: calc(env(safe-area-inset-top, 0px) + 1rem); align-self: start; max-height: calc(100vh - 2rem); overflow-y: auto;
  font-family: var(--ui); font-size: 0.82rem; line-height: 1.5; }
nav .eyebrow { font-size: 0.72rem; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 0.6rem; }
nav a { display: block; color: var(--muted); text-decoration: none; padding: 0.18rem 0; }
nav a.ch { color: var(--ink); font-weight: 600; margin-top: 0.7rem; }
nav a:hover, nav a:focus-visible { color: var(--accent); }
main { min-width: 0; max-width: 42rem; }
header.title h1 { font-size: 1.55rem; line-height: 1.45; text-wrap: balance; margin: 0 0 0.6rem; }
header.title p { font-family: var(--ui); color: var(--muted); font-size: 0.9rem; margin: 0; }
.status { font-family: var(--ui); font-size: 0.8rem; color: var(--muted); border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  padding: 0.6rem 0; margin: 1.4rem 0 2rem; }
h2.ch { font-size: 1.35rem; margin: 3.2rem 0 1rem; padding-top: 1rem; border-top: 2px solid var(--ink); text-wrap: balance; scroll-margin-top: 1rem; }
h3.sec { font-size: 1.08rem; margin: 2.2rem 0 0.8rem; text-wrap: balance; scroll-margin-top: 1rem; }
.p { position: relative; margin: 0 0 1.05rem; }
.p .tag { position: absolute; left: -4.6rem; width: 4rem; text-align: right; top: 0.32rem; font-family: var(--ui); font-size: 0.7rem;
  color: var(--muted); font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
.p:target { background: var(--mark); outline: 6px solid var(--mark); }
.def { padding-left: 1rem; border-left: 1px solid var(--rule); }
.cap { font-family: var(--ui); font-size: 0.86rem; font-weight: 600; color: var(--ink); margin: 1.6rem 0 0.5rem; }
figure { margin: 1.4rem 0 0.4rem; }
figure img { max-width: 100%; height: auto; display: block; background: #ffffff; border: 1px solid var(--rule); }
.tbl { overflow-x: auto; margin: 0 0 1.4rem; }
table { border-collapse: collapse; font-family: var(--ui); font-size: 0.82rem; line-height: 1.5; min-width: 100%; }
th, td { border-bottom: 1px solid var(--rule); padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }
th { background: var(--tablehead); font-weight: 600; }
td { font-variant-numeric: tabular-nums; }
.refs .p { font-size: 0.86rem; line-height: 1.6; }
@media (max-width: 860px) {
  .wrap { grid-template-columns: minmax(0, 1fr); gap: 1rem; }
  nav { position: static; max-height: none; border-bottom: 1px solid var(--rule); padding-bottom: 1rem; }
  .p .tag { position: static; display: block; text-align: left; width: auto; }
}
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
</style>
"""


def inline(s):
    s = html.escape(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def main(md_path, out_dir):
    lines = open(md_path, encoding="utf-8").read().split("\n")
    os.makedirs(os.path.join(out_dir, "fig"), exist_ok=True)
    nav, body = [], []
    sec_id, sec_label, count, chap = "front", "초록", 0, 0
    title_done = 0
    i = 0
    in_refs = False
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|(-+\|)+$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split(" | ")])
                i += 1
            h = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            b = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            body.append(f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            continue
        m = re.match(r"!\[\]\((.+)\)", ln)
        if m:
            src = os.path.normpath(os.path.join(os.path.dirname(md_path), m.group(1)))
            name = os.path.basename(src)
            shutil.copy(src, os.path.join(out_dir, "fig", name))
            body.append(f'<figure><img src="fig/{name}" alt="" loading="lazy"></figure>')
            i += 1
            continue
        if ln.startswith("# ") and title_done == 0:
            title = ln[2:]
            sub = lines[i + 2][4:] if lines[i + 2].startswith("### ") else ""
            body.append(f'<header class="title"><h1>{inline(title)}</h1><p>{inline(sub)}</p></header>')
            body.append('<div class="status">요약본 v8 내용 · 한글 우선 표기 적용 · 문단 번호(예: 3.5 ¶2)로 위치를 짚어 질문하시면 됩니다.</div>')
            title_done = 1
            i += 3 if sub else 1
            continue
        if ln.startswith("# "):
            t = ln[2:]
            chap += 1
            sec_id, sec_label, count = f"c{chap}", re.sub(r"^제(\d)장\..*", r"\1장", t) if t.startswith("제") else t, 0
            in_refs = t == "참고문헌"
            body.append(f'<h2 class="ch" id="{sec_id}">{inline(t)}</h2>')
            nav.append(f'<a class="ch" href="#{sec_id}">{inline(t)}</a>')
            i += 1
            continue
        if ln.startswith("## "):
            t = ln[3:]
            num = t.split(" ")[0].rstrip(".")
            sec_id, sec_label, count = "s" + num.replace(".", "-"), num, 0
            body.append(f'<h3 class="sec" id="{sec_id}">{inline(t)}</h3>')
            nav.append(f'<a href="#{sec_id}">{inline(t)}</a>')
            i += 1
            continue
        if ln.strip() in ("초록", "국문 초록"):
            if ln.strip() == "국문 초록":
                body.append('<h3 class="sec">국문 초록</h3>')
            i += 1
            continue
        if ln.startswith("**") and re.match(r"\*\*(표|그림) \d+\.", ln):
            body.append(f'<div class="cap">{inline(ln.strip("*"))}</div>')
            i += 1
            continue
        count += 1
        pid = f"{sec_id}-p{count}"
        cls = "p def" if re.match(r"^\d\) (정의|예시|논의|적용):", ln) else "p"
        body.append(f'<p class="{cls}" id="{pid}"><span class="tag">{sec_label} ¶{count}</span>{inline(ln)}</p>')
        i += 1
    # the front matter before chapter 1 is the abstract
    page = (CSS + '<div class="wrap"><nav aria-label="목차"><div class="eyebrow">목차</div>'
            + '<a class="ch" href="#front">초록</a>' + "".join(nav) + '</nav><main>'
            + "\n".join(body).replace('<div class="status">', '<div id="front" class="status">', 1)
            .replace('<h2 class="ch" id="c', '<h2 class="ch" id="c').replace('id="c' + str(chap) + '">참고문헌', 'id="c' + str(chap) + '">참고문헌')
            + "</main></div>")
    page = page.replace('<h2 class="ch" id="c%d">참고문헌</h2>' % chap, '<h2 class="ch" id="c%d">참고문헌</h2><div class="refs">' % chap)
    if '<div class="refs">' in page:
        page = page.replace("</main></div>", "</div></main></div>")
    out = os.path.join(out_dir, "summary_review.html")
    open(out, "w", encoding="utf-8").write(page)
    print("saved", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
