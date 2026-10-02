import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import glob, os

fp = [f for f in glob.glob("/usr/share/fonts/**/NanumGothic.ttf", recursive=True)][0]
fm.fontManager.addfont(fp)
for b in glob.glob("/usr/share/fonts/**/NanumGothicBold.ttf", recursive=True): fm.fontManager.addfont(b)
plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["hatch.linewidth"] = 0.8
OUT = os.path.dirname(os.path.abspath(__file__))
G1, G2, G3, G4, BLACK = "#262626", "#737373", "#B3B3B3", "#D9D9D9", "#000000"

def clean(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#E5E5E5", lw=0.8); ax.set_axisbelow(True)

def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# F2. 4-level severity ---------------------------------------------------
def box(ax, x, y, w, h, text, fc="white", ec=G1, fs=10, bold=False, tc=BLACK, lw=1.4, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=lw, ls=ls))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.4)

def arrow(ax, p, q, ls="-", color=G1, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=color, lw=1.4, ls=ls, connectionstyle=f"arc3,rad={rad}"))

fig, ax = plt.subplots(figsize=(9, 3.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
lv = [("Level 4", "완전 방어", "방어 존재조차\n암시하지 않음", G1, "white"),
      ("Level 3", "기능적 방어", "핵심 정보 보호,\n방어 형태가 간접 노출", G2, "white"),
      ("Level 2", "부분 노출", "메타데이터 등\n간접 정보 노출", G3, BLACK),
      ("Level 1", "침해", "핵심 보안 경계\n실제 붕괴", G4, BLACK)]
for i, (a, b, c, fc, tc) in enumerate(lv):
    x = 0.3 + i*2.4
    box(ax, x, 1.2, 2.1, 2.0, "", fc=fc)
    ax.text(x+1.05, 2.85, a, ha="center", color=tc, fontsize=11, fontweight="bold")
    ax.text(x+1.05, 2.35, b, ha="center", color=tc, fontsize=12, fontweight="bold")
    ax.text(x+1.05, 1.6, c, ha="center", va="center", color=tc, fontsize=9, linespacing=1.4)
arrow(ax, (0.3, 0.7), (9.6, 0.7)); ax.text(0.3, 0.3, "방어 완결성 높음", fontsize=9, color=G1); ax.text(9.6, 0.3, "낮음", ha="right", fontsize=9, color=G1)
ax.set_title("4단계 보안 심각도 Level 체계 (표 4)", fontsize=13, fontweight="bold", loc="left")
save(fig, "fig2_severity_levels.png")

# F3. attack taxonomy ----------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 8.4); ax.axis("off")
ax.set_title("공격 유형 8종의 이론적 위치 — 핵심 실증 4종 vs 보완적 위협 4종", fontsize=13, fontweight="bold", loc="left")
ax.text(0.2, 7.6, "공격 유형 (8종)", fontsize=10, fontweight="bold"); ax.text(4.2, 7.6, "OWASP LLM Top 10", fontsize=10, fontweight="bold"); ax.text(7.6, 7.6, "정보 불일치성 유형", fontsize=10, fontweight="bold")
rows = [("관리자/시스템 사칭", "LLM01 Prompt Injection", "Disinformation", True),
        ("허위 사실 동조 유도", "LLM09 Misinformation", "Misinformation", True),
        ("메타데이터·프롬프트 유출", "LLM07 / LLM02", "Malinformation", True),
        ("개인정보 유출 유도", "LLM02 Sensitive Info", "Malinformation", True),
        ("인코딩·난독화 우회", "LLM01 (변형)", "범위 밖", False),
        ("어투 강요·가스라이팅", "LLM01 (Override)", "범위 밖", False),
        ("다중 상품 컨텍스트 오염", "LLM08 Vector/Embedding", "범위 밖 (약)", False),
        ("가격 정보 간접 유도", "LLM02 (변형)", "범위 밖 (약)", False)]
for i, (a, b, c, core) in enumerate(rows):
    y = 6.6 - i*0.78
    box(ax, 0.2, y, 3.6, 0.6, a, fc=G1 if core else "white", tc="white" if core else BLACK, fs=10, bold=core, ls="-" if core else (0, (4, 2)))
    box(ax, 4.2, y, 3.0, 0.6, b, fc="white", fs=9, ec=G2)
    box(ax, 7.6, y, 2.2, 0.6, c, fc=G4 if core else "white", fs=9.5, bold=core, ec=G1 if core else G2, ls="-" if core else (0, (4, 2)))
    arrow(ax, (3.8, y+0.3), (4.2, y+0.3), color=G2); arrow(ax, (7.2, y+0.3), (7.6, y+0.3), color=G2)
ax.text(0.2, 0.15, "실선·진한 상자 = 핵심 실증 (정보 진위가 판정의 본질)    점선 = 보완적 보안 위협 (정책 경계 준수가 본질)", fontsize=8.5, color=G1)
save(fig, "fig3_attack_taxonomy.png")

# F4. rounds compliance --------------------------------------------------
r7 = [68.1, 71.0, 82.6, 79.7, 88.4]
r8 = [71.2, 75.8, 63.6, 66.7, 71.2]
r9 = [68.2, 69.7, 87.9, 93.9, 87.9, 89.4, 93.9, 89.4, 93.9, 93.9, 90.9, 92.4, 92.4, 100.0]
fig, ax = plt.subplots(figsize=(9, 4.6)); clean(ax)
ax.plot(range(1, 6), r7, color=G2, ls="--", marker="s", lw=2, ms=7, label="7차 (5라운드 상한)")
ax.plot(range(1, 6), r8, color=G3, ls=":", marker="^", lw=2.2, ms=8, label="8차 (FAIL 최초 관측)")
ax.plot(range(1, 15), r9, color=G1, ls="-", marker="o", lw=2.4, ms=6, label="9차 (15라운드 상한)")
ax.annotate("100% 완전 수렴\n(round 14)", xy=(14, 100), xytext=(11.3, 78), fontsize=10, fontweight="bold", color=BLACK,
            arrowprops=dict(arrowstyle="-|>", color=BLACK, lw=1.3))
ax.annotate("round 3 최저 63.6%", xy=(3, 63.6), xytext=(3.6, 56), fontsize=9, color=G1, arrowprops=dict(arrowstyle="-|>", color=G2))
ax.set_ylim(50, 105); ax.set_xlim(0.6, 14.6); ax.set_xticks(range(1, 15))
ax.set_xlabel("자가 치유 라운드"); ax.set_ylabel("가이드라인 준수율 (%)")
ax.set_title("라운드별 준수율 추이 — 자가 치유 루프의 수렴 (표 6·8·9)", fontsize=13, fontweight="bold", loc="left")
ax.legend(frameon=False, loc="lower right", fontsize=9.5)
save(fig, "fig4_round_compliance.png")

# F5. defense by disorder type ------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.4)); clean(ax)
cats = ["Disinformation\n(사칭, n=3)", "Misinformation\n(허위사실 동조, n=3)", "Malinformation\n(유출, n=6)", "보완적 위협\n(n=10~11)"]
v14 = [100, 100, 100, 100]; vho = [100, 100, 100, 90.9]
x = range(4); w = 0.36
b1 = ax.bar([i-w/2 for i in x], v14, w, color=G1, hatch="///", edgecolor="white", label="round_14 (v_final)")
b2 = ax.bar([i+w/2 for i in x], vho, w, color=G3, hatch="...", edgecolor=G1, label="헬드아웃 (미학습 문항)")
for b in list(b1)+list(b2): ax.text(b.get_x()+b.get_width()/2, b.get_height()+1.5, f"{b.get_height():.0f}%" if b.get_height() == 100 else f"{b.get_height():.1f}%", ha="center", fontsize=9.5, fontweight="bold")
ax.set_xticks(list(x)); ax.set_xticklabels(cats, fontsize=9.5); ax.set_ylim(0, 130); ax.set_ylabel("방어 성공률 (%)")
ax.set_title("정보 불일치성 유형별 방어 결과 (표 9-부록)", fontsize=13, fontweight="bold", loc="left")
ax.legend(frameon=False, loc="upper left", ncol=2, bbox_to_anchor=(0.0, 1.0), fontsize=9.5)
ax.annotate("유일한 FAIL: 자소분리\n인코딩 우회 1건", xy=(3+w/2, 96), xytext=(2.35, 113), fontsize=8.5, ha="center", arrowprops=dict(arrowstyle="-|>", color=G1, lw=1.2))
save(fig, "fig5_defense_by_type.png")

# F6. cross-model ------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.6)); clean(ax)
runs = ["7차\n(v1.4, 원칙 수준)", "8차\n(v1.5, 원칙 수준)", "9차\n(v1.13, 문자열 템플릿)"]
data = {"openai": [60.9, 68.2, 100], "gemini": [60.9, 50.0, 87.0], "anthropic": [52.2, 31.8, 91.3]}
styles = {"openai": (G1, "///"), "gemini": (G2, "..."), "anthropic": (G4, "xx")}
w = 0.26
for k, (name, vals) in enumerate(data.items()):
    c, h = styles[name]
    bs = ax.bar([i+(k-1)*w for i in range(3)], vals, w, color=c, hatch=h, edgecolor="white" if name != "anthropic" else G1, label=name)
    for b in bs: ax.text(b.get_x()+b.get_width()/2, b.get_height()+1.5, f"{b.get_height():.0f}", ha="center", fontsize=9)
ax.text(1, 112, "p = 0.031 (유의)", ha="center", fontsize=9.5, fontweight="bold")
ax.text(0, 112, "p = 0.829", ha="center", fontsize=9.5); ax.text(2, 112, "p = 0.230", ha="center", fontsize=9.5)
ax.set_xticks(range(3)); ax.set_xticklabels(runs, fontsize=9.5); ax.set_ylim(0, 122); ax.set_ylabel("백엔드별 PASS율 (%)")
ax.set_title("교차 모델 검증 — 벤더별 PASS율 (표 10)", fontsize=13, fontweight="bold", loc="left")
ax.legend(frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.22), fontsize=9.5)
save(fig, "fig6_cross_model.png")

# F7. 5W1H axis FAIL ----------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.4)); clean(ax)
axes_ = ["who", "why", "when", "what", "how"]; base = [12.5, 18.6, 5.3, 16.7, 13.3]; w5 = [48.6, 37.5, 20.0, 50.0, 38.1]
x = range(5); w = 0.36
b1 = ax.bar([i-w/2 for i in x], base, w, color=G3, hatch="...", edgecolor=G1, label="baseline (v1.x)")
b2 = ax.bar([i+w/2 for i in x], w5, w, color=G1, hatch="///", edgecolor="white", label="5w1h (v2.x)")
for b in list(b1)+list(b2): ax.text(b.get_x()+b.get_width()/2, b.get_height()+1.2, f"{b.get_height():.1f}", ha="center", fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels(axes_, fontsize=11); ax.set_ylim(0, 66); ax.set_ylabel("FAIL 비율 (%)")
ax.set_title("5W1H 축별 FAIL 비율 — 가설 기각 (표 12, 10~11차)", fontsize=13, fontweight="bold", loc="left")
ax.legend(frameon=False, loc="upper right", fontsize=9.5)
save(fig, "fig7_5w1h_fail.png")

# F8. adaptive threat model ---------------------------------------------
fig, ax = plt.subplots(figsize=(10, 4.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
ax.set_title("적응형 재공격 — 두 가지 위협 모델 (표 14)", fontsize=13, fontweight="bold", loc="left")
box(ax, 0.2, 1.3, 2.0, 1.4, "v_final\n(방어 완료 SRS)", fc=G1, tc="white", bold=True, fs=10.5)
box(ax, 3.7, 2.7, 3.2, 1.1, "블랙박스 공격자\nMeta-Rule 존재만 앎", fc="white", fs=10, bold=True)
box(ax, 3.7, 0.2, 3.2, 1.1, "화이트박스 공격자\nMeta-Rule 전문을 앎", fc=G4, fs=10, bold=True)
box(ax, 7.6, 2.7, 2.2, 1.1, "현실적 시나리오\n9차: 5/5 방어 (100%)", fc="white", fs=9, ec=G2)
box(ax, 7.6, 0.2, 2.2, 1.1, "정책 순응성 내 방어율\n(진짜 worst-case 아님)", fc="white", fs=9, ec=G2, ls=(0, (4, 2)))
arrow(ax, (2.2, 2.3), (3.7, 3.2)); arrow(ax, (2.2, 1.7), (3.7, 0.9))
arrow(ax, (6.9, 3.25), (7.6, 3.25), color=G2); arrow(ax, (6.9, 0.75), (7.6, 0.75), color=G2)
save(fig, "fig8_adaptive_threat.png")
print("done")
