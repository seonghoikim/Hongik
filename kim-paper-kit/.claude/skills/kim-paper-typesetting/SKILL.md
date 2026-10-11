---
name: kim-paper-typesetting
description: 논문 원고(Markdown)를 Word COM 으로 저널 양식(TIIS, 정보처리학회 논문지·학회지, IJIBC)의 DOCX·PDF 로 조판하고, 쪽수 맞춤, 표 열 폭, 그림 배치, 수식 표, 리비전 답변서, PPT 한글 줄바꿈을 처리할 때 사용한다. 조판, Word COM, pywin32, 저널 양식, 2단, 쪽수, 빈칸, 지연 배치, 열 폭, 수식 표, 리비전, 답변서, pptxgenjs, 한글 줄바꿈 같은 요청에 적용한다.
---

# 논문 조판 (Word COM)

이 스킬은 **조판** 영역만 다룬다. 문체와 내용, 그림 제작은 키트의 다른 스킬을 따른다.
규칙마다 근거(실제 사고 또는 게재본 실측)를 적었다. 근거가 빠진 항목은 시험 조판으로 확인한다. 근거를 모르면 규칙을 바꾸지 말고 확인한다.

용어: **조판기**는 원고 소스(Markdown)를 읽어 DOCX·PDF 를 만드는 스크립트다. **게재본**은 저널에 실제로 실린 PDF 다. 양식의 기준이다. **쪽별 빈칸**은 쪽 맨 아래에 남은 여백이다. 본문 근거에 나오는 `v25`, `v27` 같은 표기는 원천 빌드 스크립트의 버전이다. 키트에는 그 스크립트가 없으므로 근거 설명으로만 읽는다.

---

## 0. 시작 전 확인

| 확인 항목 | 이유 | 상세 |
|-----------|------|------|
| Windows, 정식 Microsoft Word, pywin32 | COM 은 이 조건에서만 동작한다 | `references/environment.md` §1 |
| 대상 간행물 확정 (학회지 / 논문지 / 영문 저널) | 같은 학회라도 양식이 다르다. 나중에 바꾸면 전면 재작업이다 | `references/journal-formats.md` §0 |
| 공식 템플릿과 게재본 PDF | 치수, 색, 머리글은 실측으로만 정한다 | `references/journal-formats.md` §0 |
| 한글 글꼴 설치 | 없으면 대체 글꼴로 조판되어 양식이 틀어진다 | `references/environment.md` §3 |
| 산출물 새 이름 | 기존 파일은 덮어쓰지 않는다 | `references/shell-pitfalls.md` §2 |

**검증 상태 고지**: `word_com_template.py` 의 순수 함수(열 폭, 버전 이름, 제어문자, 인라인 파서, 그림 높이 추정)와 `DeferredQueue`(가짜 기록기로 검사)는 `--selftest` 로 검증됐다. Word COM 호출부(표, 그림, 수식, 머리말)와 PowerPoint 렌더는 키트를 만든 환경에서 실행 검증하지 못했다. 첫 실행은 scratch 폴더에서 하고, 결과를 눈으로 확인한 뒤 확정본을 만든다.

---

## 1. 작업 규율 (모든 단계에 적용)

1. **덮어쓰기 금지.** 산출물은 `_v{번호}` 또는 타임스탬프가 붙은 새 이름으로 만든다. (`next_versioned_path()`, `save_new()`)
2. **원본은 읽기만 한다.** 원고 소스, 공식 템플릿, 게재본 PDF 는 조판 중에 고치지 않는다. 템플릿은 작업 사본으로 복사해 쓴다.
3. **시험은 scratch, 확정은 build.** 시험 조판과 임시 파일은 scratch 폴더에 둔다.
4. **Office COM 은 한 번에 하나.** Word 와 PowerPoint 를 병렬로 돌리지 않는다.
5. **taskkill 은 사용자 작업을 지운다.** `taskkill /f /im WINWORD.EXE` 는 열린 Word 창의 저장 안 된 내용을 날린다. 실행 전에 사용자에게 확인한다.
6. **백슬래시 코드는 heredoc 으로 만들지 않는다.** heredoc 이 `\t`, `\f` 를 실제 제어문자로 저장해 수식이 깨졌다. Write 로 파일을 만든 뒤 실행한다.
7. **한글 출력**: 파이썬 스크립트 첫머리에 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
8. **nul 파일 금지**: bash 에서는 `>/dev/null`. bash 에서 `>nul` 을 쓰면 `nul` 파일이 생겨 git 이 멈춘다. `>nul` 은 cmd.exe 를 거치는 경우(예: Python `os.system` 안)에만 쓴다. PowerShell 은 `$null`.
9. **끝나면 체크리스트로 보고한다** (§10).

