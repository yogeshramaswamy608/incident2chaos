# The corpus

The data of the study “Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage”.

497 public post-incident reports published by five cloud providers on their own sites. The 447 reports outside the pilot were coded under codebook version 2 (`codebook.md`); the 50 pilot reports keep the labels as checked by the author. License: CC BY 4.0 (`LICENSE`).

| Source | Reports | Report links on |
|---|---|---|
| AWS Post-Event Summaries (`AWS PES`) | 18 | aws.amazon.com |
| Microsoft Azure Post Incident Reviews (`Microsoft Azure PIR`) | 81 | azure.status.microsoft |
| Google Cloud incident reports (`Google Cloud incident report`) | 172 | status.cloud.google.com |
| Cloudflare blog posts tagged post-mortem (`Cloudflare blog post-mortem`) | 42 | blog.cloudflare.com |
| GitHub monthly availability reports, one row per incident heading (`GitHub availability report`) | 184 | github.blog |

Incident dates run from Apr 21, 2011 to Oct 19, 2026. `retrieved_utc` records when each source's pages were last saved, between 01:10 and 01:14 UTC on Nov 4, 2026. Each provider's site terms are in `site_terms.md`, with the date they were read. No report text is redistributed: each row holds the report's link, its title and date as the provider's index lists them, labels, and short notes that paraphrase the report. A language model proposed every label of corpus.csv and wrote the notes of the 447 first-pass rows; the author checked the proposed labels of the 50 pilot rows, agreed with 40 and changed 10. The author wrote the 50 notes of the pilot rows with his check.

## corpus.csv

| Column | Meaning |
|---|---|
| `corpus_no` | Row number: 1 to 447 for the reports coded after the pilot, P1 to P50 for the pilot |
| `source` | The provider's report series, as in the table above |
| `report_id` | The provider's identifier; for GitHub, the report's slug, the incident date and, when needed, its time or a counter |
| `title` | The title on the provider's index; the 13 titles longer than 150 characters, which on those pages are status sentences, are replaced by the source, identifier and date |
| `incident_date` | The incident's start date, YYYY-MM-DD |
| `url` | The report's link; GitHub incidents share the link of their monthly report, and an Azure link is the address of Azure's status history for the one review the row names |
| `retrieved_utc` | When the index was read |
| `in_scope` | `no` for the 6 reports that the first pass found to describe no failure of the provider's own service; their labels are empty. The author's blind coding put one of the 6, row 36, in scope (`blind_sample.csv`) |
| `trigger_primary`, `trigger_secondary` | Trigger codes T1 to T13, T99 when the report does not state it (no pilot row holds a secondary trigger) |
| `faults` | Every fault class the report states, primary first, separated by `;` (empty in the 50 pilot rows, whose one fault is in `fault_primary`) |
| `fault_primary` | The failure that caused most of the customer impact, F1 to F20, F99 when not stated |
| `injectability_primary` | A directly injectable by Chaos Mesh or LitmusChaos, P approximation only, N not injectable, NS not stated |
| `confidence` | The confidence the language model gave its first-pass labels, high, medium or low (empty for the pilot rows and for rows 36 and 256) |
| `evidence_trigger`, `evidence_fault` | The report section and a paraphrase of under 25 words, written by the language model with its first-pass labels (empty for the pilot rows and for rows 36 and 256) |
| `codebook_gap` | A case the codebook did not settle, and how it was coded, written by the language model in the first-pass rows. Each of the 50 pilot rows holds one short note of 12 to 17 words, written by the author with his pilot check. Rows 36 and 256 hold only a stray word, `low` and `high`, which is no note |
| `coded_by` | `pilot, checked by the author` for the 50 pilot reports, whose labels a language model proposed under codebook version 1 and the author then checked, or `first pass (model), codebook v2` for the 447 reports outside the pilot, whose labels a language model proposed under the frozen codebook and which were not revised afterwards |

## blind_sample.csv

The 45 reports the author coded blind to the first-pass labels (random seed 2026110402, drawn from the 402 reports outside the pilot and outside an earlier sample of 45, set aside because its codes had been produced with the help of a software tool rather than by the author alone), with both codings. corpus.csv keeps the first-pass labels for these 45. On the 44 that both codings put in scope: primary trigger 33 agree (Cohen's kappa 0.72), primary fault 39 (kappa 0.87, from 307/351 = 0.8746), injectability of the primary fault 42 (kappa 0.913). The tests rerun these figures.

## pilot_check.csv

The 50 pilot reports (random seed 20261103): the labels a language model proposed under codebook version 1, the author's verdict (AGREE 40, CHANGE 10) and the final labels. The primary trigger and the primary fault were each kept for 45 of the 50 (Cohen's kappa 0.88 and 0.89). The tests rerun these figures.

## fault_classes.json and triggers.json

The codes of sections 2 and 3 of the codebook, parsed by `tools/build_data.py`, with the injectability rule of each fault class (F3 is directly injectable on AWS only). The short name of each fault class is the one in the paper's Table 2.
