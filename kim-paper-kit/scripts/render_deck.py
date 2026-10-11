# -*- coding: utf-8 -*-
"""PowerPoint COM 으로 덱을 PDF 로 내보내고 쪽별 PNG 를 만든다 (검수용).
LibreOffice 가 없는 Windows 환경을 전제로 한다. 필요: Microsoft PowerPoint, pywin32, PyMuPDF.

사용:
  python render_deck.py <deck.pptx> <out_dir> [--dpi 110] [--kill-ppt]
  out_dir 이 이미 내용을 갖고 있으면 <out_dir>_v02, _v03 … 새 폴더를 쓴다 (검수 결과를 덮어쓰지 않는다).

동작: DispatchEx 로 PowerPoint 를 새 인스턴스로 띄우고, 끝나면 그 인스턴스만 종료한다.
      사용자가 열어 둔 프레젠테이션은 건드리지 않는다.
--kill-ppt: 멈춘 POWERPNT.EXE 를 모두 강제 종료한 뒤 시작한다. 열린 프레젠테이션의 저장 안 된
      내용이 사라지므로 사용자에게 확인을 받은 뒤에만 쓴다.
COM 호출 경로는 Windows + PowerPoint 설치에서만 실행된다. 문법 검사는 어디서나 가능하다.
"""
import argparse
import pathlib
import subprocess
import sys
import time

import fitz  # PyMuPDF
import win32com.client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PP_SAVE_AS_PDF = 32   # ppSaveAsPDF


def unique_dir(path):
    """내용이 있는 폴더는 그대로 두고 _v02, _v03 … 새 폴더를 만든다."""
    p = pathlib.Path(path)
    cand, n = p, 1
    while cand.exists() and any(cand.iterdir()):
        n += 1
        cand = p.with_name(f"{p.name}_v{n:02d}")
    cand.mkdir(parents=True, exist_ok=True)
    return cand


def export_pdf(deck, pdf, kill_ppt=False):
    if kill_ppt:                                 # 사용자 확인을 받은 뒤에만 켠다 (--kill-ppt)
        subprocess.run(["taskkill", "/f", "/im", "POWERPNT.EXE"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    # DispatchEx: 새 인스턴스. Dispatch 는 사용자가 연 PowerPoint 에 붙어 Quit() 가 그 창까지 닫는다.
    app = win32com.client.DispatchEx("PowerPoint.Application")
    pres = None
    try:
        # Open(FileName, ReadOnly, Untitled, WithWindow)
        pres = app.Presentations.Open(str(deck), True, False, False)
        pres.SaveAs(str(pdf), PP_SAVE_AS_PDF)
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()


def main():
    ap = argparse.ArgumentParser(description="PowerPoint COM 렌더 검수")
    ap.add_argument("deck")
    ap.add_argument("out_dir")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--kill-ppt", action="store_true",
                    help="시작 전에 POWERPNT.EXE 를 모두 종료 (사용자 확인 후에만)")
    a = ap.parse_args()

    deck = pathlib.Path(a.deck).resolve()
    out = unique_dir(a.out_dir).resolve()
    pdf = out / (deck.stem + ".pdf")
    export_pdf(deck, pdf, kill_ppt=a.kill_ppt)

    doc = fitz.open(str(pdf))
    for i, pg in enumerate(doc, 1):
        pg.get_pixmap(dpi=a.dpi).save(str(out / f"slide-{i:02d}.png"))
    print(f"{doc.page_count} slides -> {out}")


if __name__ == "__main__":
    main()
