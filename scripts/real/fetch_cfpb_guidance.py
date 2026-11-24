#!/usr/bin/env python
"""CFPB guidance relevant to EFT / Reg E error resolution and credit-card billing disputes.

Sources:
  * CURATED: hand-picked consumerfinance.gov pages/PDFs (FAQs, exam procedures, small entity compliance
    guides, bulletins, interpretive rules, policy statements). PDFs saved byte-for-byte; HTML pages
    converted to Markdown (main content only, wording unchanged).
  * SUPERVISORY HIGHLIGHTS: crawl https://www.consumerfinance.gov/data-research/research-reports/?title=supervisory+highlights
    (all pages), fetch each issue's PDF, and keep only issues whose text discusses Regulation E / EFTA or
    Regulation Z billing-error resolution (regex on extracted text; see SH_KEEP).
  * FEDERAL REGISTER guidance (non-rule CFPB documents on EFTA): fetched as Markdown from FR body HTML.
Output: data/real/cfpb-guidance/ + index.csv (file, title, doc_type, published_date, source_url, ...)
"""
import csv
import io
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "real" / "cfpb-guidance"
CACHE = ROOT / ".cache" / "real" / "cfpb-guidance"
BASE = "https://www.consumerfinance.gov"
F = "https://files.consumerfinance.gov/f/documents/"
S = requests.Session()
S.headers.update({"User-Agent": "accelerator-research", "Accept-Encoding": "gzip, deflate"})

# (url, title, doc_type, published_date or "")
CURATED = [
    (BASE + "/compliance/compliance-resources/deposit-accounts-resources/electronic-fund-transfers/electronic-fund-transfers-faqs/",
     "Electronic Fund Transfers FAQs (web page)", "FAQ", "2021-12-13"),
    (F + "cfbp_electronic-fund-transfers-faqs.pdf", "Electronic Fund Transfers FAQs (PDF)", "FAQ", "2021-12-13"),
    (BASE + "/compliance/compliance-resources/deposit-accounts-resources/electronic-fund-transfers/",
     "Electronic Fund Transfers compliance resources", "compliance resource page", ""),
    (F + "cfpb_supervision-and-examination-manual_efta-exam-procedures-incl-remittances_2019-03.pdf",
     "Supervision and Examination Manual - Electronic Fund Transfer Act (EFTA) examination procedures (incl. remittances)",
     "examination procedures", "2019-03"),
    (F + "cfpb_supervision-and-examination-manual_prepaid-account-exam-procedures.pdf",
     "Supervision and Examination Manual - Prepaid account examination procedures", "examination procedures", ""),
    (F + "cfpb_remittance-transfer-examination-procedures.pdf",
     "Supervision and Examination Manual - Remittance transfer examination procedures", "examination procedures", ""),
    (F + "cfpb_supervision-and-examination-manual_tila-exam-procedures_2021-10.pdf",
     "Supervision and Examination Manual - Truth in Lending Act (TILA) examination procedures", "examination procedures", "2021-10"),
    (F + "201502_cfpb_credit_card_account_management_examination_guide.pdf",
     "Credit card account management examination procedures", "examination procedures", "2015-02"),
    (F + "cfpb_unfair-deceptive-abusive-acts-practices-udaaps_procedures_2023-09.pdf",
     "Supervision and Examination Manual - UDAAP examination procedures", "examination procedures", "2023-09"),
    (F + "cfpb_prepaid_small-entity-compliance-guide.pdf", "Prepaid Accounts Rule - Small Entity Compliance Guide",
     "small entity compliance guide", ""),
    (F + "cfpb_remittance-transfers_small-entity-compliance-guide.pdf",
     "Remittance Transfer Rule - Small Entity Compliance Guide", "small entity compliance guide", ""),
    (F + "201704_cfpb_Prepaid_execsummary_v2.pdf", "Executive summary of the 2016 prepaid rule", "rule summary", "2017-04"),
    (F + "cfpb_prepaid_executive-summary_2018-amendments.pdf", "Executive summary of the 2018 prepaid rule amendments",
     "rule summary", "2018"),
    (F + "Prepaid_coveragechart_v1_10052016.pdf", "Prepaid account coverage chart", "compliance aid", "2016-10-05"),
    (F + "cfpb_prepaid_payroll-card-key-changes_2018-amendments.pdf", "Prepaid rule key changes for payroll card accounts",
     "compliance aid", "2018"),
    (F + "cfpb_prepaid_government-benefit-accounts_2018-amendments.pdf",
     "Prepaid rule key changes for government benefit accounts", "compliance aid", "2018"),
    (F + "cfpb_remittance-transfers_rule-amendments-executive-summary_2020-05.pdf",
     "Executive summary of the May 2020 Remittance Transfer Rule amendments", "rule summary", "2020-05"),
    (F + "cfpb_bulletin-2022-02_electronic-fund-transfer-act_2022-02.pdf",
     "Bulletin 2022-02: EFTA compulsory use prohibition and government benefit accounts", "compliance bulletin", "2022-02"),
    (F + "cfpb_interpretive-rule_pandemic-relief-payments-reg-e.pdf",
     "Interpretive rule: Treatment of pandemic relief payments under Regulation E", "interpretive rule", "2020-04"),
    (F + "cfpb_statement_regulation-z-error-resolution-covid-19_2020-05.pdf",
     "Statement of Policy on Supervisory and Enforcement Practices Regarding Regulation Z Billing Error Resolution Timeframes (COVID-19) [rescinded 2021-04-01]",
     "policy statement (rescinded)", "2020-05"),
    (F + "cfpb_policy-statement_remittances-covid-19_2020-04.pdf",
     "Statement on supervisory and enforcement practices regarding the Remittance Rule (COVID-19)",
     "policy statement (withdrawn)", "2020-04"),
    (BASE + "/compliance/supervisory-guidance/bulletin-consumer-authorizations-preauthorized-eft/",
     "Compliance Bulletin 2015-06: Requirements for consumer authorizations for preauthorized EFTs", "compliance bulletin", "2015-11"),
    (BASE + "/compliance/supervisory-guidance/bulletin-payroll-card-accounts/",
     "Bulletin 2013-10: Payroll card accounts (Regulation E)", "compliance bulletin", "2013-09"),
    ("https://files.consumerfinance.gov/f/201511_cfpb_compliance-bulletin-2015-06-requirements-for-consumer-authorizations-for-preauthorized-electronic-fund-transfers.pdf",
     "Compliance Bulletin 2015-06: Requirements for consumer authorizations for preauthorized EFTs (PDF)", "compliance bulletin", "2015-11"),
    ("https://files.consumerfinance.gov/f/201309_cfpb_payroll-card-bulletin.pdf",
     "Bulletin 2013-10: Payroll card accounts (Regulation E) (PDF)", "compliance bulletin", "2013-09-12"),
    (BASE + "/compliance/compliance-resources/consumer-cards-resources/prepaid-cards/",
     "Prepaid cards compliance resources", "compliance resource page", ""),
    (BASE + "/compliance/compliance-resources/deposit-accounts-resources/remittance-transfer-rule/",
     "Remittance transfers compliance resources", "compliance resource page", ""),
    (BASE + "/compliance/guidance/withdrawn-guidance/", "Withdrawn guidance (list)", "guidance index", ""),
]

