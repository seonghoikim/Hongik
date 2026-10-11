---
name: kim-paper-figures
description: 지도교수 컨펌 기준(김영철 교수님 사례)으로 논문 그림·도식을 만들거나 고칠 때 쓴다. 계층 표, 확률 트리, 매트릭스, 플롯, 스크린샷, 원서 그림 대응, 캡션, 인쇄 해상도와 실효 글자 크기, Graphviz·Mermaid·matplotlib·HTML+Playwright 도구 선택, PDF 그림 추출, Word 그림 삽입을 다룬다. 트리거 단어는 그림, figure, 도식, 다이어그램, 플롯, 캡션, dpi, 해상도, 계층 표, 확률 트리, Kim 그림, 그림 삽입, 전폭 그림이다.
---

# kim-paper-figures — 논문 그림 제작 규칙

한 연구실에서 지도교수 컨펌을 받으며 쌓은 그림 노하우를 정리했다. 여기서 "교수님"은 지도교수, "원서"는 지도교수의 박사 학위논문(Kim 박사논문)을 뜻한다. 규칙마다 **Why**(교수님 피드백이나 실제 사고)와 **How**(절차와 도구)를 함께 적었다. 수치와 사례는 프로젝트 예시이며, 규칙은 다른 주제에도 그대로 적용한다. 자기 지도교수의 원서나 기준 논문이 있으면 그것으로 바꿔 쓴다. 세부 근거는 `references/`를 읽는다.

## 0. 시작 전 확인

- **환경:** Python 3 (`matplotlib` 플롯, `Pillow` 이미지 판정, `pymupdf`(모듈명 `fitz`) PDF 처리, `playwright` 브라우저 캡처). Graphviz `dot`(트리·순서 검증). Node.js는 Mermaid를 쓸 때만.
- **Word 삽입:** Windows + Microsoft Word + pywin32(Word를 Python에서 조작하는 COM 패키지). 없으면 PNG까지 만들고 삽입은 수동으로 한다.
- **경로 표기:** `<KIT>` = 이 키트의 루트, `<PROJECT>` = 논문 프로젝트 루트. 명령의 경로는 이 두 변수로 바꿔 쓴다.
- **학술지 규정 우선:** 인쇄 폭, 캡션 형식, 색 사용은 투고 규정에서 먼저 확인한다. 이 스킬의 수치는 프로젝트 기준이다.

## 1. 그림 한 장 작업 순서

1. **메시지 한 문장을 적는다** → `references/figure-style.md` §4
2. **원서 대응을 본다** → 같은 역할의 원서 그림이 있으면 `references/kim-mapping.md` (원서 문법 우선)
3. **유형을 판정하고 도구를 고른다** → `references/tool-routing.md`
4. **소스를 쓴다.** 소스가 진실이다. 소스 없는 그림은 만들지 않는다. (`<PROJECT>/figures_src/` 등 프로젝트 관례를 따른다)
5. **렌더한다.** 산출은 PNG가 기본이다 (삽입 형식은 `word-insertion.md` §4)
6. **판정한다.** 인쇄 기준은 `check_figure_print.py`, 순서가 의미인 그림은 `verify_dot_order.py`
7. **눈으로 확인한다.** PNG를 열고 흑백 미리보기를 본다.
8. **본문에 넣는다.** 삽입과 캡션은 `references/word-insertion.md`
9. **제출 전 검수한다** → `references/review-checklist.md`의 모든 항목

## 2. 교수님 양식의 핵심 (상세: figure-style.md)

- **그림 하나에 메시지 하나.** 30초 안에 한 문장으로 읽혀야 한다. 정보량이 아니라 읽힘이 기준이다.
- **검정 선과 글자, 빨강 하나(핵심), 회색 두 단계.** 같은 색은 모든 그림에서 같은 뜻을 가진다. 데이터 플롯만 색각 안전 팔레트를 쓴다.
- **라벨은 명사구, 한 상자 3줄 이내.** 상자 안에 문장이 6~10줄 들어가고 글자가 4pt 수준인 그림은 지적을 받았다.
- **구조 문법을 먼저 쓴다:** 계층 세분화 표(실행 순번 색칠), 좌에서 우로 가는 확률 트리(갈림 확률 합 = 1).
- **공통 요소는 색으로 구분하고 블록으로 떼지 않는다.** 실행 순서대로 두고 공통 칸만 색이나 표식으로 표시한다. 같은 노드가 여러 자리에 중복되면 하나로 합친다 (`figure-style.md` §3.9).
- **캡션은 제목만.** 패널 설명, 결론, 수치 해석은 본문 문단에 쓴다.
- **프레임워크 전체를 한 장으로 보여 주는 그림**을 둔다. 부품 그림만 있으면 통과하지 못했다.
- **수치 그래프는 핵심 비교만 남긴다.** 프로젝트의 세 번째 논문을 볼 때 교수님의 잣대(2026-09-18 확인)는 수치 우위가 아니라 자동화의 편익과 논리 구성이 그림으로 읽히는지였다.
- **구도는 저자가 정한다.** 교수님은 "내 아이디어에 맞는 샘플 그림"을 원했다. AI가 구도를 정한 그림은 쓰지 않는다.
- **원서 그림 문법을 쓴다.** 새 문법을 발명하지 않는다. 용어만 우리 것으로 바꾼다.