---

## 2. 조판 절차 (원고 → 확정본)

1. **소스 점검**: `python "<KIT>/scripts/check_source.py" <sec*.md>` 로 오류 0 을 만든다. (`references/source-pipeline.md` §10)
2. **템플릿 열기**: `open_word(template, scratch_dir)` 로 사본을 열고 본문을 비운다. 스타일과 머리글·바닥글은 템플릿 것을 쓴다.
3. **기록**: `Typesetter` 로 전면부 → 본문 순서로 기록한다.
   - 표: `plan_widths()` 로 열 폭을 먼저 계산하고 `table()` 에 넘긴다.
   - 수식: `equation()` 으로 1×2 무테두리 표에 넣는다.
   - 그림: `picture()` 로 표시 폭을 지정한다. 바로 넣을 수 없으면 `DeferredQueue` 에 보류하고, 완결 문단 경계에서 `flush()` 한다 (`references/page-fitting.md` §4).
4. **뒷부분**: 참고문헌, 저자 약력, 머리글·바닥글(PAGE 필드 보존), 문서 끝 단락 1pt.
5. **저장**: `save_new(doc, build/<새 이름>.docx)` 로 새 이름에 저장하고 PDF 를 내보낸 뒤 `close_word()` 로 닫는다.
6. **측정**: `pdf_page_audit.py` 로 쪽별 빈칸을 재고, `--spans` 로 제목·헤딩·인용·캡션의 글꼴, 굵기, 색을 게재본 기준값과 대조한다.
7. **눈 검수**: 렌더 PNG 로 쪽 끝 잘림, 캡션 분리, 수식 잘림, 표가 쪽을 가르는 위치를 확인한다.

---

## 3. Word COM 필수 규칙 (요약)

| # | 규칙 | 한 줄 이유 | 상세 |
|---|------|------------|------|
| 1 | 단락은 본문 끝(마지막 단락 기호 직전)에만 쓴다. `Collapse(0)` + `InsertParagraphAfter` 패턴은 쓰지 않는다 | 다음 헤딩에 본문이 흡수된다. 프로젝트 문서에 이 패턴이 예시로 적혀 있어도 이 규칙을 따른다 | word-com-rules §1 |
| 2 | 런은 삽입 직후 `Font.Reset()`, 그다음 요청된 속성(볼드·이탤릭·색)만 준다 | `Bold = 0` 같은 명시 할당은 스타일의 색과 볼드를 죽인다 (8판본 잠복) | §2 |
| 3 | 서식은 텍스트를 찍을 때 건다. 완성된 문서에 Find 루프로 서식을 걸지 않는다 | 재페이지네이션이 누적되어 97분 대 8분 차이가 났다 | §3 |
| 4 | 한글 표와 제목은 WordWrap=True. 2단 본문은 저널 실측으로 정한다 | 기본값(False)은 한글 낱말을 글자 단위로 쪼갠다 | §4 |
| 5 | 표 열 폭은 자동 맞춤에 맡기지 않는다. 하한을 먼저 주고 배분한다 | 한글은 한 글자까지 눌려 세로로 쪼개진다 | §5 |
| 6 | 그림은 표시 폭을 무조건 지정한다. 그림 단락에 고정 줄 간격을 주지 않는다 | 2단에서 Word 가 단 폭으로 줄이고, 고정 간격은 그림을 잘라 낸다 | §8 |
| 7 | 수식은 테두리 없는 1×2 표에 넣는다. 짝 없는 ASCII 절댓값 기호는 `∣`(U+2223)로 바꾼다 | BuildUp 이 단락 경계를 삼켜 다음 문장이 잘린다 | §6 |
| 8 | 머리말을 `Range.Text` 로 덮으면 PAGE 필드가 사라진다. 덮은 뒤 필드를 다시 넣는다 (`header_with_page()`) | 쪽 번호가 빠진 채 인쇄된다 | §7 |
| 9 | `Find.Execute(Replace)` 결과를 믿지 않는다. 치환 뒤 다시 찾아 확인한다 | 일부 문자열을 소리 없이 건너뛴다 | §9 |
| 10 | Selection 으로 이어 붙이면 `EndKey` 가드를 건다 | Selection 이 문서 머리로 튀어 표지 앞에 본문이 들어갔다 | §10 |
| 11 | 학위논문 양식: 고정 줄 간격, TOC 키워드 인자, 쪽번호 3구간을 조심한다 | 각각 실제 사고가 있었다 | §11 |

---

## 4. 쪽수 맞춤 (요약)

