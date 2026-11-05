# Changelog

## 0.1.0, release day

First release, with the paper “Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage”.

- `incident2chaos faults`: the 20 fault classes of codebook version 2 and their injectability by Chaos Mesh and LitmusChaos.
- `incident2chaos generate`: a Chaos Mesh or LitmusChaos experiment for each fault class of a coded report, from a YAML or JSON file or from the released corpus, each experiment annotated with the report's link, the fault class and its injectability.
- `incident2chaos coverage`: the study's measurement rerun from the corpus, overall and by source, year or trigger, with Wilson 95 percent intervals.
- The coded corpus of 497 reports, the 50-report pilot check, the 45-report blind agreement sample and codebook version 2, under CC BY 4.0.
- Tests that rerun the figures of the paper's Tables 1 to 3 and its agreement figures and validate every experiment against the Chaos Mesh and LitmusChaos resource schemas.
