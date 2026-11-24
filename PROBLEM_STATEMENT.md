<div align="center">

# Problem Statement

### PolicyPilot &nbsp;·&nbsp; Project ID `P1-POLICYPILOT`

</div>

| | |
|:--|:--|
| **Project ID** | `P1-POLICYPILOT` |
| **Domain** | Bank card and payment disputes |
| **Regulations** | Regulation E (debit, ATM, transfers) and Regulation Z (credit cards) |
| **You build** | An agentic RAG + knowledge graph assistant |
| **Key skills** | Retrieval, knowledge graphs, agents, tool use, document versioning, evaluation |

<br>

## 1. The situation

**Harborline Bank, N.A.** is a mid-sized US bank and our case study.

Its **Card and Payment Disputes team** handles thousands of customer claims every year, like:

> "I never made this debit card purchase."
> "The ATM didn't give me my cash."
> "I was charged twice."
> "The merchant never delivered."

Every one of these claims runs on a clock set by federal law.

| Regulation | Covers | Key deadlines |
|:--|:--|:--|
| **Regulation E** (12 CFR 1005) | Debit cards, ATM, ACH, P2P, prepaid | Provisional credit in **10 business days**. Investigation in **45 days** (90 in some cases). Results to the customer in **3 business days**. |
| **Regulation Z** (12 CFR 1026.12 and 1026.13) | Credit cards | Customer reports within **60 days**. Bank acknowledges in **30 days**. Resolution within **2 billing cycles** (max 90 days). |

On top of the law sits the bank's own layer: a policy, dozens of procedures and job aids, wiki pages, memos, ops bulletins, committee minutes, audit reports and emails. **That layer is where analysts actually look for answers.**

<br>

## 2. Why this problem exists

Banks rarely get dispute handling wrong because nobody knows the rule.
They get it wrong because **the right answer is hidden in the wrong version of the wrong document.**

| What goes wrong | What it looks like |
|:--|:--|
| **Documents change all the time** | A memo raises a threshold. A procedure gets a version 3. A bulletin overrides a job aid "from next Monday". |
| **Old versions never really die** | The old cheat sheet is still linked from the intake page. Superseded PDFs sit in archive folders. Search still finds them. |
| **Sources disagree** | The policy says one thing, the wiki says another, an email says "ignore the wiki for now". |
| **Every question has a date** | "Was this case handled correctly?" must be judged by the rules in force on the day the customer called, not today. |
| **Deadlines need real maths** | Business days skip weekends and federal holidays. A guessed date can mean a fine. |
| **Some answers live in data** | "Was provisional credit on this case posted on time?" needs the case database, not a document. |
| **Regulators are watching** | Every year the CFPB orders banks and fintechs to pay for mishandled disputes. See `data/real/cfpb-enforcement/`. |

A simple "chunk, embed and chat" bot answers the easy questions and fails the expensive ones.
**PolicyPilot closes that gap.**

<br>

## 3. What we are looking for

An assistant that a disputes analyst or a compliance officer can trust.

1. **Grounded answers with citations.** Every claim is backed by a document ID, a version and an exact quote.
2. **Answers for any date.** By default it answers for today. If the user gives a past date, it uses only the documents and regulation versions in force on that date.
3. **Document lifecycle awareness.** It knows which version is active, superseded, retired, expired or deleted. It applies change releases without rebuilding everything.
4. **Conflict handling.** It notices when sources disagree and explains which one wins and why.
5. **Links to the real regulations.** It connects internal documents to Reg E and Reg Z text and official interpretations. A knowledge graph fits this well. LightRAG is a good starting point.
6. **Tools instead of guesses.** A business-day deadline calculator using the federal holiday calendar. SQL queries over the case database.
7. **Honest answers.** When the documents do not cover something, it says so instead of inventing an answer.

<br>

## 4. What the data looks like

Full details are in the [Data Guide](docs/DATA_GUIDE.md).

| Area | Where | What it is |
|:--|:--|:--|
| Bank documents | `data/corpus/` | 364 files (docx, pdf, html, eml, xlsx, pptx) from 5 systems, including old and archived versions |
| Document registry | `data/registry/dms_export.csv` | The bank's document list with ID, version, status and effective date. Useful, but not always right. |
| Case database | `data/db/` | Customers, accounts, cards, transactions, statements, dispute cases, case events, chargebacks, letters, analysts, holidays |
| Change releases | `changes/release-*/` | New and changed documents plus `events.jsonl` (UPSERT, RETIRE, DELETE) |
| Real public data | `data/real/` | Versioned Reg E, Reg Z and Reg CC text, Federal Register rules, CFPB guidance, enforcement orders, 56k consumer complaints, holidays |
| Questions | `eval/questions_public.jsonl` | 117 questions with reference answers and citations, across 10 types |
| Live APIs | [Live APIs](docs/LIVE_APIS.md) | eCFR, Federal Register and CFPB complaint APIs for fresh data |

<br>

## 5. What we expect you to build

| Component | What it does |
|:--|:--|
| **Ingestion pipeline** | Reads all 5 sources and all file types. Extracts metadata (ID, version, status, dates) and checks it against the registry. |
| **Index + knowledge graph** | Links documents, versions, sections, regulations, deadlines, roles and systems. |
| **Agent loop** | Plans, retrieves, calls tools, checks versions and dates, and writes a cited answer. |
| **Tools** | Business-day calculator, SQL over the case database, live regulation APIs. |
| **Change feed processor** | Applies each release in order: new versions, retirements and deletions. |
| **Evaluation harness** | Runs the public questions and reports accuracy by type, citation quality and refusal quality. |
| **Interface** | A CLI, API or small web app where a user asks a question and can set an as-of date. |

<br>

## 6. What you submit

Full rules are in [What to Submit](docs/SUBMISSION.md).

1. **Code repository** with a README that runs end to end
2. **`predictions.jsonl`** for all public questions, in the required format
3. **Architecture write-up** with a diagram, your design choices, and what you tried that did not work
4. **Evaluation report** with scores per question type, before and after each change release
5. **Change feed log** describing what your system did for each event
6. **Demo video** of 5 to 8 minutes

Your system will also be run on **hidden questions** of the same kinds.
**Build for the problem, not for the 117 public questions.**
