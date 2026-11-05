# incident2chaos

Chaos experiments derived from real cloud incidents.

A post-incident report, coded under a published codebook, goes in. A ready-to-run Chaos Mesh or LitmusChaos experiment for the failure it describes comes out, marked as a direct injection, an approximation, or not injectable.

The tool comes with the coded corpus of the study “Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage”: 497 public post-incident reports from AWS, Microsoft Azure, Google Cloud, Cloudflare and GitHub, 2011 to 2026, each coded for its trigger and its fault classes. Its `coverage` command reruns the study's measurement: of the 484 in-scope reports that state their primary fault, 274 (56.6 percent, Wilson 95 percent interval 52.2 to 61.0 percent) have a primary fault that Chaos Mesh or LitmusChaos can inject directly.

## Worked example, under five minutes

You need Python 3.9 or later.

```bash
pip install git+https://github.com/yogeshramaswamy608/incident2chaos@v0.1.0
incident2chaos faults
```

`faults` lists the 20 fault classes of the codebook and what the two tools can inject for each (A direct, P approximation only, N not injectable).

Take the AWS DynamoDB disruption of Oct 19, 2025 in US-EAST-1. Its report is coded in `examples/aws-dynamodb-2025-10-19.yaml`: trigger T6 (a latent defect activated), primary fault F9 (DNS resolution failure), then F19, F16, F20 and F18.

```bash
curl -sLO https://raw.githubusercontent.com/yogeshramaswamy608/incident2chaos/v0.1.0/examples/aws-dynamodb-2025-10-19.yaml
incident2chaos generate --report aws-dynamodb-2025-10-19.yaml --all-faults \
  --namespace shop --label app=checkout --dependency-label app=orders-db \
  --host dynamodb.us-east-1.amazonaws.com --out dynamodb-experiments.yaml
```

The file holds three Chaos Mesh experiments: a DNSChaos that fails the lookups of the DynamoDB endpoint for the `app=checkout` pods (F9, direct), an IOChaos that corrupts data reads (F19, approximation), and a NetworkChaos partition from the `app=orders-db` pods (F16, direct). For F20 and F18 it says that Chaos Mesh has no fault for the class and points to `--tool litmus`, which writes a k6 load generator, joined for F20 by an HTTP error fault on the dependency.

The end-to-end test (workflow `end-to-end`) builds a Kubernetes cluster with kind, installs Chaos Mesh, and applies every Chaos Mesh experiment the tool writes: all 17 reached the injected state. Every LitmusChaos experiment it writes is accepted by the Kubernetes API server with the LitmusChaos resource definitions installed; running them needs the LitmusChaos operator.

Every experiment carries the report's link, the fault class and the injectability as annotations, so a team can trace each experiment to the incident behind it.

To run the experiments, install [Chaos Mesh](https://chaos-mesh.org/docs/quick-start/) or [LitmusChaos](https://docs.litmuschaos.io/) in a test cluster, read the file, set the targets to your own services, and apply it with `kubectl apply -f dynamodb-experiments.yaml`. Run chaos experiments only on systems you own and are allowed to test.

A report from the released corpus can be used directly by its number:

```bash
incident2chaos generate --corpus-id 1 --tool litmus
```

## Coverage

```bash
incident2chaos coverage            # the whole corpus
incident2chaos coverage --by source
incident2chaos coverage --by trigger
incident2chaos coverage --by year --json
```

Each report's injectability is derived from its primary fault class and its provider under the codebook's mapping, and checked against the value stored in the corpus. Give `--corpus FILE` to measure another corpus coded with the same columns.

## A coverage badge for your own postmortems

Code your team's postmortems as YAML files like the example above, in one folder, and add this step to a GitHub Actions workflow:

```yaml
- uses: yogeshramaswamy608/incident2chaos@v0.1.0
  with:
    reports: postmortems/coded
    badge: .github/badges/chaos-coverage.svg
```

The step writes a badge with the share of your incidents whose primary failure Chaos Mesh or LitmusChaos can inject directly. Give `min-share: 0.5` to fail the step below 50 percent. The same works locally: `incident2chaos badge --reports postmortems/coded --out chaos-coverage.svg`.

## Coding a new report

Write a YAML file like the example:

```yaml
id: my-incident-2026-11-01
title: Summary of the incident
url: https://example.com/postmortem
source: AWS PES          # optional; zone loss (F3) is directly injectable on AWS only
trigger: T2              # T1 to T13, T99 when the report does not state it
faults: [F15, F14, F20]  # every failure the report states, primary first
primary_fault: F15
```

Code only what the report states. The codes, their definitions and the coding rules are in [data/codebook.md](data/codebook.md).

## What is in this repository

| Path | What it is |
|---|---|
| `src/incident2chaos/` | The command line tool (Apache 2.0) |
| `src/incident2chaos/data/corpus.csv` | The coded corpus: link, title, date and labels for each of 497 reports (CC BY 4.0) |
| `src/incident2chaos/data/blind_sample.csv` | The 45-report blind agreement sample, both codings (CC BY 4.0) |
| `src/incident2chaos/data/pilot_check.csv` | The 50-report pilot: the proposed labels, the author's verdict and the final labels (CC BY 4.0) |
| `data/codebook.md` | Codebook version 2: 13 trigger codes, 20 fault classes, the mapping to Chaos Mesh and LitmusChaos, the coding rules (CC BY 4.0) |
| `data/site_terms.md` | The site terms of each provider, read before collection |
| `data/README.md` | The columns of the data files |
| `dataset/` | The files of the Zenodo dataset record, as uploaded there |
| `tests/` | Tests that rerun the figures of the paper's Tables 1 to 3 and its agreement figures, and validate every experiment against the Chaos Mesh and LitmusChaos resource schemas |

No report text is redistributed. The corpus holds each report's link, its title and date as the provider's index lists them, and our labels with short evidence notes in our own words.

## Versions the mapping was read from

- Chaos Mesh, commit e636338c (Nov 3, 2026), the API types under `api/v1alpha1`
- LitmusChaos chaos-charts, commit b2662c23 (Apr 16, 2026), 60 fault folders

A fault added to either tool after these commits may change a class from approximation to direct.

## How to cite

Cite the paper and the software. The `CITATION.cff` file gives the software citation, and GitHub shows it under "Cite this repository".

> Ramaswamy Y (2026) Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage.

The dataset on Zenodo: https://doi.org/10.5281/zenodo.23973151 (corpus, codebook, pilot and blind samples, CC BY 4.0). The software's Zenodo DOI is added here when release 0.1.0 is archived.

## How this was made

The author designed the study and the codebook, checked every pilot label, coded the blind agreement sample, and checked every figure against the scripts that produce it. A large language model from Anthropic (Claude Opus 5.5) drafted the code, the tests and this documentation under the author's direction and proposed the first-pass labels of the 447 reports outside the pilot under the frozen codebook; those labels were not revised afterwards. The model is not an author.

## License

The code is under the Apache License 2.0 (`LICENSE`). The LitmusChaos experiment templates in `src/incident2chaos/templates/litmus/` come from the LitmusChaos project under the same license (`NOTICE`). The data files and the codebook are under the Creative Commons Attribution 4.0 International license (`data/LICENSE`).
