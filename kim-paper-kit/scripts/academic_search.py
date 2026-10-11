"""
Academic paper search and DOI verification, verified sources only.

Queries Semantic Scholar and CrossRef. Every result comes from these APIs, so
references are not written from memory. Add a reference to a manuscript only
after `verify` succeeds for its DOI.

Usage:
  python academic_search.py search "query terms" [--limit 10] [--json] [--source both|ss|cr]
  python academic_search.py verify 10.1109/52.199724
  python academic_search.py cite 10.1109/52.199724 --format ijibc --ref 19

Optional environment variables (nothing personal is stored in this file):
  ACADEMIC_SEARCH_CONTACT   contact string sent to CrossRef (polite pool), e.g. an email
  SEMANTIC_SCHOLAR_API_KEY  Semantic Scholar API key, if you have one

Exit codes: 0 success, 1 DOI not found or invalid, 2 usage error,
            3 lookup failed (network, timeout, server error). Exit 3 does not
            mean the DOI is wrong; run the same command again later.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests  # noqa: E402

SS_BASE = "https://api.semanticscholar.org/graph/v1"
CR_BASE = "https://api.crossref.org"
SS_FIELDS = "title,authors,year,externalIds,abstract,citationCount,venue,url"
TIMEOUT = 15
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")

_CONTACT = os.environ.get("ACADEMIC_SEARCH_CONTACT", "").strip()
_UA = "kim-paper-kit-academic-search/1.0"
HEADERS_CR = {"User-Agent": _UA + (f" (mailto:{_CONTACT})" if _CONTACT else "")}
HEADERS_SS = {"User-Agent": _UA}
if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
    HEADERS_SS["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]


def normalize_doi(doi):
    """Accept '10.xxx/yyy' or 'https://doi.org/10.xxx/yyy'; return the bare DOI or None."""
    doi = (doi or "").strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi if DOI_PATTERN.match(doi) else None


# --- Normalization ---
def normalize_paper(source, raw):
    """Convert an API-specific record to one canonical dict."""
    if source == "semantic_scholar":
        authors_list = [a.get("name", "") for a in (raw.get("authors") or [])]
        ext = raw.get("externalIds") or {}
        doi = ext.get("DOI")
        return {
            "title": (raw.get("title") or "").strip(),
            "authors": authors_list,
            "year": raw.get("year"),
            "doi": doi,
            "abstract": (raw.get("abstract") or "")[:500] or None,
            "citation_count": raw.get("citationCount"),
            "venue": raw.get("venue") or None,
            "url": f"https://doi.org/{doi}" if doi else raw.get("url"),
            "source": "semantic_scholar",
        }
    if source == "crossref":
        authors_list = []
        for a in raw.get("author") or []:
            authors_list.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
        title_list = raw.get("title") or [""]
        title = title_list[0] if title_list else ""
        year = None
        for date_field in ["published-print", "published-online", "created"]:
            dp = (raw.get(date_field) or {}).get("date-parts", [[]])
            if dp and dp[0] and dp[0][0]:
                year = dp[0][0]
                break
        doi = raw.get("DOI")
        venue = raw.get("container-title") or [""]
        venue = venue[0] if venue else None
        abstract = raw.get("abstract") or None
        if abstract:
            abstract = re.sub(r"<[^>]+>", "", abstract)[:500]  # strip JATS XML tags
        return {
            "title": title.strip(),
            "authors": authors_list,
            "year": year,
            "doi": doi,
            "abstract": abstract,
            "citation_count": raw.get("is-referenced-by-count"),
            "venue": venue or None,
            "url": f"https://doi.org/{doi}" if doi else None,
            "source": "crossref",
        }
    return None


# --- API functions ---
def _api_get(url, params=None, headers=None):
    """GET with one retry after HTTP 429. Returns parsed JSON or None."""
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 429:
            print("[WARN] Rate limited. Waiting 3s...", file=sys.stderr)
            time.sleep(3)
            resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out.", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        print("[ERROR] Network connection failed.", file=sys.stderr)
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP {e.response.status_code}", file=sys.stderr)
    except ValueError:
        print("[ERROR] Response was not valid JSON.", file=sys.stderr)
    return None


def search_semantic_scholar(query, limit=10):
    data = _api_get(f"{SS_BASE}/paper/search",
                    params={"query": query, "limit": limit, "fields": SS_FIELDS},
                    headers=HEADERS_SS)
    if not data or "data" not in data:
        return []
    return [normalize_paper("semantic_scholar", p) for p in data["data"] if p]


def search_crossref(query, limit=10):
    data = _api_get(f"{CR_BASE}/works",
                    params={"query": query, "rows": limit, "sort": "relevance"},
                    headers=HEADERS_CR)
    if not data or "message" not in data:
        return []
    items = data["message"].get("items", [])
    return [normalize_paper("crossref", item) for item in items if item]


def search_papers(query, limit=10, source="both"):
    """Search the chosen APIs and merge results, de-duplicated by DOI."""
    results = []
    if source in ("ss", "both"):
        ss = search_semantic_scholar(query, limit)
        results.extend(ss)
        if ss:
            print(f"[INFO] Semantic Scholar: {len(ss)} results", file=sys.stderr)
    if source in ("cr", "both"):
        cr = search_crossref(query, limit)
        if cr:
            print(f"[INFO] CrossRef: {len(cr)} results", file=sys.stderr)
        existing = {r["doi"] for r in results if r["doi"]}
        for p in cr:
            if p["doi"] and p["doi"] in existing:
                continue
            results.append(p)
    if not results:
        print("[WARN] No results from the selected API(s).", file=sys.stderr)
    return results[:limit]


def lookup_doi(doi):
    """Look up a DOI in CrossRef. Returns (status, paper).

    status is one of:
      "ok"        paper is the normalized record
      "invalid"   the string is not a DOI (no request was sent)
      "not_found" CrossRef answered 404, so the DOI does not exist
      "error"     network, timeout, server, or JSON failure; the DOI is not judged
    """
    doi = normalize_doi(doi)
    if not doi:
        return "invalid", None
    url = f"{CR_BASE}/works/{urllib.parse.quote(doi, safe='/')}"
    try:
        resp = requests.get(url, headers=HEADERS_CR, timeout=TIMEOUT)
        if resp.status_code == 429:
            print("[WARN] Rate limited. Waiting 3s...", file=sys.stderr)
            time.sleep(3)
            resp = requests.get(url, headers=HEADERS_CR, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {type(e).__name__}", file=sys.stderr)
        return "error", None
    if resp.status_code == 404:
        return "not_found", None
    if resp.status_code != 200:
        print(f"[ERROR] CrossRef answered HTTP {resp.status_code}", file=sys.stderr)
        return "error", None
    try:
        data = resp.json()
    except ValueError:
        print("[ERROR] Response was not valid JSON.", file=sys.stderr)
        return "error", None
    if not isinstance(data, dict) or "message" not in data:
        return "error", None
    return "ok", normalize_paper("crossref", data["message"])


# --- Formatting ---
def format_text(paper, index):
    lines = [f"[{index}] {paper['title']}"]
    if paper["authors"]:
        lines.append(f"    Authors: {', '.join(paper['authors'][:5])}")
        if len(paper["authors"]) > 5:
            lines[-1] += f" (+{len(paper['authors']) - 5} more)"
    parts = []
    if paper["year"]:
        parts.append(f"Year: {paper['year']}")
    if paper["venue"]:
        parts.append(f"Venue: {paper['venue']}")
    if paper["citation_count"] is not None:
        parts.append(f"Citations: {paper['citation_count']}")
    if parts:
        lines.append(f"    {' | '.join(parts)}")
    if paper["doi"]:
        lines.append(f"    DOI: {paper['doi']}")
    if paper["abstract"]:
        abstract = paper["abstract"][:200]
        if len(paper["abstract"]) > 200:
            abstract += "..."
        lines.append(f"    Abstract: {abstract}")
    if paper["url"]:
        lines.append(f"    URL: {paper['url']}")
    return "\n".join(lines)


def format_ijibc_reference(paper, ref_num=0):
    """Reference line in the IJIBC style. Add other journal styles as new functions."""
    authors = paper["authors"]
    if not authors:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]} and {authors[1]}"
    else:
        author_str = ", ".join(authors[:-1]) + f", and {authors[-1]}"
    title = paper["title"].rstrip(".")
    venue = paper["venue"] or "Unknown Venue"
    year = paper["year"] or "n.d."
    doi_part = f" DOI: https://doi.org/{paper['doi']}" if paper["doi"] else ""
    return f'[{ref_num}] {author_str}, "{title}," {venue}, {year}.{doi_part}'


FORMATTERS = {"ijibc": format_ijibc_reference}


# --- CLI ---
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Academic paper search (verified sources only)")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="search papers by keyword")
    p_search.add_argument("query", help="search query (English or Korean)")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--json", action="store_true", help="output as JSON")
    p_search.add_argument("--source", choices=["ss", "cr", "both"], default="both",
                          help="ss = Semantic Scholar, cr = CrossRef, both = merged")

    p_verify = sub.add_parser("verify", help="check that a DOI exists in CrossRef")
    p_verify.add_argument("doi", help="DOI, e.g. 10.1109/52.199724")

    p_cite = sub.add_parser("cite", help="formatted citation from a DOI")
    p_cite.add_argument("doi")
    p_cite.add_argument("--format", choices=list(FORMATTERS) + ["text"], default="ijibc",
                        dest="fmt", help="citation style; add styles to FORMATTERS")
    p_cite.add_argument("--ref", type=int, default=0, help="reference number [N]")

    args = parser.parse_args(argv)

    if args.command == "search":
        results = search_papers(args.query, args.limit, args.source)
        if not results:
            print("No papers found.")
            return 0
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for i, p in enumerate(results, 1):
                print(format_text(p, i))
                print()
        return 0

    if args.command == "verify":
        status, paper = lookup_doi(args.doi)
        if status == "invalid":
            print(f"INVALID: '{args.doi}' is not a DOI.")
            return 1
        if status == "ok":
            print(f"VERIFIED: DOI {normalize_doi(args.doi)} exists.")
            print(format_text(paper, 1))
            return 0
        if status == "not_found":
            print(f"NOT FOUND: DOI {args.doi} does not exist in CrossRef.")
            return 1
        print(f"ERROR: CrossRef lookup failed for {args.doi}. The DOI is not judged; retry later.")
        return 3

    if args.command == "cite":
        status, paper = lookup_doi(args.doi)
        if status != "ok":
            print(f"ERROR: DOI {args.doi} lookup failed ({status}). Citation not generated.")
            return 3 if status == "error" else 1
        if args.fmt == "text":
            print(format_text(paper, args.ref))
        else:
            print(FORMATTERS[args.fmt](paper, args.ref))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