- **본문부터 줄이지 않는다.** 먼저 쪽별 빈칸을 잰다. 빈칸은 대개 조판 원인이다. 본문을 줄여도 빈칸에 흡수되면 쪽수가 그대로다 (예: 한 TIIS 원고에서 본문 900자를 줄이고도 21쪽이 유지되다가, 조판 수정 뒤 20쪽이 되었다).
- **순서**: ① 표 열 폭 → ② 그림 지연 배치 → ③ 묶음 속성(KeepWithNext) 정리 → ④ 문서 끝 빈 단락 제거 → ⑤ 묶음은 표시한 표에만 → ⑥ 마지막에 본문 축약.
- **그림은 줄이지 않는다.** 그림 속 글자가 인쇄에서 읽히지 않는다. 쪽수 초과는 본문으로 해결한다.
- **지연 배치 조건**: 남은 높이 ≥ 그림 + 캡션 + 여유일 때만 넣는다. 완결 문단 뒤에서만 넣는다. 수식 뒤 소문자로 시작하는 줄, 표 바로 앞, 정의 도입 줄("…하면:") 뒤에는 넣지 않는다.
- **2단 전폭 그림**: 1단 구역으로 전환하고, 연속 구역 나누기가 만드는 균형 잔여 높이를 추정해 넣는다.
- 상세: `references/page-fitting.md`

---

## 5. 원고 소스 규칙 (요약)

- **파일 분할**: 전면부, 본문 절 파일들, `refs.md`, (리비전이면) `response.md`. 조판기가 순서대로 읽는다.
- **헤딩**: `N.` 은 절, `N.M` 은 소절이다. `References`, `Acknowledgement`, `Author Profile`, `Appendix` 는 절이다. 그 밖의 헤딩은 조판에서 건너뛴다.
- **그림**: 본문에 `[[FIGURE n]]` 한 줄, 바로 다음 줄에 `**Fig. n.** 캡션.` 캡션은 마침표로 끝낸다. 토큰 이름과 캡션 접두(`Fig. n.` 또는 `Figure n.`)는 저널과 프로젝트마다 하나로 고정한다. `check_source.py` 는 세 가지 접두를 모두 받는다.
- **표**: 파이프 표. 행마다 파이프 수가 같아야 한다. 셀 안 수식의 절댓값은 `\mid` 로 쓴다.
- **수식**: `$$ … \tag{n} $$`. 번호는 `\tag` 로 쓴다.
- **색 규정**: 인용 `[N]` 은 빨강, 본문 그림·표 참조는 파랑 굵게 (TIIS 게재본 실측). 조판 계층이 자동으로 입힌다. 소스에 색을 쓰지 않는다. 저널이 색을 요구하지 않으면 이 규정을 적용하지 않는다.
- **리비전**: `{+ … +}`, 표 전체는 `<!-- REV-TABLE -->`, 수식은 `{+$$ … $$+}`.
- **자리표시**: `‹TBD: …›` 는 노란 형광으로 강조된다. 제출 전에 모두 확정한다.
- 상세: `references/source-pipeline.md`

---

## 6. 저널 양식 (요약)

약어: **TIIS** = KSII 가 발행하는 영문 저널(KSII Transactions on Internet and Information Systems). **TKIPS** = 정보처리학회 논문지(2단). **정보처리학회지** = 회원 기고 학회지(1단). **IJIBC** = 영문 저널.

| 간행물 | 핵심 (실측 근거 있음) | 상세 |
|--------|------------------------|------|
| TIIS (영문, A4) | 13–21쪽. 인용 빨강 11pt(굵지 않음). 그림·표 참조 파랑 굵게. 섹션 헤딩 보라 12pt Arial 굵게. Copyright 줄은 머리글 2행. 약력 전원 필수. 참고문헌 게재본 실측 25–79개 | `journal-formats.md` §1 |
| 정보처리학회 논문지 TKIPS (2단) | 영문 제목·저자·ABSTRACT·Keywords 가 먼저, 국문은 그다음, 본문 2단. 본문 신명조 9pt 줄 14.2pt 정확히. 장 번호는 `1.`→`1.1`→`1)`→`a)`. 그림·표 제목은 영문(그림 아래, 표 위). 2단 본문 WordWrap=False | `journal-formats.md` §2 |
| 정보처리학회지 (1단, 기고) | 초록·영문 제목 없음. 장 제목 "1. 서 론". 캡션은 한글 `<표 1>`, `(그림 1)`. 서론은 소절 없이 한 흐름 | `journal-formats.md` §3 |
| IJIBC (영문) | 교수님 제출본 양식을 base 로 새 판을 만든다. 캡션 `Figure N. 설명.` | `journal-formats.md` §4 |

