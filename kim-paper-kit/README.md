# kim-paper-kit: 연구실 컨펌 기준 논문 작성 키트

버전 v1 (2026-10-10) · Claude Code 스킬 4종 + 명령 3종 + 스크립트 13종 + 원고 틀 2종

지도교수 컨펌을 받으며 쌓은 논문 작성 노하우를 Claude Code 스킬로 묶었다. 구성, 정의와 문체, 그림, 조판, 피드백 처리 규칙을 담았고, 이 키트를 자기 프로젝트에 넣으면 같은 기준으로 원고를 쓰고 고치고 검수할 수 있다.

- 기준의 출처: 김영철 교수님(홍익대 소프트웨어융합학과) 연구실의 컨펌 기록. 박사과정 프로젝트의 피드백 이력과 실제 조판·그림 작업에서 일반화했다.
- 예시 수치와 사례는 원천 프로젝트(가상환경 시나리오 기반 통합 테스트, SBIT-VE)의 것이다. 규칙만 가져가고 예시는 자기 연구의 것으로 바꾼다.
- 저자 개인의 경로, 계정, 연락처는 키트에 없다. 자리표시(`<KIT>`, `<PROJECT>`)로 바꿔 쓴다.

## 1. 무엇을 담았나

| 구성 | 위치 | 내용 |
|---|---|---|
| 스킬 4개 | `.claude/skills/` | 논문 작성, 그림, 조판, 피드백 루프 (아래 표) |
| 명령 3개 | `.claude/commands/` | `/feedback` (음성 피드백), `/newversion` (새 버전), `/stylechk` (스타일 검수) |
| 프로젝트 지침 | `CLAUDE.md.template` | 자기 프로젝트 CLAUDE.md 에 붙일 규칙 블록 |
| 도구 13개 | `scripts/` | 린트, 원고 점검, 전사, 그림 판정, Word COM 골격, PPT 후처리 등 |
| 설치 점검 | `scripts/check_env.py` | 환경이 갖춰졌는지 확인 (파일을 만들지 않는다) |
| 원고 골격 | `templates/manuscript_skeleton.md` | 박사논문 6단계 순서와 정의 4단, 초록 7단계를 담은 빈 틀 |
| 용어표 | `templates/terminology_register.md` | 확정 용어, 금칙어, 번복 이력, 전역 치환 기록을 담은 빈 표 |

| 스킬 | 다루는 일 |
|---|---|
| `kim-paper-writing` | 논문 구성, 정의 4단, Gap 논증, 초록과 결론, 영문 문체, 국문 번역체, 용어 확정, 수치와 인용, 발표 구성 |
| `kim-paper-figures` | 계층 표, 확률 트리, 행위 매트릭스, 플롯, 스크린샷, 그림 인쇄 기준, PDF 그림 추출, Word 그림 삽입 |
| `kim-paper-typesetting` | Word COM 조판, 저널 양식 (2단, 1단, 영문), 쪽수 맞춤, 표 열 폭, 수식 표, 리비전 답변서, PPT 한글 줄바꿈 |
| `kim-feedback-loop` | 음성 피드백 전사, 피드백 표와 체크리스트, 새 버전 (덮어쓰기 금지), 심사 리비전, 참고문헌 DOI 검증, 수치 추적, 연구 진실성, 서브에이전트 패턴 |

## 2. 교수님 기준의 핵심 7가지

1. **구조가 먼저다.** 방법론 장을 박사논문의 6단계 순서 (기본 단위 정의 → 배치 매트릭스 → 변환 → 사례 적용 → 메트릭과 우선순위 → 재사용)에 대응시킨다. 구조가 승인되면 구조를 바꾸지 않고 추가와 정정만 한다.
2. **정의는 4단으로 쓴다.** 정의 → 예시 → 논의 → 적용. 정의 본문에 단위의 입도 규칙(무엇을 한 단위로 자르는가)을 명시한다. 심사자는 "클릭 한 번인가, 구매 한 번인가"를 묻는다.
3. **선행연구는 인정 → However → Thus.** 선행 기여를 먼저 인정하고, 구체적인 빈 곳(gap)을 짚고, 본 연구가 그것을 채운다고 쓴다. 새로 제안한 기법은 기여 목록의 첫머리에 두고, 발표에서도 앞부분에 드러나게 한다 (R7).
4. **수치는 기준선과 함께, 산출 근거가 있는 것만.** "A = 0.772, 무작위 0.500"처럼 쓴다. 열거가 가능하면 몬테카를로 대신 전수 열거하고, "정확"과 "샘플링"을 한 문장에 쓰지 않는다.
5. **그림은 메시지 하나.** 검정 선과 글자, 빨강 하나 (핵심), 회색 두 단계. 계층 표와 확률 트리 문법을 쓰고, 공통 요소는 블록으로 떼지 않고 색으로 표시한다. 본문 폭 100%, 캡션은 제목만, 그림은 코드로 만든다 (GUI 도구와 AI 생성 이미지는 본문에 쓰지 않는다).
6. **문체는 번역체와 창작을 피한다.** 영문은 기존 문형을 재사용하고 "We propose ..."를 쓴다 (1인칭 I 금지). 국문은 덮다, 몫이다, 낳다, 세우다, 메우다, 갭 같은 번역체를 쓰지 않는다. 은유, 의인화, 질문-답 수사, 강조 부사를 걷어낸다.
7. **작업 규율: 덮어쓰지 않고, 순서를 지키고, 근거를 댄다.** 산출물은 `_v{N}` 새 이름으로 저장한다. 녹음, 전사, 피드백 표, 체크리스트, 새 버전, 자가 검사, 보고의 순서를 지킨다. 참고문헌은 DOI 를 확인한 뒤에만 추가하고, 수작업을 "자동"이라 쓰지 않는다.

