# data/real - public source data (unmodified text)

Generated 2026-11-23 by `scripts/real/*.py`. 218 files, 85.3 MB. Checksums in `MANIFEST.json`.

| folder | files | MB |
|---|---|---|
| calendar | 1 | 0.0 |
| cfpb-enforcement | 16 | 36.3 |
| cfpb-guidance | 47 | 16.0 |
| complaints | 3 | 18.5 |
| federal-register | 18 | 9.5 |
| regulations | 133 | 5.0 |

## 1. Regulations (eCFR Versioner API)

| regulation | sections/appendices | section-versions |
|---|---|---|
| reg-cc | 4 | 22 |
| reg-e | 31 | 85 |
| reg-z | 5 | 25 |

Reg E = 12 CFR 1005 (all 26 sections + appendices A-C + Supplement I, 2017-01-01 onward); Reg Z = 1026.2/.12/.13 + Supplement I commentary for 1026.12 and 1026.13 (extracted from the full Supplement I at each of its 77 versions, kept only when that commentary's text changed); Reg CC = 229.10-229.13. eCFR point-in-time history starts 2017-01-01, so earlier versions are not available.

## 2. Federal Register final rules

17 CFPB final rules (2011-2024) amending 12 CFR 1005 or touching 1026.12/1026.13: 16 amend part 1005, 3 touch 1026.12/13. 1,457,819 words.

## 3. CFPB guidance

46 documents: Supervisory Highlights 12, examination procedures 6, compliance bulletin 5, compliance resource page 3, rule summary 3, compliance aid 3, FAQ 2, small entity compliance guide 2, interpretive rule 1, policy statement (rescinded) 1, policy statement (withdrawn) 1, guidance index 1, Federal Register: Interpretive rule. 1, Federal Register: Compliance bulletin. 1, Federal Register: Withdrawal of Bureau guidance, interpretive rules, policy statements, and advisory opinions. 1, Federal Register: Rescission of statement of policy. 1, Federal Register: Notice of proposed interpretive rule; request for comment. 1, Federal Register: Proposed interpretive rule; withdrawal. 1.

## 4. CFPB enforcement

15 actions (2019-01-03 .. 2025-01-30); 15 primary documents (consent orders / complaints / judgments).

## 5. Consumer complaints

56,625 complaints, 20,576 with narrative. cfpb_api_live: 36,049, hf_mirror_cfpb_bulk_snapshot: 15,965, cfpb_api_live+hf_mirror_narrative: 4,611.

## 6. Calendar

134 rows (US federal holidays 2017-2027, actual + observed dates).

## Gaps / caveats

- **Complaint narratives are no longer published by the CFPB** (policy change Aug 2026): the live API ignores `has_narrative` and returns no `complaint_what_happened`; the bulk CSV dropped the narrative and consent columns. Narratives here come from a CC0 Hugging Face mirror of the earlier official bulk export (`BEE-spoke-data/consumer-finance-complaints`, config `has-text`, 2015-03..2024-02), verbatim, flagged in `record_source` / `narrative_source`.
- Live complaint records (2011-2026) have structured fields only.
- CFPB Supervisory Highlights issue pages are archived (content only on CFPB's Archive-It collection); PDFs were located via the snapshot and downloaded from files.consumerfinance.gov.
- Many CFPB guidance documents were withdrawn on 2025-05-12 (FR 2025-08286); withdrawn/rescinded items kept here are labelled as such in index.csv and remain useful as historical context.
- Several 2024-2025 enforcement matters were later terminated or dismissed (e.g. Comerica, Zelle/EWS dismissed 2025; Navy Federal overdraft order terminated). Navy Federal (overdraft / debt collection) and Wells Fargo 2022 were reviewed and excluded as not about dispute/error-resolution handling.
- eCFR point-in-time data begins 2017-01-01.

## Self-check

- problems: 0
- notes: 4
  - PDF looks image-only / little text: cfpb-enforcement/2022-10-04_choice-money-transfer_consent-order.pdf (47 pages, 0 chars on sampled pages)
  - reserved section (heading only, as published): regulations/reg-cc/229.11/2017-01-01.md
  - reserved section (heading only, as published): regulations/reg-cc/229.11/2019-07-03.md
  - reserved section (heading only, as published): regulations/reg-e/appendix-b/2017-01-01.md
