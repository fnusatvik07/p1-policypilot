#!/usr/bin/env python
"""Fetch versioned regulation text from the eCFR Versioner API and write Markdown.

Regulations:
  Reg E  = 12 CFR 1005 (all sections, appendices, Supplement I)
  Reg Z  = 12 CFR 1026: 1026.2, 1026.12, 1026.13 + Supplement I commentary for 1026.12/1026.13
  Reg CC = 12 CFR 229: 229.10-229.13

API used (compression required):
  GET https://www.ecfr.gov/api/versioner/v1/versions/title-12.json?part=1005
  GET https://www.ecfr.gov/api/versioner/v1/full/{date}/title-12.xml?part=1005&section=1005.11
  GET https://www.ecfr.gov/api/versioner/v1/full/{date}/title-12.xml?part=1005&appendix=Appendix%20A%20to%20Part%201005

Re-runnable: raw XML is cached in data/real/regulations/_raw/ and skipped if present.
Text is never altered; XML elements are mapped to Markdown markup only.
"""
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "real" / "regulations"
RAW = ROOT / ".cache" / "real" / "ecfr"  # raw XML cache (kept out of the dataset)
BASE = "https://www.ecfr.gov/api/versioner/v1"
S = requests.Session()
S.headers.update({"User-Agent": "accelerator-research", "Accept-Encoding": "gzip, deflate"})

CONFIG = {
    "reg-e": {"part": "1005", "sections": None},  # None => everything in the part
    "reg-z": {"part": "1026", "sections": ["1026.2", "1026.12", "1026.13"],
              "supplement_extract": {"Supplement I to Part 1026": ["1026.12", "1026.13"]}},
    "reg-cc": {"part": "229", "sections": ["229.10", "229.11", "229.12", "229.13"]},
}


def get(url, **kw):
    for attempt in range(5):
        try:
            r = S.get(url, timeout=120, **kw)
            if r.status_code == 200:
                time.sleep(0.5)
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print("  retry", url, e, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"failed {url}")


def full_url(date, part, identifier, kind):
    params = {"part": part}
    if kind == "section":
        params["section"] = identifier
    else:
        params["appendix"] = identifier
    return f"{BASE}/full/{date}/title-12.xml?" + urlencode(params, quote_via=quote)


def fetch_xml(date, part, identifier, kind):
    safe = re.sub(r"[^A-Za-z0-9.]+", "_", identifier)
    p = RAW / part / safe / f"{date}.xml"
    url = full_url(date, part, identifier, kind)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(get(url).content)
    return p.read_bytes(), url


# ---------------- XML -> Markdown ----------------
def inline(el):
    """Render inline content of an element to Markdown (text unchanged)."""
    out = [el.text or ""]
    for ch in el:
        tag = ch.tag if isinstance(ch.tag, str) else ""
        inner = inline(ch)
        if tag in ("I",) or (tag == "E" and ch.get("T") in ("03", "04", "05", "51", "52", "7462")):
            if ch.get("T") in ("51",):
                inner_md = f"<sub>{inner}</sub>"
            elif ch.get("T") in ("52",):
                inner_md = f"<sub>{inner}</sub>"
            elif inner.strip():
                lead = inner[: len(inner) - len(inner.lstrip())]
                trail = inner[len(inner.rstrip()):]
                inner_md = f"{lead}*{inner.strip()}*{trail}"
            else:
                inner_md = inner
        elif tag == "B" or (tag == "E" and ch.get("T") in ("02",)):
            inner_md = f"**{inner.strip()}**" if inner.strip() else inner
        elif tag == "SU":
            inner_md = f"<sup>{inner}</sup>"
        elif tag == "img":
            inner_md = f"![image]({ch.get('src', '')})"
        elif tag == "br":
            inner_md = "  \n"
        else:
            inner_md = inner
        out.append(inner_md)
        out.append(ch.tail or "")
    return "".join(out)


def clean(s):
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


def table_md(tbl):
    rows = []
    for row in tbl.iter("BOXHD", "ROW"):
        if row.tag == "BOXHD":
            rows.append([clean(inline(c)) for c in row if c.tag == "CHED"])
        else:
            rows.append([clean(inline(c)) for c in row if c.tag == "ENT"])
    rows = [r for r in rows if r]
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    esc = lambda x: x.replace("|", "\\|")
    lines = ["| " + " | ".join(esc(c) for c in rows[0]) + " |", "|" + "---|" * w]
    lines += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows[1:]]
    ttl = tbl.find("TTITLE")
    head = f"**{clean(inline(ttl))}**\n\n" if ttl is not None and clean(inline(ttl)) else ""
    return head + "\n".join(lines)


HEAD_LEVEL = {"HEAD": 1, "HD1": 2, "HD2": 3, "HD3": 4, "HD4": 5, "HD5": 5, "HD6": 6}


