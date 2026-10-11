# 도구 라우팅 — 그림 유형별 도구

본문 그림은 **코드로 생성**한다 (소스 보관, 재현 가능). GUI 도구와 AI 래스터 생성은 본문에 쓰지 않는다 (§4).

## 1. 한눈에 보는 표

상태 표기: **실증** = 렌더해서 확인하고 논문에 실제로 넣었다. **실사용** = 프로젝트 논문 그림에 쓰였다. **배정** = 도구 성격상 가능하다고 판단했으나 아직 검증하지 않았다.

| 그림 유형 | 1순위 도구 | 소스 → 산출 | 상태 | 비고 |
|-----------|-----------|-------------|------|------|
| 플로차트·파이프라인 (스텝 플로우) | Mermaid | `.mmd` → SVG, PNG | 실사용 | `htmlLabels:false`, 줄바꿈 `<br/>`. 단계 번호를 라벨에 넣는다 (`figure-style.md` §3.8) |
| 시퀀스 다이어그램 (메시지 흐름) | Mermaid `sequenceDiagram` | `.mmd` → SVG, PNG | 실사용 | 구조 제어가 어려우면 HTML |
| 유스케이스(액터 포함) | Graphviz | `.dot` → PNG | 실증 | `cluster`, 이미지 액터, `dir=back` |
| 상태·전이·다이얼로그 맵 (확률 라벨) | Graphviz | `.dot` → PNG | 실증 | 간선 라벨 겹침이 자동으로 줄어든다 |
| 행동 매트릭스 (행×열 표) | Graphviz HTML-like 라벨, `shape=plaintext` | `.dot` → PNG | 실증 | 9행 × 16열 검증 |
| 알고리즘 상태 전개도, 분류 계보도 | Graphviz | `.dot` → PNG | 배정 | 순서가 의미면 `verify_dot_order.py` |
| 가중 그래프 (BU 그래프 등) | networkx + matplotlib | `.py` → SVG, PNG | 실사용 | 노드 배치는 networkx 레이아웃 |
| 데이터 플롯 (막대·선·산점도) | matplotlib + `paper_style.py` | `.py` → SVG, PNG | 실사용 | Okabe-Ito 팔레트 |
| 히트맵·공통성 매트릭스 | seaborn 또는 matplotlib `imshow` | `.py` → SVG, PNG | 실사용 | `paper_style.py` 적용 |
| 다중 패널 (2×2, 3×1) | matplotlib `GridSpec` | `.py` → SVG, PNG | 배정 | 패널마다 한 메시지 |
| 계층 세분화 표, 확률 트리, 대비 도식, 커스텀 레이아웃 | HTML/CSS → Playwright | `.html` → PNG | 실사용 | `render_html_figure.py`, 배율 3 |
| 데모 화면 스크린샷 + 주석 | Playwright 캡처 → 주석 도구 | 원본 PNG + `*_annotated.png` | 실사용 | 원본 보존 |
| 3D 합성 | Blender 헤드리스 | `.py` → PNG | 실사용 | 스크립트를 보관한다 |
| 원서·스캔 PDF 그림 읽기 | `extract_pdf_figures.py --render-pages` | PDF → PNG | 실사용 | PNG로 뽑아 직접 본다 |
| 발표용 도식 | HTML 별도 소스 (`*_pptsrc.html`) | → `*_ppt.png` | 실사용 | `print-quality.md` §9 |

## 2. 도구 고르는 순서

1. 노드와 간선을 자동 배치해야 한다 → **Graphviz**.
2. 표, 트리, 정확한 좌표, 원서 문법 재현이 필요하다 → **HTML/CSS**.
3. 수치 데이터를 그린다 → **matplotlib** (`paper_style.py`).
4. 메시지 흐름의 순서가 중요하다 → **Mermaid** 또는 HTML.
5. 실제 화면을 보여 준다 → **캡처 + 주석**.

- HTML에 좌표를 손으로 쓰면 나중에 고치기 어렵다. 좌표를 생성하는 스크립트를 두고 HTML은 산출물로 취급한다.

## 3. 도구별 설정

### 3.1 Graphviz

