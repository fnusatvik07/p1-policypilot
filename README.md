# P1-POLICYPILOT · PolicyPilot

**An agentic RAG + knowledge-graph assistant for a bank's card & payment disputes team.**

> Harborline Bank's disputes analysts must answer "what is the rule, and was it followed?" under Regulation E and Regulation Z — across hundreds of documents that keep changing, disagree with each other, and come in five different systems. Build the assistant that gets it right, for any date, with citations.

| | |
|---|---|
| Project ID | `P1-POLICYPILOT` |
| Problem statement | [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) |
| Data guide | [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) |
| Live APIs | [docs/LIVE_APIS.md](docs/LIVE_APIS.md) |
| What to submit | [docs/SUBMISSION.md](docs/SUBMISSION.md) |
| Walkthrough video | [video/SCRIPT.md](video/SCRIPT.md) (video file being produced) |

## Repository layout

```
PROBLEM_STATEMENT.md      the brief
docs/                     data guide, live APIs, submission rules
data/
  corpus/                 364 bank documents (5 source systems, 6 file types)
  registry/               DMS export: doc_id, version, status, effective date
  db/                     disputes case database (SQLite, CSV, Postgres)
  real/                   real regulations, Federal Register, CFPB guidance,
                          enforcement orders, consumer complaints, holidays
changes/release-NN_*/     change feed you must apply (events.jsonl + files/)
eval/questions_public.jsonl   117 questions with reference answers
scripts/real/             re-runnable fetchers for everything in data/real
video/                    project walkthrough
```

## Quick start

```bash
git clone https://github.com/fnusatvik07/p1-policypilot.git
cd p1-policypilot
python -m venv .venv && source .venv/bin/activate
pip install pandas pyarrow requests lxml beautifulsoup4 pypdf holidays

# peek at the data
sqlite3 data/db/harborline_disputes.sqlite ".tables"
head -n 3 eval/questions_public.jsonl
cat data/real/SUMMARY.md
```

## The challenge in one picture

```
 question + as-of date
        │
        ▼
 ┌──────────────┐   plan    ┌───────────────────────────────┐
 │  agent loop  │ ───────▶  │ retrieve (vector + graph)      │
 │              │ ◀───────  │ filter by version / effective  │
 │              │           │ date / status                  │
 │              │   tools   ├───────────────────────────────┤
 │              │ ───────▶  │ business-day calculator        │
 │              │           │ SQL over case database         │
 │              │           │ eCFR / Federal Register APIs   │
 └──────┬───────┘           └───────────────────────────────┘
        ▼
 answer + citations (doc_id, version, verbatim quote) + reg refs
```

The library keeps changing: apply each `changes/release-*` and your answers must change with it.

## Data sources and licences

- Regulations, Federal Register documents, CFPB guidance and enforcement documents are US federal government works (public domain). Text is unmodified.
- CFPB Consumer Complaint Database records are CC0. The CFPB no longer publishes consumer narratives; narratives here come from the last official bulk export via a public mirror and are labelled in `narrative_source`.
- Harborline Bank, N.A. is a case-study bank created for this programme; any resemblance to a real institution is coincidental.