## 3. 도구 라우팅 (상세: tool-routing.md)

| 그림 유형 | 1순위 도구 | 상태 |
|-----------|-----------|------|
| 스텝 플로우, 파이프라인 | Mermaid → SVG, PNG | 실사용 |
| 유스케이스, 상태·전이, 다이얼로그 맵(사용자 대화 흐름, 확률 라벨 간선), 행동 매트릭스(시나리오 × 단위, 셀에 실행 순서) | Graphviz `.dot` → PNG | 실증 |
| 알고리즘 상태 전개도, 분류 계보도 | Graphviz | 배정 (미검증) |
| 데이터 플롯 (막대, 선, 산점도, 히트맵) | matplotlib + `scripts/paper_style.py` | 실사용 |
| 계층 표, 확률 트리, 대비 도식, 원서 문법 재현 | HTML/CSS → `scripts/render_html_figure.py` (배율 3) | 실사용 |
| 데모 화면 스크린샷 | 캡처 → 주석본 (원본 보존) | 실사용 |
| 3D 합성 | Blender 헤드리스 | 실사용 |
| 원서·스캔 PDF 그림 | `scripts/extract_pdf_figures.py` | 실사용 |

- 본문 그림은 **코드로 생성**한다. Canva, Figma, Gamma 같은 GUI 도구와 AI 래스터 이미지는 본문에 쓰지 않는다. 발표 초안이나 장식 용도로만 쓴다.

## 4. 인쇄 품질 (상세: print-quality.md)

- **기준 A, 픽셀 폭:** PNG 픽셀 폭 ≥ 인쇄 폭(in) × 300. 인쇄 폭 368pt이면 1533.3px이므로 게이트는 **1534px**(올림)이다. 1533px는 299.9dpi라서 미달이다.
- **기준 B, 실효 글자:** 실효 글자(pt) = 글자 크기 ÷ 캔버스 폭 × 인쇄 폭. 가장 작은 글자가 **8pt 이상**이어야 한다. 중앙값으로 판정하지 않는다.
- **DPI 메타데이터는 판정에 쓰지 않는다.** 조립기가 폭을 강제하므로 결과에 영향이 없다.
- **그림은 본문 폭 100%.** 쪽 수는 본문을 줄여 맞춘다. 그림을 줄이면 글자가 안 읽힌다.
- **글자가 작으면 캔버스를 좁힌다.** 해상도를 올려도 실효 글자는 커지지 않는다.
- **옛 기록의 수치를 그대로 쓰지 않는다.** 기록 중에는 공식과 맞지 않는 값이 있었다. 새 그림은 공식으로 다시 계산한다 (`print-quality.md` §4).

## 5. 파일과 버전 규율

- 소스(`.dot`, `.mmd`, `.html`, `.py`)는 저장소에 두고 git으로 추적한다.
- **같은 이름 재생성은 초안 단계에서만 허용한다.** 교수님께 보낸 확정본과 제출본은 새 이름(`_v2`, `_v3` …)으로 보존한다. 원천 프로젝트의 그림 스킬은 그림 파일 재생성을 허용했고 "덮어쓰기 금지"는 DOCX에만 적용했다. 전역 규칙은 파일 전체에 덮어쓰기 금지를 두므로, 키트는 두 기록을 절충해 위 방식을 권장한다. 프로젝트의 "기존 파일 덮어쓰기 금지" 규칙이 있으면 그 규칙을 우선한다.
- 스크린샷과 PDF 추출 원본은 보존하고, 주석본과 변환본은 별도 파일(`*_annotated.png`)로 만든다.
- 원서 그림은 참고용이다. 원서 그림을 본문에 싣지 않고, 문법만 가져와 새로 그린다.

