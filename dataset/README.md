# Coded corpus of 497 public cloud post-incident reports, with codebook version 2

The data of the study “Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage” (Yogesh Ramaswamy, 2026). The tool incident2chaos, which reruns the study's figures from these files, is at https://github.com/yogeshramaswamy608/incident2chaos

497 public post-incident reports published by five cloud providers on their own sites. The 447 reports outside the pilot were coded under codebook version 2 (`codebook.md`); the 50 pilot reports keep the labels as checked by the author. License: CC BY 4.0 (LICENSE).

This is version 1.0.1 of the record, of Nov 16, 2026. It corrects the documentation of version 1.0.0 and leaves the five data files unchanged, byte for byte. The last section lists each correction.

| Source | Reports | Report links on |
|---|---|---|
| AWS Post-Event Summaries (`AWS PES`) | 18 | aws.amazon.com |
| Microsoft Azure Post Incident Reviews (`Microsoft Azure PIR`) | 81 | aka.ms (54), azure.status.microsoft (27) |
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
| `url` | The report's link; GitHub incidents share the link of their monthly report |
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

The codes of sections 2 and 3 of the codebook, parsed from the codebook by the tool's build script, with the injectability rule of each fault class (F3 is directly injectable on AWS only). The short name of each fault class is the one in the paper's Table 2.

## What version 1.0.1 corrects

This is version 1.0.1, of Nov 16, 2026. The first version, 1.0.0, is https://doi.org/10.5281/zenodo.23973151, and https://doi.org/10.5281/zenodo.23973150 always points to the newest version. The five data files (corpus.csv, blind_sample.csv, pilot_check.csv, fault_classes.json and triggers.json) are the files of version 1.0.0, byte for byte. No label or code changed, and no rule changed in what it requires.

The notes and the labels. LICENSE, README.md and section 1 of codebook.md of version 1.0.0 said the notes were in the author's own words, and site_terms.md called the labels our own. That was wrong for all but the 50 notes of the pilot rows. A language model wrote the notes of the 447 first-pass rows and proposed every label of the corpus, the pilot labels included. The author checked the proposed labels of the 50 pilot rows, agreed with 40 and changed 10, and wrote the 50 notes of those rows with his check. LICENSE and README.md now say who produced the labels and the notes, and codebook.md and site_terms.md no longer call them ours.

The fault folder count. codebook.md said the LitmusChaos catalog held 60 fault folders. Under faults/ of chaos-charts at commit b2662c23, the seven group folders hold 60 folders, 7 of them icon folders, so the count is 53. No fault class and no injectability rule depends on that count.

The fault kappa. The blind agreement on the primary fault is 307/351 = 0.8746. The first version printed it to three decimals as 0.875. To two decimals it is 0.87, not 0.88, and the files now print 0.87.

The fetch dates and the site terms. README.md said the pages were fetched on Nov 3 and 4, 2026 (UTC), and README.md and site_terms.md said the site terms were read before collection. `retrieved_utc` gives Nov 4, 2026 (UTC) for every source, and the terms were read on Nov 4, 2026 (UTC). No record shows a fetch on Nov 3, 2026 (UTC), and none shows which came first on Nov 4. README.md now gives the times `retrieved_utc` holds, and both files give only the date the terms were read. The summary of Cloudflare's clause on automated bots in site_terms.md now names every purpose the clause names.

The columns. README.md now says that the first pass made the 6 out-of-scope calls and that the author's blind coding put one of them, row 36, in scope. It also says that the pilot rows hold no list of fault classes and no secondary trigger, and that the short names in fault_classes.json come from the paper's Table 2.

Two stray words. In rows 36 and 256 of corpus.csv, two of the 6 out-of-scope reports, the column `codebook_gap` holds the word `low` and the word `high` in place of a note. The data files are unchanged, so both words remain.