## 3. 설치 방법

> zip 을 풀면 `kim-paper-kit/` 폴더가 나온다. 스킬과 명령은 숨김 폴더 `.claude/` 안에 있으므로, 탐색기에서 보이지 않으면 "숨긴 항목 표시"를 켜거나 터미널에서 복사한다. 가장 간단한 방법은 Claude Code 에게 "kim-paper-kit 의 README 대로 이 프로젝트에 설치해줘"라고 요청하는 것이다.

### ① 스킬 복사

키트의 `.claude/skills/*` 폴더 4개를 다음 중 한 곳에 복사한다.

- 프로젝트만 쓰면: `<프로젝트>/.claude/skills/`
- 모든 프로젝트에서 쓰면: `<HOME>/.claude/skills/`

### ② 명령 복사

키트의 `.claude/commands/*.md` 3개를 같은 방식으로 `.claude/commands/` 에 복사한다.

### ③ 프로젝트 CLAUDE.md 작성

`CLAUDE.md.template` 의 내용을 자기 프로젝트의 `CLAUDE.md` 에 붙이고, 모든 `<...>` 자리표시를 채운다. 특히 다음을 확인한다.

- `<KIT>`: 키트 루트의 절대경로. 스킬이 `<KIT>/scripts/` 를 호출하므로 키트를 옮기면 이 값도 고친다.
- `<PROJECT>`: 논문 작업 폴더.
- 정본 파일, 저널 양식 파일, 버전 이력 문서.
- Python 과 ffmpeg 경로 (PATH 에 있으면 비워 둔다).

### ④ 필요 프로그램과 점검

| 프로그램 | 필요한 일 | 설치 |
|---|---|---|
| Python 3.11 이상 (최소 3.10) | 모든 스크립트 | 공식 설치 |
| pywin32 + 정식 Microsoft Word | Word COM 조판, 새 버전 생성 | `pip install pywin32` (Windows 전용) |
| PyMuPDF | PDF 그림 추출, 쪽별 빈칸 측정 | `pip install pymupdf` |
| Playwright + Chromium | HTML 도식을 PNG 로 렌더 | `pip install playwright` 후 `python -m playwright install chromium` |
| faster-whisper | 음성 피드백 전사 | `pip install faster-whisper` |
| ffmpeg | 녹음 변환 | `winget install Gyan.FFmpeg`, 또는 `transcribe_meeting.py --ffmpeg <경로>` |
| Node.js + pptxgenjs | PPT 생성 (선택) | `npm install pptxgenjs` |
| requests, python-pptx, matplotlib, pillow | 참고문헌 검색, PPT 후처리, 플롯 | `pip install -r scripts/requirements.txt` |
| Graphviz (`dot`) | 그림 순서 검사, 트리 도식 | 설치 후 PATH 또는 `GRAPHVIZ_DOT` |
| PowerPoint (정식) | PPT 검수 렌더 (선택) | Windows 에서만 |
| 한글 글꼴 (저널 지정 글꼴) | 조판 양식 | 저널 안내에 따른다 |

설치 후 확인:

```
python "<KIT>/scripts/check_env.py"
```

MISSING 항목이 있으면 그 줄의 힌트를 따른다. 기능별로 필요한 것만 설치해도 된다.

## 4. 사용 예

| 요청 | 쓰이는 스킬과 도구 |
|---|---|
| "교수님 녹음 전사하고 체크리스트 만들어줘" | `/feedback`, `kim-feedback-loop`, `transcribe_meeting.py` |
| "피드백 반영해서 새 버전 만들어줘" | `/newversion`, `kim-feedback-loop` (versioning), `kim-paper-typesetting` |
| "3장 정의 절을 정의-예시-논의-적용 4단으로 고쳐줘" | `kim-paper-writing` (definitions-and-gap) |
| "초록을 7단계로 다시 써줘" | `kim-paper-writing` (abstract-and-conclusion) |
| "이 원고 연구실 기준으로 검수해줘" | `/stylechk`, `kim-paper-writing`, `style_lint.py` |
| "영문 문장을 교정해줘 (창작 말고 문형으로)" | `kim-paper-writing` (english-style) |
| "확률 트리 그림 만들어줘" | `kim-paper-figures` (tool-routing), `render_html_figure.py` |
| "PDF 논문에서 그림 뽑아줘" | `kim-paper-figures`, `extract_pdf_figures.py` |
| "저널 양식으로 DOCX 조판하고 쪽수 맞춰줘" | `kim-paper-typesetting` (journal-formats, page-fitting), `pdf_page_audit.py` |
| "심사 답변서 만들어줘" | `kim-feedback-loop` (revision-response), `kim-paper-typesetting` (revision-and-response) |
| "참고문헌 추가해줘" | `kim-feedback-loop` (references-verification), `academic_search.py verify` |
| "이 수치가 어디서 나왔는지 추적해줘" | `kim-feedback-loop` (numeric-authority) |
| "발표 PPT 한글 줄바꿈 고쳐줘" | `kim-paper-typesetting` (pptx-decks), `deck_korean_wrap.py` |
| "발표 구성을 짜줘" | `kim-paper-writing` (presentation) |

