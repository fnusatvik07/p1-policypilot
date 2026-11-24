#!/usr/bin/env python
"""Build a dispute-focused CFPB Consumer Complaint Database extract.

Two public sources (both CC0 / public domain):
 1. LIVE  CFPB API  https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/
    - filters: product=<Product>, issue=<Issue> or issue=<Issue>•<Sub-issue>  (repeatable params)
    - bulk export: format=csv  (frm/size are ignored, returns all matching rows)  <- used here, 1 call per bucket
    - JSON paging: size<=100, sort=created_date_desc, search_after=<sort[0]>_<complaint_id> of the last hit
    - NOTE: since Aug 2026 the CFPB no longer publishes consumer narratives. `has_narrative` is ignored and
      the API / CSV / bulk zip no longer contain `complaint_what_happened` or "Consumer complaint narrative".
 2. NARRATIVES: a CC0 mirror of the pre-2026 CFPB bulk export (with "Consumer complaint narrative"),
    Hugging Face dataset BEE-spoke-data/consumer-finance-complaints, config `has-text` (2015-03 .. 2024-02).
    Read column-selectively with HTTP Range requests (see httpfile.py). Narrative text is kept verbatim
    (CFPB's own XXXX redactions included).
"""
import io
import sys
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from httpfile import HTTPRangeFile  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "real" / "complaints"
RAW = ROOT / ".cache" / "real" / "complaints"  # raw export cache (kept out of the dataset)
API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
MIRROR = "https://huggingface.co/datasets/BEE-spoke-data/consumer-finance-complaints/resolve/main/has-text/train-0000{i}-of-00003.parquet"
S = requests.Session()
S.headers.update({"User-Agent": "accelerator-research", "Accept-Encoding": "gzip, deflate"})

CHK, CC, CCP, PP, MT = ("Checking or savings account", "Credit card", "Credit card or prepaid card", "Prepaid card",
                        "Money transfer, virtual currency, or money service")
# (product, issue, sub_issue or None, live_cap, narrative_cap)
BUCKETS = [
    (CHK, "Problem with a lender or other company charging your account", None, 5000, 3000),
    (CHK, "Managing an account", "Problem using a debit or ATM card", 4000, 2500),
    (CHK, "Managing an account", "Banking errors", 2500, 1500),
    (CHK, "Managing an account", "Deposits and withdrawals", 2000, 1000),
    (CHK, "Opening an account", "Account opened as a result of fraud", 800, 400),
    (CC, "Problem with a purchase shown on your statement", None, 6000, 2000),
    (CC, "Billing disputes", None, 1500, 600),
    (CC, "Identity theft / Fraud / Embezzlement", None, 1000, 400),
    (CC, "Transaction issue", None, 500, 200),
    (CCP, "Problem with a purchase shown on your statement", None, 3000, 3500),
    (CCP, "Problem with a purchase or transfer", None, 1500, 1200),
    (PP, "Problem with a purchase or transfer", None, 2500, 400),
    (PP, "Unauthorized transactions/trans. issues", None, 1325, 300),
    (PP, "Fraud or scam", None, 735, 300),
    (MT, "Fraud or scam", None, 3500, 2000),
    (MT, "Unauthorized transactions or other transaction problem", None, 3000, 800),
    (MT, "Wrong amount charged or received", None, 1000, 300),
    (MT, "Money was not available when promised", None, 800, 300),
]

COLMAP = {"Date received": "date_received", "Product": "product", "Sub-product": "sub_product", "Issue": "issue",
          "Sub-issue": "sub_issue", "Consumer complaint narrative": "complaint_what_happened",
          "Company public response": "company_public_response", "Company": "company", "State": "state",
          "ZIP code": "zip_code", "Tags": "tags", "Consumer consent provided?": "consumer_consent_provided",
          "Submitted via": "submitted_via", "Date sent to company": "date_sent_to_company",
          "Company response to consumer": "company_response", "Timely response?": "timely",
          "Consumer disputed?": "consumer_disputed", "Complaint ID": "complaint_id"}