- 실행 파일: PATH의 `dot`, 또는 Windows 기본 설치 경로(`C:/Program Files/Graphviz/bin/dot.exe`). 키트 `verify_dot_order.py`는 `--dot-bin`, 환경변수 `GRAPHVIZ_DOT`도 받는다.
- **한글:** 모든 노드와 간선에 `fontname="Malgun Gothic"` (또는 본문과 맞춘 한글 폰트)을 지정한다. 지정하지 않으면 한글이 깨진다.
- **PNG 픽셀 수:** Graphviz에서는 `-Gdpi=300`처럼 dpi 속성이 **픽셀 수**를 바꾼다. 이것은 파일 메타데이터와 다르며 실제로 의미가 있다. 결과를 `check_figure_print.py`로 확인한다.
- **아래첨자 라벨:** HTML-like 라벨 `<I>L</I><SUB>fas</SUB>`. 노드 ID는 평문으로 둔다 (`pitfalls.md` §10).
- **순서 검증:** 순서가 의미를 가지면 `verify_dot_order.py`로 좌표를 확인한다 (`pitfalls.md` §4).
- 벡터는 `dot -Tsvg`, 래스터는 `dot -Tpng -Gdpi=300`.
- **`-Gdpi=300`은 게이트에 걸리기 쉽다.** 그래프 폭이 368pt(5.11in)이면 약 1533px이라 1534px 게이트를 넘지 못할 수 있다. 픽셀이 모자라면 dpi를 올린다(예: 400). 조립기가 폭을 368pt로 맞추므로 인쇄 결과는 같고, 실효 글자 크기는 dpi가 아니라 캔버스 폭으로 정해진다. 결과는 `check_figure_print.py --png`로 확인한다.

### 3.2 Mermaid

- 설정: 본문과 같은 세리프 폰트, 중립 테마, `htmlLabels:false` (텍스트가 순수 SVG 텍스트로 남아 Word에서 안정적이다), 줄바꿈은 `<br/>`.
- 렌더 방식 (프로젝트 기록): mermaid-cli(`mmdc`)로 SVG를 만들고, Playwright로 같은 그림을 배율 3에서 캡처해 PNG를 만든다. Mermaid를 CDN에서 가져오면 네트워크가 필요하므로 버전을 고정하거나 로컬 패키지를 쓴다. 사용한 도구와 버전은 본문이나 부록에 적는다 (`review-checklist.md` E).
- 한계: 노드 위치를 세밀하게 제어하기 어렵다. 제어가 필요하면 Graphviz 또는 HTML로 옮긴다.

### 3.3 matplotlib (`scripts/paper_style.py`)

```python
import sys; sys.path.insert(0, r"<KIT>/scripts")
import paper_style                       # import applies the rcParams
fig, ax = paper_style.new_figure(16, 9)  # width, height in cm; take the width from the venue
# ... plot ...
paper_style.save(fig, "fig9_metric")     # figures_svg/fig9_metric.svg + figures_png/fig9_metric.png
```

- 출력 폴더는 환경변수 `FIG_ROOT`(기본: 현재 폴더). 덮어쓰기 규칙은 `SKILL.md` §5를 따른다.
- Windows에서 `sys.path.insert`에 넣는 경로는 `C:/...` 형식이어야 한다. Git Bash의 `/c/...` 경로는 Python 안에서 모듈을 찾지 못한다.
- **폭을 인쇄 폭에 맞춘다.** `new_figure` 폭을 368pt = 12.98cm (또는 게재지의 인쇄 폭)에 맞추면 글자 크기를 pt로 잡을 때 인쇄 크기와 거의 같아진다. `savefig`가 여백을 자르므로 PNG 픽셀 폭은 `폭cm / 2.54 × 300`과 정확히 같지 않다. `check_figure_print.py --png`로 잰다.
- 수식 표기: matplotlib mathtext (`$L_{fas}$`, `$p<10^{-4}$`). 통계 주석이 필요하면 p 값과 효과 크기를 함께 표기한다.
- 색은 Okabe-Ito 8색이다. 노랑은 흰 바탕에서 약하므로 마지막에 쓴다.
- SVG는 `svg.fonttype: none`이라 글자가 글자로 남는다.

### 3.4 HTML/CSS → PNG (`scripts/render_html_figure.py`)

Playwright는 화면 없이 실행되는 Chromium을 Python에서 조작해 페이지나 요소를 PNG로 캡처하는 라이브러리다.