명령 세 개:

- `/feedback [녹음 경로]`: 녹음 전사 → 피드백 문서 → 우선순위 체크리스트
- `/newversion [수정 요청]`: 다음 `_vN` 파일을 만들고 수정을 적용
- `/stylechk [파일]`: 연구실 기준 7항목과 린트로 검수

## 5. 폴더 구조

```
kim-paper-kit/
├── README.md                     이 문서
├── CLAUDE.md.template            프로젝트 CLAUDE.md 에 붙일 규칙 블록
├── .claude/
│   ├── skills/
│   │   ├── kim-paper-writing/    논문 작성 (SKILL.md + references/ 11개)
│   │   ├── kim-paper-figures/    그림과 도식 (SKILL.md + references/ 7개)
│   │   ├── kim-paper-typesetting/  조판 (SKILL.md + references/ 9개)
│   │   └── kim-feedback-loop/    피드백 루프 (SKILL.md + references/ 7개)
│   └── commands/
│       ├── feedback.md
│       ├── newversion.md
│       └── stylechk.md
├── scripts/
│   ├── README.md                 스크립트별 사용법과 의존성 표
│   ├── requirements.txt          pip 의존성
│   ├── check_env.py              설치 점검
│   ├── style_lint.py             원고 린트
│   ├── check_source.py           조판용 원고 소스 점검
│   ├── academic_search.py        논문 검색과 DOI 검증
│   ├── transcribe_meeting.py     음성 전사 (청크, 체크포인트)
│   ├── check_figure_print.py     그림 인쇄 기준 판정
│   ├── verify_dot_order.py       Graphviz 노드 순서 검사
│   ├── render_html_figure.py     HTML 도식 렌더
│   ├── paper_style.py            matplotlib 프리셋
│   ├── extract_pdf_figures.py    PDF 그림 추출
│   ├── pdf_page_audit.py         쪽별 빈칸 측정
│   ├── word_com_template.py      Word COM 조판 골격
│   ├── render_deck.py            PowerPoint 검수 렌더
│   └── deck_korean_wrap.py       PPT 한글 언어 태그 후처리
└── templates/
    ├── manuscript_skeleton.md    원고 빈 틀
    └── terminology_register.md   용어표 빈 틀
```

## 6. 한계

- **지도교수 개인 기준이다.** 김영철 교수님 연구실의 컨펌 기록을 일반화했다. 다른 지도교수나 다른 분야라면 스킬의 기준 (문체 금칙, 캡션 형식, 수치 규칙)을 그 기준으로 바꿔야 한다.
- **저널마다 다르다.** TIIS, 정보처리학회 논문지, IJIBC 의 양식 실측은 예시로 들어 있다. 조판은 게재본 PDF 와 공식 템플릿으로 확인한다. 키트에는 저널 템플릿 파일이 없다.
- **Windows 와 정식 Word 를 전제한다.** Word COM 조판, PowerPoint 검수, 한글 자동화는 Windows 에서만 동작한다.
- **일부 COM 호출부는 실제 Word 에서 아직 시험하지 않았다.** 열 폭 계산, 지연 배치, 버전 이름 등 순수 함수는 `word_com_template.py --selftest` 로 검사된다. 표, 그림, 수식, 머리말 호출은 scratch 폴더에서 시험 조판 후 쓴다.
- **학위논문 조판기는 없다.** 학위논문의 장 구성 표준은 `kim-paper-writing` 의 structure.md 에 있고, 조립 함정은 `kim-paper-typesetting` 의 word-com-rules.md §11 에 있다. 학위 양식 템플릿과 조판기는 포함하지 않았다.
- **본문 그림 도구는 Blender 스크립트를 포함하지 않는다.** 3D 합성 그림을 쓰려면 별도 Blender 헤드리스 스크립트를 준비한다.
- **판단은 바뀐다.** `kim-paper-writing/references/feedback-history.md` 의 "번복된 판단"을 먼저 확인한다. 같은 지적이 다시 나오면 그 항목부터 본다.
- **책임은 저자에게 있다.** AI 가 만든 초안은 저자가 직접 읽고 고친다. 실행하지 않은 실험과 수작업은 그렇게 적고, 학습 기반이 아닌 방법을 AI 기반이라고 쓰지 않는다.
