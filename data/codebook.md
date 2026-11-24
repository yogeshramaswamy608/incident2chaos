Codebook, version 3, Tue Nov 24, 2026, for the study “Which Real Cloud Failures Can Chaos Tools Inject? A Mapping Study of 437 Public Post-Incident Reports and Two Fault Catalogs”. Replaces version 2 of Wed Nov 4, 2026, whose labels it keeps.
Status: frozen for dataset 2.0.0. Version 3 changes only the injectability of four fault classes in section 3 (F3, F8, F16, F19), from the author's check of the 20 mapping lines against the two catalogs; no trigger or fault label changed. Logged in section 7.

1. Unit and rules
One row per public post-incident report from a cloud provider's own site (first-party). The report's link and its labels are kept; none of its text is redistributed.
Code only what the report states. A label the report does not support is T99 or F99, never a guess.
Trigger: the first event or change the report names as the start of the incident. One primary trigger; one secondary trigger only when the report names two starting events.
Fault classes: every technical failure the report says a component experienced, as a chaos tool would have to inject it. Multi-label; one marked primary (the failure that caused most of the customer impact).
Evidence: for each label, the report section and a paraphrase of under 25 words, never a quotation.

2. Trigger codes (T)
T1 Code or binary change: a software deployment, rollout or release.
T2 Configuration change: a change to configuration data, a feature flag, a policy or a rule, by a person or a pipeline.
T3 Planned operation: maintenance, migration, capacity addition or removal, decommissioning, scaling work done on purpose.
T4 Automation acting wrongly: an automated system (scaler, remediation, DNS or routing automation) took an action nobody intended.
T5 Demand surge: organic traffic growth, a spike, or a retry storm that starts the incident.
T6 Latent defect activated: a bug present for some time that fires on a date, time, data size, limit or rare condition.
T7 Hardware failure: server, disk, switch, router or other device failure.
T8 Facility event: power loss, cooling or thermal event, fire, flood, weather.
T9 External network event: fiber cut, route leak or outage at a carrier or internet exchange outside the provider.
T10 Upstream dependency failure outside the provider: a third party the provider relies on.
T11 Expiry or exhaustion: a certificate, credential or key expired, or a fixed resource ran out (address space, disk, quota) without a demand surge.
T12 Attack: a denial-of-service attack or other malicious action.
T13 Operator error: a person ran the wrong command, on the wrong target, or with wrong input, outside a planned change.
T99 Not stated.

3. Fault classes (F) and what Chaos Mesh and LitmusChaos can inject
Injectability: A = a built-in fault of either tool injects it directly; P = only an approximation; N = neither tool can inject it.
Catalogs read Tue Nov 3, 2026 from source: Chaos Mesh commit e636338c (Nov 3, 2026), api/v1alpha1; LitmusChaos chaos-charts commit b2662c23 (Apr 16, 2026), faults/ (53 fault folders).

F1 Process or pod crash. A. Chaos Mesh PodChaos pod-kill, container-kill; Litmus pod-delete, container-kill, spring-boot-app-kill.
F2 Node, VM or instance loss. A. Chaos Mesh AWSChaos ec2-stop and ec2-restart, GCPChaos node-stop and node-reset, AzureChaos vm-stop and vm-restart, PodChaos pod-failure; Litmus node-drain, node-restart, node-poweroff, kubelet-service-kill, docker-service-kill, ec2-stop-by-id, gcp-vm-instance-stop, azure-instance-stop, vm-poweroff.
F3 Zone or data-center loss, only when the report says a whole zone or data center was lost; part of a facility is F2. P. Closest: several node stops at once, or Litmus aws-az-chaos, which removes a zone from a load balancer while the services in that zone keep running.
F4 Region-wide or provider control-plane loss. N.
F5 Network latency. A. Chaos Mesh NetworkChaos delay, HTTPChaos delay, BlockChaos delay; Litmus pod-network-latency, pod-http-latency.
F6 Packet loss, corruption or duplication. A. Chaos Mesh NetworkChaos loss, corrupt, duplicate; Litmus pod-network-loss, pod-network-corruption, pod-network-duplication.
F7 Network partition or link loss between components. A. Chaos Mesh NetworkChaos partition; Litmus pod-network-partition, pod-http-reset-peer.
F8 Network capacity saturation. P. Closest: Chaos Mesh NetworkChaos bandwidth, Litmus pod-network-rate-limit; a bandwidth cap lowers a link's capacity, and the link saturates only when enough traffic reaches it.
F9 DNS resolution failure. A. Chaos Mesh DNSChaos error, random; Litmus pod-dns-error, pod-dns-spoof.
F10 CPU exhaustion. A. Chaos Mesh StressChaos cpu; Litmus pod-cpu-hog, node-cpu-hog.
F11 Memory exhaustion or leak. A. Chaos Mesh StressChaos memory; Litmus pod-memory-hog, node-memory-hog.
F12 Storage fault: disk full, I/O errors or latency, volume loss. A. Chaos Mesh IOChaos latency and fault, AWSChaos detach-volume, GCPChaos disk-loss, AzureChaos disk-detach; Litmus disk-fill, pod-io-stress, node-io-stress, ebs-loss-by-id, gcp-vm-disk-loss, azure-disk-loss.
F13 Clock or time fault. A in Chaos Mesh only (TimeChaos); none in the Litmus catalog.
F14 Error responses or exceptions from a service. A. Chaos Mesh HTTPChaos abort, replace, patch, JVMChaos exception; Litmus pod-http-status-code, pod-http-modify-body, spring-boot-exceptions.
F15 Bad configuration state spread to running systems. P. Closest: Chaos Mesh IOChaos mistake or attrOverride on a config file, HTTPChaos replace on a config service's answer.
F16 A dependency inside the provider becomes unavailable, as the report states. A third party's outage is the trigger T10; the provider's own service that failed with it is F16. P. Closest: partition or abort one caller's calls to it (F7 or F14 faults aimed at the dependency); the dependency still serves other callers.
F17 Credential, certificate or authentication failure. P. Closest: Chaos Mesh TimeChaos moved past the expiry date.
F18 Software resource limit hit: connection pool, thread pool, file handles, quota or rate limit inside a service. P. Closest: Litmus k6-loadgen load against the limit.
F19 Data corruption or inconsistent state. A. Chaos Mesh IOChaos mistake, which can change bytes during a file write and so corrupt the stored data directly.
F20 Overload or retry storm: queues back up or clients retry, from demand or from a failure, whether or not the system recovered alone. P. Closest: Litmus k6-loadgen with a dependency fault (F14 or F16).
F99 Not stated.

