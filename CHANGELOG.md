# Changelog

## 0.2.0, Nov 2026

A data release. The tool's code is unchanged but for the codebook version it prints.

- The corpus now holds 437 reports from three sources: Microsoft Azure (81), Google Cloud (172) and GitHub (184). The 18 AWS reports and the 42 Cloudflare reports are withdrawn, with their 16 rows of `pilot_check.csv` and 2 rows of `blind_sample.csv`. Both sources' pages were fetched by script and labelled with a language model, which their site terms do not allow (`data/site_terms.md`). Every remaining row is the row of release 0.1.2, byte for byte, and keeps its `corpus_no`, so the numbers have gaps.
- Codebook version 3: the author checked the 20 mapping lines against the Chaos Mesh and LitmusChaos catalogs and changed four. F3, F8 and F16 are now approximation only, F19 is now direct; 73 corpus values and 5 pilot values follow. `incident2chaos faults` prints the new values, and `tools/build_data.py` now reads the value of the F16 line correctly.
- The headline is 199 of the 429 in-scope reports that state their primary fault, 46.4 percent (Wilson 95 percent interval 41.7 to 51.1), in place of 274 of 484, 56.6 percent. The withdrawal alone gives 240 of 429, 55.9 percent. The tests rerun the new figures of every table and agreement figure.
- The worked example is the Azure Storage incident of Nov 13, 2024 (`examples/azure-storage-2024-11-13.yaml`, corpus row 31), in place of an AWS report.
- `dataset/` holds the files of Zenodo dataset version 2.0.0.
- The teaching lab still installs release 0.1.2, whose corpus it uses.

## 0.1.2, Nov 16, 2026

A correction release. The tool's code is unchanged, and no label, code or figure changed.

- The links of the 81 Microsoft Azure reports are corrected. In releases 0.1.0 and 0.1.1, 54 of them held `https://aka.ms/AzPIR/ID`, which opens Microsoft's feedback survey for the review, and 27 held an address that opens Azure's status history without the review. All 81 now hold `https://azure.status.microsoft/en-us/status/history/?trackingId=ID`, where ID is the review's tracking id. Only those `url` cells changed, in `corpus.csv` (81 rows), `blind_sample.csv` (12 rows) and `pilot_check.csv` (12 rows), so an experiment that `generate --corpus-id` writes for an Azure report now carries the new link.
- The new `tools/check_links.py` opened every link of the corpus on Nov 16, 2026 (UTC). The links of the 416 rows of the other four providers opened their reports. Of the 81 new Azure links, 80 opened their review. The address of row P9 (PLT7-RTZ) returned Azure's status history with no review, and `dataset/README.md` says what was seen.
- `dataset/` holds the files of Zenodo dataset version 1.0.2, which carries the same correction.
- The coverage report tells the reader to install this release in place of 0.1.0.

## 0.1.1, Nov 16, 2026

A correction release. The tool and the five data files are unchanged; the labels, the codes and the figures are the same.

- `data/LICENSE`, `data/README.md`, `data/codebook.md` and `README.md` said the short notes of the corpus were in the author's own words. That was wrong for all but the 50 notes of the pilot rows: a language model wrote the notes of the 447 first-pass rows and proposed every label, and the author checked the proposed labels of the 50 pilot rows, changed 10 and wrote the notes of those rows. The four files now say so. The lab handout, its instructor guide and the coverage report named the model for the 447 reports only; they now name it for all 497. The kubectl plugin archive carries the corrected `LICENSE-data`.
- `data/codebook.md` counts 53 LitmusChaos fault folders in place of 60, a count that included 7 icon folders, with a dated erratum line. No fault class or injectability rule depends on the count.
- The blind agreement on the primary fault is printed as kappa 0.87 (307/351 = 0.8746) in place of 0.875.
- `README.md`, `data/README.md` and `data/site_terms.md` no longer say the site terms were read before collection; they give the date the terms were read. `data/README.md` gives the times `retrieved_utc` holds in place of fetch dates no record supports, and `data/site_terms.md` names every purpose of Cloudflare's clause on automated bots.
- `data/README.md` describes four columns more exactly: who made the out-of-scope calls, what the pilot rows leave empty, and where the short names of the fault classes come from.
- `dataset/` holds the files of Zenodo dataset version 1.0.1, which carries the same corrections.
- The package metadata names both licenses (Apache-2.0 for the code, CC BY 4.0 for the data), and the source archive now carries the tests with their schemas and example files.

## 0.1.0, Nov 5, 2026

First release, with the paper “Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage”.

- `incident2chaos faults`: the 20 fault classes of codebook version 2 and their injectability by Chaos Mesh and LitmusChaos.
- `incident2chaos generate`: a Chaos Mesh or LitmusChaos experiment for each fault class of a coded report, from a YAML or JSON file or from the released corpus, each experiment annotated with the report's link, the fault class and its injectability.
- `incident2chaos coverage`: the study's measurement rerun from the corpus, overall and by source, year or trigger, with Wilson 95 percent intervals.
- The coded corpus of 497 reports, the 50-report pilot check, the 45-report blind agreement sample and codebook version 2, under CC BY 4.0.
- Tests that rerun the figures of the paper's Tables 1 to 3 and its agreement figures and validate every experiment against the Chaos Mesh and LitmusChaos resource schemas.
