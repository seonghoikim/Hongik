# -*- coding: utf-8 -*-
"""Make thesis_summary_visual_v2.docx from v1 (v1 is read only).

- Replace every figure image with the code-generated v2 figure (diagrams/summary_v2/).
- Figures 6 and 12 had two images under one caption; each becomes one image.
- Images are set to the full body width (kim-paper-kit: figures at 100 % width).
- Figure and table captions end with a period (kim-paper-kit korean-style §7).
"""
import sys
import re
import os
import docx
from docx.oxml.ns import qn
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = "/home/user/hongik"
SRC = os.path.join(ROOT, "thesis_summary_visual.docx")
DST = os.path.join(ROOT, "thesis_summary_visual_v2.docx")
FIG = os.path.join(ROOT, "diagrams/summary_v2")
assert not os.path.exists(DST), "v2 already exists; do not overwrite"

FIG_FOR = {1: "fig_struct1", 2: "fig_struct2", 3: "fig_struct3", 4: "fig_overview",
           5: "fig_integrated", 6: "fig_taxonomy", 7: "fig_levels", 8: "plot_rounds",
           9: "plot_defense", 10: "plot_cross", 11: "plot_5w1h", 12: "fig_adaptive",
           13: "fig_overview", 14: "fig_prep", 15: "fig_struct1", 16: "fig_struct2", 17: "fig_struct3"}
BODY_W_IN = 6.07
EMU = 914400

d = docx.Document(SRC)
body = d.element.body


def ptext(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


# 1) group drawings by the caption that follows them
pending, groups = [], {}
for p in body.iter(qn("w:p")):
    pending += list(p.iter(qn("w:drawing")))
    m = re.search(r"그림 (\d+)\.", ptext(p))
    if m and pending:
        groups[int(m.group(1))] = pending
        pending = []
assert sorted(groups) == list(range(1, 18)), sorted(groups)
assert not pending

# 2) swap images
for n, drs in groups.items():
    path = os.path.join(FIG, FIG_FOR[n] + ".png")
    rid, _ = d.part.get_or_add_image(path)
    w, h = Image.open(path).size
    cx, cy = int(BODY_W_IN * EMU), int(BODY_W_IN * EMU * h / w)
    keep = drs[0]
    keep.find(".//" + qn("a:blip")).set(qn("r:embed"), rid)
    for e in (keep.find(".//" + qn("wp:extent")), keep.find(".//" + qn("a:ext"))):
        e.set("cx", str(cx)); e.set("cy", str(cy))
    for extra in drs[1:]:                     # merge two-image figures into one
        run = extra.getparent()
        run.getparent().remove(run)
    print(f"그림 {n}: {FIG_FOR[n]} ({len(drs)} image(s) -> 1)")

# 3) captions end with a period
cap = re.compile(r"^\s*(그림|표) \d+\. ")
fixed = 0
for p in body.iter(qn("w:p")):
    if not cap.match(ptext(p)):
        continue
    ts = [t for t in p.iter(qn("w:t")) if t.text]
    last = ts[-1]
    if not last.text.rstrip().endswith("."):
        last.text = last.text.rstrip() + "."
        fixed += 1
print("captions given a period:", fixed)

# 4) text that described the old two-image figure 6
for t in body.iter(qn("w:t")):
    if t.text and "그림 6의 위쪽 그림과 같이" in t.text:
        t.text = t.text.replace("그림 6의 위쪽 그림과 같이", "그림 6의 왼쪽 열과 같이")
        print("text: figure 6 reference updated")

d.save(DST)
print("saved", DST)