- 가이드 문서의 치수가 재단 치수일 수 있다. 공식 템플릿의 페이지 설정을 그대로 쓴다.
- 게재본과 교수님 샘플이 다르면 게재본을 기준으로 두고 교수님께 확인한다.

---

## 7. 리비전과 답변서 (요약)

- 수정 문장은 파랑 굵게, 수정 안의 인용은 빨강을 유지한다.
- 구조: **답변서(첫 구역) → 다음 쪽 구역 나누기 → 원고(쪽 번호 1부터)**. 머리글·바닥글은 두 구역을 끊어서 따로 준다.
- 답변서 쪽수 = 원고 첫 쪽의 절대 쪽 번호 − 1. 원고 쪽수는 전체에서 답변서를 뺀다.
- 이 키트 문서에는 심사평 원문을 싣지 않는다. 답변서에 코멘트를 넣을지는 저널 지침을 따른다. 조판기는 `response.md` 의 `@COMMENT` 줄을 형식(라벨 굵게, 본문 이탤릭 회색, 들여쓰기)대로 조판한다.
- 상세: `references/revision-and-response.md`

---

## 8. PPT 덱 (요약)

- 생성(pptxgenjs) 직후 `deck_korean_wrap.py` 로 모든 글자 런, 표 셀, 문단 끝 표시, 발표자 노트의 언어를 `ko-KR` 로 바꾼다.
- 이유: `en-US` 런은 한글을 글자 단위로 끊는다. `eaLnBrk` 와 `WordWrap` 은 효과가 없었고, 언어 태그만 효과가 있었다 (2026-10-06 실험).
- 검수: `render_deck.py` 가 PowerPoint COM 으로 PDF 와 쪽별 PNG 를 만든다. LibreOffice 는 쓰지 않는다. 새 PowerPoint 인스턴스를 띄우므로 사용자가 열어 둔 파일은 닫히지 않는다. `--kill-ppt`(모든 POWERPNT.EXE 강제 종료)는 사용자 확인 후에만 쓴다.
- 상세: `references/pptx-decks.md`

---

## 9. 셸과 환경 함정 (요약)

- **heredoc 백슬래시**: `\t`, `\f`, `\to`, `\frac` 가 제어문자로 저장된다. 패치 파일은 Write 로 만든다.
- **`>nul` 파일**: bash 에서 만든 nul 파일이 `git add` 를 죽여 자동 백업이 13일간 멈췄다. 삭제는 `[System.IO.File]::Delete('\?\…\nul')` 로 한다.
- **`| tail` 버퍼링**: 장시간 작업의 진행을 가린다. `python -u` 와 로그 파일을 쓴다.
- **taskkill**: 사용자의 Office 창을 닫는다. 실행 전 확인한다.
- **한컴 뷰어만 있는 PC**: HWP OLE 조판이 안 된다. 정식 한글이나 웹 한글 편집기(대안, 함정 많음)를 쓴다.
- 상세: `references/shell-pitfalls.md`, `references/environment.md`, `references/hwp-web-pitfalls.md`

---

## 10. 완료 체크리스트 (보고 형식)

- [ ] 산출물은 새 이름이고, 이전 판과 원고 소스는 그대로다
- [ ] `check_source.py` 오류 0 (확정본은 TBD 경고 0)
- [ ] 쪽수가 저널 범위 안이다 (본문과 답변서를 나눠 셌다)
- [ ] `pdf_page_audit.py` 에서 빈칸 기준 이상인 쪽이 없거나, 사유를 적었다
- [ ] `--spans` 로 제목, 헤딩, 인용, 캡션의 색과 굵기를 게재본 기준값과 대조했다
- [ ] 첫 쪽: 저널이 요구하는 표제 요소(TIIS 는 copyright 머리글, 사사, DOI·ISSN 줄, 교신저자 표기)가 있다
- [ ] 표: 글자가 세로로 쪼개지지 않고, 쪽을 넘는 머리 행이 반복된다
- [ ] 수식: 렌더에서 잘림이 없다. 이탤릭으로 남은 수식은 따로 확인했다
- [ ] 그림: 본문 폭을 유지했고, 캡션이 그림과 붙어 있다
- [ ] PPT: ko-KR 후처리 후 렌더 검수를 했다
- [ ] taskkill 과 덮어쓰기 대상처럼 사용자 확인이 필요한 항목은 확인을 받았다

---

## 11. 스크립트 (`scripts/`)

모든 스크립트는 경로를 인자로 받는다. `<KIT>` 는 키트 루트의 절대 경로로 바꿔 쓴다.

