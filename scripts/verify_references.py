# -*- coding: utf-8 -*-
"""요약본 참고문헌을 원문 서지와 대조한다 (2026-10-16).

- arXiv 번호가 있으면 arXiv API에서 제목·저자·제출 연도·학술지 정보·DOI를 가져온다.
- 제목으로 Crossref를 검색해 DOI와 게재처를 찾는다(제목 유사도 0.9 이상만 채택).
- 결과는 docs/reference_check_20261016.md 표로 남긴다. 자동 판정이 애매하면 '확인 필요'로 둔다.

    python3 scripts/verify_references.py docs/summary_review_v12.md
"""
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "academic-reference-check/1.0 (thesis research)"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", s.lower())).strip()


def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def parse_refs(md: str) -> list[dict]:
    refs = []
    sec = md[md.index("# 참고문헌"):]
    for n, text in re.findall(r"^(\d+)\. (.+)$", sec, flags=re.M):
        arx = re.search(r"arXiv:(\d{4}\.\d{4,5})", text)
        year = re.search(r"\((\d{4})\)", text)
        # title: text after "(year). " up to next ". "
        m = re.search(r"\(\d{4}\)\.\s*(.+?)\.\s", text + " ")
        refs.append({"n": int(n), "text": text, "arxiv": arx.group(1) if arx else None,
                     "year": year.group(1) if year else None, "title": m.group(1) if m else None,
                     "first_author": re.split(r"[,(&]", text)[0].strip()})
    return refs


def arxiv_meta(ids: list[str]) -> dict:
    out = {}
    root = ET.fromstring(get("https://export.arxiv.org/api/query?max_results=50&id_list=" + ",".join(ids)))
    for e in root.findall("a:entry", NS):
        aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.rsplit("/", 1)[-1])
        out[aid] = {
            "title": re.sub(r"\s+", " ", e.find("a:title", NS).text).strip(),
            "authors": [a.find("a:name", NS).text for a in e.findall("a:author", NS)],
            "published": e.find("a:published", NS).text[:10],
            "journal_ref": (e.find("arxiv:journal_ref", NS).text if e.find("arxiv:journal_ref", NS) is not None else ""),
            "doi": (e.find("arxiv:doi", NS).text if e.find("arxiv:doi", NS) is not None else ""),
        }
    return out


def crossref(title: str) -> dict | None:
    q = urllib.parse.quote(title)
    data = json.loads(get(f"https://api.crossref.org/works?rows=3&query.bibliographic={q}"))
    best = None
    for it in data["message"]["items"]:
        t = (it.get("title") or [""])[0]
        s = sim(t, title)
        if s >= 0.9 and (best is None or s > best["sim"]):
            best = {"sim": round(s, 3), "doi": it.get("DOI"), "title": t,
                    "venue": (it.get("container-title") or [""])[0] or (it.get("event", {}) or {}).get("name", ""),
                    "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0], "type": it.get("type")}
    return best


def main(md_path: str) -> None:
    refs = parse_refs(Path(md_path).read_text(encoding="utf-8"))
    ids = [r["arxiv"] for r in refs if r["arxiv"]]
    meta = arxiv_meta(ids) if ids else {}
    rows = []
    for r in refs:
        notes, verdict = [], "일치"
        a = meta.get(r["arxiv"]) if r["arxiv"] else None
        if r["arxiv"] and not a:
            verdict = "확인 필요"
            notes.append("arXiv 번호로 조회되지 않음")
        if a:
            s = sim(a["title"], r["title"] or "")
            if s < 0.9:
                verdict = "확인 필요"
                notes.append(f"제목 불일치(유사도 {s:.2f}): arXiv '{a['title']}'")
            surname = r["first_author"].split()[0].rstrip(",")
            if surname and not any(surname.lower() in x.lower() for x in a["authors"][:2]):
                verdict = "확인 필요"
                notes.append(f"첫 저자 불일치: arXiv {a['authors'][:2]}")
            if r["year"] and a["published"][:4] != r["year"]:
                notes.append(f"arXiv 제출 {a['published'][:4]} (표기 {r['year']}, 게재 연도면 문제없음)")
            if a["journal_ref"]:
                notes.append(f"arXiv 게재 정보: {a['journal_ref']}")
        cr = None
        if r["title"]:
            time.sleep(1)
            try:
                cr = crossref(r["title"])
            except Exception as e:  # noqa: BLE001
                notes.append(f"Crossref 조회 실패: {e}")
        doi = (a or {}).get("doi") or (cr or {}).get("doi") or ""
        if cr:
            notes.append(f"Crossref: {cr['venue']} {cr['year']} ({cr['type']})")
        if not r["arxiv"] and not cr:
            verdict = "수동 확인"
            notes.append("arXiv 번호 없음, Crossref 일치 항목 없음(보고서·웹 문서일 수 있음)")
        rows.append((r["n"], r["text"][:70] + ("…" if len(r["text"]) > 70 else ""), verdict, doi, "; ".join(notes)))
        time.sleep(0.5)
    out = ["# 참고문헌 서지 대조 (2026-10-16)", "",
           f"대상: `{md_path}` 참고문헌 {len(refs)}건. arXiv API와 Crossref로 자동 대조했다. "
           "'확인 필요'와 '수동 확인'은 저자가 원문을 보고 확정한다.", "",
           "| # | 참고문헌(앞부분) | 판정 | DOI | 비고 |", "|---|---|---|---|---|"]
    out += [f"| {n} | {t} | {v} | {d} | {no} |" for n, t, v, d, no in rows]
    dst = ROOT / "docs" / "reference_check_20261016.md"
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("saved", dst)
    for row in rows:
        print(row[0], row[2], row[3], "|", row[4][:160])


if __name__ == "__main__":
    main(sys.argv[1])
