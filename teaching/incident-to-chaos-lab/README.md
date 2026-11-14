# Lab: from a real cloud incident to a chaos experiment

A two-hour lab for courses in cloud computing, distributed systems and software engineering. Students work in pairs.

You read three public post-incident reports, code each one under a published codebook, turn the coded failure into a Chaos Mesh or LitmusChaos experiment, and measure, over 484 real incidents whose reports state their main failure, what share have a main failure that today's chaos tools can inject directly. Part 4, which needs Docker, runs one experiment on a Kubernetes cluster on your own laptop.

## What you will be able to do

1. Read a provider's post-incident report and name its trigger and its failures under a fixed set of codes.
2. Turn a coded failure into a chaos experiment and judge how closely it matches the real incident.
3. Measure a share with a 95 percent confidence interval and say what the interval means.
4. Run a fault injection on a test cluster and see its effect (Part 4).

## Before the lab

You need Python 3.9 or newer and an internet connection. On Windows, run the lab in WSL (Windows Subsystem for Linux).

Part 4 also needs Docker, kind 0.29 or newer, kubectl and Helm 3, and about 4 GB of free memory. Start the cluster before the lab, on the same network you will use: these commands take 10 to 15 minutes, most of it downloading images.

<!-- part: 4 -->
```bash
kind create cluster --name lab
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/containerd/containerd.sock --set dnsServer.create=true --wait --timeout 10m
kubectl apply -f https://raw.githubusercontent.com/yogeshramaswamy608/incident2chaos/v0.1.0/tools/e2e/app.yaml
kubectl -n shop rollout status deploy/my-service --timeout=180s
kubectl -n shop scale deploy/my-service --replicas=1
kubectl -n shop rollout status deploy/my-service --timeout=180s
```

This starts a Kubernetes cluster inside Docker, installs Chaos Mesh, and deploys two small test services in a namespace `shop`: the service `app=my-service`, scaled to one pod, and its dependency `app=orders-db`.

## Plan

| Part | What you do | Minutes |
|---|---|---|
| 0 | Set up the tool | 10 |
| 1 | Code three real incidents | 35 |
| 2 | Generate and read the experiments | 25 |
| 3 | Measure coverage | 25 |
| 4 | Run one experiment on a cluster (needs Docker) | 25 |

Without Docker, use the time of Part 4 for questions 3.3 and 5.1 in more depth.

Write your answers in one text file, `answers.txt`, with the question numbers.

## Part 0. Set up the tool (10 minutes)

<!-- part: 0 -->
```bash
python3 -m venv lab
. lab/bin/activate
pip install git+https://github.com/yogeshramaswamy608/incident2chaos@v0.1.0
incident2chaos --version
incident2chaos faults
```

`faults` prints the 20 fault classes of the codebook. For each class it shows whether Chaos Mesh or LitmusChaos can inject it: A means a built-in fault injects it directly, P means only an approximation exists, N means neither tool can inject it.

**Question 0.1.** Which fault classes are P or N? Pick one and say in one sentence why a fault injection tool cannot reproduce it directly.

## Part 1. Code three real incidents (35 minutes)

Open the codebook: https://github.com/yogeshramaswamy608/incident2chaos/blob/v0.1.0/data/codebook.md

Read sections 1, 2, 3 and 6 (about 10 minutes). Three rules matter most:

1. Code only what the report states. If the report does not say it, the code is T99 or F99.
2. The trigger is the first event or change the report names as the start of the incident.
3. The primary fault is the failure that caused most of the customer impact. List it first in `faults`, then every other failure the report states.

Now read the three reports, about 8 minutes each:

| Report | Provider | Link |
|---|---|---|
| R1 | Cloudflare, Jan 8, 2026 | https://blog.cloudflare.com/cname-a-record-order-dns-standards/ |
| R2 | Cloudflare, Jun 12, 2025 | https://blog.cloudflare.com/cloudflare-service-outage-june-12-2025/ |
| R3 | Cloudflare, Sep 12, 2025 | https://blog.cloudflare.com/deep-dive-into-cloudflares-sept-12-dashboard-and-api-outage/ |

For each report, write a file in a folder named `coded`: `coded/r1.yaml`, `coded/r2.yaml` and `coded/r3.yaml`. Use this form, with the report's title and link and your own codes in place of TX, FX and FY:

```yaml
id: r1
title: The report's title
url: https://blog.cloudflare.com/the-report-link/
source: Cloudflare blog post-mortem
trigger: TX
faults: [FX, FY]
primary_fault: FX
```

Then compare your codes with the published coding of the study. The three reports are rows P42, P39 and P41 of its corpus. Each command prints the published trigger on its fourth line and the published primary fault on its sixth:

<!-- part: 1 -->
```bash
incident2chaos generate --corpus-id P42 | head -6
incident2chaos generate --corpus-id P39 | head -6
incident2chaos generate --corpus-id P41 | head -6
```

**Question 1.1.** For each report, write your trigger and primary fault beside the published ones. Where you differ, name the codebook rule that settles it, and say which of the two you would defend.

**Question 1.2.** R2 began with an outage at a company outside Cloudflare. Why is its trigger T10 while its primary fault is F16? Use rule V7.

## Part 2. Generate and read the experiments (25 minutes)

The target service in these commands is a set of pods labeled `app=my-service` in a namespace `shop`, and its dependency is labeled `app=orders-db`. Part 4 builds exactly these services.

