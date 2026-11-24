#!/usr/bin/env python
"""CFPB enforcement actions about EFTA/Reg E error resolution or card dispute handling.

Method:
  1. Crawl every page of https://www.consumerfinance.gov/enforcement/actions/?page=N (all actions).
  2. Fetch each action page; keep it if its description matches EFT/Reg E/billing-dispute language
     AND dispute/error-resolution/unauthorized language (see RELEVANT below).
  3. Download the "Consent Order" PDF (or Stipulated Final Judgment / Complaint for court cases) as-is,
     and take the first paragraphs of the linked press release as the summary.
Output: data/real/cfpb-enforcement/*.pdf + index.csv
"""
import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "real" / "cfpb-enforcement"
CACHE = ROOT / ".cache" / "real" / "cfpb-enforcement"
BASE = "https://www.consumerfinance.gov"
S = requests.Session()
S.headers.update({"User-Agent": "accelerator-research", "Accept-Encoding": "gzip, deflate"})

EFT = re.compile(r"Electronic Fund Transfer Act|Regulation E\b|EFTA|Fair Credit Billing Act|billing error|"
                 r"Regulation Z.{0,80}(billing|dispute)", re.I)
DISPUTE = re.compile(r"error[- ]resolution|investigat\w* (and resolv\w* )?(consumer )?(disputes|errors|notices of error|claims)|"
                     r"dispute|unauthorized (electronic fund )?(transactions|transfers|charges|EFTs)|notices? of error|"
                     r"provisional credit|chargeback", re.I)
# verified by reading the action pages: card/P2P dispute handling cases whose short page text lacks the keywords
INCLUDE = {"apple-inc", "citizens-bank", "comerica-bank",
           "early-warning-services-llc-bank-of-america-na-jpmorgan-chase-bank-na-wells-fargo-bank-na"}
DOC_PREF = ["consent order", "stipulated final judgment", "stipulated judgment", "final judgment", "order", "complaint"]


def get(url, binary=False):
    for attempt in range(5):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 200:
                time.sleep(0.5)
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    return None


def cached_html(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url.replace(BASE, ""))[:180] + ".html")
    if not p.exists():
        r = get(url)
        if r is None:
            return None
        p.write_text(r.text, encoding="utf-8")
    return p.read_text(encoding="utf-8")


def list_actions():
    actions, page = [], 1
    while True:
        html = cached_html(f"{BASE}/enforcement/actions/?page={page}")
        s = BeautifulSoup(html, "lxml")
        found = 0
        for a in s.select("main a[href^='/enforcement/actions/']"):
            h = a["href"]
            if h.count("/") == 4 and "definitions" not in h and h != "/enforcement/actions/":
                actions.append((a.get_text(" ", strip=True), urljoin(BASE, h)))
                found += 1
        if not found or not any(a.get_text(strip=True).startswith("Next") and "page=" in a["href"] for a in s.find_all("a", href=True)):
            break
        page += 1
    seen, out = set(), []
    for t, u in actions:
        if u not in seen:
            seen.add(u)
            out.append((t, u))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    actions = list_actions()
    print("actions listed:", len(actions))
    rows = []
    for respondent, url in actions:
        html = cached_html(url)
        if not html:
            continue
        s = BeautifulSoup(html, "lxml")
        main_ = s.find("main") or s
        h1 = main_.find("h1")
        desc_parts = []
        for p in main_.find_all("p"):
            t = p.get_text(" ", strip=True)
            if t:
                desc_parts.append(t)
            if len(" ".join(desc_parts)) > 6000:
                break
        desc = " ".join(desc_parts)
        slug = url.rstrip("/").split("/")[-1]
        if not ((EFT.search(desc) and DISPUTE.search(desc)) or slug in INCLUDE):
            continue
        links = [(a.get_text(" ", strip=True), urljoin(BASE, a["href"])) for a in main_.find_all("a", href=True)]
        pdfs = [(t, u) for t, u in links if u.lower().endswith(".pdf")]
        # never pick a dismissal/termination order as the primary document when the order/complaint exists
        primary = [(t, u) for t, u in pdfs if not re.search(r"dismiss|terminat|amend|modif", t, re.I)]
        pdfs = primary + [x for x in pdfs if x not in primary]
        doc = None
        for pref in DOC_PREF:
            doc = next(((t, u) for t, u in primary if t.lower().startswith(pref)), None)
            if doc:
                break
        if not doc and pdfs:
            doc = pdfs[0]
        date = None
        m = re.search(r"On (\w+ \d{1,2}, \d{4})", desc)
        if m:
            date = time.strftime("%Y-%m-%d", time.strptime(m.group(1), "%B %d, %Y"))
        if not date:
            m2 = re.search(r"Initial filing date\s*([A-Z]{3} \d{2}, \d{4})", main_.get_text(" ", strip=True))
            if m2:
                date = time.strftime("%Y-%m-%d", time.strptime(m2.group(1).title(), "%b %d, %Y"))
        docket = ""
        dd = main_.find(string=re.compile("Docket number"))
        if dd and dd.find_parent():
            nxt = dd.find_parent().find_next_sibling()
            docket = nxt.get_text(" ", strip=True) if nxt else ""
        pr = next(((t, u) for t, u in links if "/about-us/newsroom/" in u and u.rstrip("/") != f"{BASE}/about-us/newsroom"), None)
        pr_summary = ""
        if pr:
            ph = cached_html(pr[1])
            if ph:
                ps = BeautifulSoup(ph, "lxml")
                pm = ps.find("main") or ps
                paras = [p.get_text(" ", strip=True) for p in pm.find_all("p")]
                paras = [p for p in paras if len(p) > 120]
                pr_summary = " ".join(paras[:2])
        fname = ""
        if doc:
            fname = f"{date or 'undated'}_{url.rstrip('/').split('/')[-1]}_{re.sub(r'[^a-z]+', '-', doc[0].lower()).strip('-')}.pdf"
            p = OUT / fname
            if not p.exists():
                r = get(doc[1])
                if r is None or not r.content.startswith(b"%PDF"):
                    print("  !! could not download", doc[1])
                    fname = ""
                else:
                    p.write_bytes(r.content)
        rows.append({"file": fname, "respondent": (h1.get_text(" ", strip=True) if h1 else respondent), "date": date or "",
                     "docket_number": docket, "document_type": doc[0] if doc else "",
                     "summary": pr_summary or desc[:1500], "summary_source": "press release" if pr_summary else "action page",
                     "action_page_description": desc[:3000], "source_url": doc[1] if doc else "",
                     "action_page_url": url, "press_release_url": pr[1] if pr else ""})
        print("KEEP", date, respondent[:70], "|", doc[0] if doc else "NO PDF")
    rows.sort(key=lambda r: r["date"], reverse=True)
    with open(OUT / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("kept", len(rows))


if __name__ == "__main__":
    main()
