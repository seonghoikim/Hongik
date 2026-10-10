import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import glob, os

for f in glob.glob("/usr/share/fonts/**/NanumGothic*.ttf", recursive=True): fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "NanumGothic"
OUT = os.path.dirname(os.path.abspath(__file__))
G1, G2, G3, G4, BLACK = "#262626", "#737373", "#B3B3B3", "#E6E6E6", "#000000"

def box(ax, x, y, w, h, text, fc="white", ec=G1, fs=10, tc=BLACK, lw=1.4, ls="-", bold_first=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=lw, ls=ls))
    lines = text.split("\n")
    if bold_first and len(lines) > 1:
        ax.text(x + w/2, y + h/2, lines[0] + "\n" + " " * 0, ha="center", va="center", alpha=0)  # spacing anchor
        n = len(lines); lh = 0.055 * fs / 10 * 4.2
        top = y + h/2 + (n - 1) * lh / 2
        for i, t in enumerate(lines):
            ax.text(x + w/2, top - i*lh, t, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if i == 0 else "normal")
    else:
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.45)

def arrow(ax, p, q, color=G1, ls="-", rad=0.0, lw=1.4):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=color, lw=lw, ls=ls, connectionstyle=f"arc3,rad={rad}"))

def container(ax, x, y, w, h, title, fc="#F7F7F7"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=G2, lw=1.6))
    ax.text(x + 0.15, y + h - 0.22, title, ha="left", va="center", fontsize=10.5, fontweight="bold", color=G1)

STAGES = ["사전 점검", "공격 생성", "자가 치유 루프 (구조 1·2)", "사후 검증 (구조 3)"]
def strip(ax, active, y):
    xs = [0.2, 2.75, 5.3, 7.85]
    for i, (x, s) in enumerate(zip(xs, STAGES)):
        on = i in active
        ax.add_patch(FancyBboxPatch((x, y), 2.2, 0.42, boxstyle="round,pad=0.01,rounding_size=0.05", fc=G1 if on else "white", ec=G1 if on else G3, lw=1.1))
        ax.text(x + 1.1, y + 0.21, s, ha="center", va="center", fontsize=9, color="white" if on else G2, fontweight="bold" if on else "normal")
        if i < 3: arrow(ax, (x + 2.22, y + 0.21), (xs[i+1] - 0.02, y + 0.21), color=G3, lw=1.0)
    ax.text(0.2, y + 0.62, "전체 흐름에서의 위치", fontsize=8.5, color=G2)
    ax.plot([0.2, 10.05], [y - 0.2, y - 0.2], color=G4, lw=1)

def new(w, h):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 10.2); ax.set_ylim(0, h); ax.axis("off"); return fig, ax

def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# 0. 전체 개요 -------------------------------------------------------------
fig, ax = new(10.2, 3.6); ax.set_ylim(0.75, 3.6)
box(ax, 0.2, 0.9, 1.9, 1.7, "사전 점검\n결정론적 차단 문구 검증\nDrift 카나리아\n대화형 검토 도구", fs=9)
box(ax, 2.5, 0.9, 1.9, 1.7, "공격 생성\n레드팀 LLM이\n카테고리별\n시나리오 생성", fs=9)
box(ax, 4.8, 0.9, 2.7, 1.7, "자가 치유 루프\n구조 1: 유닛 A~D 파이프라인\n구조 2: 채점 → Meta-Rule 생성\n→ SRS 병합", fs=9, fc=G4, lw=2)
box(ax, 8.1, 0.9, 2.0, 1.7, "사후 검증 (구조 3)\n헬드아웃 검증\n적응형 재공격\n교차 모델 검증·통계 검정", fs=9)
arrow(ax, (2.1, 1.75), (2.5, 1.75)); arrow(ax, (4.4, 1.75), (4.8, 1.75)); arrow(ax, (7.5, 1.75), (8.1, 1.75))
arrow(ax, (7.0, 2.6), (5.3, 2.6), rad=0.6)
ax.text(6.15, 3.3, "미수렴 시 반복 (라운드 상한까지)", ha="center", fontsize=9, color=G1)
ax.text(7.8, 1.9, "수렴 시", ha="center", va="bottom", fontsize=8.5, color=G1)
save(fig, "1_전체_흐름_개요.png")

