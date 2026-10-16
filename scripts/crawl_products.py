# -*- coding: utf-8 -*-
"""난이도 탐색·본 실험용 상품 문서 수집 (2026-10-16, 저자 요청).

판매처 사이트의 robots.txt는 상품 상세 페이지를 허용한다(/app/mypage, /app/order만 금지). 상품 목록은
자바스크립트로 불러와져서, 사이트가 공개한 sitemap.xml과 llms.txt의 상품 주소를 쓴다. 상세 페이지 안의
구조화 데이터(JSON-LD Product: 상품명, 브랜드, 모델명, 분류, 판매가, 사양)만 추출한다.

원칙 (docs/probe_criterion_20261016.md):
- 요청 간격 1.2초 이상, 페이지는 구조화 데이터가 나올 때까지만 읽는다(최대 250KB).
- 연구용 내부 보관만 하고 재배포하지 않는다. 문서마다 출처 주소, 수집 시각, 원문 해시를 manifest에 남긴다.

    python3 scripts/crawl_products.py scan     # sitemap을 앞에서부터 훑어 목표 분류를 채울 때까지 색인
    python3 scripts/crawl_products.py build    # 색인에서 문서(.txt)와 manifest.json 생성
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "rag" / "crawled"
INDEX = OUT / "scan_index.jsonl"
UA = "Mozilla/5.0 (compatible; academic-research-crawler)"
BASE = "https://www.e-himart.co.kr"
DELAY = 1.2
MAX_BYTES = 250_000

# 기존 실제 사례 6종과 같은 분류의 유사 상품을 모은다(상품명 기준). PLUX는 모두 포함.
TARGETS = {
    "냉장고": (lambda n: "냉장고" in n and "김치" not in n and "와인" not in n, 6),
    "냉동고": (lambda n: "냉동고" in n, 6),
    "건조기": (lambda n: "건조기" in n and not any(x in n for x in ("식기", "신발", "손", "헤어", "음식", "식품", "빨래건조대")), 6),
    "청소기": (lambda n: "청소기" in n and "로봇" not in n, 6),
    "TV": (lambda n: "TV" in n.upper() and "인치" in n and "거치" not in n and "스탠드" not in n, 6),
    "인덕션": (lambda n: "인덕션" in n or "하이라이트" in n, 6),
}


def fetch_head(url: str) -> str:
    """구조화 데이터 블록이 끝날 때까지만 읽는다."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    buf = b""
    with urllib.request.urlopen(req, timeout=30) as r:
        while len(buf) < MAX_BYTES:
            chunk = r.read(16384)
            if not chunk:
                break
            buf += chunk
            i = buf.find(b"ld+json")
            if i >= 0 and buf.find(b"</script>", i) >= 0:
                break
    return buf.decode("utf-8", errors="ignore")