## 6. 가장 비싼 실수 여섯 가지 (상세: pitfalls.md)

1. **PDF 이미지 추출 시 투명 배경(SMask, 투명도 마스크 이미지) 누락** → 검은 배경에 글자가 묻힌다. `extract_pdf_figures.py --images`로 추출하고, 검은 배경을 보면 추출을 의심한다.
2. **Graphviz `rank=same` 순서가 선언 순서와 다르다** → 눈으로 확인하지 말고 `verify_dot_order.py`로 좌표를 검사한다.
3. **스캔 PDF의 도식을 판독하지 않고 추측한다** → PNG로 뽑아 직접 본다. 서브에이전트에 판독을 맡기면 그럴듯한 허위 판독이 돌아온다.
4. **글자만 키운 고정좌표 도식** → 라벨이 겹치고 잘린다. 좌표, 간격, 캔버스를 함께 재배치한다.
5. **자동 보정 스크립트가 논문 원본을 편집** → 편집 대상을 발표용 소스로만 제한하고 원본은 읽기 전용으로 둔다.
6. **아래첨자 명칭을 바꾸려고 데이터 키를 치환** → 키는 평문으로 두고 표시 계층에서만 변환한다.

## 7. 금지 사항

- 본문 그림에 AI 래스터 생성 이미지를 쓰지 않는다. 재현할 수 없고 심사 위험이 있다.
- 본문 그림을 GUI 디자인 도구로 만들지 않는다. 소스가 없어 재현과 일괄 수정이 안 된다.
- 원서 그림을 복제해 싣지 않는다.
- 기존 DOCX를 덮어쓰지 않는다. Word 편집은 COM으로만 한다 (`word-insertion.md` §2).

## 8. 스크립트 (`<KIT>/scripts/`)

| 파일 | 용도 | 대표 명령 |
|------|------|-----------|
| `render_html_figure.py` | HTML/SVG 도식을 PNG로 렌더, 폭 게이트 검사 | `python <KIT>/scripts/render_html_figure.py fig.html fig.png --selector .container --scale 3` |
| `check_figure_print.py` | PNG 픽셀 폭(dpi)과 실효 글자 크기 판정, 흑백 미리보기 | `python <KIT>/scripts/check_figure_print.py --font-px 37 --canvas-px 1700 --print-width-pt 368` |
| `verify_dot_order.py` | Graphviz 노드의 실제 위·아래(또는 좌·우) 순서 검사 | `python <KIT>/scripts/verify_dot_order.py fig.dot --nodes "AF-1,AF-2,AF-3,AF-4"` |
| `paper_style.py` | matplotlib 논문 프리셋, SVG와 PNG 동시 저장 | `import paper_style; paper_style.save(fig, "fig9")` |
| `extract_pdf_figures.py` | PDF 이미지 추출 (SMask 합성), 페이지와 영역 렌더 | `python <KIT>/scripts/extract_pdf_figures.py paper.pdf out --images --render-pages 3 --dpi 190` |

- 덮어쓰기 동작이 다르다. `extract_pdf_figures.py`는 기존 파일을 덮어쓰지 않고 `_v2`를 붙인다. `render_html_figure.py`와 `paper_style.save()`는 같은 이름을 덮어쓴다. 확정본을 만들 때는 출력 이름을 새로 준다.
- 두 게이트(`render_html_figure.py`의 `--min-width`, `check_figure_print.py --png`)는 모두 1534px(368pt, 300dpi)이다. 인쇄 폭이 다르면 `--print-width-pt`로 명시한다.
- `render_html_figure.py`가 브라우저를 찾지 못하면 `python -m playwright install chromium`을 실행하거나 `--chromium-path`로 기존 브라우저 경로를 준다.

## 9. 참고 문서 안내 (언제 무엇을 읽나)

| 상황 | 읽을 문서 |
|------|-----------|
| 새 그림을 설계하거나 교수님 피드백을 그림으로 바꿀 때 | `references/figure-style.md` |
| 원서 그림과 대응표를 만들 때 | `references/kim-mapping.md` |
| 어떤 도구로 그릴지 고를 때, 명령과 설정이 필요할 때 | `references/tool-routing.md` |
| 해상도, 글자 크기, 발표용 그림을 판정할 때 | `references/print-quality.md` |
| 이상한 결과가 나와 원인을 찾을 때 | `references/pitfalls.md` |
| Word에 넣거나 전폭 그림의 쪽 배치를 맞출 때 | `references/word-insertion.md` |
| 제출 전 마지막 점검 | `references/review-checklist.md` |
