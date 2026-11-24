# Data guide — P1-POLICYPILOT

Everything a student needs is in this repository. Sizes are approximate.

## 1. `data/corpus/` — Harborline's document library (364 files, ~28 MB)

Exported as-is from five source systems, so folder layout, file names and formats differ by system.

| Folder | Source system | Typical content |
|---|---|---|
| `policy-portal/` | PolicyHub | Board-approved policies (with `_Archive` of old versions), customer agreements & disclosures, assurance / audit reports |
| `sharepoint/` | Disputes Ops Library, Consumer Compliance Committee | SOPs, job aids, memos and ops bulletins (by year), letter templates, committee minutes & decks |
| `wiki/OpsWiki/` | OpsWiki (Confluence) | how-to pages, FAQs, cheat sheets (some outdated but still linked) |
| `shared-drive/S_CPS_Disputes/` | Shared drive `S:\CPS\Disputes` | trackers, spreadsheets, working copies |
| `email/YYYY-MM/` | Exchange archive | `.eml` threads where decisions and exceptions are discussed |

File types: docx 159 · html 98 · pdf 66 · eml 20 · xlsx 13 · pptx 8.
Document IDs look like `POL-001`, `CPS-SOP-211`, `JA-114`, `WI-031`, `MEMO-2021-08`, `OB-2026-21`, `IA-2021-07`, `EML-008`.

## 2. `data/registry/dms_export.csv` — document registry

One row per file: `path, source_system, doc_id, title, version, status, effective_date, owner, last_modified`.
Statuses: `active`, `superseded`, `final`, `expired` (and some blank). Treat it like a real DMS export — useful, but not always complete or correct; the documents themselves are the source of truth.

## 3. `data/db/` — disputes case database (~150 MB)

Same data in three forms: `harborline_disputes.sqlite`, `csv/*.csv`, and `schema_postgres.sql` + `load_postgres.sql`.

| Table | Rows | |
|---|---|---|
| customers | 6,500 | |
| accounts | 10,853 | checking, savings, credit card, prepaid |
| cards | 10,853 | |
| transactions | 248,761 | |
| statements | 472,007 | statement cycles (needed for 60-day / billing-cycle rules) |
| dispute_cases | 8,182 | case number `HL-YYYY-NNNNNN`, regime (Reg E / Reg Z), dates, amounts, outcome |
| case_events | 54,176 | notice, provisional credit, letters, decisions… |
| chargebacks | 2,737 | network chargebacks linked to cases |
| letters | 13,955 | customer letters sent |
| analysts | 128 | |
| holidays | 145 | bank holiday calendar |

## 4. `changes/release-NN_*/` — change feed

Each release has `events.jsonl` plus a `files/` folder. Event fields:
`event_id, emitted_at, source_system, action (UPSERT | RETIRE | DELETE), doc_id, version, title, effective_from, file, target_path, sha256, supersedes, comment`.
Apply releases in order. `effective_from` can be in the future — the new rule is not in force until then.

## 5. `data/real/` — real public data (unmodified text)

| Folder | Content |
|---|---|
| `regulations/` | Point-in-time versions of Reg E (12 CFR 1005, all sections, appendices, official interpretations), Reg Z 1026.2/.12/.13 + commentary, Reg CC 229.10–229.13, as Markdown with front matter (`version_effective_date`, `next_version_date`). Index: `versions_index.csv` |
| `federal-register/` | CFPB final rules that amended these regulations, as Markdown + `index.csv` |
| `cfpb-guidance/` | EFT FAQs, examination procedures, compliance guides, bulletins, Supervisory Highlights (PDF/MD) + `index.csv` |
| `cfpb-enforcement/` | Consent orders / complaints about dispute and error-resolution failures + `index.csv` with summaries |
| `complaints/` | ~56,600 CFPB consumer complaints about disputes, unauthorized transactions and fraud (~20,500 with the consumer's own narrative). `complaints.parquet`, `complaints_sample.csv`, `README_stats.txt` |
| `calendar/` | US federal holidays (actual + observed dates, Federal Reserve closures) |

`data/real/MANIFEST.json` lists every file with sha256 and source URL; `SUMMARY.md` lists counts and known gaps. Rebuild with `scripts/real/*.py`.

## 6. `eval/questions_public.jsonl` — 117 public questions

Fields: `id, qtype, question, answer, as_of, citations[{doc_id, version, quote}], reg_refs, difficulty, requires, notes`.

| qtype | n | What it tests |
|---|---|---|
| document_detail | 30 | find the specific rule in the right document |
| fact | 20 | simple lookup, often repeated across documents |
| as_of | 14 | answer for a past date using the version in force then |
| report_detail | 10 | audit / assurance report findings, owners, due dates |
| multi_hop | 8 | chain across documents (audit → memo → SOP) |
| deadline_calc | 8 | business-day / calendar-day arithmetic with holidays |
| conflict | 7 | sources disagree or an outdated page is still linked |
| unanswerable | 7 | correct behaviour is to decline |
| database | 7 | needs SQL over the case database |
| decision_detail | 6 | committee decisions and action items |

Default `as_of` is the date the snapshot was taken; questions with another `as_of` must be answered for that date.