# CFPB guidance published in the Federal Register (non-rule documents) about EFTA / Reg E / billing errors
FR_DOCS = ["2020-08084", "2022-03587", "2025-08286", "2021-06969", "2025-00565", "2025-08646"]

# issues missing from the research-reports listing; PDF URLs verified (HTTP 200) on files.consumerfinance.gov
SH_EXTRA = [("Supervisory Highlights, Issue 30, Summer 2023", F + "cfpb_supervisory-highlights_issue-30_2023-07.pdf", "2023-07"),
            ("Supervisory Highlights, Issue 15, Spring 2017", F + "201704_cfpb_Supervisory-Highlights_Issue-15.pdf", "2017-04")]
SH_LIST = BASE + "/data-research/research-reports/?title=supervisory+highlights&page={}"
SH_KEEP = re.compile(r"(Regulation E|Electronic Fund Transfer Act|EFTA)[\s\S]{0,4000}?"
                     r"(error[- ]resolution|notice of error|unauthorized|provisional credit)"
                     r"|billing[- ]error|Fair Credit Billing", re.I)


def get(url):
    for attempt in range(5):
        try:
            r = S.get(url, timeout=180)
            if r.status_code == 200:
                time.sleep(0.5)
                return r
            if r.status_code in (403, 404, 410):
                print("  HTTP", r.status_code, url)
                return None
        except requests.RequestException as e:
            print("  retry", url, e)
        time.sleep(5 * (attempt + 1))
    return None


