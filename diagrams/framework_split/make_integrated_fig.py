import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import glob, os, sys
for f in glob.glob("/usr/share/fonts/**/NanumGothic*.ttf", recursive=True): fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "NanumGothic"
G1, G2, G3, G4 = "#262626", "#737373", "#B3B3B3", "#E3E3E3"

fig, ax = plt.subplots(figsize=(8, 13.6)); ax.set_xlim(0, 10); ax.set_ylim(3.9, 17); ax.axis("off")

def box(x, y, w, h, t, fc="white", ec=G1, lw=1.3, ls="-", fs=8.6, bold_first=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.05", fc=fc, ec=ec, lw=lw, ls=ls))
    lines = t.split("\n"); lh = 0.205 * fs / 8.6
    top = y + h/2 + (len(lines)-1)*lh/2
    for i, s in enumerate(lines):
        ax.text(x + w/2, top - i*lh, s, ha="center", va="center", fontsize=fs, fontweight="bold" if (bold_first and i == 0 and len(lines) > 1) else "normal")

def cont(x, y, w, h, t, bottom=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.06", fc="#F7F7F7", ec=G2, lw=1.6))
    ax.text(x + 0.12, (y + 0.2) if bottom else (y + h - 0.2), t, fontsize=9.2, fontweight="bold", va="center", color=G1)

def arr(pts, color=G1, ls="-", head=True, lw=1.2):
    for i in range(len(pts) - 1):
        last = i == len(pts) - 2
        ax.add_patch(FancyArrowPatch(pts[i], pts[i+1], arrowstyle="-|>" if (head and last) else "-", mutation_scale=11, color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))

# 사전 점검
cont(0.1, 13.2, 2.6, 3.6, "사전 점검")
for i, t in enumerate(["① 결정론적 차단\n문구 사전 검증", "② Zero-cost\nDrift 카나리아", "③ 대화형\n검토 도구"]):
    box(0.35, 15.55 - i*0.95, 2.1, 0.78, t, bold_first=False)
box(0.35, 11.2, 2.1, 1.5, "【구조 3-①】 공격 생성\n레드팀 LLM이\n카테고리별\n시나리오 생성", fc="#F0F0F0")
arr([(1.4, 13.2), (1.4, 12.7)])

# 유닛 A 주석 + 구조 1
box(3.0, 15.85, 6.9, 0.95, "유닛 A는 명백한 우회만 차단한다. 교묘한 사회공학적 공격(가스라이팅, 어투 강요)은\n의도적으로 통과시켜 유닛 C의 SRS·Meta-Rule이 실제로 방어하도록 남긴다.", ec=G2, ls=(0, (3, 2)), fs=8.2, bold_first=False)
cont(3.0, 13.2, 6.9, 2.45, "구조 1 — 파이프라인 아키텍처 (유닛 A~D)")
units = ["A. 입력 가드레일\n명백한 탈옥·사칭·\n인코딩 우회만\n1차 차단", "B. RAG 검색\n내부 지식베이스\n에서만 관련\n정보 조회", "C. LLM 추론\nSRS 페르소나 +\nMeta-Rule로\n응답 생성", "D. 출력 가드레일\n메타데이터·경쟁사\n노출 등\n최종 필터링"]
xs = [3.15, 4.85, 6.55, 8.25]
for i, (x, t) in enumerate(zip(xs, units)):
    box(x, 13.4, 1.55, 1.75, t, fs=8.2)
    if i < 3: arr([(x + 1.55, 14.27), (xs[i+1], 14.27)])

# 구조 2
cont(2.85, 7.0, 5.15, 5.55, "구조 2 — 자가 치유 폐쇄 루프", bottom=True)
box(3.1, 10.75, 2.1, 1.25, "② 적대적 실행\n공격 시나리오로\n챗봇 응답 생성")
box(5.7, 10.75, 2.1, 1.25, "③ 심판관 채점\n무상태 LLM이\nAction Matrix로 판정", fc=G4, lw=2.2)
box(3.1, 9.05, 2.1, 1.25, "① SRS 정의\n고객사 페르소나 +\n제약 조건")
box(5.7, 9.05, 2.1, 1.25, "④ Meta-Rule 생성\n실패 사례를 분석해\n방어 규칙 자동 작성", fc=G4, lw=2.2)
box(5.7, 7.35, 2.1, 1.25, "⑤ SRS 병합\n헤더·푸터에 삽입\nSRS v(n) → v(n+1)")
arr([(4.15, 10.3), (4.15, 10.75)])                          # ① → ②
arr([(4.15, 12.0), (4.15, 13.4)])                           # ② → 유닛 A
arr([(9.0, 13.4), (9.0, 12.8), (6.75, 12.8), (6.75, 12.0)])  # 유닛 D → ③
arr([(6.75, 10.75), (6.75, 10.3)]); ax.text(6.85, 10.53, "미수렴 시", fontsize=7.8, va="center")
arr([(6.75, 9.05), (6.75, 8.6)])                            # ④ → ⑤
arr([(5.7, 7.97), (4.65, 7.97), (4.65, 9.05)])              # ⑤ → ①
ax.text(4.55, 8.5, "갱신된 SRS로\n②부터 반복\n(라운드 상한까지)", fontsize=7.4, ha="right", va="center", color=G1, linespacing=1.3)
arr([(1.4, 11.2), (1.4, 9.67), (3.1, 9.67)])                 # 공격 생성 → ①
box(5.2, 4.75, 2.8, 1.75, "Meta-Rule은 SRS 프롬프트의\n헤더+푸터에 이중 삽입된다.\n방어 메커니즘 자체는 규칙을\n두 번 강조하되, 심판관 채점\n프롬프트에서는 비용 절감을\n위해 한 번만 삽입한다.", ec=G2, ls=(0, (3, 2)), fs=7.8, bold_first=False)
arr([(6.75, 7.35), (6.75, 6.5)], color=G2, ls=":", head=False, lw=1)

# 구조 3
arr([(7.8, 11.37), (9.15, 11.37), (9.15, 10.95)])
ax.text(9.05, 12.25, "수렴 시\n(전원 FULL_DEFENSE)", fontsize=7.8, ha="center", va="center", bbox=dict(fc=G4, ec="none", pad=2))
steps = ["【구조 3-③】\n헬드아웃 검증\n치유에 쓰지 않은\n별도 문항으로 재검증", "【구조 3-④】\n적응형 재공격\n블랙박스·화이트박스\n두 위협 모델로 재공격",
         "【구조 3-⑤】\n교차 모델 검증\n3개 벤더로 응답만\n교체(심판관은 고정)", "【구조 3-⑥】\n통계 검정\nWilcoxon·\nMann-Whitney·\nKruskal-Wallis·\n카이제곱"]
for i, t in enumerate(steps):
    y = 9.55 - i*1.75
    box(8.2, y, 1.75, 1.4, t, fc="#F0F0F0", fs=7.6)
    if i < 3: arr([(9.075, y), (9.075, y - 0.35)])
out = sys.argv[1] if len(sys.argv) > 1 else "integrated.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
