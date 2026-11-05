"""Coverage of a team's own coded postmortems, and an SVG badge for a README."""

import glob
import os

from .codebook import injectability
from .coverage import wilson
from .generate import load_report


def reports_coverage(folder):
    """Share of a folder's coded reports (YAML or JSON) whose primary fault a chaos tool injects directly."""
    paths = sorted(p for ext in ("*.yaml", "*.yml", "*.json")
                   for p in glob.glob(os.path.join(folder, "**", ext), recursive=True))
    counts = {"A": 0, "P": 0, "N": 0, "NS": 0}
    for path in paths:
        report = load_report(path)
        counts[injectability(report.primary_fault or "F99", report.source)] += 1
    stated = counts["A"] + counts["P"] + counts["N"]
    low, high = wilson(counts["A"], stated)
    return {"reports": len(paths), "stated": stated, **counts,
            "A_share": counts["A"] / stated if stated else 0.0, "A_low": low, "A_high": high}


def badge_svg(share, label="chaos coverage"):
    """A flat badge: the label on grey, the directly injectable share on a colour by band."""
    value = f"{round(100 * share)}%"
    colour = "#1F7A3D" if share >= 0.75 else "#B7791F" if share >= 0.5 else "#B42318"
    left, right = 6 * len(label) + 12, 6 * len(value) + 12
    width = left + right
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" '
            f'aria-label="{label}: {value}"><title>{label}: {value}</title>'
            f'<rect width="{left}" height="20" fill="#555"/>'
            f'<rect x="{left}" width="{right}" height="20" fill="{colour}"/>'
            f'<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11">'
            f'<text x="{left / 2}" y="14">{label}</text><text x="{left + right / 2}" y="14">{value}</text></g></svg>')