COLS = ["complaint_id", "date_received", "product", "sub_product", "issue", "sub_issue", "company", "state",
        "zip_code", "tags", "submitted_via", "date_sent_to_company", "company_response", "timely",
        "company_public_response", "consumer_disputed", "consumer_consent_provided", "complaint_what_happened",
        "has_narrative", "narrative_source", "record_source", "dispute_bucket", "api_query_url"]


SEED = 42


def spread_sample(df, n, date_col="date_received"):
    """Deterministic sample of n rows spread evenly across years (not just the most recent)."""
    if len(df) <= n:
        return df
    yr = df[date_col].str[:4]
    years = sorted(yr.unique())
    out, remaining, quota_left = [], n, len(years)
    sizes = yr.value_counts()
    for y in sorted(years, key=lambda y: sizes[y]):  # small years first, leftover quota flows to big years
        q = remaining // quota_left
        g = df[yr == y]
        take = g.sample(n=min(q, len(g)), random_state=SEED)
        out.append(take)
        remaining -= len(take)
        quota_left -= 1
    return pd.concat(out)


def bucket_name(b):
    return f"{b[0]} | {b[1]}" + (f" | {b[2]}" if b[2] else "")


def live_bucket(b):
    product, issue, sub, cap, _ = b
    params = {"format": "csv", "no_aggs": "true", "product": product,
              "issue": f"{issue}•{sub}" if sub else issue}
    req = requests.Request("GET", API, params=params).prepare()
    safe = "".join(c if c.isalnum() else "_" for c in bucket_name(b))[:120]
    p = RAW / f"live_{safe}.csv"
    if not p.exists():
        for attempt in range(5):
            r = S.get(API, params=params, timeout=600)
            if r.status_code == 200 and r.text.startswith("Date received"):
                p.write_bytes(r.content)
                break
            time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f"live export failed {req.url}")
        time.sleep(0.5)
    df = pd.read_csv(p, dtype=str, keep_default_na=False)
    df = df.rename(columns=COLMAP)
    df = df.replace({"None": None, "": None})
    df["date_received"] = df["date_received"].str[:10]
    df["date_sent_to_company"] = df["date_sent_to_company"].str[:10]
    df = spread_sample(df, cap)
    df["dispute_bucket"] = bucket_name(b)
    df["record_source"] = "cfpb_api_live"
    df["api_query_url"] = req.url
    print(f"live {bucket_name(b)}: total {len(pd.read_csv(p, usecols=[0]))}, kept {len(df)}", flush=True)
    return df


