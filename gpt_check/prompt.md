You label one public post-incident report from a cloud provider, using the codebook below and nothing else.

Rules:
- Use only what the report text states. A label the report does not support is T99 or F99, never a guess.
- in_scope is "yes" when the text is a post-incident report of a technical failure at the provider; otherwise "no".
- trigger_primary is the first event or change the report names as the start of the incident. trigger_secondary is a second starting event only when the report names two; otherwise "".
- faults lists every fault class the report says a component experienced. fault_primary is the one that caused most of the customer impact, and it must also appear in faults.
- Apply the version 2 rules (V1 to V8) exactly as written.
- confidence is "high", "medium" or "low" for your primary labels.
- evidence_trigger and evidence_fault each name the report section and paraphrase it in under 25 words, never quoting.

The codebook follows.