# 1. 준비 단계: 사전 점검 + 공격 생성 ------------------------------------------
fig, ax = new(10.2, 4.9)
strip(ax, [0, 1], 4.1)
container(ax, 0.2, 0.2, 4.4, 3.4, "사전 점검 (루프 시작 전)")
box(ax, 0.5, 2.35, 3.8, 0.75, "① 결정론적 차단 문구 사전 검증", fs=9.5, bold_first=False)
box(ax, 0.5, 1.4, 3.8, 0.75, "② Zero-cost Drift 카나리아", fs=9.5, bold_first=False)
box(ax, 0.5, 0.45, 3.8, 0.75, "③ 대화형 검토 도구", fs=9.5, bold_first=False)
box(ax, 5.3, 1.1, 2.6, 1.5, "공격 생성 (구조 3-①)\n레드팀 LLM이\n카테고리별 시나리오 생성", fs=9.5, fc=G4)
box(ax, 8.4, 1.35, 1.7, 1.0, "다음 단계\n자가 치유 루프", fs=9, ls=(0, (4, 2)), ec=G2)
arrow(ax, (4.6, 1.85), (5.3, 1.85)); arrow(ax, (7.9, 1.85), (8.4, 1.85))
save(fig, "2_준비단계_사전점검_공격생성.png")

# 2. 구조 1: 유닛 A~D --------------------------------------------------------
fig, ax = new(10.2, 5.1)
strip(ax, [2], 4.4)
ax.text(5.1, 3.85, "입력: ② 적대적 실행의 공격 문장   →   출력: 챗봇 응답 (③ 심판관 채점으로 전달)", ha="center", fontsize=9, color=G2)
container(ax, 0.2, 1.25, 9.9, 2.35, "구조 1 — 파이프라인 아키텍처 (유닛 A~D)")
units = ["A. 입력 가드레일\n명백한 탈옥·사칭·\n인코딩 우회만\n1차 차단", "B. RAG 검색\n내부 지식베이스\n에서만 관련\n정보 조회",
         "C. LLM 추론\nSRS 페르소나 +\nMeta-Rule로\n응답 생성", "D. 출력 가드레일\n메타데이터·경쟁사\n노출 등\n최종 필터링"]
xs = [0.5, 2.95, 5.4, 7.85]
for i, (x, t) in enumerate(zip(xs, units)):
    box(ax, x, 1.45, 2.05, 1.75, t, fs=9.5, fc=G4 if i == 2 else "white", lw=2 if i == 2 else 1.4)
    if i < 3: arrow(ax, (x + 2.05, 2.32), (xs[i+1], 2.32))
box(ax, 0.2, 0.05, 9.9, 0.85, "유닛 A는 명백한 우회만 차단한다. 교묘한 사회공학적 공격(가스라이팅, 어투 강요)은 의도적으로 통과시켜\n유닛 C의 SRS·Meta-Rule이 실제로 방어하도록 남긴다.", fs=9, ls=(0, (3, 2)), ec=G2, bold_first=False)
ax.plot([1.5, 1.5], [0.9, 1.45], color=G2, lw=1, ls=":")
save(fig, "3_구조1_유닛AD_파이프라인.png")

