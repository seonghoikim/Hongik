# Word 삽입과 배치

Windows, Microsoft Word, pywin32 환경을 전제로 한다. 다른 환경에서는 PNG를 만들고 삽입은 수동으로 한다.

## 1. 원칙: 서식과 그림은 쓰는 시점에 넣는다

- 완성된 문서를 열고 Find 루프로 서식을 입히면 매 건마다 쪽 배치가 전면 재계산되어 실패한다. 한 사례는 97분 걸리다가 중단됐고, 쓰는 시점에 넣는 방식으로 바꾸자 8분에 끝났다.
- 그림과 서식은 조립 단계에서 **쓰는 순간** 넣는다. 이미 쓴 문장을 찾아 고치는 방식은 피한다.

## 2. 필요 조건과 작업 규칙

- Windows + Microsoft Word + pywin32 (`win32com.client`).
- **COM만 쓴다.** COM(Word 자동화 인터페이스)으로만 편집하고, 문서 XML을 직접 고치거나 압축을 풀어 편집하지 않는다. (프로젝트 규칙에 명시된 경우가 많다. 프로젝트 `CLAUDE.md`를 먼저 확인한다.)
- 실행 전에 남은 Word 프로세스를 정리한다: `taskkill /f /im WINWORD.EXE`.
- **기존 DOCX를 덮어쓰지 않는다.** 결과는 새 이름(`_v2`, `_v3` …)으로 `SaveAs2` 한다.
- 한글 출력이 있는 스크립트는 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`를 맨 위에 둔다.

## 3. 그림 삽입 코드

```python
import sys
import win32com.client

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(src_path)

# ... locate the insertion point (the caption or a placeholder paragraph) ...
shp = doc.InlineShapes.AddPicture(png_path, LinkToFile=False, SaveWithDocument=True)
shp.LockAspectRatio = True     # set before Width: otherwise the aspect ratio can break
shp.Width = print_width_pt     # width only; height follows the aspect ratio

doc.SaveAs2(dst_path)          # new _vN name, never the source name
doc.Close()
word.Quit()
```

- **2단 문단에 넣으면 Word가 그림을 단 폭으로 자동 축소한다.** 전폭 그림은 조건 없이 `Width`를 강제한다.
- **텍스트 상자 안에 `AddPicture`를 직접 호출하면 Word가 비정상 종료(크래시)한다.** 블록을 본문에서 만든 뒤 `FormattedText`로 상자에 옮긴다 (`tf.TextRange.FormattedText = 블록.FormattedText`).
- 조립 후 PDF로 내보내 그림이 보이는지, 쪽 빈칸이 있는지 확인한다.

## 4. 이미지 형식

- **기본은 PNG.** 배율 3의 HTML 렌더, 300dpi 이상의 matplotlib 저장을 쓴다. 픽셀 기준은 `print-quality.md` §1.
- **SVG 직접 삽입은 판정이 보류 상태다.** 기록이 서로 다르다 (`pitfalls.md` §9). 아래 절차를 통과한 경우에만 쓴다.
  1. 테스트 문서에 SVG를 한 장 넣는다.
  2. PDF로 내보낸다.
  3. 그림이 보이고 빈 상자가 아닌지 확인한다.
  4. 같은 Word 버전과 같은 종류의 그림에만 쓴다.

## 5. 캡션

- 캡션은 **그림 아래**에 둔다. 표 캡션은 표 위에 둔다 (TKIPS 양식 기록).
- 스타일은 기존 캡션 단락을 복제한다. 새 스타일을 만들지 않는다.
- 접두, 언어, 구두점은 투고 규정을 따른다 (`figure-style.md` §5). 캡션 본문은 제목만 쓴다.

## 6. 전폭 그림과 쪽 빈칸

**목표:** 그림을 본문 폭 100%로 넣으면서 쪽 하단에 빈칸이 생기지 않게 한다.

- **부동 프레임(텍스트 감싸기)은 쓰지 않는다.** 표나 제목이 많은 절에서는 앵커 문단을 찾지 못해 그림이 뒤쪽으로 밀리고, 쪽 하단에 큰 빈칸이 생겼다.
- **1단 구역 + 지연 삽입이 결과가 좋았다.**
  1. 전폭 그림이 들어갈 구간을 1단 구역으로 만든다.
  2. 그림 토큰 자리에서 바로 넣지 않는다. 대기열에 넣고, 현재 세로 위치를 `Range.Information(6)` (쪽 기준 세로 위치)로 읽는다.
  3. 잔여 높이 ≥ 그림 높이 + 캡션 높이 + 여유(약 24pt)일 때만 넣는다. 아니면 다음 **완결 문단**의 경계로 미룬다.
  4. 완결 문단은 "~다."로 끝나는 문단이다. 정의를 도입하는 줄("…하면:")이나 식 줄 바로 뒤에는 넣지 않는다. 정의와 식이 갈라진다.
- 2단 레이아웃에서는 연속 구역 나누기가 두 단을 균형 있게 맞추므로 `Information(6)`만으로는 잔여 높이를 정확히 재기 어렵다. 프로젝트에서는 `잔여 = 본문 하단 − (구역 시작 + 채움 / 2)`로 추정했다. 우측 단이면 좌측 단은 가득 찬 것으로 본다. 직전 그림의 구역 하단을 새 구역 시작으로 쓴다. 다음 줄이 표이면 보류한다.
- 추정이 맞는지는 쪽 하단 빈칸을 PDF로 실측해 확인하고, 기준(여유 값)을 맞춘다.
- **Why:** 그림을 줄이면 글자가 안 읽힌다. 빈칸이 남으면 쪽 수가 늘어난다. 지연 삽입은 둘 다 피한다 (`print-quality.md` §8).

## 7. 표가 쪽을 넘을 때

- 표의 **행은 쪽을 나누지 않는다** (`AllowBreakAcrossPages = False`).
- 표 전체의 쪽 분할은 허용하되, 헤더 행을 매 쪽 반복한다 (`HeadingFormat = True`).
- 캡션과 첫 행은 함께 묶는다 (`KeepWithNext`).
- 다섯 행 이상인 표만 분할을 허용한다. 짧은 표는 한 쪽에 묶되, 모든 짧은 표를 일괄로 묶으면 쪽 하단에 빈칸이 생긴다. 묶을 표만 표시해 고른다.

## 8. 쪽 수가 넘칠 때 해결 순서

1. 본문 문장을 줄인다. 그림은 줄이지 않는다 (`print-quality.md` §8).
2. 지연 삽입 (§6)으로 빈칸을 줄인다.
3. 표의 행 분할 규칙 (§7)을 적용한다.
