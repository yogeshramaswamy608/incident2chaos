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

1. The tool installs with pip from the tagged release `v0.2.1` on GitHub and needs only PyYAML. It writes experiment files and never contacts a cluster; Parts 0 to 3 need no Kubernetes.
2. On lab machines without internet access, download the release once (`pip download git+https://github.com/yogeshramaswamy608/incident2chaos@v0.2.1 -d wheels`) and install from the folder with `pip install --no-index --find-links wheels incident2chaos`.
3. Part 4 runs a kind cluster inside Docker on each laptop and needs about 4 GB of free memory. The Chaos Mesh install takes up to 10 minutes; start it at the beginning of Part 3 if time is short.
4. The script `run_lab.py` in this folder runs every command of the handout and checks its results: `python3 run_lab.py` runs Parts 0 to 3, and `python3 run_lab.py --parts 0,1,2,3,4` adds Part 4 on a machine with Docker, kind, kubectl and Helm. Parts 0 to 3 were run that way against the code of release 0.2.1; the repository's workflow `lab-check` runs all five parts on a GitHub runner on every change to this folder.
5. The answer key below sits in a public repository, so students can read it. If that matters for marking, mark the reasoning of questions 1.1, 2.2, 2.3 and 5.1, which the key does not settle word for word.

## Answer key

The published codes come from the study's corpus, rows 420, P45 and P48. Rows P45 and P48 are from the pilot, whose labels the author checked against each report; he agreed with both. Row 420 is a first-pass row: a language model proposed its labels under the frozen codebook, and the author did not check them one by one. No pilot report of the three sources that remain has a DNS failure as its primary fault, and Part 4 needs one. Accept a student's different code when the pair can point to a sentence in the report and a codebook rule that supports it: the point is the reasoning, not the match.

**0.1.** P: F3 zone or data-center loss, F8 network capacity saturation, F15 bad configuration state, F16 an internal dependency unavailable, F17 credential or certificate failure, F18 software resource limit, F20 overload or retry storm. N: F4 region-wide or control-plane loss. A good reason, for F15: a bad configuration is a wrong value spread by the provider's own systems, and a tool can only corrupt a file or an answer it is pointed at, not reproduce how the value spread.

**1.1.** Published codes:

| Report | Trigger | Primary fault | Injectability |
|---|---|---|---|
| R1, row 420 | T3, a planned operation | F9, DNS resolution failure | A |
| R2, row P45 | T3, a planned operation | F16, a dependency inside the provider unavailable | P |
| R3, row P48 | T5, a demand surge | F20, overload or retry storm | P |

What the reports state, in our words: R1, an infrastructure migration that moved the global DNS name of Codespaces to a new load balancer: the old record was deleted, the new one failed to be added, so requests to the name were refused, and the first rollback failed too. R2, a database host that came back from routine maintenance able only to read, so the notifications service could not send notifications for about an hour until the host was made writable again. R3, a sharp rise in traffic, mostly to search endpoints, that slowed or timed out pages and API calls for users who were not signed in, until the source was found and traffic management restored service.

Common differences. R1: T2, a configuration change, since a DNS record is configuration; the report frames the change as part of a migration, a planned operation, and rule V2 makes the operation that started the chain the trigger. R2: T6, a latent defect, for a host that came up in the wrong state; rule V1 makes the named operation the trigger over a defect it exposed. R3: F5, latency, for the slow pages; the report names the traffic spike as the cause of the impact, which is F20 under rule V8.

**1.2.** The maintenance is the operation the report names as the start, and rules V1 and V2 make a named planned operation the trigger, T3, over a defect it exposed, T6. The failure the notifications service suffered was that the database it depends on could not accept writes, a dependency inside the provider unavailable as the report states it, F16 under rule V5. F19 needs stated corrupt or invalid data, and the report states none.

**2.1.** `r1-chaos-mesh.yaml` makes every lookup fail: its `patterns` list is `'*'`, because the coded report names no host. On a shared cluster, narrow it with `--host` to one name the service under test resolves, and keep `--duration` short. Part 4 does both.

**2.2.** Chaos Mesh has no built-in fault for an overload or a retry storm, so the tool writes the class's injectability and points to LitmusChaos. `r3-litmus.yaml` holds three manifests: a Secret with a k6 script that sends 200 virtual users at the service for 60 seconds, a ChaosEngine that runs that load, and a ChaosEngine that makes the dependency answer HTTP 503 for 60 seconds, so that clients retry. It reproduces load against the service. It leaves out what made the real incident: traffic from outside, mostly to one kind of endpoint, from users who were not signed in, while signed-in traffic was not affected. The defense that mattered was a limiter that separates those classes of traffic, and the report names no retries at all. That gap is why the class is P.

