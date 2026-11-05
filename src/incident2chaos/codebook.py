"""The paper 1 codebook: trigger codes, fault classes and their injectability.

The data files are parsed from codebook version 2 by tools/build_data.py.
Injectability: A = a built-in fault of Chaos Mesh or LitmusChaos injects the
failure directly; P = only an approximation exists; N = neither tool can inject it.
"""

import json
from functools import lru_cache
from importlib import resources

CODEBOOK_VERSION = "2"
CHAOS_MESH_COMMIT = "e636338c"
LITMUS_CHARTS_COMMIT = "b2662c23"

INJECTABILITY_WORDS = {"A": "direct", "P": "approximation only", "N": "not injectable"}


def _load(name):
    return json.loads(resources.files("incident2chaos.data").joinpath(name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def fault_classes():
    """Return the fault classes keyed by code, F1 to F20."""
    return {item["code"]: item for item in _load("fault_classes.json")}


@lru_cache(maxsize=None)
def triggers():
    """Return the trigger codes keyed by code, T1 to T13 and T99."""
    return {item["code"]: item for item in _load("triggers.json")}


def injectability(fault, source=None):
    """Return A, P or N for a fault class; F3 depends on the provider (A on AWS only)."""
    if fault in ("", "F99"):
        return "NS"
    rule = fault_classes()[fault]["injectability"]
    return rule.get(source or "", rule["default"])


def fault_name(fault):
    """Return the short name of a fault class, or 'Not stated' for F99."""
    if fault == "F99":
        return "Not stated"
    return fault_classes()[fault]["name"]
