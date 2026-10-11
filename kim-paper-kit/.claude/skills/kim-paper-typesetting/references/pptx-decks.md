# PPT 덱 생성과 검수 (한글)

발표 덱(.pptx)을 만들 때의 한글 줄바꿈 처리와 검수 절차다. 덱 내용과 발표 구성은 다른 영역 문서를 따른다.

---

## 1. 필요 조건

- 생성: pptxgenjs (Node) 로 덱을 만든다. 생성 방식은 프로젝트가 정한다.
- 후처리: python-pptx (`pip install python-pptx`).
- 검수 렌더: **Microsoft PowerPoint** (COM 으로 PDF 를 내보낸다). LibreOffice 는 쓰지 않는다. 이 환경에는 LibreOffice 가 없다는 전제다.
- PNG 변환: PyMuPDF.

## 2. 한글 줄바꿈 함정

**증상**: 한글 낱말이 줄 끝에서 글자 단위로 쪼개진다. 예: "없었/다", "따/라가지".

**원인**: pptxgenjs 는 모든 글자 런을 `lang="en-US"` 로 쓴다. PowerPoint 는 en-US 런의 한글을 글자 단위로 끊을 수 있다.

**실험 기록 (PowerPoint COM 렌더, 2026-10-06)**
| 시도 | 결과 |
|------|------|
| `a:pPr eaLnBrk="0"` | 효과 없음 |
| `ParagraphFormat.WordWrap` | 효과 없음 |
| `a:rPr lang="ko-KR"` (altLang en-US) | **낱말 단위 줄바꿈 성공** |

- 결론: 글자 런의 언어 태그를 `ko-KR` 로 바꾼다. 런, 표 셀의 런, 문단 끝 표시(endParaRPr), 발표자 노트의 런까지 모두 바꾼다.
- Word 의 한글 줄바꿈 함정(`word-com-rules.md` §4)과 증상은 같지만 원인과 해법이 다르다. Word 는 WordWrap 속성이고, PowerPoint 는 언어 태그다.

**처리**: 덱을 생성한 **직후** 후처리한다.
```bash
python "<KIT>/scripts/deck_korean_wrap.py" deck.pptx          # deck_kowrap.pptx 를 만든다
```
- 원본은 건드리지 않는다. 같은 이름이 있으면 `_v02` 처럼 새 이름을 쓴다.
- 원천 구현은 원본 파일을 직접 고쳤으므로 같은 빌드에서 막 만든 파일에만 썼다. 범용 스크립트는 새 파일을 만들어 원본을 남기지만, 덱을 생성한 직후에 한 번 적용한다는 원칙은 그대로 둔다.

## 3. 검수 렌더

```bash
python "<KIT>/scripts/render_deck.py" deck_kowrap.pptx "<scratch>/render"
```
- PowerPoint 로 PDF 를 내보내고, 쪽마다 PNG 를 만든다 (기본 110dpi).
- 출력 폴더가 이미 내용을 갖고 있으면 `_v02` 폴더를 쓴다. 이전 검수 결과를 덮어쓰지 않는다.
- `render_deck.py` 는 `DispatchEx` 로 PowerPoint 를 새 인스턴스로 띄우고, 끝나면 그 인스턴스만 닫는다. 사용자가 연 프레젠테이션은 건드리지 않는다.
- 멈춘 `POWERPNT.EXE` 를 정리해야 할 때만 `--kill-ppt` 를 쓴다. 열린 프레젠테이션의 저장 안 된 내용이 사라지므로 사용자에게 먼저 확인한다 (`shell-pitfalls.md` §1-4).
- 이 방식(DispatchEx, 새 인스턴스)은 키트 환경에서 PowerPoint 로 실행 검증하지 못했다. 첫 실행은 scratch 폴더에서 확인한다.

## 4. 검수 순서

1. 덱을 생성한다 (새 파일 이름, 예: 날짜 또는 버전).
2. `deck_korean_wrap.py` 로 한글 언어 태그를 적용한다.
3. `render_deck.py` 로 PDF 와 PNG 를 만든다.
4. PNG 를 한 장씩 본다. 확인할 것:
   - 줄 끝에서 한글 낱말이 쪼개지는지
   - 글상자 밖으로 넘치는지
   - 표 셀의 글자가 잘리는지
   - 캡션과 본문의 글자 크기 차이가 의도대로인지
5. 문제가 있으면 **원고(소스)나 생성 스크립트를 고치고 다시 만든다.** 산출 파일을 손으로 고치는 것은 최소한으로 한다. 손으로 고친 파일은 다음 생성 때 사라진다.

## 5. 덱 파일 관리

- 덱의 버전은 파일 이름에 붙인다. 이전 버전을 덮어쓰지 않는다.
- 검수 PNG 폴더도 버전별로 나눈다.
- 최종본을 보낼 때는 한글 후처리를 거친 파일을 보낸다. 후처리 전의 파일을 보내면 줄 바꿈 문제가 그대로 남는다.
