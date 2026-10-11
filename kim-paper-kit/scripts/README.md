# scripts/ 사용 설명

키트 스킬이 호출하는 스크립트 모음이다. 모든 명령의 `<KIT>` 는 키트 루트의 절대경로로 바꿔 쓴다 (예: `C:/Users/<이름>/kim-paper-kit`).
스크립트는 경로를 인자로 받는다. 프로젝트 안의 파일 이름이나 개인 경로를 코드에 넣지 않았다.

## 한눈에 보기

| 스크립트 | 용도 | 주요 의존성 | 쓰는 스킬 | 검증 상태 |
|---|---|---|---|---|
| `check_env.py` | 설치 점검. 파일을 만들지 않는다 | 표준 라이브러리 | 전체 | 실행 확인 |
| `style_lint.py` | 원고 린트 (번역체, 금칙 제목, 쉼표 인용, 표 열 수 등) | 표준 라이브러리 | kim-paper-writing | 샘플 원고로 실행 확인 |
| `check_source.py` | 조판용 원고 소스 점검 (제어문자, 표 파이프, 리비전 짝, 그림 캡션, TBD) | 표준 라이브러리 | kim-paper-typesetting | 샘플 원고로 실행 확인 |
| `academic_search.py` | 논문 검색, DOI 검증, 인용 문자열 생성 | requests, 인터넷 | kim-feedback-loop | DOI 검증 실행 확인 |
| `transcribe_meeting.py` | 긴 음성 녹음 청크 전사 (체크포인트, 재개) | faster-whisper, ffmpeg | kim-feedback-loop | `--plan-only` 확인. 실제 전사 미실행 |
| `check_figure_print.py` | 그림 인쇄 기준 판정 (픽셀 폭, 실효 글자 크기, 흑백 미리보기) | Pillow (`--png` 때만) | kim-paper-figures | 글자 크기 판정 확인 |
| `verify_dot_order.py` | Graphviz 노드의 실제 위·아래(좌·우) 순서 검사 | Graphviz `dot` | kim-paper-figures | 샘플 `.dot` 으로 확인 |
| `render_html_figure.py` | HTML/SVG 도식을 고배율 PNG로 렌더, 폭 게이트 검사 | playwright (+ Chromium), Pillow | kim-paper-figures | 실행 미확인 |
| `paper_style.py` | matplotlib 논문 프리셋, SVG와 PNG 동시 저장 | matplotlib | kim-paper-figures | import 확인 |
| `extract_pdf_figures.py` | PDF 내장 이미지 추출 (투명 마스크 합성), 페이지 렌더 | PyMuPDF, Pillow | kim-paper-figures | 도움말 확인. 실제 PDF 미실행 |
| `pdf_page_audit.py` | 조판 PDF 의 쪽별 빈칸 측정, 글꼴·색 실측 | PyMuPDF | kim-paper-typesetting | 도움말 확인. 실제 PDF 미실행 |
| `word_com_template.py` | Word COM 조판 골격 (열 폭 계산, 지연 배치, 버전 이름, 저장) | pywin32, Microsoft Word, Pillow | kim-paper-typesetting | `--selftest` 통과. COM 호출부 미검증 |
| `render_deck.py` | PowerPoint COM 으로 덱을 PDF와 쪽별 PNG로 내보내기 (검수) | pywin32, Microsoft PowerPoint, PyMuPDF | kim-paper-typesetting | 도움말 확인. 실행 미확인 |
| `deck_korean_wrap.py` | PPT 한글 언어 태그를 ko-KR 로 바꾸는 후처리 (새 파일로 저장) | python-pptx | kim-paper-typesetting | 도움말 확인 (이 점검에서 `--help` 오류를 고쳤다) |

의존성 목록은 `requirements.txt`, 설치 확인은 `python "<KIT>/scripts/check_env.py"` 를 쓴다.

## 공통 규칙

