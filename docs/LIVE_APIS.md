# Live APIs students must call

## eCFR (regulation text, point-in-time) — https://www.ecfr.gov/reader-aids/ecfr-developer-resources
- Requires gzip: send `Accept-Encoding: gzip` (curl `--compressed`).
- List versions: `GET https://www.ecfr.gov/api/versioner/v1/versions/title-12.json?part=1005`  (history starts 2017-01-01)
- Text on a date: `GET https://www.ecfr.gov/api/versioner/v1/full/{YYYY-MM-DD}/title-12.xml?part=1005&section=1005.11`
- Official interpretations: `...&appendix=Supplement%20I%20to%20Part%201005`
- Reg Z commentary: fetch Supplement I to Part 1026 and cut at the `<HD2>Section 1026.12—` heading.

## Federal Register (rule changes) — https://www.federalregister.gov/developers/documentation/api/v1
- `GET https://www.federalregister.gov/api/v1/documents.json?conditions[cfr][title]=12&conditions[cfr][part]=1005&conditions[type][]=RULE&conditions[agencies][]=consumer-financial-protection-bureau&conditions[publication_date][gte]=2010-01-01&per_page=1000`
- Filter `action` containing "final rule"; fetch `body_html_url`. `cfr_references.part` may be an int — cast to str.

## CFPB Consumer Complaint Database — https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/
- Filters: `?product=<name>&issue=<Issue>` (sub-issue: `issue=<Issue>•<Sub-issue>`)
- Bulk: `format=csv` returns all matching rows in one call.
- JSON paging: `size` ≤ 100, `sort=created_date_desc`, `search_after=<sort[0]>_<complaint_id>` (`frm` alone does not page).
- Narratives (`complaint_what_happened`) are no longer returned by the live API; the data pack ships narratives from the last official bulk export (via public mirror), labelled in `narrative_source`.

## Be polite
Send a descriptive `User-Agent`, keep ~0.5 s between calls, and cache responses locally. The scripts in `scripts/real/` show working, re-runnable examples of every call above.
