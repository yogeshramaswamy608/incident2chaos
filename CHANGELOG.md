# Changelog

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
