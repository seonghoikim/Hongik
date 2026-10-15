"""Shared paths, fonts, palette and data loaders for the presentation figures.

All numbers are read from the raw experiment JSON files (never typed in by hand).
Run any make_*.py script from anywhere:  python3 scripts/make_charts.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path("/home/user/hongik")
PRES = ROOT / "papers/gangneung_2026/presentation"
FIGS = PRES / "figs"
DATA_OUT = PRES / "data"
FIGS.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

RUN7 = ROOT / "data/results/experiment_real_20260804_060902.json"
RUN9 = ROOT / "data/results/experiment_real_20260804_102353.json"
RELEVEL9 = ROOT / "data/results/relevel4tier_real_20260804_102353.json"
SRS7_DIR = ROOT / "data/srs/real_20260804_060902"
SRS9_DIR = ROOT / "data/srs/real_20260804_102353"

# ---------------------------------------------------------------- palette
BLACK = "#1a1a1a"
DGRAY = "#555555"
MGRAY = "#8c8c8c"
LGRAY = "#c8c8c8"
XLGRAY = "#ececec"
RED = "#c8102e"
WHITE = "#ffffff"

# ---------------------------------------------------------------- fonts
FONT_REG = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"
for f in (FONT_REG, FONT_BOLD):
    font_manager.fontManager.addfont(f)
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
FONT_NAME = font_manager.FontProperties(fname=FONT_REG).get_name()

plt.rcParams.update({
    "font.family": FONT_NAME,
    "font.size": 20,
    "axes.titlesize": 24,
    "axes.labelsize": 20,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 17,
    "axes.unicode_minus": False,
    "axes.edgecolor": MGRAY,
    "axes.linewidth": 1.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": DGRAY,
    "ytick.color": DGRAY,
    "axes.labelcolor": BLACK,
    "text.color": BLACK,
    "figure.facecolor": WHITE,
    "axes.facecolor": WHITE,
    "savefig.facecolor": WHITE,
    "savefig.dpi": 160,
})

FIGSIZE_WIDE = (13.33, 7.5)   # full 16:9 slide
FIGSIZE_PANEL = (8.0, 6.5)    # left 55~65% of a 16:9 slide; place at native size -> pt == slide pt

# ---------------------------------------------------------------- categories
# 8 categories actually used by the 7th/9th runs (read from JSON; rag_poisoning was added
# to the code on 2026-10-12 and is NOT part of these runs). OWASP IDs follow
# src/hongik_selfheal/attack_taxonomy.py owasp_mapping.
CATEGORIES = [
    ("impersonation", "권한자 사칭", "LLM01", "프롬프트 인젝션"),
    ("encoding_bypass", "인코딩 우회", "LLM01", "프롬프트 인젝션(변형)"),
    ("tone_gaslighting", "페르소나 재정의", "LLM01", "프롬프트 인젝션(지시 재정의)"),
    ("misinformation", "허위사실 동조", "LLM09", "허위 정보"),
    ("metadata_leak", "시스템 프롬프트 유출", "LLM07·LLM02", "시스템 프롬프트 유출"),
    ("pii_leak", "개인정보 유출", "LLM02", "민감정보 노출"),
    ("cross_product_leak", "RAG 다중 문서 유출", "LLM08", "벡터·임베딩 약점"),
    ("price_probing", "영업 정책 우회(가격)", "LLM02", "민감정보 노출(정책 경계 우회)"),
]
CAT_KO = {k: ko for k, ko, _, _ in CATEGORIES}
CAT_OWASP = {k: o for k, _, o, _ in CATEGORIES}

GRADE_SCORE_3 = {"PASS": 3, "WARNING": 2, "FAIL": 1}

# Real brand / product names that appear in the persona and chatbot responses.
_MASKS = [
    (re.compile(r"롯데\s*하이마트\s*PLUX|하이마트\s*PLUX"), "○○사"),
    (re.compile(r"롯데\s*하이마트|하이마트"), "○○사"),
    (re.compile(r"PLX-?[A-Z0-9]{4,}"), "○○ 제품"),
    (re.compile(r"PLUX"), "○○"),
    (re.compile(r"김○○"), "○○○"),
    (re.compile(r"\b0\d{1,2}-\d{3,4}-\d{4}\b|\b1\d{3}-\d{4}\b"), "○○○-○○○○"),
]
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️​]")


def mask(text: str) -> str:
    for pat, rep in _MASKS:
        text = pat.sub(rep, text)
    text = re.sub(r"○○사\s*○○", "○○사", text)
    return text


def strip_emoji(text: str) -> str:
    """Nanum fonts have no emoji glyphs; replace with a visible marker."""
    return _EMOJI.sub("[이모지]", text).replace("[이모지][이모지]", "[이모지]")


def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def srs_rule_counts(srs_dir: Path) -> dict[str, int]:
    out = {}
    for p in srs_dir.glob("v*.json"):
        d = load(p)
        out[d["version"]] = len(d["meta_rules"])
    return out


def save(fig, name: str):
    out = FIGS / name
    fig.savefig(out, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", out)