- **덮어쓰기 금지.** 산출물 이름이 이미 있으면 `_v2`, `_v3` 를 붙이는 것이 원칙이다. 예외는 아래 "덮어쓰기 동작" 표를 본다.
- **시험은 scratch, 확정은 새 이름.** 시험 출력은 임시 폴더에 두고, 확정본만 새 이름으로 만든다.
- **판정 기준은 스크립트에 있다.** 예: 인쇄 폭 368pt 와 300dpi 면 픽셀 폭 게이트는 1534px 이다 (1533px 는 299.9dpi 라서 미달이다).
- **Windows 경로.** `sys.path` 나 명령 인자에는 `C:/...` 형식을 쓴다. Git Bash 의 `/c/...` 는 Python 안에서 모듈을 찾지 못하는 경우가 있다.
- **bash 에서 `>nul` 을 쓰지 않는다.** `>/dev/null` 을 쓴다. `nul` 파일은 `git add` 를 막는다.

### 덮어쓰기 동작

| 스크립트 | 같은 이름이 있으면 |
|---|---|
| `extract_pdf_figures.py` | `_v2` 를 붙여 새 파일로 쓴다 |
| `transcribe_meeting.py` | 결과 `.txt` 에 `_v2` 를 붙인다. 체크포인트는 모델 이름별 폴더에 나눠 둔다 |
| `render_deck.py` | 출력 폴더가 있으면 `<이름>_v02` 를 쓴다 |
| `deck_korean_wrap.py` | 출력 파일이 있으면 `_v02` 를 붙인다 |
| `word_com_template.py` (`save_new`) | `next_versioned_path()` 로 `_vNN` 을 붙인다 |
| `render_html_figure.py` | 같은 이름의 PNG 를 **덮어쓴다**. 확정본은 출력 이름을 새로 준다 |
| `paper_style.py` (`save`) | 같은 이름의 SVG 와 PNG 를 **덮어쓴다**. 확정본은 이름을 새로 준다 |
| `academic_search.py` | 파일을 쓰지 않는다 (출력만 한다) |
| `check_source.py`, `style_lint.py`, `pdf_page_audit.py`, `check_figure_print.py`, `verify_dot_order.py` | 입력 파일을 읽기만 한다 |

## 스크립트별 사용법

### check_env.py
- 용도: 키트와 스킬이 기대하는 환경 점검 (Python 버전, 모듈, ffmpeg, Graphviz, Word/PowerPoint COM 등록, 한글 글꼴).
- 명령: `python "<KIT>/scripts/check_env.py"` · 묶음만: `--group figures` (writing, feedback, figures, typesetting, ppt)
- 판정: OK / MISSING / NOTE. 파일을 만들지 않고 Office 를 실행하지 않는다 (COM 이름만 레지스트리에서 확인).
- 종료 코드: Python 3.10 미만이거나 키트 scripts 폴더가 없으면 1.

