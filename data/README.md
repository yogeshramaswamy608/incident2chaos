# The paper 1 corpus

497 public post-incident reports published by five cloud providers on their own sites, coded under codebook version 2 (`codebook.md`). License: CC BY 4.0 (`LICENSE`).

| Source | Reports | Report links on |
|---|---|---|
| AWS Post-Event Summaries (`AWS PES`) | 18 | aws.amazon.com |
| Microsoft Azure Post Incident Reviews (`Microsoft Azure PIR`) | 81 | aka.ms (54), azure.status.microsoft (27) |
| Google Cloud incident reports (`Google Cloud incident report`) | 172 | status.cloud.google.com |
| Cloudflare blog posts tagged post-mortem (`Cloudflare blog post-mortem`) | 42 | blog.cloudflare.com |
| GitHub monthly availability reports, one row per incident heading (`GitHub availability report`) | 184 | github.blog |

Incident dates run from Apr 21, 2011 to Oct 19, 2026. The indexes were read on Nov 4, 2026 (UTC). Each provider's site terms, read before collection, are in `site_terms.md`. No report text is redistributed: each row holds the report's link, its title and date as the provider's index lists them, our labels, and evidence notes of under 25 words in our own words.

## corpus.csv

| Column | Meaning |
|---|---|
| `corpus_no` | Row number: 1 to 447 for the reports coded after the pilot, P1 to P50 for the pilot |
| `source` | The provider's report series, as in the table above |
| `report_id` | The provider's identifier; for GitHub, the report's slug, the incident date and, when needed, its time or a counter |
| `title` | The title on the provider's index |
| `incident_date` | The incident's start date, YYYY-MM-DD |
| `url` | The report's link; GitHub incidents share the link of their monthly report |
| `retrieved_utc` | When the index was read |
| `in_scope` | `no` for the 6 reports that describe no failure of the provider's own service; their labels are empty |
| `trigger_primary`, `trigger_secondary` | Trigger codes T1 to T13, T99 when the report does not state it |
| `faults` | Every fault class the report states, primary first, separated by `;` (the pilot rows keep the primary fault only) |
| `fault_primary` | The failure that caused most of the customer impact, F1 to F20, F99 when not stated |
| `injectability_primary` | A directly injectable by Chaos Mesh or LitmusChaos, P approximation only, N not injectable, NS not stated |
| `confidence` | The coder's confidence, high, medium or low (empty for the pilot rows) |
| `evidence_trigger`, `evidence_fault` | The report section and a paraphrase in our own words |
| `codebook_gap` | A case the codebook did not settle, and how it was coded |
| `coded_by` | `pilot, checked by the author` or `first pass (model), codebook v2` |

## blind_sample.csv

The 45 reports the author coded blind to the first-pass labels (random seed 2026110402, drawn from the 402 reports outside the pilot and an earlier sample), with both codings. On the 44 that both codings put in scope: primary trigger 33 agree (Cohen's kappa 0.72), primary fault 39 (kappa 0.875), injectability of the primary fault 42 (kappa 0.913). The tests rerun these figures.

## fault_classes.json and triggers.json

The codes of sections 2 and 3 of the codebook, parsed by `tools/build_data.py`, with the injectability rule of each fault class (F3 is directly injectable on AWS only).
