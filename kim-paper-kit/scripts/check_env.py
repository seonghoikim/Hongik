# -*- coding: utf-8 -*-
"""설치 점검 (표준 라이브러리만 사용). 키트 스크립트와 스킬이 기대하는 환경이 갖춰졌는지 본다.

사용:
  python check_env.py                    # 전체 점검
  python check_env.py --group figures    # 묶음 하나만 (writing, feedback, figures, typesetting, ppt)

판정:
  OK       갖춰짐
  MISSING  해당 기능이 동작하지 않음 (설치 힌트를 함께 출력)
  NOTE     선택 사항이거나 이 OS 에서는 확인할 수 없음

아무 파일도 만들거나 고치지 않는다. Word 나 PowerPoint 를 실행하지 않는다
(레지스트리에 COM 등록 이름이 있는지만 본다).
종료 코드: Python 이 3.10 미만이거나 키트 scripts 폴더가 없으면 1, 그 밖에는 0.
"""
import argparse
import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KIT = Path(__file__).resolve().parent.parent
SCRIPTS = KIT / "scripts"
GROUPS = ["writing", "feedback", "figures", "typesetting", "ppt"]
IS_WINDOWS = platform.system() == "Windows"

rows = []  # (group, status, label, detail, hint)


def add(group, status, label, detail="", hint=""):
    rows.append((group, status, label, detail, hint))


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def find_dot():
    env = os.environ.get("GRAPHVIZ_DOT")
    if env and Path(env).exists():
        return env
    found = shutil.which("dot")
    if found:
        return found
    for cand in ("C:/Program Files/Graphviz/bin/dot.exe",
                 "C:/Program Files (x86)/Graphviz/bin/dot.exe"):
        if Path(cand).exists():
            return cand
    return None


def registry_has(progid):
    """COM 등록 이름이 있는지 본다. Office 를 실행하지 않는다."""
    import winreg  # Windows 전용, 호출 전에 IS_WINDOWS 를 확인한다
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid):
            return True
    except OSError:
        return False


def check_python():
    vi = sys.version_info
    ver = f"{vi.major}.{vi.minor}.{vi.micro}"
    if vi < (3, 10):
        add("writing", "MISSING", "Python", ver, "Python 3.11 이상을 설치한다 (최소 3.10)")
    elif vi < (3, 11):
        add("writing", "NOTE", "Python", ver, "동작은 하지만 3.11 이상을 권장한다")
    else:
        add("writing", "OK", "Python", ver)


def check_kit():
    needed = ["style_lint.py", "check_source.py", "academic_search.py", "word_com_template.py",
              "transcribe_meeting.py", "render_html_figure.py", "check_figure_print.py",
              "verify_dot_order.py", "paper_style.py", "extract_pdf_figures.py",
              "pdf_page_audit.py", "render_deck.py", "deck_korean_wrap.py"]
    missing = [n for n in needed if not (SCRIPTS / n).exists()]
    if missing:
        add("writing", "MISSING", "키트 scripts 폴더", str(SCRIPTS), "누락: " + ", ".join(missing))
    else:
        add("writing", "OK", "키트 scripts 폴더", str(SCRIPTS))


def check_modules():
    mods = [
        ("writing", "requests", "academic_search.py (DOI 검증)", "pip install requests"),
        ("feedback", "faster_whisper", "transcribe_meeting.py (음성 전사)", "pip install faster-whisper"),
        ("figures", "matplotlib", "paper_style.py (데이터 플롯)", "pip install matplotlib"),
        ("figures", "fitz", "extract_pdf_figures.py, pdf_page_audit.py (PyMuPDF)", "pip install pymupdf"),
        ("figures", "PIL", "check_figure_print.py, render_html_figure.py (Pillow)", "pip install pillow"),
        ("figures", "playwright", "render_html_figure.py (HTML 도식 렌더)",
         "pip install playwright 후 python -m playwright install chromium"),
        ("ppt", "pptx", "deck_korean_wrap.py (python-pptx)", "pip install python-pptx"),
        ("typesetting", "win32com", "word_com_template.py, render_deck.py (pywin32)",
         "pip install pywin32 (Windows 전용)"),
    ]
    for group, mod, use, hint in mods:
        if has_module(mod):
            add(group, "OK", mod, use)
        elif mod == "win32com" and not IS_WINDOWS:
            add(group, "NOTE", mod, use, "Windows 전용 모듈이다. 이 OS 에서는 조판을 할 수 없다")
        else:
            add(group, "MISSING", mod, use, hint)


