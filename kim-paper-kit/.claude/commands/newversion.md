---
description: 논문의 다음 버전 파일(_vN)을 만들고 요청한 수정을 적용한다 (DOCX는 Word COM, Markdown 원고는 패치 파일)
argument-hint: "[수정 요청 내용]"
---

논문의 새 버전을 만든다. 규칙은 키트 스킬 `kim-feedback-loop` (`references/versioning.md`)과
`kim-paper-typesetting` (`references/word-com-rules.md`)을 따른다. 작업 전에 두 문서를 읽는다.

## 경로 변수

- `<KIT>`: 키트 루트의 절대경로. 프로젝트 CLAUDE.md 에 적혀 있다.
- `<PROJECT>`: 논문 작업 폴더. 프로젝트 CLAUDE.md 에 적혀 있다.
- `<PAPER>`: 논문 파일의 공통 이름 (예: `paper_title`). 프로젝트 CLAUDE.md 에 적혀 있다.

## 절차

1. **최신 판본 찾기**
   - `<PROJECT>` 에서 `<PAPER>_v{NN}.docx` 또는 `<PAPER>_v{NN}.md` 중 번호가 가장 큰 파일을 찾는다.
   - 버전 이력 문서가 있으면 그 문서의 정본 표기를 우선한다.
2. **다음 번호 정하기**
   - 예: `v07` → `v08`. 기존 파일 이름과 겹치지 않는지 확인한다.
   - 원본은 읽기만 한다. 사본을 만들어 그 사본에 작업한다.
3. **DOCX 편집 (Word COM 만)**
   - pywin32 Word COM 만 쓴다. JSZip, docx 라이브러리, XML 직접 수정은 쓰지 않는다.
   - 작업 전 `taskkill /f /im WINWORD.EXE` 를 실행하면 열린 Word 창의 저장 안 된 내용이 사라진다. 실행 전 사용자에게 확인을 받는다.
   - 골격은 `<KIT>/scripts/word_com_template.py` 의 `kill_word()`, `open_word(template, scratch_dir)`, `save_new(doc, out_path)`, `close_word(word, doc)` 를 쓴다.
   - 스크립트 첫머리에 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` 를 둔다.
   - 시험 결과는 scratch 폴더에서 확인한 뒤 확정본을 만든다.
4. **Markdown 원고 편집**
   - 수정은 패치 스크립트 파일로 적용한다 (Write 로 만든 뒤 실행). 직접 편집보다 재현과 롤백이 쉽다.
   - 백슬래시가 든 수식은 heredoc 으로 넣지 않는다. `\t`, `\f`, `\frac` 가 제어문자로 바뀐다.
5. **저장**
   - DOCX 는 `SaveAs2` 또는 `save_new` 로 새 이름에 저장한다.
   - 기존 파일은 덮어쓰지 않는다.
6. **자가 검사**
   - Markdown 원고: `python "<KIT>/scripts/check_source.py" <원고.md>` 로 오류 0 을 만든다.
   - 린트: `python "<KIT>/scripts/style_lint.py" <원고.md>` 로 error 를 고친다.
   - 수치와 인용 번호를 원천과 대조한다. 확인하지 못한 항목은 "미확인"으로 적는다.
7. **보고**
   - 체크리스트로 보고한다.
   - 새 파일 절대경로, 이전 판과의 차이 (절·표·그림 단위), 확인하지 못한 항목을 적는다.

## 금지

- 기존 파일 덮어쓰기.
- XML 직접 수정, JSZip 으로 DOCX 열기.
- 사용자 확인 없이 `taskkill` 실행.

수정 요청: $ARGUMENTS
