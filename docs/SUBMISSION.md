<div align="center">

# What to Submit

### PolicyPilot &nbsp;·&nbsp; `P1-POLICYPILOT`

</div>

## Checklist

| # | Deliverable | Where | Details |
|:--|:--|:--|:--|
| 1 | **Code repository** | Your Git repo | Public or shared with mentors. README with setup, one command to ingest, one command to ask a question. Never commit API keys. |
| 2 | **Predictions** | `submission/predictions.jsonl` | One line for every question in `eval/questions_public.jsonl` |
| 3 | **Architecture write-up** | `submission/ARCHITECTURE.md` | Diagram, components, graph schema, how you handle versions and dates, what you tried and dropped |
| 4 | **Evaluation report** | `submission/EVAL_REPORT.md` | Scores per question type, before and after each change release, and 5 failures you analysed |
| 5 | **Change feed log** | `submission/changes_applied.md` | What your system did for each event in each release |
| 6 | **Demo video** | Link in your README | 5 to 8 minutes |

<br>

## Predictions format

One JSON object per line:

```json
{
  "id": "Q002",
  "answer": "By the 7th business day after the notice of error (the regulatory limit is 10 business days).",
  "as_of": "YYYY-MM-DD",
  "citations": [
    {"doc_id": "CPS-SOP-211", "version": 2, "quote": "exact sentence copied from the document"}
  ],
  "reg_refs": ["12 CFR 1005.11(c)(2)"],
  "refused": false
}
```

**Rules**

- `quote` must appear word for word in the cited version.
- For questions the documents do not cover, set `"refused": true` and explain briefly in `answer`.

<br>

## How you are graded

| Area | Weight |
|:--|--:|
| Correct answers on public **and hidden** questions | 35% |
| Citation quality (right document, right version, exact quote) | 15% |
| Dates, versions and change feed handling | 20% |
| Engineering quality (pipeline, tools, tests, reproducibility) | 15% |
| Write-up, evaluation report and demo | 15% |

<br>

## Your demo video must show

1. Ingesting the documents (briefly)
2. One question of each type: `as_of`, `conflict`, `deadline_calc`, `database`, `unanswerable`
3. A change release being applied, and an answer that changes because of it
4. Your evaluation numbers