def cached(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / re.sub(r"[^A-Za-z0-9.]+", "_", url.split("//", 1)[1])[:200]
    if not p.exists():
        r = get(url)
        if r is None:
            return None
        p.write_bytes(r.content)
    return p.read_bytes()


def html_main_to_md(html, url):
    s = BeautifulSoup(html, "lxml")
    main = s.find("main") or s.body
    for bad in main.select("script, style, nav, .o-breadcrumbs, .m-related-posts, .o-related-posts, footer, form"):
        bad.decompose()
    blocks = []

    def inline(el):
        out = []
        for c in el.children:
            if isinstance(c, NavigableString):
                out.append(str(c))
            elif isinstance(c, Tag):
                if c.name in ("em", "i"):
                    t = inline(c)
                    out.append(f"*{t.strip()}*" if t.strip() else t)
                elif c.name in ("strong", "b"):
                    t = inline(c)
                    out.append(f"**{t.strip()}**" if t.strip() else t)
                elif c.name == "a" and c.get("href"):
                    t = inline(c)
                    out.append(f"[{t.strip()}]({urljoin(url, c['href'])})" if t.strip() else t)
                elif c.name == "br":
                    out.append(" ")
                else:
                    out.append(inline(c))
        return "".join(out)

    def norm(t):
        return re.sub(r"\s+", " ", t).strip()

    def walk(el):
        for c in el.children:
            if isinstance(c, NavigableString):
                t = norm(str(c))
                if t and el.name not in ("ul", "ol", "table", "tr"):
                    blocks.append(t)
                continue
            if not isinstance(c, Tag):
                continue
            if re.fullmatch(r"h[1-6]", c.name):
                t = norm(c.get_text(" "))
                if t:
                    blocks.append("#" * int(c.name[1]) + " " + t)
            elif c.name == "p":
                t = norm(inline(c))
                if t:
                    blocks.append(t)
            elif c.name in ("ul", "ol"):
                items = [norm(inline(li)) for li in c.find_all("li", recursive=False)]
                blocks.append("\n".join(f"- {i}" for i in items if i))
            elif c.name == "table":
                rows = [[norm(td.get_text(" ")).replace("|", "\\|") for td in tr.find_all(["td", "th"])]
                        for tr in c.find_all("tr")]
                rows = [r for r in rows if r]
                if rows:
                    w = max(map(len, rows))
                    rows = [r + [""] * (w - len(r)) for r in rows]
                    blocks.append("\n".join(["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w] +
                                            ["| " + " | ".join(r) + " |" for r in rows[1:]]))
            elif c.name == "summary":
                t = norm(c.get_text(" "))
                if t:
                    blocks.append("**" + t + "**")
            else:
                walk(c)

    walk(main)
    title = s.title.get_text(strip=True) if s.title else ""
    return title, "\n\n".join(b for b in blocks if b) + "\n"


def fr_to_md(dn):
    meta = get(f"https://www.federalregister.gov/api/v1/documents/{dn}.json").json()
    html = cached(meta["body_html_url"]).decode("utf-8", "replace")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fetch_federal_register import html_to_md  # same converter as source 2
    return meta, html_to_md(html)


def pdf_text(b):
    try:
        r = PdfReader(io.BytesIO(b))
        return "\n".join((p.extract_text() or "") for p in r.pages), len(r.pages)
    except Exception as e:  # noqa: BLE001
        return "", 0


def fm(d):
    import json
    return "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in d.items()) + "---\n\n"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    def add(fname, title, doc_type, date, url, note=""):
        rows.append({"file": fname, "title": title, "doc_type": doc_type, "published_date": date,
                     "source_url": url, "note": note})

    for url, title, doc_type, date in CURATED:
        b = cached(url)
        if b is None:
            print("FAILED", url)
            continue
        if url.lower().endswith(".pdf"):
            if not b.startswith(b"%PDF"):
                print("not a pdf", url)
                continue
            fname = url.rsplit("/", 1)[1]
            (OUT / fname).write_bytes(b)
        else:
            ptitle, md = html_main_to_md(b.decode("utf-8", "replace"), url)
            fname = re.sub(r"[^a-z0-9]+", "-", url.rstrip("/").rsplit("/", 1)[1].lower()) + ".md"
            (OUT / fname).write_text(fm({"title": title, "page_title": ptitle, "doc_type": doc_type,
                                         "published_date": date, "source_url": url}) + md, encoding="utf-8")
        add(fname, title, doc_type, date, url)
        print("ok", fname)

    for dn in FR_DOCS:
        try:
            meta, md = fr_to_md(dn)
        except Exception as e:  # noqa: BLE001
            print("FR failed", dn, e)
            continue
        fname = f"FR_{meta['publication_date']}_{dn}.md"
        (OUT / fname).write_text(fm({"title": meta["title"], "doc_type": meta.get("action"), "published_date":
                                     meta["publication_date"], "source_url": meta["body_html_url"],
                                     "html_url": meta["html_url"], "pdf_url": meta["pdf_url"]}) + md, encoding="utf-8")
        add(fname, meta["title"], f"Federal Register: {meta.get('action')}", meta["publication_date"], meta["html_url"])
        print("ok", fname)

    # Supervisory Highlights
    issues, page = [], 1
    while page < 15:
        b = cached(SH_LIST.format(page))
        if b is None:
            break
        s = BeautifulSoup(b, "lxml")
        found = [(a.get_text(" ", strip=True), urljoin(BASE, a["href"]))
                 for a in s.select("main a[href*='/data-research/research-reports/supervisory-highlights']")]
        found = [f for f in found if f[0]]
        if not found:
            break
        issues += found
        if not any(a.get_text(strip=True).startswith("Next") and "page=" in a["href"] for a in s.find_all("a", href=True)):
            break
        page += 1
    seen = set()
    issues = [i for i in issues if not (i[1] in seen or seen.add(i[1]))]
    print("supervisory highlights issues:", len(issues))
    for title, url, date in SH_EXTRA:
        pb = cached(url)
        text, n = pdf_text(pb) if pb else ("", 0)
        if pb and SH_KEEP.search(text):
            fname = url.rsplit("/", 1)[1]
            (OUT / fname).write_bytes(pb)
            hits = len(re.findall(r"error[- ]resolution|billing error", text, re.I))
            add(fname, title, "Supervisory Highlights", date, url,
                f"not in listing; PDF URL verified directly; error-resolution/billing-error mentions: {hits}")
            print("ok SH", fname, hits)
    for title, url in issues:
        b = cached(url)
        if b is None:
            continue
        s = BeautifulSoup(b, "lxml")
        main = s.find("main") or s
        pdf = next((urljoin(BASE, a["href"]) for a in main.find_all("a", href=True) if a["href"].lower().endswith(".pdf")
                    and "supervisory" in a["href"].lower()), None) or \
            next((urljoin(BASE, a["href"]) for a in main.find_all("a", href=True) if a["href"].lower().endswith(".pdf")), None)
        date = ""
        tm = main.find("time")
        if tm and tm.get("datetime"):
            date = tm["datetime"][:10]
        via = "live page"
        if not pdf:
            # Archived issues: the live page only links to CFPB's Archive-It snapshot; take the PDF link from
            # there and download the PDF itself from files.consumerfinance.gov (still served), else the snapshot.
            arch = next((a["href"] for a in main.find_all("a", href=True) if "archive-it.org" in a["href"]), None)
            ab = cached(arch) if arch else None
            if ab:
                links = re.findall(r'href="([^"]+\.pdf)"', ab.decode("utf-8", "replace"))
                links = [l for l in links if "supervisory" in l.lower()] or links
                if links:
                    orig = re.sub(r"^https?://wayback\.archive-it\.org/\d+/\d+\w*/", "", links[0])
                    pdf, via = orig, "archive-it snapshot of issue page"
                    if cached(orig) is None:
                        pdf, via = links[0], "archive-it copy of PDF"
        if not pdf:
            print("  no pdf", url)
            continue
        pb = cached(pdf)
        if pb is None or not pb.startswith(b"%PDF"):
            continue
        text, n = pdf_text(pb)
        m = SH_KEEP.search(text)
        if not m:
            print("  skip (no Reg E/billing error discussion):", title)
            continue
        fname = pdf.rsplit("/", 1)[1]
        (OUT / fname).write_bytes(pb)
        hits = len(re.findall(r"error[- ]resolution|billing error", text, re.I))
        add(fname, title, "Supervisory Highlights", date, pdf, f"issue page {url}; pdf link found via {via}; error-resolution/billing-error mentions: {hits}")
        print("ok SH", fname, hits)

    with open(OUT / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("documents:", len(rows))


if __name__ == "__main__":
    main()
