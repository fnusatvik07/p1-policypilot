#!/usr/bin/env python
"""Fetch CFPB final rules amending 12 CFR 1005 or 12 CFR 1026.12/1026.13 from the Federal Register API.

API (no key needed):
  GET https://www.federalregister.gov/api/v1/documents.json
      ?conditions[cfr][title]=12&conditions[cfr][part]=1005
      &conditions[type][]=RULE
      &conditions[agencies][]=consumer-financial-protection-bureau
      &conditions[publication_date][gte]=2010-01-01
      &per_page=1000&fields[]=...
Full text: the `body_html_url` of each document (converted to Markdown; wording unchanged).

Selection:
  * part 1005: every CFPB RULE whose `action` contains "final rule" (incl. interim final, corrections, delays)
  * part 1026: same, AND the document text contains amendatory language / commentary headings for
    1026.12 or 1026.13 (e.g. "Section 1026.12 is amended", "Section 1026.13—Billing Error Resolution",
    "§ 1026.12 ... revised").
"""
import csv
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "real" / "federal-register"
RAW = ROOT / ".cache" / "real" / "federal-register"  # raw HTML cache
API = "https://www.federalregister.gov/api/v1/documents.json"
S = requests.Session()
S.headers.update({"User-Agent": "accelerator-research", "Accept-Encoding": "gzip, deflate"})
FIELDS = ["document_number", "title", "publication_date", "effective_on", "action", "type", "agencies",
          "cfr_references", "html_url", "pdf_url", "body_html_url", "raw_text_url", "page_length",
          "start_page", "end_page", "citation", "abstract", "docket_ids", "regulation_id_numbers"]

REGZ_PAT = re.compile(
    r"(Section|§)\s*1026\.1[23]\b[^.\n]{0,120}?\b(is|are)\s+(amended|revised|added)"
    r"|(Section|§)\s*1026\.1[23]\s*[—-]\s*(Special Credit Card|Billing Error)"
    r"|Under\s+Section\s+1026\.1[23]\b",
    re.I)


def get(url, params=None):
    for attempt in range(5):
        r = S.get(url, params=params, timeout=120)
        if r.status_code == 200:
            time.sleep(0.5)
            return r
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()


def search(part):
    params = [("per_page", "1000"), ("conditions[cfr][title]", "12"), ("conditions[cfr][part]", part),
              ("conditions[type][]", "RULE"), ("conditions[agencies][]", "consumer-financial-protection-bureau"),
              ("conditions[publication_date][gte]", "2010-01-01"), ("order", "oldest")]
    params += [("fields[]", f) for f in FIELDS]
    out, url = [], API
    while url:
        d = get(url, params).json()
        out += d.get("results", [])
        url, params = d.get("next_page_url"), None
    return out


def html_to_md(html):
    soup = BeautifulSoup(html, "lxml")
    body = soup.body or soup
    blocks = []

    def text_of(el):
        parts = []
        for c in el.children:
            if isinstance(c, NavigableString):
                parts.append(str(c))
            elif isinstance(c, Tag):
                if c.name in ("em", "i"):
                    t = text_of(c)
                    parts.append(f"*{t.strip()}*" if t.strip() else t)
                elif c.name in ("strong", "b"):
                    t = text_of(c)
                    parts.append(f"**{t.strip()}**" if t.strip() else t)
                elif c.name == "sup":
                    parts.append(f"<sup>{text_of(c)}</sup>")
                elif c.name == "br":
                    parts.append("\n")
                else:
                    parts.append(text_of(c))
        return "".join(parts)

    def norm(t):
        return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\s*\n\s*", "\n", t)).strip()

    def walk(el):
        for c in el.children:
            if isinstance(c, NavigableString):
                t = norm(str(c))
                if t:
                    blocks.append(t)
                continue
            if not isinstance(c, Tag):
                continue
            n = c.name
            if n in ("script", "style"):
                continue
            if re.fullmatch(r"h[1-6]", n):
                t = norm(text_of(c)).replace("\n", " ")
                if t:
                    blocks.append("#" * int(n[1]) + " " + t)
            elif n == "p":
                t = norm(text_of(c))
                if t:
                    blocks.append(t)
            elif n in ("ul", "ol"):
                for li in c.find_all("li", recursive=False):
                    t = norm(text_of(li))
                    if t:
                        blocks.append("- " + t.replace("\n", " "))
            elif n == "table":
                rows = []
                for tr in c.find_all("tr"):
                    cells = [norm(text_of(td)).replace("\n", " ").replace("|", "\\|")
                             for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    w = max(len(r) for r in rows)
                    rows = [r + [""] * (w - len(r)) for r in rows]
                    md = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
                    md += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                    blocks.append("\n".join(md))
            elif n == "pre":
                blocks.append("```\n" + c.get_text() + "\n```")
            elif n == "img":
                blocks.append(f"![image]({c.get('src', '')})")
            else:
                walk(c)

    walk(body)
    return "\n\n".join(blocks) + "\n"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    docs = {}
    for part in ("1005", "1026"):
        for d in search(part):
            if "final rule" not in (d.get("action") or "").lower():
                continue
            if not any(a.get("slug") == "consumer-financial-protection-bureau" for a in d["agencies"]):
                continue
            docs.setdefault(d["document_number"], d)
    print("candidates", len(docs))
    rows = []
    for dn, d in sorted(docs.items(), key=lambda kv: kv[1]["publication_date"]):
        raw = RAW / f"{dn}.html"
        if not raw.exists():
            raw.write_bytes(get(d["body_html_url"]).content)
        html = raw.read_text(encoding="utf-8", errors="replace")
        parts = {str(c.get("part")) for c in d.get("cfr_references") or []}
        md = html_to_md(html)
        hits_regz = bool(REGZ_PAT.search(md))
        if "1005" not in parts and not hits_regz:
            continue  # 1026-only rule that does not touch 1026.12/1026.13
        reason = []
        if "1005" in parts:
            reason.append("amends 12 CFR 1005")
        if hits_regz:
            reason.append("touches 12 CFR 1026.12/1026.13")
        fname = f"{d['publication_date']}_{dn}.md"
        cfr = "; ".join(f"{c.get('title')} CFR {c.get('part')}" for c in d.get("cfr_references") or [])
        fm = ("---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
                                for k, v in [("document_number", dn), ("title", d["title"]),
                                             ("citation", d.get("citation")), ("action", d.get("action")),
                                             ("publication_date", d["publication_date"]),
                                             ("effective_on", d.get("effective_on")), ("cfr_references", cfr),
                                             ("selection_reason", ", ".join(reason)),
                                             ("source_url", d["body_html_url"]), ("html_url", d["html_url"]),
                                             ("pdf_url", d["pdf_url"])]) + "---\n\n")
        (OUT / fname).write_text(fm + md, encoding="utf-8")
        rows.append({"file": fname, "document_number": dn, "title": d["title"], "citation": d.get("citation"),
                     "action": d.get("action"), "publication_date": d["publication_date"],
                     "effective_on": d.get("effective_on") or "", "cfr_references": cfr,
                     "selection_reason": ", ".join(reason), "html_url": d["html_url"], "pdf_url": d["pdf_url"],
                     "body_html_url": d["body_html_url"], "page_length": d.get("page_length"),
                     "words": len(md.split())})
        print(fname, reason)
    with open(OUT / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("kept", len(rows))


if __name__ == "__main__":
    main()
