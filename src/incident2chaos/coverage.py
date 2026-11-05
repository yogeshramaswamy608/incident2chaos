"""Coverage: the share of real incidents whose primary failure a chaos tool can inject.

This is the measurement of paper 1, rerun from the coded corpus. Each report's
injectability is derived here from its primary fault class and its provider,
and checked against the value stored in the corpus.
"""

import math
from collections import Counter, defaultdict

from .codebook import injectability
from .generate import corpus_rows


def wilson(successes, total, z=1.959963984540054):
    """Wilson score interval for a proportion, as fractions (low, high)."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (centre - half, centre + half)


def _group_key(row, by):
    if by == "source":
        return row["source"]
    if by == "year":
        return row["incident_date"][:4]
    if by == "trigger":
        return row["trigger_primary"]
    return "All"


def measure(rows=None, by=None):
    """Return coverage figures overall and, optionally, by source, year or trigger."""
    rows = corpus_rows() if rows is None else rows
    mismatches = []
    groups = defaultdict(Counter)
    for row in rows:
        key = _group_key(row, by)
        groups[key]["reports"] += 1
        if row["in_scope"] != "yes":
            continue
        groups[key]["in_scope"] += 1
        derived = injectability(row["fault_primary"], row["source"])
        if derived != row["injectability_primary"]:
            mismatches.append(row["corpus_no"])
        groups[key][derived] += 1
        if derived != "NS":
            listed = [row["fault_primary"]] + [f for f in row["faults"].split(";") if f and f != "F99"]
            if any(injectability(f, row["source"]) == "A" for f in listed):
                groups[key]["any_A"] += 1
    result = []
    for key in sorted(groups, key=lambda k: (k == "All", k)):
        c = groups[key]
        stated = c["A"] + c["P"] + c["N"]
        low, high = wilson(c["A"], stated)
        result.append({
            "group": key, "reports": c["reports"], "in_scope": c["in_scope"], "stated": stated,
            "A": c["A"], "P": c["P"], "N": c["N"], "not_stated": c["NS"], "any_fault_A": c["any_A"],
            "A_share": c["A"] / stated if stated else 0.0, "A_low": low, "A_high": high,
        })
    return result, mismatches


def format_table(result):
    """Plain-text table of coverage figures."""
    header = (f"{'group':<30} {'reports':>7} {'in scope':>8} {'A':>5} {'P':>5} {'N':>3} {'NS':>3}  "
              f"{'A share (95% Wilson)':<24} {'any fault A':>11}")
    lines = [header, "-" * len(header)]
    for r in result:
        share = f"{100 * r['A_share']:.1f}% ({100 * r['A_low']:.1f}-{100 * r['A_high']:.1f})"
        lines.append(f"{r['group']:<30} {r['reports']:>7} {r['in_scope']:>8} {r['A']:>5} {r['P']:>5} "
                     f"{r['N']:>3} {r['not_stated']:>3}  {share:<24} {r['any_fault_A']:>11}")
    lines.append("")
    lines.append("A: directly injectable by Chaos Mesh or LitmusChaos. P: approximation only. N: not injectable. "
                 "NS: primary fault not stated. Shares use the in-scope reports with a stated primary fault.")
    return "\n".join(lines)