### style_lint.py
- 용도: 연구실 기준 문체 린트. 국문 번역체, 금칙 제목('소결', '본 연구의 위치'), 질문형과 구어체, 영문 1인칭, 수동태, 쉼표 인용 `[1,2]`, 번호 주어 `[23]은`, 정의 번호 체계, maximal/maximum 혼동, 표 열 수 불일치.
- 명령: `python "<KIT>/scripts/style_lint.py" 원고.md [원고2.md] [--ban "단어1,단어2"] [--json]`
- 심각도: error (반드시 고침), warn (문맥 판단), info (참고). error 가 있으면 종료 코드 1.
- 한계: 코드 블록(``` 구간)은 검사하지 않는다. 문맥 판단이 필요한 번역체는 warn 으로 잡힌다.

### check_source.py
- 용도: 조판기에 넣기 전 원고 소스 점검. 제어문자(heredoc 백슬래시 손상), 표 행의 파이프 수, 셀 안 리터럴 `|`, `{+ +}` 짝, `$$` 짝, `[[FIGURE n]]` 과 캡션 짝, `‹TBD: …›` 잔여.
- 명령: `python "<KIT>/scripts/check_source.py" sec1_front.md sec2.md`
- 오류가 있으면 종료 코드 1. TBD 는 경고다. 확정본에서는 0 이 되어야 한다.
- 캡션 접두는 `Fig. n.`, `Figure n.`, `그림 n.` 을 모두 받는다. 저널마다 하나로 고정한다.

### academic_search.py
- 용도: 검색, DOI 검증, 인용 문자열 생성. Semantic Scholar 와 CrossRef 만 쓴다. 기억에서 서지를 쓰지 않게 하는 장치다.
- 명령:
  - `python "<KIT>/scripts/academic_search.py" search "검색어" --limit 5 [--json] [--source both|ss|cr]`
  - `python "<KIT>/scripts/academic_search.py" verify <DOI>`
  - `python "<KIT>/scripts/academic_search.py" cite <DOI> --format ijibc --ref <N>`
- 환경변수: `ACADEMIC_SEARCH_CONTACT` (CrossRef 예의 요청용 연락 문자열), `SEMANTIC_SCHOLAR_API_KEY` (선택).
- 종료 코드: 0 성공, 1 DOI 없음 또는 형식 오류, 2 사용법 오류, 3 조회 실패 (네트워크, 시간 초과). 3 은 DOI 가 틀렸다는 뜻이 아니므로 나중에 다시 실행한다.
- 인용 형식은 IJIBC 만 구현돼 있다. 다른 저널 형식은 함수를 추가한다.

### transcribe_meeting.py
- 용도: 긴 녹음을 겹치는 청크로 나눠 병렬 전사한다. 청크마다 체크포인트를 저장하므로 중단돼도 이어서 돈다.
- 명령: `python "<KIT>/scripts/transcribe_meeting.py" 녹음.m4a --tag 작업명 --out-dir "<작업 폴더>" --terms "전문 용어, 쉼표 구분"`
- 주요 옵션: `--plan-only` (청크 계획만 출력), `--chunks 1` (단일 스트림), `--model` (기본 small 또는 환경변수 `WHISPER_MODEL`), `--language ko`, `--chunk-sec 480`, `--workers`, `--ffmpeg <경로>`.
- 출력: `<작업명>_<모델>.txt` (`[mm:ss] 텍스트`) 와 `_segments.json`. 작업 폴더 기본값은 `<out-dir>/_work/<tag>` 이며 `.gitignore` 에 넣는다.
- 필요 조건: ffmpeg, CPU 에서 실행된다. 첫 실행 때 모델을 내려받는다.
- 주의: 전사 품질은 낮을 수 있다. 고유명사와 전공 용어는 `--terms` 로 알려 준다. 해석은 원음 시각으로 확인한다.

### check_figure_print.py
- 용도: 그림의 인쇄 기준 판정.
  - PNG 픽셀 폭 게이트: `--png 그림.png` (기본 인쇄 폭 368pt, 300dpi, 게이트 1534px).
  - 실효 글자 크기: `--font-px 37 --canvas-px 1700 --print-width-pt 368` (가장 작은 글자가 8pt 이상이어야 PASS).
  - 흑백 미리보기: `--gray-out 미리보기.png`. 투명 픽셀이 있으면 경고한다.
- 판정은 가장 작은 글자 기준이다. 중앙값으로 판정하지 않는다.
- 인쇄 폭이 다르면 `--print-width-pt` 로 명시한다. 예: 2단 논문지의 전체 본문 폭 485pt, 단 하나의 폭 232.5pt (저널 규정에서 확인한다).

### verify_dot_order.py
- 용도: Graphviz 가 `rank=same` 블록이나 평면 체인의 노드 순서를 바꾸는 문제를 좌표로 검사한다. 눈으로 PNG 를 보는 것보다 확실하다.
- 명령: `python "<KIT>/scripts/verify_dot_order.py" 그림.dot --nodes "AF-1,AF-2,AF-3,AF-4" [--order y|x] [--layout dot]`
- 기대 순서(`--nodes`)는 위에서 아래(또는 왼쪽에서 오른쪽)로 적는다. 좌표가 같으면 추측하지 않고 종료 코드 2.
- `dot` 위치: `--dot-bin`, 환경변수 `GRAPHVIZ_DOT`, PATH, 기본 설치 경로 순으로 찾는다.
- 오프라인 검사: `--plain-file` 에 `dot -Tplain` 출력 파일을 주면 `dot` 없이 검사한다.

### render_html_figure.py
- 용도: 계층 표, 확률 트리, 대비 도식 같은 HTML/CSS/SVG 그림을 고배율 PNG 로 렌더한다.
- 명령: `python "<KIT>/scripts/render_html_figure.py" fig.html fig.png --selector ".container" --scale 3 --bg white`
- 기본값: 배율 3, 뷰포트 1700×1200, 선택자 `.container` (없으면 전체 화면). 폭이 `--min-width` (기본 1534px) 보다 작으면 종료 코드 2.
- Chromium: `python -m playwright install chromium` 을 한 번 실행하거나 `--chromium-path` (환경변수 `CHROMIUM_PATH`) 로 기존 브라우저를 준다.
- 주의: 같은 이름의 PNG 를 덮어쓴다. 확정본은 새 이름으로 낸다.

### paper_style.py
- 용도: matplotlib 데이터 플롯 프리셋 (Okabe-Ito 색각 안전 팔레트, 세리프 글꼴, 한글 대체 글꼴). SVG 와 PNG (300dpi)를 함께 저장한다.
- 사용:

  ```python
  import sys; sys.path.insert(0, "C:/.../kim-paper-kit/scripts")
  import paper_style
  fig, ax = paper_style.new_figure(16, 9)   # 가로, 세로 (cm)
  # ... 그리기 ...
  paper_style.save(fig, "fig9_metric")      # FIG_ROOT/figures_svg, figures_png 에 저장
  ```

- 출력 위치: 환경변수 `FIG_ROOT`, 없으면 현재 폴더. 같은 이름은 덮어쓴다.
- 도식 (트리, 매트릭스, 계층 표)에는 이 팔레트를 쓰지 않는다. 검정, 빨강 하나, 회색 두 단계 규칙을 쓴다 (`kim-paper-figures` 의 figure-style.md).

### extract_pdf_figures.py
- 용도: PDF 의 내장 이미지를 뽑는다. 투명 마스크 (SMask)를 흰 배경에 합성한다. 합성하지 않으면 투명 부분이 검게 나와 검은 글자와 선이 사라진다.
- 명령:
  - `python "<KIT>/scripts/extract_pdf_figures.py" paper.pdf out_dir --images`
  - `python "<KIT>/scripts/extract_pdf_figures.py" paper.pdf out_dir --render-pages 3,5 --dpi 190`
  - `python "<KIT>/scripts/extract_pdf_figures.py" paper.pdf out_dir --render-pages 4 --dpi 520 --clip 50,80,550,400`
- 스캔 PDF (텍스트 층 없음)는 `--render-pages` 로 PNG 를 만들어 직접 본다. 서브에이전트에 판독을 맡기지 않는다.

### pdf_page_audit.py
- 용도: 조판 시험 PDF 의 쪽별 빈칸 (쪽 아래 빈 높이, pt) 을 잰다. 쪽수 맞춤의 첫 단계다.
- 명령:
  - `python "<KIT>/scripts/pdf_page_audit.py" trial.pdf --flag 100` (기본 본문 하단 기준은 쪽 높이 − 72)
  - `--bottom 770 --top 60` (여백에 맞춘 기준선)
  - `--columns 2 --flag 100` (2단 논문지)
  - `--ignore "문구"` (첫 쪽 각주 등 제외)
  - `--spans "Abstract"` (해당 문구의 글꼴, 크기, 굵기, 색 출력. 게재본 기준값과 대조)

### word_com_template.py
- 용도: Word COM 조판 골격. 단락, 그림 (지연 배치), 표 (열 폭), 수식 (1×2 무테두리 표), 구역, 머리말 PAGE 필드, 새 이름 저장.
- 사용: 템플릿 파일을 인자로 받아 `open_word(template, scratch_dir)` 로 사본을 연다. 저장은 `save_new(doc, out_path)` (PDF 도 함께 낸다), 종료는 `close_word(word, doc)`.
- 자체 점검: `python "<KIT>/scripts/word_com_template.py" --selftest` (Word 없이 순수 함수와 지연 배치 큐를 검사한다).
- 필요 조건: Windows, 정식 Microsoft Word, pywin32, Pillow.
- 주의: Word COM 호출부 (표, 그림, 수식, 머리말)는 selftest 로 검사되지 않는다. 처음에는 scratch 폴더에서 시험 조판하고 PDF 를 눈으로 확인한다. `kill_word()` 는 `taskkill /f /im WINWORD.EXE` 를 실행하므로 열린 Word 창의 저장 안 된 내용이 사라진다. 실행 전에 사용자 확인을 받는다.

### render_deck.py
- 용도: PowerPoint COM 으로 덱을 PDF 와 쪽별 PNG 로 내보낸다 (검수용). LibreOffice 는 쓰지 않는다.
- 명령: `python "<KIT>/scripts/render_deck.py" deck_kowrap.pptx "<scratch>/render" [--dpi 110]`
- 새 PowerPoint 인스턴스를 띄우고 그 인스턴스만 종료한다. 사용자가 연 프레젠테이션은 건드리지 않는다.
- `--kill-ppt` 는 모든 POWERPNT.EXE 를 강제 종료한다. 저장 안 된 작업이 사라지므로 사용자 확인 후에만 쓴다.

### deck_korean_wrap.py
- 용도: pptxgenjs 가 만든 덱의 모든 런, 표 셀, 발표자 노트의 언어를 `ko-KR` 로 바꾼다. 한글이 글자 단위로 쪼개지는 문제를 막는다 (`en-US` 태그가 원인이었다).
- 명령: `python "<KIT>/scripts/deck_korean_wrap.py" deck.pptx` → `deck_kowrap.pptx` 를 만든다. 원본은 건드리지 않는다.
- 생성 후 `render_deck.py` 로 검수한다.

## 외부 프로그램 (pip 가 아닌 것)

| 프로그램 | 쓰는 스크립트 | 설치 힌트 |
|---|---|---|
| ffmpeg | transcribe_meeting.py | `winget install Gyan.FFmpeg`, 또는 `--ffmpeg <경로>` |
| Graphviz `dot` | verify_dot_order.py, 그림 생성 | Graphviz 설치 후 PATH 또는 `GRAPHVIZ_DOT` |
| Chromium (Playwright) | render_html_figure.py | `python -m playwright install chromium` |
| Microsoft Word (정식) | word_com_template.py | Windows 에서만 동작 |
| Microsoft PowerPoint | render_deck.py | Windows 에서만 동작 |
| Node.js + pptxgenjs | PPT 생성 (스크립트 외부) | `npm install pptxgenjs` |
| 한글 글꼴 | Word 조판 | 저널 지정 글꼴 설치 |

## 알려진 한계

- `verify_dot_order.py` 에 존재하지 않는 `--plain-file` 경로를 주면 Python 예외 메시지가 그대로 나온다. 경로를 확인한다.
- 이 키트는 Windows 와 Word 를 전제로 만들었다. 다른 OS 에서는 COM 스크립트를 쓸 수 없다.
- `render_html_figure.py`, `render_deck.py`, `extract_pdf_figures.py`, `pdf_page_audit.py` 의 실제 실행은 이 키트의 점검에서 확인하지 못했다. 첫 사용 때 scratch 폴더에서 결과를 본다.
