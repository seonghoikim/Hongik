# 필요 조건 (환경)

이 키트의 조판 절차는 아래 환경을 전제로 한다. 하나라도 빠지면 해당 단계만 대체 경로를 쓰거나 건너뛴다. 대체 경로가 없는 단계는 작업 전에 사용자에게 알린다.

---

## 1. 필수

| 항목 | 용도 | 확인 방법 |
|------|------|-----------|
| Windows 10 또는 11 | Word·PowerPoint COM 은 Windows 에서만 동작 | `ver` |
| Microsoft Word (정식 설치) | DOCX 조판 (pywin32 `Word.Application`) | Word 를 한 번 실행해 정상 기동을 확인 |
| Python 3.x | 조판·검사 스크립트 | `python --version` |
| pywin32 | Word·PowerPoint COM 호출 | `python -c "import win32com.client"` |
| PyMuPDF (`fitz`) | 쪽별 빈칸 측정, PNG 변환 | `python -c "import fitz"` |
| Pillow | 그림 크기 읽기, 약력 사진 자르기 | `python -c "import PIL"` |
| python-pptx | PPT 한글 후처리 | `python -c "import pptx"` |
| Git Bash 또는 PowerShell | 명령 실행 (`shell-pitfalls.md`) | — |

설치 예시:
```bash
python -m pip install pywin32 pymupdf pillow python-pptx
```
- 설치 뒤 `scripts/word_com_template.py --selftest` 로 순수 함수 검사를 돌린다. Word 없이도 열 폭, 버전 이름, 제어문자 검사가 통과해야 한다.

## 2. 조건부 (해당 저널이나 작업일 때만)

| 항목 | 필요한 경우 | 비고 |
|------|-------------|------|
| 한글 글꼴 (HY신명조, HY중고딕, HY견명조, HY견고딕, HY태명조 등) | 한국 학회지·논문지 양식 조판 | 글꼴이 없으면 대체 글꼴로 조판되어 양식이 틀어진다. 조판 전에 글꼴 이름을 확인한다. |
| 정식 한글 프로그램 | HWP 파일을 OLE 로 직접 조판 | 한컴 뷰어만 있으면 `HWPFrame.HwpObject` 가 등록되지 않아 조판할 수 없다. |
| 웹 한글 편집기 (브라우저 자동화) | 정식 한글이 없을 때 대안 | 함정이 많다 (`hwp-web-pitfalls.md`). 결과는 PDF 와 텍스트로 검증한다. |
| Microsoft PowerPoint | PPT 검수 렌더 (`render_deck.py`) | LibreOffice 는 이 환경에 없다. PowerPoint 가 없으면 PPT 검수를 사용자에게 맡긴다. |
| python-docx | 기존 정상본 DOCX 에서 열 폭 읽기 | 열 폭 기준값을 JSON 으로 저장해 두면 재사용할 수 있다 |
| Node.js + pptxgenjs | PPT 덱 생성 | 덱 생성 방식은 프로젝트가 정한다 |

## 3. 글꼴 확인 방법

- Windows 의 글꼴 폴더 또는 설정의 글꼴 목록에서 이름을 확인한다.
- 조판 결과의 글꼴은 PDF 스팬 실측으로 확인한다 (`pdf_page_audit.py --spans`). 스팬의 글꼴 이름이 템플릿 지정과 다르면 대체 글꼴이 쓰인 것이다.
- 한글 글꼴을 설치해야 할 때는 저널 공식 양식 문서에 적힌 글꼴 목록을 따른다. 이름을 추측해 설치하지 않는다.

## 4. 작업 디렉터리 구조 (권장)

```
<프로젝트>/
  paper/                     원고 소스 (sec*.md, refs.md, response.md)
  templates/                 공식 양식 DOCX (읽기 전용으로 취급)
  figs/                      그림 파일 (토큰 번호와 매핑)
  build/                     조판 산출물 (판마다 새 이름)
  scratch/                   시험 조판, 임시 파일
  <KIT>/                     이 키트 (scripts/, .claude/skills/)
```
- 키트의 스크립트는 경로를 인자로 받는다. 스크립트 안에 특정 사용자의 경로를 박아 두지 않는다.