# 3. 구조 2: 자가 치유 폐쇄 루프 ----------------------------------------------
fig, ax = new(10.2, 7.2)
strip(ax, [2], 6.55)
container(ax, 0.2, 0.95, 9.9, 5.25, "구조 2 — 자가 치유 폐쇄 루프")
box(ax, 0.5, 4.5, 2.3, 1.15, "① SRS 정의\n고객사 페르소나 +\n제약 조건", fs=9.5)
box(ax, 3.95, 4.5, 2.3, 1.15, "⑤ SRS 병합\n헤더·푸터에 삽입\nSRS v(n) → v(n+1)", fs=9.5)
box(ax, 7.5, 4.5, 2.3, 1.15, "④ Meta-Rule 생성\n실패 사례를 분석해\n방어 규칙 자동 작성", fs=9.5, fc=G4, lw=2)
box(ax, 0.5, 1.2, 2.3, 1.15, "② 적대적 실행\n공격 시나리오로\n챗봇 응답 생성", fs=9.5)
box(ax, 3.95, 1.2, 2.3, 1.15, "구조 1 통과\n유닛 A → B → C → D", fs=9.5, ls=(0, (4, 2)), ec=G2)
box(ax, 7.5, 1.2, 2.3, 1.15, "③ 심판관 채점\n무상태 LLM이\nAction Matrix로 판정", fs=9.5, fc=G4, lw=2)
arrow(ax, (1.65, 4.5), (1.65, 2.35)); arrow(ax, (2.8, 1.78), (3.95, 1.78)); arrow(ax, (6.25, 1.78), (7.5, 1.78))
arrow(ax, (8.65, 2.35), (8.65, 4.5)); ax.text(8.8, 3.42, "미수렴 시", fontsize=9, color=G1, va="center")
arrow(ax, (7.5, 5.08), (6.25, 5.08)); arrow(ax, (3.95, 5.08), (2.8, 5.08))
ax.text(3.37, 4.95, "라운드 상한까지\n반복", ha="center", va="top", fontsize=8, color=G1, linespacing=1.3)
box(ax, 3.7, 2.75, 2.8, 1.45, "Meta-Rule은 SRS 프롬프트의\n헤더+푸터에 이중 삽입된다.\n심판관 채점 프롬프트에는\n비용 절감을 위해 한 번만 삽입한다.", fs=8.5, ls=(0, (3, 2)), ec=G2, bold_first=False)
ax.plot([5.1, 5.1], [4.2, 4.5], color=G2, lw=1, ls=":")
box(ax, 6.9, 0.05, 3.2, 0.62, "수렴 시 (전원 FULL_DEFENSE) → 사후 검증", fs=9, fc="white", ec=G1, bold_first=False)
arrow(ax, (8.65, 1.2), (8.65, 0.67))
save(fig, "4_구조2_자가치유_루프.png")

# 4. 구조 3: 사후 검증 ---------------------------------------------------------
fig, ax = new(10.2, 4.3)
strip(ax, [3], 3.6)
box(ax, 0.15, 1.05, 1.4, 1.2, "수렴 시\n(전원\nFULL_DEFENSE)", fs=8.5, fc=G4, ec=G2, bold_first=False)
container(ax, 1.75, 0.3, 8.35, 2.8, "구조 3 — 사후 검증 (v_final 대상)")
steps = ["구조 3-③\n헬드아웃 검증\n치유에 쓰지 않은\n별도 문항으로 재검증", "구조 3-④\n적응형 재공격\n블랙박스·화이트박스\n두 위협 모델로 재공격",
         "구조 3-⑤\n교차 모델 검증\n3개 벤더로 응답만 교체\n(심판관은 고정)", "구조 3-⑥\n통계 검정\nWilcoxon·\nMann-Whitney·\nKruskal-Wallis·\n카이제곱"]
xs = [1.95, 4.05, 6.15, 8.25]
for i, (x, t) in enumerate(zip(xs, steps)):
    box(ax, x, 0.55, 1.8, 2.0, t, fs=8.5)
    if i < 3: arrow(ax, (x + 1.8, 1.55), (xs[i+1], 1.55))
arrow(ax, (1.55, 1.65), (1.95, 1.65))
save(fig, "5_구조3_사후검증.png")
print("done")