**2.3.** Only in part. GitHub reports that the database host was up and in read-only mode: it was reachable and could answer reads, but the notifications service could not do its writes, and the delivery jobs that failed were retried once the host was writable. A partition tests a dependency that cannot be reached at all. A passing result shows the service survives losing the dependency; it does not show how it handles a dependency that accepts connections and refuses writes, nor that the failed jobs are retried and none are lost. A closer test aims an F14 fault at the writes alone; making a database read-only is not a built-in fault of either catalog, which is the codebook's reason for P.

**2.4.** The annotations `incident2chaos.io/report`, `incident2chaos.io/fault-class`, `incident2chaos.io/injectability` and `incident2chaos.io/version`. Good reasons: a failed experiment can be traced to the incident it guards against, and a team can show which past incidents its experiments cover.

**3.1.** p = 199 / 429 = 0.464, so 46.4 percent. With z = 1.96: center 0.4642, half width 0.0470, interval 41.7 to 51.1 percent, as the tool prints.

**3.2.** T12, an attack: 0 of 5 directly injectable, 0.0 percent (0.0 to 43.4). Its reports end in an overload (F20) or a saturated network (F8), both P. T11, expiry or exhaustion: 1 of 13, 7.7 percent (1.4 to 33.3). An expired certificate or an exhausted fixed resource leads to F17 or F18, which are P. Accept T5 or T9 (both 16.7 percent) as the second answer if the student notes that T9 has only 6 reports. The unlabeled first row holds the one report that describes no failure of the provider's own service.

**3.3.** Examples. T1 or T2, a code or configuration change: test with staged rollouts, canary analysis and automatic rollback rather than fault injection. T11, an expiry: monitor expiry dates and test renewal; a TimeChaos that moves the clock past an expiry date is the closest approximation. T8, a facility event: drills of zone evacuation. T12, an attack: load tests and denial-of-service exercises with the provider's permission.

**3.4.** With the published codes the badge reads 1 of 3, 33.3 percent, and the Wilson interval for 1 of 3 runs from 6.1 to 79.2 percent. A figure from a handful of postmortems carries almost no information; a team needs dozens of coded incidents before its coverage figure means something.

**4.1.** Before: `getent` prints an address for example.com, then `lookup worked`. During: `getent` prints nothing and exits with an error, then `lookup failed`. The experiment made the pod's lookups of example.com fail; lookups of other names, the pod itself and its network were left alone.

**4.2.** Partly. What users met was a name that no longer led to the service, and a failing lookup tests what the clients and the service do then. The defenses that mattered sat in the change itself: replacing the record in one step, and a rollback that works, which GitHub names in its follow-up along with a mirrored test zone for DNS. A fault injection does not test a change procedure. And recovery took longer than the fix because of DNS caching, which a two-minute experiment in one pod does not show. A closer exercise rehearses the migration in a test zone and measures how long clients keep the old answer.

**5.1.** Good answers name two of these: the reports are written by the providers themselves and choose what to disclose; a language model proposed the labels of all 437 reports, one author checked the proposed labels of the 34 pilot reports (agreeing with 25, changing 9) and coded a sample of 43 blind, and the labels of the other 403 reports were not revised afterwards, with agreement on the primary fault of kappa 0.87 and on its injectability of kappa 0.86 in the blind sample; the mapping to the tools was read from one commit of each tool's catalog and judged by the same author, who changed four of its lines, and a fault added since may change a class; three providers do not stand for every cloud.

## Suggested marking, 10 points

Part 1, 3 points: codes with a rule and a report sentence for each. Part 2, 3 points: questions 2.2 and 2.3 carry 1 point each, 2.1 and 2.4 half a point each. Part 3, 3 points: a correct interval in 3.1 and a reasoned answer to 3.3. Part 5, 1 point. Part 4, when run, replaces the marks of question 3.4.

## Sources and license

The tool, the codebook and the corpus: incident2chaos release 0.2.1, https://github.com/yogeshramaswamy608/incident2chaos (code Apache 2.0, data and codebook CC BY 4.0). Dataset: https://doi.org/10.5281/zenodo.23973150. Software: https://doi.org/10.5281/zenodo.23973728. Both addresses always open the newest version. The three reports belong to GitHub; the lab links to them and quotes none of their text.

The handout and this guide are licensed CC BY 4.0: adapt them for your course and keep the attribution. If you use the lab in a course, a short note in the repository's issues helps keep it working with new releases of Chaos Mesh and LitmusChaos.

Written under the direction of Yogesh Ramaswamy, author of incident2chaos, by a large language model from Anthropic (Claude Opus 5.5), and moved on Nov 25, 2026 to release 0.2.1 and to three GitHub reports, since the corpus no longer holds the Cloudflare reports of the first version. Parts 0 to 3 were run against the code of release 0.2.1 and checked by the script run_lab.py; the workflow lab-check runs all five parts, Part 4 included, on a GitHub runner.
