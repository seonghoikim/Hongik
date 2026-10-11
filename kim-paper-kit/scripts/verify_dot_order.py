#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_dot_order.py -- check the on-page order of nodes in a Graphviz layout.

Graphviz does not keep declaration order for nodes in rank=same blocks or for
flat-edge chains: crossing minimization reorders them (a chain AF-1..AF-4 came
out as AF-2, AF-3, AF-4, AF-1). Edge weight and ordering=out did not fix it in
the reference project, so verify the coordinates instead of looking at the PNG.

The script runs `dot -Tplain` and reads node coordinates.
Graphviz y grows upward, so top-to-bottom order = descending y.
Use --order y (default, top to bottom) or --order x (left to right).
Choose the axis by the layout: with rankdir=LR, a rank=same block stacks vertically
(use --order y); a flat chain inside one rank is laid out horizontally (use --order x).
If the coordinates tie on the chosen axis, the script stops with exit 2 instead of guessing.

Usage:
  python verify_dot_order.py figure.dot --nodes "AF-1,AF-2,AF-3,AF-4"
  python verify_dot_order.py figure.dot --nodes "A,B,C" --order x --layout dot
  python verify_dot_order.py --plain-file layout.plain --nodes "A,B,C"   # offline check

Locating dot: --dot-bin, else env GRAPHVIZ_DOT, else PATH, else common install paths.

Exit codes: 0 order matches, 1 order differs, 2 node missing or dot not found/failed.
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DOT_CANDIDATES = [
    "C:/Program Files/Graphviz/bin/dot.exe",
    "/usr/bin/dot",
    "/usr/local/bin/dot",
]


def find_dot(explicit):
    if explicit:
        return explicit
    env = os.environ.get("GRAPHVIZ_DOT")
    if env:
        return env
    found = shutil.which("dot")
    if found:
        return found
    for cand in DEFAULT_DOT_CANDIDATES:
        if os.path.isfile(cand):
            return cand
    return None


def run_plain(dot_bin, dot_file, layout):
    cmd = [dot_bin, "-Tplain", f"-K{layout}", dot_file]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or f"dot exited with {res.returncode}")
    return res.stdout


def parse_plain(text):
    """Return {node_name: (x, y)} from `dot -Tplain` output.

    Node lines: node name x y width height label style shape color fillcolor
    """
    coords = {}
    for line in text.splitlines():
        if not line.startswith("node "):
            continue
        try:
            tok = shlex.split(line, posix=True)  # handles quoted names and labels
        except ValueError:
            tok = line.split()
        coords[tok[1]] = (float(tok[2]), float(tok[3]))
    return coords


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify the visual order of Graphviz nodes.")
    ap.add_argument("dot", nargs="?", help=".dot file (omit when --plain-file is given)")
    ap.add_argument("--plain-file", help="existing `dot -Tplain` output to check offline")
    ap.add_argument("--nodes", required=True, help="comma-separated node IDs in the EXPECTED order")
    ap.add_argument("--order", choices=["y", "x"], default="y",
                    help="y = top to bottom (default), x = left to right")
    ap.add_argument("--layout", default="dot", help="Graphviz layout engine (default: dot)")
    ap.add_argument("--dot-bin", help="path to the dot executable")
    args = ap.parse_args(argv)

    expected = [n.strip() for n in args.nodes.split(",") if n.strip()]
    if len(expected) < 2:
        print("[error] give at least two node IDs in --nodes")
        return 2

    if args.plain_file:
        text = Path(args.plain_file).read_text(encoding="utf-8", errors="replace")
    else:
        if not args.dot:
            print("[error] give a .dot file or --plain-file")
            return 2
        dot_bin = find_dot(args.dot_bin)
        if not dot_bin:
            print("[error] dot executable not found: pass --dot-bin or set GRAPHVIZ_DOT")
            return 2
        try:
            text = run_plain(dot_bin, args.dot, args.layout)
        except (RuntimeError, OSError) as exc:
            print(f"[error] dot failed: {exc}")
            return 2

    coords = parse_plain(text)
    missing = [n for n in expected if n not in coords]
    if missing:
        print(f"[error] nodes not found in layout: {missing}")
        return 2

    key_of = (lambda n: -coords[n][1]) if args.order == "y" else (lambda n: coords[n][0])
    print(f"{'node':<16}{'x':>10}{'y':>10}")
    for n in expected:
        x, y = coords[n]
        print(f"{n:<16}{x:>10.1f}{y:>10.1f}")

    # equal coordinates make the sort stable, which would pass by accident
    keys = [round(key_of(n), 2) for n in expected]
    if len(set(keys)) < len(keys):
        print(f"[error] tied coordinates along --order {args.order}; the order is undetermined. "
              f"Use the other axis or add separation.")
        return 2

    actual = sorted(expected, key=key_of)  # for y: larger y = higher on the page
    direction = "top to bottom" if args.order == "y" else "left to right"
    print(f"expected ({direction}):", " > ".join(expected))
    print(f"actual   ({direction}):", " > ".join(actual))
    if actual == expected:
        print(f"[pass] visual order matches ({direction})")
        return 0
    print("[fail] visual order differs from the expected order")
    print("       fix: change the chain or rank constraints, re-run dot, and record the chosen form in a dot comment")
    return 1


if __name__ == "__main__":
    sys.exit(main())
