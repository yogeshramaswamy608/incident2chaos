# Changelog

## 0.1.0, release day

First release, with paper 1.

- `incident2chaos faults`: the 20 fault classes of codebook version 2 and their injectability by Chaos Mesh and LitmusChaos.
- `incident2chaos generate`: a Chaos Mesh or LitmusChaos experiment for each fault class of a coded report, from a YAML or JSON file or from the released corpus, each experiment annotated with the report's link, the fault class and its injectability.
- `incident2chaos coverage`: the paper 1 measurement rerun from the corpus, overall and by source, year or trigger, with Wilson 95 percent intervals.
- The coded corpus of 497 reports, the 45-report blind agreement sample and codebook version 2, under CC BY 4.0.
- Tests that rerun every figure of paper 1 and validate every experiment against the Chaos Mesh and LitmusChaos resource schemas.
