#!/usr/bin/env python
"""Write data/real/MANIFEST.json + data/real/SUMMARY.md and run self-checks.

Checks: every MANIFEST file exists (and sha256 matches), PDFs open with pypdf and have extractable text
(image-only flagged), Markdown files non-empty (beyond front matter), regulation versions per section are
chronologically consistent (next_version_date chain), complaints parquet loads with expected columns.
"""
import csv
import hashlib
import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

warnings.filterwarnings("ignore")
import logging  # noqa: E402

logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "real"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def front_matter(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(": ")
            try:
                meta[k] = json.loads(v)
            except Exception:  # noqa: BLE001
                meta[k] = None if v == "null" else v
    return meta, t[m.end():] if m else t


def load_index(path, key="file"):
    if not path.exists():
        return {}
    with open(path) as f:
        return {r[key]: r for r in csv.DictReader(f)}


def source_url_for(rel, p):
    parts = rel.split("/")
    if p.suffix == ".md":
        meta, _ = front_matter(p)
        if meta.get("source_url"):
            return meta["source_url"]
    if parts[0] == "regulations":
        return "https://www.ecfr.gov/api/versioner/v1/"
    if parts[0] == "federal-register":
        return "https://www.federalregister.gov/api/v1/documents.json"
    if parts[0] == "cfpb-guidance":
        return GUID.get(parts[-1], {}).get("source_url") or "https://www.consumerfinance.gov/"
    if parts[0] == "cfpb-enforcement":
        return ENF.get(parts[-1], {}).get("source_url") or "https://www.consumerfinance.gov/enforcement/actions/"
    if parts[0] == "complaints":
        return ("https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/ ; "
                "https://huggingface.co/datasets/BEE-spoke-data/consumer-finance-complaints (narratives)")
    if parts[0] == "calendar":
        return "python package `holidays` (US federal calendar)"
    return ""


GUID = load_index(DATA / "cfpb-guidance" / "index.csv")
ENF = load_index(DATA / "cfpb-enforcement" / "index.csv")


def main():
    files = sorted(p for p in DATA.rglob("*") if p.is_file() and p.name not in ("MANIFEST.json", "SUMMARY.md")
                   and not p.name.startswith(".") and not p.name.startswith("_"))
    manifest = []
    for p in files:
        rel = str(p.relative_to(DATA))
        manifest.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha(p), "source_url": source_url_for(rel, p)})
    (DATA / "MANIFEST.json").write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                    "file_count": len(manifest),
                                                    "total_bytes": sum(m["bytes"] for m in manifest),
                                                    "files": manifest}, indent=1))

    problems, notes = [], []
    # 1. manifest files exist + hash
    for m in json.loads((DATA / "MANIFEST.json").read_text())["files"]:
        p = DATA / m["path"]
        if not p.exists():
            problems.append(f"missing: {m['path']}")
        elif sha(p) != m["sha256"]:
            problems.append(f"hash mismatch: {m['path']}")
    # 2. PDFs
    pdf_stats = {}
    for p in files:
        if p.suffix.lower() != ".pdf":
            continue
        try:
            r = PdfReader(str(p))
            n = len(r.pages)
            sample = [r.pages[i] for i in sorted({0, n // 2, n - 1})]
            chars = sum(len((pg.extract_text() or "").strip()) for pg in sample)
            pdf_stats[str(p.relative_to(DATA))] = (n, chars)
            if chars < 200:
                notes.append(f"PDF looks image-only / little text: {p.relative_to(DATA)} ({n} pages, {chars} chars on sampled pages)")
        except Exception as e:  # noqa: BLE001
            problems.append(f"PDF unreadable: {p.relative_to(DATA)}: {e}")
    # 3. markdown non-empty
    for p in files:
        if p.suffix == ".md":
            _, body = front_matter(p)
            if len(body.strip()) < 50 and "[Reserved]" in body:
                notes.append(f"reserved section (heading only, as published): {p.relative_to(DATA)}")
            elif len(body.strip()) < 50:
                problems.append(f"markdown nearly empty: {p.relative_to(DATA)} ({len(body.strip())} chars)")
    # 4. regulation chronology
    idx = pd.read_csv(DATA / "regulations" / "versions_index.csv", dtype=str, keep_default_na=False)
    for (reg, sec), g in idx.groupby(["regulation", "section_id"]):
        g = g.sort_values("version_effective_date")
        d = list(g.version_effective_date)
        nx = list(g.next_version_date)
        if len(set(d)) != len(d):
            problems.append(f"duplicate version dates {reg}/{sec}")
        for i in range(len(d)):
            want = d[i + 1] if i + 1 < len(d) else ""
            if nx[i] != want:
                problems.append(f"chronology break {reg}/{sec} {d[i]} next={nx[i]} expected={want}")
        for f_ in g.file:
            meta, _ = front_matter(DATA / f_)
            if meta.get("version_effective_date") != Path(f_).stem:
                problems.append(f"front-matter date mismatch {f_}")
    # 5. complaints
    expected = {"complaint_id", "date_received", "product", "sub_product", "issue", "sub_issue", "company", "state",
                "company_response", "timely", "complaint_what_happened", "has_narrative", "record_source"}
    cdf = pd.read_parquet(DATA / "complaints" / "complaints.parquet")
    miss = expected - set(cdf.columns)
    if miss:
        problems.append(f"complaints parquet missing columns {miss}")
    if cdf.complaint_id.duplicated().any():
        problems.append("duplicate complaint_id in parquet")

    # ---- SUMMARY.md
    by_dir = defaultdict(lambda: [0, 0])
    for m in manifest:
        k = m["path"].split("/")[0]
        by_dir[k][0] += 1
        by_dir[k][1] += m["bytes"]
    fr = pd.read_csv(DATA / "federal-register" / "index.csv")
    guid = pd.read_csv(DATA / "cfpb-guidance" / "index.csv")
    enf = pd.read_csv(DATA / "cfpb-enforcement" / "index.csv")
    hol = pd.read_csv(DATA / "calendar" / "us_federal_holidays.csv")
    regs = idx.groupby("regulation").agg(sections=("section_id", "nunique"), versions=("section_id", "size"))
    L = ["# data/real - public source data (unmodified text)", "",
         f"Generated {datetime.now(timezone.utc).date()} by `scripts/real/*.py`. {len(manifest)} files, "
         f"{sum(m['bytes'] for m in manifest) / 1e6:.1f} MB. Checksums in `MANIFEST.json`.", "",
         "| folder | files | MB |", "|---|---|---|"]
    L += [f"| {k} | {v[0]} | {v[1] / 1e6:.1f} |" for k, v in sorted(by_dir.items())]
    L += ["", "## 1. Regulations (eCFR Versioner API)", "",
          "| regulation | sections/appendices | section-versions |", "|---|---|---|"]
    L += [f"| {r} | {row.sections} | {row.versions} |" for r, row in regs.iterrows()]
    L += ["", "Reg E = 12 CFR 1005 (all 26 sections + appendices A-C + Supplement I, 2017-01-01 onward); "
          "Reg Z = 1026.2/.12/.13 + Supplement I commentary for 1026.12 and 1026.13 (extracted from the full "
          "Supplement I at each of its 77 versions, kept only when that commentary's text changed); "
          "Reg CC = 229.10-229.13. eCFR point-in-time history starts 2017-01-01, so earlier versions are not available.", "",
          "## 2. Federal Register final rules", "",
          f"{len(fr)} CFPB final rules (2011-2024) amending 12 CFR 1005 or touching 1026.12/1026.13: "
          f"{int(fr.selection_reason.str.contains('1005').sum())} amend part 1005, "
          f"{int(fr.selection_reason.str.contains('1026.12').sum())} touch 1026.12/13. {int(fr.words.sum()):,} words.", "",
          "## 3. CFPB guidance", "", f"{len(guid)} documents: " +
          ", ".join(f"{k} {v}" for k, v in guid.doc_type.value_counts().items()) + ".", "",
          "## 4. CFPB enforcement", "", f"{len(enf)} actions ({enf.date.min()} .. {enf.date.max()}); "
          f"{int(enf.file.notna().sum())} primary documents (consent orders / complaints / judgments).", "",
          "## 5. Consumer complaints", "",
          f"{len(cdf):,} complaints, {int(cdf.has_narrative.sum()):,} with narrative. "
          + ", ".join(f"{k}: {v:,}" for k, v in cdf.record_source.value_counts().items()) + ".", "",
          "## 6. Calendar", "", f"{len(hol)} rows (US federal holidays 2017-2027, actual + observed dates).", "",
          "## Gaps / caveats", "",
          "- **Complaint narratives are no longer published by the CFPB** (policy change Aug 2026): the live API "
          "ignores `has_narrative` and returns no `complaint_what_happened`; the bulk CSV dropped the narrative and "
          "consent columns. Narratives here come from a CC0 Hugging Face mirror of the earlier official bulk export "
          "(`BEE-spoke-data/consumer-finance-complaints`, config `has-text`, 2015-03..2024-02), verbatim, "
          "flagged in `record_source` / `narrative_source`.",
          "- Live complaint records (2011-2026) have structured fields only.",
          "- CFPB Supervisory Highlights issue pages are archived (content only on CFPB's Archive-It collection); "
          "PDFs were located via the snapshot and downloaded from files.consumerfinance.gov.",
          "- Many CFPB guidance documents were withdrawn on 2025-05-12 (FR 2025-08286); withdrawn/rescinded items "
          "kept here are labelled as such in index.csv and remain useful as historical context.",
          "- Several 2024-2025 enforcement matters were later terminated or dismissed (e.g. Comerica, Zelle/EWS "
          "dismissed 2025; Navy Federal overdraft order terminated). Navy Federal (overdraft / debt collection) and "
          "Wells Fargo 2022 were reviewed and excluded as not about dispute/error-resolution handling.",
          "- eCFR point-in-time data begins 2017-01-01.", ""]
    L += ["## Self-check", "", f"- problems: {len(problems)}"] + [f"  - {x}" for x in problems] + \
         [f"- notes: {len(notes)}"] + [f"  - {x}" for x in notes] + [""]
    (DATA / "SUMMARY.md").write_text("\n".join(L))
    print("\n".join(L[-(len(problems) + len(notes) + 4):]))
    print("files", len(manifest), "bytes", sum(m["bytes"] for m in manifest))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
