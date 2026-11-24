# What to submit — P1-POLICYPILOT

| # | Deliverable | Format |
|---|---|---|
| 1 | **Code repository** | Git repo (public or shared with mentors). `README.md` with setup and one command to ingest and one to ask a question. No API keys committed. |
| 2 | **Predictions** | `submission/predictions.jsonl` — one line per question in `eval/questions_public.jsonl` |
| 3 | **Architecture write-up** | `submission/ARCHITECTURE.md` — diagram, components, data model / graph schema, how versions and as-of dates are handled, what you tried and dropped |
| 4 | **Evaluation report** | `submission/EVAL_REPORT.md` — scores by question type; before and after each change release; 5 failure cases you analysed |
| 5 | **Change-feed log** | `submission/changes_applied.md` — what your system did for each event in each release |
| 6 | **Demo video** | 5–8 minutes, link in your README |

## predictions.jsonl format

```json
{"id": "Q002",
 "answer": "By the 7th business day after the notice of error (regulatory limit: 10 business days).",
 "as_of": "YYYY-MM-DD",
 "citations": [{"doc_id": "CPS-SOP-211", "version": 2, "quote": "exact sentence copied from the document"}],
 "reg_refs": ["12 CFR 1005.11(c)(2)"],
 "refused": false}
```

- `quote` must appear verbatim in the cited version.
- For unanswerable questions set `"refused": true` and explain briefly in `answer`.

## How it is assessed

| Area | Weight |
|---|---|
| Answer correctness on public **and hidden** questions | 35% |
| Citation quality (right doc, right version, verbatim quote) | 15% |
| As-of / lifecycle / change-feed handling | 20% |
| Engineering quality (pipeline, tools, tests, reproducibility) | 15% |
| Write-up, evaluation report and demo | 15% |

## The demo video must show

1. Ingestion of the corpus (briefly).
2. One question from each of: `as_of`, `conflict`, `deadline_calc`, `database`, `unanswerable`.
3. A change release being applied, and an answer that changes because of it.
4. Your evaluation numbers.
