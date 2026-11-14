# Instructor guide: from a real cloud incident to a chaos experiment

The student handout is `README.md` in this folder. This guide gives the course fit, the timing, the setup notes and the answer key.

## Course fit

The lab fits a unit on reliability, failure or testing in a course on cloud computing, distributed systems or software engineering, at final year undergraduate or master's level. Students need basic Python and the command line. Kubernetes experience helps for Part 4 but is not required: every command is given.

It teaches three things a lecture rarely shows: how engineers write up real outages, how far fault injection tools are from those outages, and how to put a confidence interval on a measured share.

## Timing for a two-hour session

| Minutes | Part | Notes |
|---|---|---|
| 0 to 10 | 0, set up | Have students install before the session if lab machines are slow to reach PyPI and GitHub. |
| 10 to 45 | 1, code three incidents | The longest part. Give 10 minutes to the codebook, then about 8 minutes a report. |
| 45 to 70 | 2, generate and read | Discuss question 2.2 with the class: it is the core of the lab. |
| 70 to 95 | 3, measure coverage | Question 3.1 can be done in pairs with a calculator. |
| 95 to 120 | 4, cluster run | Needs Docker, and the cluster started before the lab as the handout's Before the lab section says. Without it, run a class discussion on questions 3.3 and 5.1. |

For a 90-minute session, drop Part 4 and give question 5.1 as homework.

## Setup notes

1. The tool installs with pip from the tagged release `v0.1.0` on GitHub and needs only PyYAML. It writes experiment files and never contacts a cluster; Parts 0 to 3 need no Kubernetes.
2. On lab machines without internet access, download the release once (`pip download git+https://github.com/yogeshramaswamy608/incident2chaos@v0.1.0 -d wheels`) and install from the folder with `pip install --no-index --find-links wheels incident2chaos`.
3. Part 4 runs a kind cluster inside Docker on each laptop and needs about 4 GB of free memory. The Chaos Mesh install takes up to 10 minutes; start it at the beginning of Part 3 if time is short.
4. The script `run_lab.py` in this folder runs every command of the handout and checks its results: `python3 run_lab.py` runs Parts 0 to 3, and `python3 run_lab.py --parts 0,1,2,3,4` adds Part 4 on a machine with Docker, kind, kubectl and Helm. Parts 0 to 3 were run that way against release 0.1.0; the repository's workflow `lab-check` runs all five parts on a GitHub runner on every change to this folder.
5. The answer key below sits in a public repository, so students can read it. If that matters for marking, mark the reasoning of questions 1.1, 2.2, 2.3 and 5.1, which the key does not settle word for word.

## Answer key

The published codes come from the study's corpus, rows P42, P39 and P41. These three rows are from the 50-report pilot, whose labels the author checked against each report. Accept a student's different code when the pair can point to a sentence in the report and a codebook rule that supports it: the point is the reasoning, not the match.

**0.1.** P: F3 outside AWS (zone or data-center loss), F15 bad configuration state, F17 credential or certificate failure, F18 software resource limit, F19 data corruption, F20 overload or retry storm. N: F4 region-wide or control-plane loss. A good reason, for F15: a bad configuration is a wrong value spread by the provider's own systems, and a tool can only corrupt a file or an answer it is pointed at, not reproduce how the value spread.

**1.1.** Published codes:

| Report | Trigger | Primary fault | Injectability |
|---|---|---|---|
| R1, row P42 | T1, a code release | F9, DNS resolution failure | A |
| R2, row P39 | T10, an upstream dependency outside the provider | F16, a dependency inside the provider unavailable | A |
| R3, row P41 | T1, a code release | F20, overload or retry storm | P |

What the reports state, in our words: R1, a release of the 1.1.1.1 resolver that changed the order of records in its answers, after which some clients failed to resolve names. R2, an outage at a third-party cloud provider that backs part of the storage of Workers KV, after which Workers KV and the services that rely on it failed. R3, a new dashboard version with a bug that sent many repeated calls to the Tenant Service API, which became overloaded and recovered only after a rate limit, more pods and a revert.

Common differences. R1: T6, a latent defect, for the client software that could not handle the new order; rule V1 makes the named release the trigger. R2: F16 versus T10 confusion, settled by rule V7. R3: F14, error responses, as the primary fault; the report describes the overload of the Tenant Service as the cause of the impact, which is F20 under rule V8.

**1.2.** The outage at the outside provider is where the incident starts, and rule V7 codes an outage of a third party as the trigger, T10. What Cloudflare's customers lost was Workers KV, a service inside Cloudflare that depended on that provider, so the failure the tool must inject is an unavailable internal dependency, F16.

**2.1.** `r1-chaos-mesh.yaml` makes every lookup fail: its `patterns` list is `'*'`, because the coded report names no host. On a shared cluster, narrow it with `--host` to one name the service under test resolves, and keep `--duration` short. Part 4 does both.