def mirror_rows():
    cache = RAW / "mirror_dispute_narratives.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    keys = {}
    for b in BUCKETS:
        if b[4]:
            keys.setdefault((b[0], b[1]), []).append(b)
    frames = []
    for i in range(3):
        f = HTTPRangeFile(MIRROR.format(i=i), session=S)
        pf = pq.ParquetFile(f)
        meta = pf.read(columns=["Product", "Issue", "Sub-issue"])
        prod, iss = meta["Product"].to_pylist(), meta["Issue"].to_pylist()
        mask = [(p, s) in keys for p, s in zip(prod, iss)]
        # map global row index -> row group
        starts, n = [], 0
        for g in range(pf.num_row_groups):
            starts.append(n)
            n += pf.metadata.row_group(g).num_rows
        groups = sorted({g for g in range(pf.num_row_groups)
                         if any(mask[starts[g]:starts[g] + pf.metadata.row_group(g).num_rows])})
        print(f"mirror file {i}: {sum(mask)} matching rows in {len(groups)}/{pf.num_row_groups} row groups", flush=True)
        for g in groups:
            t = pf.read_row_group(g)
            m = pa.array(mask[starts[g]:starts[g] + t.num_rows])
            frames.append(t.filter(m).to_pandas())
        print(f"   http range requests so far: {f.nreq}", flush=True)
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(cache, index=False)
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    live = pd.concat([live_bucket(b) for b in BUCKETS], ignore_index=True)
    live = live.drop_duplicates("complaint_id")

    m = mirror_rows().rename(columns=COLMAP)
    m["complaint_id"] = m["complaint_id"].astype(str)
    m = m[m["complaint_what_happened"].fillna("").str.strip() != ""]
    parts = []
    for b in BUCKETS:
        if not b[4]:
            continue
        sel = (m["product"] == b[0]) & (m["issue"] == b[1])
        if b[2]:
            sel &= m["sub_issue"] == b[2]
        else:
            # exclude sub-issues already claimed by a more specific bucket
            specific = [x[2] for x in BUCKETS if x[0] == b[0] and x[1] == b[1] and x[2]]
            sel &= ~m["sub_issue"].isin(specific)
        d = spread_sample(m[sel], b[4]).copy()
        d["dispute_bucket"] = bucket_name(b)
        parts.append(d)
        print(f"narr {bucket_name(b)}: avail {int(sel.sum())}, kept {len(d)}")
    narr = pd.concat(parts, ignore_index=True).drop_duplicates("complaint_id")
    narr["record_source"] = "hf_mirror_cfpb_bulk_snapshot"
    narr["api_query_url"] = "https://huggingface.co/datasets/BEE-spoke-data/consumer-finance-complaints (config has-text)"
    narr["narrative_source"] = "CFPB bulk export snapshot (pre-2024-02) via HF mirror BEE-spoke-data/consumer-finance-complaints"

    # attach narratives to live rows that overlap; drop duplicated mirror rows
    nmap = narr.set_index("complaint_id")
    overlap = live["complaint_id"].isin(nmap.index)
    live.loc[overlap, "complaint_what_happened"] = live.loc[overlap, "complaint_id"].map(nmap["complaint_what_happened"])
    live.loc[overlap, "consumer_consent_provided"] = live.loc[overlap, "complaint_id"].map(nmap["consumer_consent_provided"])
    live.loc[overlap, "consumer_disputed"] = live.loc[overlap, "complaint_id"].map(nmap["consumer_disputed"])
    live.loc[overlap, "narrative_source"] = narr["narrative_source"].iloc[0]
    live.loc[overlap, "record_source"] = "cfpb_api_live+hf_mirror_narrative"
    narr = narr[~narr["complaint_id"].isin(live["complaint_id"])]

    df = pd.concat([live, narr], ignore_index=True)
    for c in COLS:
        if c not in df:
            df[c] = None
    df["has_narrative"] = df["complaint_what_happened"].fillna("").str.strip() != ""
    df = df[COLS].sort_values(["has_narrative", "date_received"], ascending=[False, False]).reset_index(drop=True)
    df["complaint_id"] = df["complaint_id"].astype(str)
    df.to_parquet(OUT / "complaints.parquet", index=False)
    df.head(1000).to_csv(OUT / "complaints_sample.csv", index=False)

    yr = df["date_received"].str[:4]
    with open(OUT / "README_stats.txt", "w") as f:
        f.write(f"CFPB Consumer Complaint Database - dispute-focused extract\nrows: {len(df)}\n")
        f.write(f"with narrative: {int(df.has_narrative.sum())}\nwithout narrative: {int((~df.has_narrative).sum())}\n")
        f.write(f"date range: {df.date_received.min()} .. {df.date_received.max()}\n\n")
        f.write("NOTE: The CFPB stopped publishing consumer narratives in Aug 2026; the live API/CSV no longer\n"
                "return complaint_what_happened (has_narrative param is ignored). Narratives here come from a CC0\n"
                "mirror of the earlier CFPB bulk export (BEE-spoke-data/consumer-finance-complaints, 2015-03..2024-02).\n\n")
        for title, s in [("record_source", df.record_source), ("dispute_bucket", df.dispute_bucket),
                         ("product", df["product"]), ("issue", df["issue"]), ("year", yr)]:
            f.write(f"== by {title} (rows / with narrative)\n")
            g = df.groupby(s).has_narrative.agg(["size", "sum"]).sort_values("size", ascending=False)
            for k, r in g.iterrows():
                f.write(f"  {r['size']:>7} / {r['sum']:>6}  {k}\n")
            f.write("\n")
        f.write("== top 40 companies (rows / with narrative)\n")
        g = df.groupby("company").has_narrative.agg(["size", "sum"]).sort_values("size", ascending=False).head(40)
        for k, r in g.iterrows():
            f.write(f"  {r['size']:>7} / {r['sum']:>6}  {k}\n")
    print("rows", len(df), "narratives", int(df.has_narrative.sum()))


if __name__ == "__main__":
    main()
