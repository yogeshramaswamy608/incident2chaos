# The corpus

The data of the study “Which Real Cloud Failures Can Chaos Tools Inject? A Mapping Study of 437 Public Post-Incident Reports and Two Fault Catalogs”.

437 public post-incident reports published by three providers on their own sites: Microsoft Azure, Google Cloud and GitHub. The 403 reports outside the pilot were coded under codebook version 2 (`codebook.md`); the 34 pilot reports keep the labels as checked by the author. Version 2.0.0 withdrew the 60 reports of AWS and Cloudflare, for the reason in `site_terms.md` and in the section “What version 2.0.0 changes” below. License: CC BY 4.0 (`LICENSE`).

| Source | Reports | Report links on |
|---|---|---|
| Microsoft Azure Post Incident Reviews (`Microsoft Azure PIR`) | 81 | azure.status.microsoft |
| Google Cloud incident reports (`Google Cloud incident report`) | 172 | status.cloud.google.com |
| GitHub monthly availability reports, one row per incident heading (`GitHub availability report`) | 184 | github.blog |

Incident dates run from Jul 13, 2020 to Oct 19, 2026. `retrieved_utc` records when each source's pages were last saved, between 01:10 and 01:14 UTC on Nov 4, 2026. Each provider's site terms are in `site_terms.md`, with the date they were read. No report text is redistributed: each row holds the report's link, its title and date as the provider's index lists them, labels, and short notes that paraphrase the report. A language model proposed every label of corpus.csv and wrote the notes of the 403 first-pass rows; the author checked the proposed labels of the 34 pilot rows, agreed with 25 and changed 9. The author wrote the 34 notes of the pilot rows with his check.

## corpus.csv

| Column | Meaning |
|---|---|
| `corpus_no` | Row number as in versions 1.0.0 to 1.0.2: 1 to 447 for the reports coded after the pilot, P1 to P50 for the pilot. The numbers of the 60 withdrawn rows are not reused, so the numbers have gaps |
| `source` | The provider's report series, as in the table above |
| `report_id` | The provider's identifier; for GitHub, the report's slug, the incident date and, when needed, its time or a counter |
| `title` | The title on the provider's index; the 13 titles longer than 150 characters, which on those pages are status sentences, are replaced by the source, identifier and date |
| `incident_date` | The incident's start date, YYYY-MM-DD |
| `url` | The report's link; GitHub incidents share the link of their monthly report, and an Azure link is the address of Azure's status history for the one review the row names |
| `retrieved_utc` | When the index was read |
| `in_scope` | `no` for the 1 report, row 36, that the first pass found to describe no failure of the provider's own service; its labels are empty. The author's blind coding put it in scope (`blind_sample.csv`). The other 5 out-of-scope reports of versions 1.0.0 to 1.0.2 were Cloudflare reports and were withdrawn |
| `trigger_primary`, `trigger_secondary` | Trigger codes T1 to T13, T99 when the report does not state it (no pilot row holds a secondary trigger) |
| `faults` | Every fault class the report states, primary first, separated by `;` (empty in the 34 pilot rows, whose one fault is in `fault_primary`) |
| `fault_primary` | The failure that caused most of the customer impact, F1 to F20, F99 when not stated |
| `injectability_primary` | A directly injectable by Chaos Mesh or LitmusChaos, P approximation only, N not injectable, NS not stated |
| `confidence` | The confidence the language model gave its first-pass labels, high, medium or low (empty for the pilot rows and for row 36) |
| `evidence_trigger`, `evidence_fault` | The report section and a paraphrase of under 25 words, written by the language model with its first-pass labels (empty for the pilot rows and for row 36) |
| `codebook_gap` | A case the codebook did not settle, and how it was coded, written by the language model in the first-pass rows. Each of the 34 pilot rows holds one short note of 12 to 17 words, written by the author with his pilot check. Row 36 holds only a stray word, `low`, which is no note |
| `coded_by` | `pilot, checked by the author` for the 34 pilot reports, whose labels a language model proposed under codebook version 1 and the author then checked, or `first pass (model), codebook v2` for the 403 reports outside the pilot, whose labels a language model proposed under the frozen codebook and which were not revised afterwards |

## blind_sample.csv

The 43 reports, of the 45 of versions 1.0.0 to 1.0.2, that the author coded blind to the first-pass labels (random seed 2026110402, drawn from the 402 reports outside the pilot and outside an earlier sample of 45, set aside because its codes had been produced with the help of a software tool rather than by the author alone), with both codings. The 2 Cloudflare reports of the sample were withdrawn with their source. corpus.csv keeps the first-pass labels for these 43. On the 42 that the first pass put in scope: primary trigger 31 agree (Cohen's kappa 0.70), primary fault 37 (kappa 0.87), injectability of the primary fault 40 (kappa 0.91). The tests rerun these figures.

## pilot_check.csv

The 34 pilot reports, of the 50 of versions 1.0.0 to 1.0.2 (random seed 20261103, drawn from five sources; the 16 AWS and Cloudflare reports were withdrawn with their sources): the labels a language model proposed under codebook version 1, the author's verdict (AGREE 25, CHANGE 9) and the final labels. The primary trigger was kept for 30 of the 34 (Cohen's kappa 0.86) and the primary fault for 29 (kappa 0.83). The tests rerun these figures.

## fault_classes.json and triggers.json

The codes of sections 2 and 3 of the codebook, parsed by `tools/build_data.py`, with the injectability rule of each fault class (F3 is directly injectable on AWS only). The short name of each fault class is the one in the paper's Table 2.

## What version 2.0.0 changes

Dataset version 2.0.0 (tool release 0.2.0), of Nov 2026, withdraws the 18 AWS reports and the 42 Cloudflare reports: their 60 rows of corpus.csv, their 16 rows of pilot_check.csv and their 2 rows of blind_sample.csv. Every row that remains is the row of version 1.0.2, byte for byte. No label, code, note or link of a remaining row changed. fault_classes.json, triggers.json and codebook.md are the files of version 1.0.2; codebook.md keeps the study's first title, the title of its date. LICENSE changes only the study's title.

Why. The pages of both sources were fetched by script on Nov 4, 2026 and read by a language model. AWS's site terms leave data mining, robots and similar data gathering tools outside the licence they grant. Cloudflare's website terms bar automated bots that access its pages to develop or operate an AI system unless its robots.txt allows that bot by name. Versions 1.0.0 to 1.0.2 did not name either clause in this context. `site_terms.md` gives each source's clause on automated access. The three sources that remain allow the collection, as `site_terms.md` says.

What moved. On the 429 in-scope reports that state their primary fault, 240 have a primary fault that Chaos Mesh or LitmusChaos can inject directly: 55.9 percent (Wilson 95 percent interval 51.2 to 60.6). Version 1.0.2 gave 274 of 484, 56.6 percent. Without the 34 pilot reports, the figure is 226 of 395, 57.2 percent (52.3 to 62.0).

Versions 1.0.0 to 1.0.2 stay on Zenodo with a note that points to this version.
