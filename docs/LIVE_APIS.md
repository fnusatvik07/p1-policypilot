<div align="center">

# Live APIs

### PolicyPilot &nbsp;·&nbsp; `P1-POLICYPILOT`

</div>

Your assistant should be able to pull fresh regulation data from these free public APIs. No API key is needed.

| API | Use it for | Docs |
|:--|:--|:--|
| **eCFR** | Regulation text on any date | [ecfr.gov developer resources](https://www.ecfr.gov/reader-aids/ecfr-developer-resources) |
| **Federal Register** | Rules that changed the regulations | [federalregister.gov API](https://www.federalregister.gov/developers/documentation/api/v1) |
| **CFPB Complaints** | Real consumer complaints | [CFPB complaint API](https://cfpb.github.io/api/ccdb/) |

<br>

## 1. eCFR: regulation text on any date

> **Important:** eCFR only answers compressed requests. Send `Accept-Encoding: gzip` (with curl, use `--compressed`).

**List all versions of Regulation E**

```
GET https://www.ecfr.gov/api/versioner/v1/versions/title-12.json?part=1005
```

History starts on 2017-01-01.

**Get one section as it was on a given date**

```
GET https://www.ecfr.gov/api/versioner/v1/full/{YYYY-MM-DD}/title-12.xml?part=1005&section=1005.11
```

**Get the official interpretations**

```
GET https://www.ecfr.gov/api/versioner/v1/full/{YYYY-MM-DD}/title-12.xml?part=1005&appendix=Supplement%20I%20to%20Part%201005
```

**Regulation Z commentary:** fetch Supplement I to Part 1026 the same way, then cut out the part that starts at the heading `Section 1026.12` (or `Section 1026.13`).

<br>

## 2. Federal Register: rule changes

```
GET https://www.federalregister.gov/api/v1/documents.json
    ?conditions[cfr][title]=12
    &conditions[cfr][part]=1005
    &conditions[type][]=RULE
    &conditions[agencies][]=consumer-financial-protection-bureau
    &conditions[publication_date][gte]=2010-01-01
    &per_page=1000
```

- Keep results whose `action` contains "final rule".
- Download the full text from each result's `body_html_url`.
- `cfr_references.part` is sometimes a number and sometimes text. Convert it to text before comparing.

<br>

## 3. CFPB Consumer Complaint Database

```
GET https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/
```

| Need | Parameters |
|:--|:--|
| Filter by product and issue | `?product=<name>&issue=<Issue>` |
| Filter by sub-issue | `issue=<Issue>•<Sub-issue>` |
| Get everything in one call | `format=csv` (returns all matching rows) |
| Page through JSON | `size` up to 100, `sort=created_date_desc`, `search_after=<sort[0]>_<complaint_id>` from the last result |

- `frm` on its own does not page.
- The live API no longer returns consumer narratives (`complaint_what_happened`). The data in this repo includes narratives from the last official bulk export, marked in `narrative_source`.

<br>

## Be a good API citizen

- Send a clear `User-Agent`.
- Wait about half a second between calls.
- Cache responses on disk.

Working examples of every call are in [`scripts/real/`](../scripts/real).