<!-- part: 2 -->
```bash
incident2chaos generate --report coded/r1.yaml --namespace shop --label app=my-service --out r1-chaos-mesh.yaml
incident2chaos generate --report coded/r2.yaml --namespace shop --label app=my-service --dependency-label app=orders-db --out r2-chaos-mesh.yaml
incident2chaos generate --report coded/r3.yaml --namespace shop --label app=my-service --dependency-label app=orders-db --out r3-chaos-mesh.yaml
incident2chaos generate --report coded/r3.yaml --tool litmus --namespace shop --label app=my-service --dependency-label app=orders-db --url http://my-service.shop.svc.cluster.local/ --out r3-litmus.yaml
```

Open each file. The comment lines at the top give the report, its link, the trigger and, for each fault class, its injectability. Every experiment carries the same facts as annotations under `metadata`.

If your codes for a report differ from the published ones, your file holds a different experiment. Answer for the file you generated, and say which codes it came from.

**Question 2.1.** The R1 experiment is a DNSChaos. Which host names does it make fail? Before you ran it on a cluster that other people share, what would you change, and with which option of `generate`?

**Question 2.2.** Why does `r3-chaos-mesh.yaml` hold no experiment? Read `r3-litmus.yaml`: what does the approximation reproduce of the real incident, and what does it leave out?

**Question 2.3.** The R2 experiment cuts the network between the service and its dependency. Is that the failure Cloudflare's customers saw? What would a passing result of this experiment tell a team, and what would it not tell them?

**Question 2.4.** Find the annotations that tie each experiment to its incident. Give one reason a reliability team would want them on every experiment it runs.

## Part 3. Measure coverage (25 minutes)

<!-- part: 3 -->
```bash
incident2chaos coverage
incident2chaos coverage --by source
incident2chaos coverage --by trigger
incident2chaos badge --reports coded --out coverage.svg
```

The first line of `coverage` is the study's headline figure: of the reports that state their primary fault, the share whose primary fault Chaos Mesh or LitmusChaos can inject directly, with its 95 percent Wilson interval.

The Wilson interval for k successes in n trials, with p = k / n and z = 1.96, is

center = (p + z²/(2n)) / (1 + z²/n)

half width = z × √(p(1 − p)/n + z²/(4n²)) / (1 + z²/n)

and the interval runs from center minus half width to center plus half width.

**Question 3.1.** The headline counts 274 directly injectable reports out of 484 with a stated primary fault. Work out the share and its Wilson interval by hand or in a few lines of Python, and check them against the tool.

**Question 3.2.** In the trigger table, which two triggers have the lowest direct share? Leave out the unlabeled first row: it holds the 6 reports that describe no failure of the provider's own service. Read their definitions in the codebook and give one reason for each.

**Question 3.3.** Chaos tools inject faults, not triggers. Name two trigger codes that no chaos tool can start, and say how a team could test its defenses against each one instead.

**Question 3.4.** `badge` measured your three coded reports. Work out the Wilson interval for your share with n = 3. What does it tell you about a coverage figure from one team's handful of postmortems?

## Part 4. Run one experiment on a cluster (25 minutes, needs Docker)

Run chaos experiments only on clusters you own. This one runs on your laptop and is deleted at the end.

You started the cluster before the lab (see Before the lab). The experiment from your R1 file acts on one pod, so the service runs one pod and you can watch it. Check that a lookup works, generate the R1 experiment for one host only, apply it, and check again:

<!-- part: 4 -->
```bash
kubectl -n shop exec deploy/my-service -- getent hosts example.com && echo "lookup worked"
incident2chaos generate --report coded/r1.yaml --namespace shop --label app=my-service --host example.com --duration 120 --out r1-dns.yaml
kubectl apply -f r1-dns.yaml
kubectl -n shop wait dnschaos --all --for=condition=AllInjected --timeout=120s
kubectl -n shop exec deploy/my-service -- getent hosts example.com || echo "lookup failed"
kubectl delete -f r1-dns.yaml
kind delete cluster --name lab
```

If your R1 file does not have F9 as its primary fault, your `r1-dns.yaml` holds a different experiment. Generate this step from the published coding instead: `incident2chaos generate --corpus-id P42 --namespace shop --label app=my-service --host example.com --duration 120 --out r1-dns.yaml`.

**Question 4.1.** Paste the two lookup results. What did the experiment change inside the pod, and what did it leave alone?

**Question 4.2.** In the real incident the resolver returned records in a new order and some clients failed to resolve names. The experiment makes every lookup of one name fail. Is that a fair test of the defense that would have mattered, and what experiment would come closer?

## Part 5. Wrap up

**Question 5.1.** In one paragraph: would you trust the study's figure of 56.6 percent? Name two threats to its validity, using what you saw today (who wrote the reports, how they were coded, which tool versions the mapping was read from).

## Sources

The codebook, the corpus and the tool: incident2chaos release 0.1.0, https://github.com/yogeshramaswamy608/incident2chaos (code Apache 2.0, data and codebook CC BY 4.0). Dataset: https://doi.org/10.5281/zenodo.23973151. Software: https://doi.org/10.5281/zenodo.23973729.

The study: Ramaswamy Y (2026) Do Chaos Experiments Match Real Cloud Incidents? Mapping 497 Public Postmortems to Fault-Injection Coverage. Manuscript under review.

How the corpus was coded: the author checked the labels of a 50-report pilot and coded a sample of 45 reports blind; a large language model proposed the labels of the other 447 reports under the frozen codebook, and those labels were not revised afterwards (the corpus file's column `coded_by` says which is which).

This lab is licensed CC BY 4.0. The timing, the setup notes and the answer key are in `INSTRUCTOR.md` beside this file; it sits in a public repository, so students can read it too.

Written under the direction of Yogesh Ramaswamy, author of incident2chaos, by a large language model from Anthropic (Claude Opus 5.5). Parts 0 to 3 were run against release 0.1.0 and checked by the script run_lab.py; the workflow lab-check runs all five parts, Part 4 included, on a GitHub runner.
