# Project P1-POLICYPILOT — PolicyPilot

**Project ID:** `P1-POLICYPILOT`
**Domain:** bank card & payment disputes (Regulation E / Regulation Z)
**You build:** an agentic RAG + knowledge-graph assistant that answers compliance questions *correctly for a given date*, with citations, while the document library keeps changing underneath it.

---

## 1. The situation

Harborline Bank, N.A. is a mid-sized US bank used as our case study. Its **Card & Payment Disputes** team handles thousands of customer claims every year:
"I never made this debit card purchase", "the ATM didn't give me my cash", "I was charged twice", "the merchant never delivered".

Every one of those claims runs on a clock set by federal law:

- **Regulation E** (12 CFR 1005) for debit cards, ATM, ACH, P2P and prepaid — e.g. provisional credit within **10 business days**, investigation within **45 days** (90 in some cases), results to the customer within **3 business days**.
- **Regulation Z** (12 CFR 1026.12–1026.13) for credit cards — billing-error notices within **60 days**, acknowledgement within **30 days**, resolution within **two billing cycles (max 90 days)**.

On top of the law sits the bank's own layer: a policy, dozens of SOPs and job aids, wiki pages, memos, ops bulletins, committee minutes, audit reports, emails. That layer is where analysts actually look for answers.

## 2. Why this problem exists (and why it is hard)

Banks do not fail dispute exams because nobody knows the rule. They fail because **the right answer is buried in the wrong version of the wrong document**:

- **Documents change constantly.** A memo raises a threshold, an SOP gets a v3, a wiki page is retired, a bulletin overrides a job aid "effective next Monday".
- **Old versions never really die.** The 2018 cheat sheet is still linked from the intake page. Superseded PDFs sit in `_Archive` folders. Search happily returns them.
- **Sources disagree.** Policy says one thing, a team wiki says another, an email thread says "ignore the wiki for now".
- **The question has a date.** "Was this case handled correctly?" must be judged against the rules *in force on the day the customer called*, not today's rules.
- **Deadlines need arithmetic.** "Business day" means skipping weekends and federal holidays — an LLM that guesses dates gets people fined.
- **Some answers live in data, not text.** "Was provisional credit on case HL-… posted on time?" needs the case database.
- **The regulators are watching.** Every year the CFPB orders banks and fintechs to pay redress for mishandled disputes (see `data/real/cfpb-enforcement/`). Real consumers describe these failures in their own words (see `data/real/complaints/`).

A plain "chunk-and-embed" chatbot gets the easy questions right and the expensive ones wrong. That is the gap PolicyPilot closes.

## 3. What we are looking for

An assistant a disputes analyst or compliance officer can trust:

1. **Grounded answers with citations** — every claim backed by `doc_id` + `version` + a verbatim quote.
2. **As-of-date reasoning** — answer for *today* by default, or for any past date the user gives, using only documents (and regulation versions) effective on that date.
3. **Document lifecycle awareness** — knows which version is active, superseded, retired, expired or deleted; ingests change events and updates itself without a full rebuild.
4. **Conflict handling** — spots when sources disagree, says which one wins and why (effective date, hierarchy, supersession).
5. **Regulation linkage** — connects internal documents to the real Reg E / Reg Z text and official interpretations (a knowledge graph is the natural fit; LightRAG is a good starting point).
6. **Tools, not guesses** — business-day deadline calculator using the federal holiday calendar; SQL over the case database.
7. **Honest refusals** — says "not covered by the available documents" instead of inventing an answer.

## 4. What the data looks like

Full details in [`docs/DATA_GUIDE.md`](docs/DATA_GUIDE.md).

| Area | Where | What |
|---|---|---|
| Bank document library | `data/corpus/` | 364 files (docx, pdf, html, eml, xlsx, pptx) from 5 source systems: policy portal, SharePoint, OpsWiki, shared drive, email archive — including superseded and archived versions |
| Document registry | `data/registry/dms_export.csv` | the bank's DMS export: path, system, doc_id, version, status, effective date, owner (not always right — verify) |
| Case database | `data/db/` | SQLite + CSV + Postgres scripts: customers, accounts, cards, transactions, statements, dispute cases, case events, chargebacks, letters, analysts, holidays |
| Change feed | `changes/release-*/` | releases of `events.jsonl` (UPSERT / RETIRE / DELETE) plus new files — your system must absorb these |
| Real regulations & public data | `data/real/` | versioned Reg E / Reg Z / Reg CC text, Federal Register rules, CFPB guidance, enforcement orders, ~56k CFPB consumer complaints, federal holidays |
| Evaluation questions | `eval/questions_public.jsonl` | 117 questions with reference answers and citations, across 10 question types |
| Live APIs | [`docs/LIVE_APIS.md`](docs/LIVE_APIS.md) | eCFR, Federal Register and CFPB complaint APIs your system should call for fresh regulation data |

## 5. What we expect you to build

- **Ingestion pipeline** for all five source systems and all file types, with metadata (doc_id, version, status, effective dates) — reconciled against the registry.
- **Index + knowledge graph** linking documents, versions, sections, regulations, deadlines, roles and systems.
- **Agentic answering loop** that plans, retrieves, calls tools (deadline calculator, SQL, live regulation APIs), checks versions/dates, and composes a cited answer.
- **Change-feed processor** that applies each release incrementally (new versions, retirements, deletions).
- **Evaluation harness** that runs `eval/questions_public.jsonl` and reports accuracy by question type, citation precision, and refusal correctness.
- **A simple interface** — CLI, API or small web UI — where a user asks a question and optionally sets an as-of date.

## 6. What you submit

See [`docs/SUBMISSION.md`](docs/SUBMISSION.md). In short:

1. Your **code repository** (public or shared with mentors) with a README that runs end to end.
2. **`predictions.jsonl`** for the public questions, in the required format.
3. A short **architecture write-up** (diagram + design choices + what you tried that did not work).
4. **Evaluation report** — your scores per question type, before and after each change release.
5. A **demo video (5–8 minutes)** showing ingestion, a few hard questions (as-of, conflict, deadline, database), and a change release being applied live.

Your system will also be run on **hidden questions** of the same kinds. Build for the problem, not for the 117 public questions.