def block_md(el, blocks):
    tag = el.tag if isinstance(el.tag, str) else ""
    if tag in HEAD_LEVEL:
        t = clean(inline(el))
        if t:
            blocks.append("#" * HEAD_LEVEL[tag] + " " + t)
    elif tag in ("P", "FP", "NOTE", "PSPACE"):
        t = clean(inline(el))
        if t:
            blocks.append(t)
    elif tag == "XREF":
        t = clean(inline(el))
        if t:
            blocks.append("> " + t)
    elif tag in ("CITA", "SECAUTH", "AUTH", "SOURCE", "EDNOTE", "EFFDNOT"):
        t = clean(inline(el))
        if t:
            blocks.append("> " + t)
    elif tag == "GPOTABLE":
        blocks.append(table_md(el))
    elif tag == "img":
        blocks.append(f"![image]({el.get('src', '')})")
    elif tag in ("FTNT",):
        t = clean(inline(el))
        if t:
            blocks.append("[^note] " + t)
    else:
        # containers (DIV*, EXTRACT, NOTE wrappers, etc.)
        children = [c for c in el if isinstance(c.tag, str)]
        if not children:
            t = clean(inline(el))
            if t:
                blocks.append(t)
        for c in children:
            block_md(c, blocks)


def to_markdown(root):
    blocks = []
    block_md(root, blocks)
    return "\n\n".join(b for b in blocks if b) + "\n"


def extract_supplement_section(root, sec):
    """Return a synthetic element holding the commentary block for `sec` (HD2 'Section 1026.12—...')."""
    pat = re.compile(r"^\s*Section\s+" + re.escape(sec) + r"\b")
    # commentary for Reg Z is a flat sequence of siblings under DIV9
    kids = [c for c in root if isinstance(c.tag, str)]
    start = None
    for i, c in enumerate(kids):
        if c.tag == "HD2" and pat.match("".join(c.itertext())):
            start = i
            break
    if start is None:
        return None
    holder = etree.Element("DIV")
    for c in kids[start:]:
        if c is not kids[start] and c.tag in ("HD1", "HD2"):
            break
        holder.append(etree.fromstring(etree.tostring(c)))
    return holder


def yaml_val(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return json.dumps(str(v), ensure_ascii=False)


def write_md(path, meta, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = "---\n" + "".join(f"{k}: {yaml_val(v)}\n" for k, v in meta.items()) + "---\n\n"
    path.write_text(fm + body, encoding="utf-8")


def section_slug(identifier):
    m = re.match(r"(Appendix [A-Z]+|Supplement [IVX]+) to Part \d+", identifier)
    if m:
        return m.group(1).lower().replace(" ", "-")
    return identifier


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for reg, cfg in CONFIG.items():
        part = cfg["part"]
        vurl = f"{BASE}/versions/title-12.json?part={part}"
        versions = get(vurl).json()["content_versions"]
        (RAW).mkdir(parents=True, exist_ok=True)
        (RAW / f"versions_part{part}.json").write_text(json.dumps(versions, indent=1))
        by_id = {}
        for v in versions:
            by_id.setdefault(v["identifier"], []).append(v)
        wanted = cfg["sections"] if cfg["sections"] else sorted(by_id)
        targets = [(i, by_id[i][0]["type"], None) for i in wanted]
        for supp, secs in cfg.get("supplement_extract", {}).items():
            for s in secs:
                targets.append((supp, "appendix", s))
        for identifier, kind, sub in targets:
            vs = by_id.get(identifier, [])
            dates = sorted({v["date"] for v in vs})
            print(f"{reg} {identifier} {sub or ''}: {len(dates)} versions", flush=True)
            sid = section_slug(identifier) if sub is None else f"supplement-i-{sub}"
            prev_hash = None
            kept = []
            for d in dates:
                entries = [v for v in vs if v["date"] == d]
                raw, url = fetch_xml(d, part, identifier, kind)
                root = etree.fromstring(raw)
                if sub:
                    node = extract_supplement_section(root, sub)
                    if node is None:
                        print("   missing", sub, d)
                        continue
                    body = to_markdown(node)
                    h = hashlib.sha256(body.encode()).hexdigest()
                    if h == prev_hash:
                        continue  # commentary for this section unchanged at this supplement version
                    prev_hash = h
                    title = clean("".join(node[0].itertext()))
                    substantive = True
                else:
                    body = to_markdown(root)
                    head = root.find("HEAD")
                    title = clean("".join(head.itertext())) if head is not None else entries[0]["name"]
                    substantive = any(v["substantive"] for v in entries)
                kept.append(dict(date=d, url=url, body=body, title=title, substantive=substantive,
                                 removed=any(v["removed"] for v in entries if v["substantive"]),
                                 issue_dates=sorted({v["issue_date"] for v in entries})))
            for i, k in enumerate(kept):
                nxt = kept[i + 1]["date"] if i + 1 < len(kept) else None
                meta = {
                    "source_url": k["url"], "regulation": reg, "part": part,
                    "section": sid if sub is None else f"Supplement I to Part {part}, Section {sub}",
                    "title": k["title"], "version_effective_date": k["date"],
                    "next_version_date": nxt, "substantive": k["substantive"],
                    "removed_flag_in_ecfr": k["removed"],
                    "ecfr_issue_dates": ",".join(k["issue_dates"]),
                }
                p = OUT / reg / sid / f"{k['date']}.md"
                write_md(p, meta, k["body"])
                rows.append({"regulation": reg, "part": part, "section_id": sid, "title": k["title"],
                             "version_effective_date": k["date"], "next_version_date": nxt or "",
                             "substantive": k["substantive"], "removed_flag_in_ecfr": k["removed"],
                             "file": str(p.relative_to(ROOT / "data" / "real")), "chars": len(k["body"]),
                             "source_url": k["url"]})
    with open(OUT / "versions_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "section-versions")


if __name__ == "__main__":
    main()