| 파일 | 용도 | 사용 예 |
|------|------|---------|
| `word_com_template.py` | Word COM 골격. `Typesetter`(단락·그림·표·수식·구역), `DeferredQueue`(그림 지연 배치), `plan_widths()`(열 폭), `estimate_balanced_bottom()`(2단 잔여 높이), `next_versioned_path()`(버전 이름), `scan_control_chars()` | `python "<KIT>/scripts/word_com_template.py" --selftest` |
| `pdf_page_audit.py` | 쪽별 빈칸 측정, 글꼴·색 실측 | `python "<KIT>/scripts/pdf_page_audit.py" trial.pdf --flag 100` · `--spans "Abstract"` |
| `check_source.py` | 원고 소스 점검 (제어문자, 표 열 수, 셀 안 리터럴 파이프 기호, 리비전 짝, 그림 캡션, TBD) | `python "<KIT>/scripts/check_source.py" sec1_front.md sec2.md` |
| `deck_korean_wrap.py` | PPT 한글 언어 태그 후처리 (슬라이드, 표, 노트. 새 파일로 저장) | `python "<KIT>/scripts/deck_korean_wrap.py" deck.pptx` |
| `render_deck.py` | PowerPoint COM 으로 PDF 와 쪽별 PNG 를 만든다 (검수). `--kill-ppt` 는 사용자 확인 후에만 | `python "<KIT>/scripts/render_deck.py" deck_kowrap.pptx "<scratch>/render"` |

조판기 골격 예 (의사 코드):
```python
import sys; sys.path.insert(0, "<KIT>/scripts")
from word_com_template import (kill_word, open_word, save_new, close_word, Typesetter,
                               plan_widths, DeferredQueue, figure_block_height, CM)

kill_word()                                     # 사용자 확인 후
word, doc, work = open_word("<템플릿>.docx", "<scratch>")
ts = Typesetter(word, doc)
ts.para("**굵은 제목**", style="제목1")          # 스타일 이름은 템플릿에 있는 이름을 쓴다
widths, ok = plan_widths(grid, total_pt=411)    # ok=False 면 글자 쪼개짐 위험
ts.table(grid, widths, style_header="table title", style_cell="table text", keep_rows=2)
dq = DeferredQueue(ts, body_bottom=765.9)       # 본문 하단 기준선(pt), 여백에 맞춘다
h = figure_block_height(411, iw, ih)            # 그림 블록 높이 추정 (iw, ih: PIL 로 읽은 픽셀 크기)
dq.offer(h, lambda: ts.picture("<그림>.png", width_pt=411), label="Fig. 3")
dq.flush()                                      # 완결 문단 경계마다 호출
dq.flush(force=True)                            # 참고문헌 전에 강제 배출
out = save_new(doc, "<build>/paper.docx")       # 새 이름 + PDF
close_word(word, doc)
```

---

## 12. 참고 문서 찾기

| 상황 | 읽을 문서 |
|------|-----------|
| Word COM 코드를 짜거나 고칠 때 | `references/word-com-rules.md` |
| 원고 소스 형식, 헤딩, 색 규정, 수식 변환 | `references/source-pipeline.md` |
| 쪽수 초과, 빈칸, 그림 배치 | `references/page-fitting.md` |
| 저널 양식 규격, 색, 글꼴, 첫 쪽 구조 | `references/journal-formats.md` |
| 리비전 원고, 답변서 구조 | `references/revision-and-response.md` |
| PPT 덱 생성과 검수 | `references/pptx-decks.md` |
| 셸 명령, 파일 규율 | `references/shell-pitfalls.md` |
| 설치, 필요 조건, 글꼴 확인 | `references/environment.md` |
| 웹 한글 편집기 자동화 | `references/hwp-web-pitfalls.md` |

---

## 13. 교수님 컨펌에서 확인된 조판 기준

- **그림은 본문 폭 100%.** 쪽수를 맞추려고 그림을 줄이지 않는다. 그림 글자가 안 읽히면 논문을 그림만으로 읽는 독자에게 전달되지 않는다 (저자 지시, 2026-09-30. 교수님이 그림만으로 논문을 읽으신다는 점이 근거다).
- **쪽수 초과는 본문 축약으로 푼다.**
- **학회지 기고의 서론은 소절 없이 한 흐름으로 쓴다.** 교수님이 1.1, 1.2 로 나누는 것을 원하지 않으셨다 (2026-10-01 확정).
- **양식과 게재본이 어긋나면** 게재본을 기준으로 하고, 어긋난 점을 교수님께 확인받는다.