**2.2.** Chaos Mesh has no built-in fault for an overload or a retry storm, so the tool writes the class's injectability and points to LitmusChaos. `r3-litmus.yaml` holds three manifests: a Secret with a k6 script that sends 200 virtual users at the service for 60 seconds, a ChaosEngine that runs that load, and a ChaosEngine that makes the dependency answer HTTP 503 for 60 seconds, so that clients retry. It reproduces load and retries against the service. It leaves out what made the real incident: a client bug that multiplied calls, new versions of the Tenant Service deployed during the incident, one of which made it worse, and the slow recovery of the overloaded service. That gap is why the class is P.

**2.3.** Only in part. Cloudflare reports that about 90 percent of Workers KV requests failed with HTTP 503 or 500, the uncached reads that needed its storage, while cached reads kept working. So the services that depend on Workers KV received error answers, not silence. A partition tests a dependency that cannot be reached at all. A passing result shows the service survives losing the dependency; it does not show how it handles a dependency that answers most requests with errors. A closer test aims an F14 fault at the dependency, such as LitmusChaos pod-http-status-code with 503. The experiment says nothing about the outside provider.

**2.4.** The annotations `incident2chaos.io/report`, `incident2chaos.io/fault-class`, `incident2chaos.io/injectability` and `incident2chaos.io/version`. Good reasons: a failed experiment can be traced to the incident it guards against, and a team can show which past incidents its experiments cover.

**3.1.** p = 274 / 484 = 0.566, so 56.6 percent. With z = 1.96: center 0.5656, half width 0.0440, interval 52.2 to 61.0 percent, as the tool prints.

**3.2.** T11, expiry or exhaustion: 1 of 13 directly injectable, 7.7 percent (1.4 to 33.3). An expired certificate or an exhausted fixed resource leads to F17 or F18, which are P. T5, demand surge: 9 of 37, 24.3 percent (13.4 to 40.1). A surge leads to overload or retry storms, F20, which is P. Accept T4 or T12 (both 33.3 percent) as the second answer if the student notes their small counts. The unlabeled first row holds the 6 reports that describe no failure of the provider's own service.

**3.3.** Examples. T1 or T2, a code or configuration change: test with staged rollouts, canary analysis and automatic rollback rather than fault injection. T11, an expiry: monitor expiry dates and test renewal; a TimeChaos that moves the clock past an expiry date is the closest approximation. T8, a facility event: drills of zone evacuation. T12, an attack: load tests and denial-of-service exercises with the provider's permission.

**3.4.** With the published codes the badge reads 2 of 3, 66.7 percent, and the Wilson interval for 2 of 3 runs from 20.8 to 93.9 percent. A figure from a handful of postmortems carries almost no information; a team needs dozens of coded incidents before its coverage figure means something.

**4.1.** Before: `getent` prints an address for example.com, then `lookup worked`. During: `getent` prints nothing and exits with an error, then `lookup failed`. The experiment made the pod's lookups of example.com fail; lookups of other names, the pod itself and its network were left alone.

**4.2.** Partly. The defense that mattered was a client that copes with an answer it does not expect, and a failing lookup tests only the fallback when resolution fails. A closer test would return answers in a changed order, which neither tool's catalog offers as a built-in fault; that is a good class discussion of where the A mark overstates a match.

**5.1.** Good answers name two of these: the reports are written by the providers themselves and choose what to disclose; one author checked the proposed labels of the 50-report pilot (agreeing with 40, changing 10) and coded a sample of 45 blind, and a language model proposed the labels of the other 447 reports under the frozen codebook, with agreement on the primary fault of kappa 0.875 in the blind sample; the mapping to the tools was read from one commit of each tool's catalog, and a fault added since may change a class; five providers do not stand for every cloud.

## Suggested marking, 10 points

Part 1, 3 points: codes with a rule and a report sentence for each. Part 2, 3 points: questions 2.2 and 2.3 carry 1 point each, 2.1 and 2.4 half a point each. Part 3, 3 points: a correct interval in 3.1 and a reasoned answer to 3.3. Part 5, 1 point. Part 4, when run, replaces the marks of question 3.4.

## Sources and license

The tool, the codebook and the corpus: incident2chaos release 0.1.0, https://github.com/yogeshramaswamy608/incident2chaos (code Apache 2.0, data and codebook CC BY 4.0). Dataset: https://doi.org/10.5281/zenodo.23973151. Software: https://doi.org/10.5281/zenodo.23973729. The three reports belong to Cloudflare; the lab links to them and quotes none of their text.

The handout and this guide are licensed CC BY 4.0: adapt them for your course and keep the attribution. If you use the lab in a course, a short note in the repository's issues helps keep it working with new releases of Chaos Mesh and LitmusChaos.

Written under the direction of Yogesh Ramaswamy, author of incident2chaos, by a large language model from Anthropic (Claude Opus 5.5). Parts 0 to 3 were run against release 0.1.0 and checked by the script run_lab.py; the workflow lab-check runs all five parts, Part 4 included, on a GitHub runner.