def check_executables():
    ff = shutil.which("ffmpeg")
    if ff:
        add("feedback", "OK", "ffmpeg", ff)
    else:
        add("feedback", "MISSING", "ffmpeg", "PATH 에 없음",
            "winget install Gyan.FFmpeg 후 PATH 추가, 또는 transcribe_meeting.py --ffmpeg <경로>")
    dot = find_dot()
    if dot:
        add("figures", "OK", "dot (Graphviz)", dot)
    else:
        add("figures", "MISSING", "dot (Graphviz)", "찾지 못함",
            "Graphviz 설치 후 PATH 추가, 또는 환경변수 GRAPHVIZ_DOT, 또는 verify_dot_order.py --dot-bin")
    node = shutil.which("node")
    if node:
        add("ppt", "OK", "node", node, "pptxgenjs 는 npm install pptxgenjs 로 프로젝트에 설치")
    else:
        add("ppt", "NOTE", "node", "PATH 에 없음", "PPT 를 pptxgenjs 로 만들 때만 필요")


def check_windows_only():
    if not IS_WINDOWS:
        add("typesetting", "NOTE", "Word.Application (COM)", "Windows 가 아님", "조판은 Windows 에서만 한다")
        add("ppt", "NOTE", "PowerPoint.Application (COM)", "Windows 가 아님", "PPT 검수는 Windows 에서만 한다")
        return
    if registry_has("Word.Application"):
        add("typesetting", "OK", "Word.Application (COM)", "등록 확인 (실행하지 않음)")
    else:
        add("typesetting", "MISSING", "Word.Application (COM)", "등록되지 않음",
            "정식 Microsoft Word 가 필요하다. 뷰어 전용 설치로는 조판할 수 없다")
    if registry_has("PowerPoint.Application"):
        add("ppt", "OK", "PowerPoint.Application (COM)", "등록 확인 (실행하지 않음)")
    else:
        add("ppt", "MISSING", "PowerPoint.Application (COM)", "등록되지 않음",
            "render_deck.py 검수에 정식 PowerPoint 가 필요하다")
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    hangul = [f for f in ("malgun.ttf", "batang.ttc", "gulim.ttc") if (fonts / f).exists()]
    if hangul:
        add("typesetting", "OK", "한글 글꼴", ", ".join(hangul))
    else:
        add("typesetting", "NOTE", "한글 글꼴", "기본 한글 글꼴을 찾지 못함",
            "없으면 대체 글꼴로 조판되어 양식이 틀어진다. 저널 지정 글꼴을 설치한다")


def print_report(only):
    order = {g: i for i, g in enumerate(GROUPS)}
    shown = [r for r in rows if only is None or r[0] in only or r[0] == "writing"]
    shown.sort(key=lambda r: order.get(r[0], 99))  # 묶음별로 모아 출력한다
    current = None
    for group, status, label, detail, hint in shown:
        if group != current:
            current = group
            print(f"\n[{group}]")
        line = f"  {status:<8} {label}"
        if detail:
            line += f"  |  {detail}"
        print(line)
        if hint and status != "OK":
            print(f"           -> {hint}")
    missing = sum(1 for r in shown if r[1] == "MISSING")
    notes = sum(1 for r in shown if r[1] == "NOTE")
    print(f"\n요약: MISSING {missing} · NOTE {notes} · 전체 {len(shown)}개 항목")
    return missing


def main(argv):
    ap = argparse.ArgumentParser(description="kim-paper-kit 설치 점검 (파일을 만들지 않는다)")
    ap.add_argument("--group", choices=GROUPS, help="이 묶음만 보고 (writing 묶음은 항상 포함)")
    args = ap.parse_args(argv)
    only = {args.group} if args.group else None

    print(f"kim-paper-kit 설치 점검 (KIT = {KIT})")
    check_python()
    check_kit()
    check_modules()
    check_executables()
    check_windows_only()
    print_report(only)

    hard_fail = any(r[1] == "MISSING" and r[2] in ("Python", "키트 scripts 폴더") for r in rows)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
