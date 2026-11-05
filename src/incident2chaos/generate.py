"""Turn a coded incident report into chaos experiment files."""

import csv
import re
from dataclasses import dataclass, field
from importlib import resources

import yaml

from . import __version__
from .codebook import INJECTABILITY_WORDS, fault_name, injectability
from .recipes import Target, chaos_mesh, litmus

TOOLS = {"chaos-mesh": chaos_mesh, "litmus": litmus}
ANNOTATION = "incident2chaos.io"


@dataclass
class Report:
    """A post-incident report coded under the paper 1 codebook."""

    id: str
    title: str
    url: str
    source: str = ""
    trigger: str = "T99"
    faults: list = field(default_factory=list)
    primary_fault: str = ""

    @classmethod
    def from_mapping(cls, data):
        faults = data.get("faults") or []
        if isinstance(faults, str):
            faults = [f for f in faults.split(";") if f]
        primary = data.get("primary_fault") or (faults[0] if faults else "")
        if primary and primary not in faults:
            faults = [primary] + faults
        report = cls(id=str(data["id"]), title=data.get("title", ""), url=data.get("url", ""),
                     source=data.get("source", ""), trigger=data.get("trigger", "T99"),
                     faults=faults, primary_fault=primary)
        report.validate()
        return report

    def validate(self):
        bad = [f for f in self.faults if not re.fullmatch(r"F([1-9]|1\d|20|99)", f)]
        if bad:
            raise ValueError(f"unknown fault class {bad}; the codebook has F1 to F20 and F99")
        if not re.fullmatch(r"T([1-9]|1[0-3]|99)", self.trigger):
            raise ValueError(f"unknown trigger {self.trigger!r}; the codebook has T1 to T13 and T99")


def load_report(path):
    """Read a coded report from a YAML or JSON file."""
    with open(path, encoding="utf-8") as handle:
        return Report.from_mapping(yaml.safe_load(handle))


def corpus_rows(path=None):
    """Read the coded corpus released with paper 1 (or another file with the same columns)."""
    if path:
        handle = open(path, encoding="utf-8", newline="")
    else:
        handle = resources.files("incident2chaos.data").joinpath("corpus.csv").open(encoding="utf-8", newline="")
    with handle:
        return list(csv.DictReader(handle))


def report_from_corpus(key, path=None):
    """Find one report in the corpus by its corpus number (1 to 447, P1 to P50) or report_id."""
    for row in corpus_rows(path):
        if key in (row["corpus_no"], row["report_id"]):
            if row["in_scope"] != "yes":
                raise ValueError(f"report {key} is out of scope: it describes no failure of the provider")
            return Report.from_mapping({"id": row["report_id"] or row["corpus_no"], "title": row["title"],
                                        "url": row["url"], "source": row["source"],
                                        "trigger": row["trigger_primary"] or "T99",
                                        "faults": row["faults"], "primary_fault": row["fault_primary"]})
    raise KeyError(f"no report {key!r} in the corpus")


def _slug(text, limit=40):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].strip("-") or "report"


@dataclass
class Experiment:
    """The experiment for one fault class of a report in one tool."""

    fault: str
    injectability: str
    summary: str
    manifests: list


def experiments(report, tool="chaos-mesh", target=None, all_faults=False):
    """Return the experiments for the report's primary fault, or for every fault it lists."""
    if tool not in TOOLS:
        raise ValueError(f"tool must be one of {sorted(TOOLS)}")
    target = target or Target()
    faults = report.faults if all_faults else [report.primary_fault]
    result = []
    for fault in faults:
        if fault in ("", "F99"):
            result.append(Experiment("F99", "NS", "The report does not state this failure; nothing to inject.", []))
            continue
        inj = injectability(fault, report.source)
        name = f"i2c-{fault.lower()}-{_slug(report.id)}"[:63].strip("-")
        recipe = TOOLS[tool](fault, name, target) if inj != "N" else None
        if recipe is None:
            other = [t for t in TOOLS if t != tool and inj != "N" and TOOLS[t](fault, name, target)]
            why = ("Neither Chaos Mesh nor LitmusChaos can inject this failure."
                   if inj == "N" else f"The {tool} catalog has no fault for this class"
                   + (f"; try --tool {other[0]}." if other else "."))
            result.append(Experiment(fault, inj, why, []))
            continue
        for manifest in recipe.manifests:
            notes = manifest.setdefault("metadata", {}).setdefault("annotations", {})
            notes.update({
                f"{ANNOTATION}/report": report.url or report.id,
                f"{ANNOTATION}/fault-class": f"{fault} {fault_name(fault)}",
                f"{ANNOTATION}/injectability": f"{inj} ({INJECTABILITY_WORDS[inj]})",
                f"{ANNOTATION}/version": __version__,
            })
        result.append(Experiment(fault, inj, recipe.summary, recipe.manifests))
    return result


def render(report, items, tool):
    """Render experiments as one multi-document YAML file with a short header per experiment."""
    lines = [f"# incident2chaos {__version__}, tool: {tool}",
             f"# report: {report.title or report.id}",
             f"# link: {report.url}" if report.url else "# link: none given",
             f"# trigger: {report.trigger}"]
    for item in items:
        lines.append("")
        lines.append(f"# {item.fault} {fault_name(item.fault)}: injectability {item.injectability}"
                     + (f" ({INJECTABILITY_WORDS[item.injectability]})" if item.injectability in
                        INJECTABILITY_WORDS else " (not stated)"))
        lines.append(f"# {item.summary}")
        for manifest in item.manifests:
            lines.append("---")
            lines.append(yaml.safe_dump(manifest, sort_keys=False, width=1000).rstrip())
    return "\n".join(lines) + "\n"