def parse(page: str) -> dict | None:
    m = re.search(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', page, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    if d.get("@type") != "Product":
        return None
    props: dict[str, list[str]] = {}
    for p in d.get("additionalProperty") or []:
        props.setdefault(p.get("name", ""), []).append(p.get("value", ""))
    return {
        "name": html.unescape(d.get("name") or "").strip(),
        "brand": (d.get("brand") or {}).get("name") or "",
        "model": d.get("model") or "",
        "category": d.get("category") or "",
        "price": (d.get("offers") or {}).get("price") or "",
        "description": html.unescape(d.get("description") or "").strip(),
        "keywords": d.get("keywords") or [],
        "props": props,
        "sha256": hashlib.sha256(m.group(1).encode("utf-8")).hexdigest(),
    }


def goods_urls() -> list[str]:
    plux = []
    llms = urllib.request.urlopen(urllib.request.Request(BASE + "/llms.txt", headers={"User-Agent": UA}), timeout=30)
    text = llms.read().decode("cp949", errors="ignore")
    sec = text[text.find("## PLUX"):]
    plux = re.findall(r"URL: (https://www\.e-himart\.co\.kr/app/goods/goodsDetail\?goodsNo=\d+)", sec)
    time.sleep(DELAY)
    sm = urllib.request.urlopen(urllib.request.Request(BASE + "/sitemap.xml", headers={"User-Agent": UA}), timeout=60)
    xml = sm.read().decode("utf-8", errors="ignore")
    pairs = re.findall(r"<loc>(https://www\.e-himart\.co\.kr/app/goods/goodsDetail\?goodsNo=(\d+))</loc>\s*"
                       r"<lastmod>([\d-]+)</lastmod>", xml)
    # 최근 수정·최근 등록 상품부터(오래된 단종 상품이 앞쪽에 몰려 있음)
    sitemap = [u for u, _, _ in sorted(pairs, key=lambda x: (x[2], x[1]), reverse=True)]
    seen, out = set(), []
    for u in plux + sitemap:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out, set(plux)


def classify(name: str) -> str | None:
    for key, (pred, _) in TARGETS.items():
        if pred(name):
            return key
    return None


def scan(max_requests: int = 1500) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = {}
    if INDEX.exists():
        for line in INDEX.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[r["url"]] = r
    urls, plux = goods_urls()
    counts = {k: 0 for k in TARGETS}
    for r in done.values():
        if r.get("selected") and r.get("group") in counts:
            counts[r["group"]] += 1
    n_req = 0
    with INDEX.open("a", encoding="utf-8") as f:
        for url in urls:
            is_plux = url in plux
            if url in done:
                continue
            if not is_plux and all(counts[k] >= TARGETS[k][1] for k in TARGETS):
                continue
            if n_req >= max_requests:
                break
            time.sleep(DELAY)
            n_req += 1
            try:
                info = parse(fetch_head(url))
            except Exception as e:  # noqa: BLE001 - record and move on
                info = None
                print("fail", url, e, file=sys.stderr)
            rec = {"url": url, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            if info:
                group = "PLUX" if (is_plux or info["brand"].upper() == "PLUX") else classify(info["name"])
                selected = group == "PLUX" or (group in counts and counts[group] < TARGETS[group][1])
                if selected and group in counts:
                    counts[group] += 1
                rec.update(info, group=group, selected=selected)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if n_req % 50 == 0:
                print(n_req, counts, flush=True)
    print("requests", n_req, "counts", counts)


def safe(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", s)[:60]


def build() -> None:
    recs = [json.loads(line) for line in INDEX.read_text(encoding="utf-8").splitlines()]
    sel = [r for r in recs if r.get("selected")]
    manifest = []
    for r in sel:
        lines = [f"# {r['name']}", f"브랜드: {r['brand']}", f"모델명: {r['model']}",
                 f"분류: {r['category']}", f"판매가: {int(float(r['price'])):,}원" if r.get("price") else "판매가: 미표기"]
        if r.get("description"):
            lines += ["", "[상품 설명]", r["description"]]
        if r.get("props"):
            lines += ["", "[주요 사양]"] + [f"- {k}: {', '.join(v)}" for k, v in r["props"].items()]
        if r.get("keywords"):
            lines += ["", "[검색 키워드]", ", ".join(r["keywords"])]
        lines += ["", f"(출처: 판매처 상품 상세 페이지, 수집 {r['fetched_at'][:10]})"]
        fname = f"{safe(r['model'] or r['url'][-10:])}.txt"
        (OUT / fname).write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest.append({"file": fname, "group": r["group"], "url": r["url"], "fetched_at": r["fetched_at"],
                         "name": r["name"], "model": r["model"], "price": r.get("price"), "sha256": r["sha256"]})
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    by = {}
    for m in manifest:
        by[m["group"]] = by.get(m["group"], 0) + 1
    print("documents", len(manifest), by)


if __name__ == "__main__":
    {"scan": scan, "build": build}[sys.argv[1]]()
