"""Agreement of the second model's labels with a reference label set (see gpt_check/PLAN.md).

Usage:
    python gpt_check/analyze.py SECOND_LABELS_CSV [REFERENCE_CORPUS_CSV] [REPEAT_LABELS_CSV]
REFERENCE_CORPUS_CSV defaults to dataset/corpus.csv; pass the label set that is final after the
paper 1 package ruling. Prints percent agreement and Cohen's kappa for the primary trigger, the
primary fault class and injectability, the coverage figure from each label set, and, when a
repeat file is given, run-to-run agreement.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from incident2chaos.codebook import injectability  # noqa: E402
from incident2chaos.coverage import wilson  # noqa: E402


def load(path):
    return {r["corpus_no"]: r for r in csv.DictReader(open(path, encoding="utf-8"))}


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return float("nan"), 0.0
    agree = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return ((agree - expected) / (1 - expected) if expected < 1 else 1.0), agree


def coverage(rows, sources):
    stated = a = 0
    for no, r in rows.items():
        if r.get("in_scope") != "yes":
            continue
        inj = injectability(r["fault_primary"], sources[no])
        if inj == "NS":
            continue
        stated += 1
        a += inj == "A"
    low, high = wilson(a, stated)
    return a, stated, low, high


def main(second_path, reference_path=None, repeat_path=None):
    ref = load(reference_path or REPO / "dataset" / "corpus.csv")
    sec = {k: v for k, v in load(second_path).items() if v.get("fetch_status") == "ok" and v.get("fault_primary")}
    sources = {k: v["source"] for k, v in ref.items()}
    both = [k for k in sec if k in ref and ref[k]["in_scope"] == "yes" and sec[k]["in_scope"] == "yes"]
    print(f"Reports labelled by the second model: {len(sec)}; in scope in both label sets: {len(both)}")
    measures = {
        "primary trigger": lambda r, k: r["trigger_primary"],
        "primary fault class": lambda r, k: r["fault_primary"],
        "injectability": lambda r, k: injectability(r["fault_primary"], sources[k]),
    }
    for name, get in measures.items():
        k_value, agree = kappa([(get(ref[k], k), get(sec[k], k)) for k in both])
        print(f"{name:<22} agreement {100 * agree:5.1f}%  kappa {k_value:.2f}  (n={len(both)})")
    for label, rows in (("released", {k: ref[k] for k in sec if k in ref}), ("second model", sec)):
        a, stated, low, high = coverage(rows, sources)
        share = 100 * a / stated if stated else 0.0
        print(f"coverage, {label:<13} {a}/{stated} = {share:.1f}% (95% Wilson {100 * low:.1f}-{100 * high:.1f})")
    if repeat_path:
        rep = {k: v for k, v in load(repeat_path).items() if v.get("fetch_status") == "ok" and v.get("fault_primary")}
        twice = [k for k in rep if k in sec]
        for name in ("trigger_primary", "fault_primary"):
            k_value, agree = kappa([(sec[k][name], rep[k][name]) for k in twice])
            print(f"run to run, {name:<16} agreement {100 * agree:5.1f}%  kappa {k_value:.2f}  (n={len(twice)})")


if __name__ == "__main__":
    main(*sys.argv[1:])