4. What the pilot measures
For each report: the primary trigger, every fault class with its injectability, and the best injectability among them (the report is covered if its primary fault class is A).
The study's headline figure is the share of reports whose primary fault class is A, with a 95 percent confidence interval, overall, by provider and by trigger. Its second figure is the share of triggers no tool can start, since chaos tools inject faults, not triggers.

5. How a label is checked
The pilot: the author reads each of the 50 reports and marks each proposed label AGREE or CHANGE with the right code. Each CHANGE is one line in the change log at the end of this file, with the rule it adds.
The full corpus: every other report was coded with version 2; the author coded a random sample of 45 reports blind to those labels, and Cohen's kappa between the two codings is the agreement figure the study reports (blind_sample.csv).

6. Rules added in version 2 (from the author's pilot check, Tue Nov 3, 2026; pilot rows in brackets)
V1 A named change or planned operation is the primary trigger over a latent defect it exposed; T6 is primary only when no change is named (8, 14).
V2 A planned operation that started the chain is the trigger, not the automation that acted in it (26); maintenance that is only context is not the trigger (12).
V3 When the report does not state the kind of change, or that a party was outside the provider, the trigger is T99 (9, 46).
V4 A mistake made during planned work is T3, with T13 as the secondary trigger; T13 alone is an error outside any planned work (2, 34).
V5 Code only the failure the report states: errors returned with no stated cause are F14; F5 needs stated latency, F17 a stated credential or authentication failure, F16 a stated unavailable dependency, F19 stated corrupt or invalid data; schema errors are F14 (27, 29, 32, 47).
V6 F3 needs a whole zone or data center lost; part of a facility is F2 (18).
V7 F16 covers the provider's own dependency; a third party's outage is the trigger (39).
V8 F20 covers any overload from demand or retries (3, 48).
Not adopted: a new fault class for software logic defects and one for network device failure; the pilot coded them as F14, F6 or F7 without loss (11, 47).

7. Change log
Wed Nov 4, 2026: the author's blind coding of 45 reports (blind_sample.csv) agreed with the first pass on injectability 42 of 44 (kappa 0.913), primary fault 39 of 44 (kappa 0.87) and trigger 33 of 44 (kappa 0.72); no rule added; version 2 stays frozen.
Mon Nov 16, 2026, erratum: section 3 counted 60 fault folders; the seven group folders under faults/ at that commit hold 60 folders, 7 of them icon folders, so the count is 53. Section 1 called the labels ours and said the evidence paraphrase was in our own words; a language model proposed the labels, which the author checked for the 50 pilot reports, and wrote the paraphrases of the 447 first-pass rows, so section 1 now says its labels and a paraphrase, never a quotation. The line above, as first released, printed the primary fault kappa to three decimals as 0.875; the value is 307/351 = 0.8746, now printed to two decimals as 0.87. No code or label changed, and no rule changed in what it requires; version 2 stays frozen.
Tue Nov 24, 2026, version 3: the author checked each of the 20 mapping lines against his own reading of the Chaos Mesh and LitmusChaos catalogs at the commits in section 3 and changed four. F3 A on AWS to P: Litmus aws-az-chaos removes a zone from a load balancer, but the services in the zone keep running. F8 A to P: a bandwidth cap lowers a link's capacity, but the link saturates only when enough traffic reaches it. F16 A to P: blocking one caller's requests makes the dependency look unavailable while it still serves other callers. F19 P to A: Chaos Mesh IOChaos mistake can change bytes during a file write and so corrupt the stored data directly. The other 16 lines stand. On the 429 reports with a stated primary fault, 73 injectability values follow (F16 45, F8 12, F19 16; no AWS report remains for F3), and the share directly covered moves from 240 (55.9 percent) to 199 (46.4 percent, 95 percent interval 41.7 to 51.1). No trigger or fault label changed.