- 구조: 최상위 `.container`에 고정 폭을 준다 (예: 1700px). 글자 크기는 px로 지정한다. `body`에 흰 배경을 명시한다.
- 폰트 스택: `'Times New Roman', 'Malgun Gothic', serif` 처럼 본문과 맞춘다.
- 렌더:
  ```
  python <KIT>/scripts/render_html_figure.py figures_html/fig2.html figures_png/fig2.png --selector .container --scale 3
  ```
  배율 3이면 1700px 캔버스가 5100px PNG가 된다. 폭 게이트(1534px) 미달이면 종료 코드 2를 돌려준다.
- 최초 설정: `pip install playwright pillow` 후 `python -m playwright install chromium`. 기존 브라우저를 쓰려면 `--chromium-path`를 준다.
- 캡처 대상 선택자가 없으면 뷰포트 전체를 캡처하고 경고를 낸다.

### 3.5 스크린샷 주석

- 원본은 손대지 않는다. 주석본은 별도 파일 (`*_annotated.png`).
- 프로젝트는 Node 주석 스크립트(`sharp` 계열, 자르기·박스·화살표·배율을 명령 옵션으로 받음)를 썼다. Python으로 같은 작업을 하려면 Pillow를 쓸 수 있다 (키트에서는 미검증). 명령을 남겨 두면 재현된다.
- 주석 색은 그림 전체의 강조 색과 맞춘다. 프로젝트 기록에는 주황 `#E69F00` 주석과 빨강 `#B03A2E` 도식 강조가 함께 있었다. 한 논문 안에서는 강조색을 하나로 통일한다.

### 3.6 3D 합성 (Blender)

- 헤드리스 실행하고 스크립트를 파일로 보관한다. 카메라와 조명 값은 스크립트에 고정한다.
- 출력 PNG의 픽셀 폭을 `check_figure_print.py`로 확인한다.

### 3.7 PDF 그림 추출과 페이지 렌더

- `extract_pdf_figures.py --images`: 내장 이미지를 추출하면서 SMask를 흰 배경에 합성한다 (`pitfalls.md` §3).
- `extract_pdf_figures.py --render-pages 3,5 --dpi 190`: 페이지를 PNG로 뽑는다. 스캔 PDF(텍스트 층 없음)를 읽을 때 쓴다.
- `--clip x0,y0,x1,y1`: 도식 영역만 고해상도로 뽑는다 (PDF 포인트 단위).
- 이 환경에서 Read 도구가 PDF 페이지를 렌더하지 못할 수 있다. 그때는 PNG로 뽑아서 직접 본다.

## 4. 쓰지 말 것 · 검토 후 미채택

- **AI 래스터 이미지 생성 (Freepik류 등):** 본문 그림 금지. 재현할 수 없고 심사 위험이 있다. 슬라이드 배경이나 포스터 장식에만 쓴다.
- **GUI 디자인 도구 (Canva, Figma, Gamma 등)로 본문 그림:** 소스가 없어 재현이 안 되고, 여러 그림을 한 번에 고칠 수 없다. 발표 초안 용도로만 쓰고 최종 판은 소스 기반으로 만든다.
- **검토 후 미채택 (필요해지면 재검토):**
  - PlantUML: Java 설치가 필요하다. 현재 도구로 대부분 커버된다.
  - D2: npm 패키지가 불완전하고 Windows 설치 경로가 복잡하다.
  - TikZ/PGF: 학습 곡선이 길다. 현재 Word 삽입 흐름과 맞추기 어렵다.
  - drawsvg: Windows에서 SVG를 PNG로 바꾸는 환경을 맞추기 어렵다.
- **선택 확장:** 교수님이 직접 고치기를 원하면 Mermaid를 `.drawio`로 변환해 편집 가능한 파일을 드리는 방법이 있다.

## 5. 폴더 관례 (권장)

```
<PROJECT>/
  figures_src/      Mermaid .mmd, Graphviz .dot, matplotlib .py 소스
  figures_html/     HTML 도식 소스 (좌표 생성기 포함)
  figures_svg/      벡터 산출 (paper_style.save)
  figures_png/      래스터 산출 (Word 삽입용)
  scripts/figures/  생성 스크립트
```
