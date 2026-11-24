<div align="center">

# Data Guide

### PolicyPilot &nbsp;·&nbsp; `P1-POLICYPILOT`

</div>

Everything you need is in this repository. Here is what each part is and how to use it.

| # | Part | Folder |
|:--|:--|:--|
| 1 | Bank documents | `data/corpus/` |
| 2 | Document registry | `data/registry/` |
| 3 | Case database | `data/db/` |
| 4 | Change releases | `changes/` |
| 5 | Real public data | `data/real/` |
| 6 | Questions | `eval/` |

<br>

## 1. Bank documents

**Folder:** `data/corpus/` &nbsp;·&nbsp; **364 files** &nbsp;·&nbsp; about 28 MB

These are exported as-is from five systems, so folder layout, file names and formats differ by system.

| Folder | System | Typical content |
|:--|:--|:--|
| `policy-portal/` | PolicyHub | Board-approved policies (old versions in `_Archive`), customer agreements and disclosures, audit reports |
| `sharepoint/` | Disputes Ops Library, Consumer Compliance Committee | Procedures (SOPs), job aids, memos and bulletins by year, letter templates, committee minutes and decks |
| `wiki/OpsWiki/` | OpsWiki (Confluence) | How-to pages, FAQs, cheat sheets. Some are outdated but still linked. |
| `shared-drive/S_CPS_Disputes/` | Shared drive | Trackers, spreadsheets, working copies |
| `email/YYYY-MM/` | Email archive | `.eml` threads where decisions and exceptions are discussed |

**File types:** docx 159 &nbsp;·&nbsp; html 98 &nbsp;·&nbsp; pdf 66 &nbsp;·&nbsp; eml 20 &nbsp;·&nbsp; xlsx 13 &nbsp;·&nbsp; pptx 8

**Document IDs** look like `POL-001`, `CPS-SOP-211`, `JA-114`, `WI-031`, `MEMO-2021-08`, `OB-2026-21`, `IA-2021-07`, `EML-008`.

<br>

## 2. Document registry

**File:** `data/registry/dms_export.csv`

One row per file with these columns:

`path` · `source_system` · `doc_id` · `title` · `version` · `status` · `effective_date` · `owner` · `last_modified`

**Status values:** `active`, `superseded`, `final`, `expired`, and some blank.

> **Tip:** treat it like a real export from a document system. It is useful, but not always complete or correct. The documents themselves are the source of truth.

<br>

## 3. Case database

**Folder:** `data/db/` &nbsp;·&nbsp; about 150 MB

The same data in three forms:

- `harborline_disputes.sqlite` (easiest to start with)
- `csv/*.csv`
- `schema_postgres.sql` and `load_postgres.sql`

| Table | Rows | Notes |
|:--|--:|:--|
| customers | 6,500 | |
| accounts | 10,853 | Checking, savings, credit card, prepaid |
| cards | 10,853 | |
| transactions | 248,761 | |
| statements | 472,007 | Statement cycles, needed for the 60-day and billing-cycle rules |
| dispute_cases | 8,182 | Case number `HL-YYYY-NNNNNN`, regulation, dates, amounts, outcome |
| case_events | 54,176 | Notice, provisional credit, letters, decisions |
| chargebacks | 2,737 | Card network chargebacks linked to cases |
| letters | 13,955 | Letters sent to customers |
| analysts | 128 | |
| holidays | 145 | Bank holiday calendar |

<br>

## 4. Change releases

**Folder:** `changes/release-NN_*/`

Each release has an `events.jsonl` file and a `files/` folder with the new documents.

| Field | Meaning |
|:--|:--|
| `event_id` | Unique ID of the event |
| `emitted_at` | When the event was sent |
| `source_system` | Which system it came from |
| `action` | `UPSERT` (new or changed), `RETIRE` (keep for history, remove from search) or `DELETE` |
| `doc_id`, `version`, `title` | Which document |
| `effective_from` | When the change takes effect. **Can be in the future.** |
| `file`, `target_path`, `sha256` | Where the new file is and where it belongs |
| `supersedes` | Which version it replaces |
| `comment` | Why the change was made |

> **Tip:** apply releases in order. A change with a future `effective_from` is not in force until that date.

<br>

## 5. Real public data

**Folder:** `data/real/` &nbsp;·&nbsp; about 82 MB &nbsp;·&nbsp; text is unmodified

| Folder | Content |
|:--|:--|
| `regulations/` | Every version of Reg E (all sections, appendices, official interpretations), Reg Z 1026.2, 1026.12, 1026.13 plus commentary, and Reg CC 229.10 to 229.13. Markdown with `version_effective_date` and `next_version_date`. Index: `versions_index.csv` |
| `federal-register/` | CFPB final rules that changed these regulations, plus `index.csv` |
| `cfpb-guidance/` | EFT FAQs, exam procedures, compliance guides, bulletins, Supervisory Highlights, plus `index.csv` |
| `cfpb-enforcement/` | Consent orders and complaints about dispute handling failures, plus `index.csv` with summaries |
| `complaints/` | About 56,600 CFPB consumer complaints about disputes, unauthorized transactions and fraud. About 20,500 include the consumer's own story. |
| `calendar/` | US federal holidays with actual and observed dates, and Federal Reserve closures |

`data/real/MANIFEST.json` lists every file with a checksum and source URL. `data/real/SUMMARY.md` has counts and known gaps. Rebuild any of it with the scripts in `scripts/real/`.

<br>

## 6. Questions

**File:** `eval/questions_public.jsonl` &nbsp;·&nbsp; **117 questions**

Each line has: `id`, `qtype`, `question`, `answer`, `as_of`, `citations` (doc_id, version, quote), `reg_refs`, `difficulty`, `requires`, `notes`.

| Type | Count | What it tests |
|:--|--:|:--|
| `document_detail` | 30 | Find the exact rule in the right document |
| `fact` | 20 | Simple lookup, often repeated across documents |
| `as_of` | 14 | Answer for a past date using the version in force then |
| `report_detail` | 10 | Audit report findings, owners, due dates |
| `multi_hop` | 8 | Follow a chain across documents (audit, then memo, then procedure) |
| `deadline_calc` | 8 | Business-day and calendar-day maths with holidays |
| `conflict` | 7 | Sources disagree, or an outdated page is still linked |
| `unanswerable` | 7 | The right behaviour is to say it is not covered |
| `database` | 7 | Needs SQL over the case database |
| `decision_detail` | 6 | Committee decisions and action items |

> **Tip:** most questions use the snapshot date as `as_of`. When a question has a different `as_of`, answer it for that date.
