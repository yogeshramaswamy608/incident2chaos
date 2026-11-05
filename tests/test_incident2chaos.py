import csv
import json
import re
from collections import Counter
from importlib import resources
from pathlib import Path

import jsonschema
import pytest
import yaml

from incident2chaos import cli
from incident2chaos.codebook import fault_classes, injectability, triggers
from incident2chaos.coverage import measure, wilson
from incident2chaos.generate import Report, corpus_rows, experiments, load_report, render, report_from_corpus
from incident2chaos.recipes import Target, chaos_mesh, litmus

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "tests" / "schemas"
FAULTS = [f"F{i}" for i in range(1, 21)]
FULL_TARGET = Target(namespace="shop", label="app=checkout", dependency_label="app=orders-db", node="node-1",
                     zone="us-east-1a", host="db.example.com", port=8080, url="http://checkout.shop/")


# The codebook

def test_codebook_has_20_fault_classes_and_14_trigger_codes():
    assert list(fault_classes()) == FAULTS
    assert list(triggers()) == [f"T{i}" for i in range(1, 14)] + ["T99"]


def test_injectability_matches_each_codebook_line():
    for code, item in fault_classes().items():
        label = re.match(r"F\d+ .+?\. (A|P|N)", item["codebook_line"]).group(1)
        assert injectability(code) == ("P" if code == "F3" else label), code
    assert injectability("F3", "AWS PES") == "A"
    assert injectability("F3", "Google Cloud incident report") == "P"
    assert injectability("F99") == "NS"


# The corpus and the paper's figures

def test_corpus_rows_are_unique_and_carry_no_report_text():
    rows = corpus_rows()
    assert len(rows) == 497
    assert len({(r["source"], r["report_id"]) for r in rows}) == 497
    for row in rows:
        assert row["url"].startswith("https://")
        for column in ("evidence_trigger", "evidence_fault"):
            assert len(row[column].split()) < 25, (row["corpus_no"], column)
            assert '"' not in row[column] and "“" not in row[column]
        if row["in_scope"] == "no":
            assert row["fault_primary"] == "" and row["trigger_primary"] == ""


def test_coverage_reproduces_paper_1_headline():
    result, mismatches = measure()
    assert mismatches == []
    (overall,) = result
    assert (overall["reports"], overall["in_scope"], overall["stated"]) == (497, 491, 484)
    assert (overall["A"], overall["P"], overall["N"], overall["not_stated"]) == (274, 208, 2, 7)
    assert round(100 * overall["A_share"], 1) == 56.6
    assert (round(100 * overall["A_low"], 1), round(100 * overall["A_high"], 1)) == (52.2, 61.0)
    assert overall["any_fault_A"] == 425


def test_coverage_by_source_matches_paper_table_3():
    expected = {  # source: reports, in scope, A, P, N, not stated, A share %, low %, high %
        "AWS PES": (18, 18, 13, 5, 0, 0, 72.2, 49.1, 87.5),
        "Microsoft Azure PIR": (81, 80, 47, 32, 1, 0, 58.8, 47.8, 68.9),
        "Google Cloud incident report": (172, 172, 108, 63, 1, 0, 62.8, 55.4, 69.7),
        "Cloudflare blog post-mortem": (42, 37, 21, 16, 0, 0, 56.8, 40.9, 71.3),
        "GitHub availability report": (184, 184, 85, 92, 0, 7, 48.0, 40.8, 55.3),
    }
    result, _ = measure(by="source")
    got = {r["group"]: (r["reports"], r["in_scope"], r["A"], r["P"], r["N"], r["not_stated"],
                        round(100 * r["A_share"], 1), round(100 * r["A_low"], 1), round(100 * r["A_high"], 1))
           for r in result if r["group"] != "All"}
    assert got == expected


def test_coverage_by_trigger_matches_paper_table_1():
    expected = {"T99": (55, 80), "T2": (42, 85), "T3": (43, 84), "T1": (38, 68), "T5": (9, 37), "T8": (24, 32),
                "T10": (23, 26), "T6": (15, 21), "T11": (1, 13), "T7": (9, 10), "T4": (3, 9), "T9": (7, 8),
                "T12": (2, 6), "T13": (3, 5)}
    result, _ = measure(by="trigger")
    got = {r["group"]: (r["A"], r["stated"]) for r in result if r["group"] not in ("All", "")}
    assert got == expected


def test_primary_fault_counts_match_paper_table_2():
    rows = [r for r in corpus_rows() if r["in_scope"] == "yes"]
    counts = Counter(r["fault_primary"] for r in rows)
    assert counts["F20"] == 69 and counts["F14"] == 68 and counts["F16"] == 48 and counts["F99"] == 7
    assert sum(counts.values()) == 491


def test_wilson_interval():
    low, high = wilson(274, 484)
    # Cross-check with the quadratic form of the score interval: (p - x)^2 = z^2 x (1 - x) / n.
    n, p, z = 484, 274 / 484, 1.959963984540054
    a, b, c = 1 + z * z / n, -(2 * p + z * z / n), p * p
    roots = sorted(((-b - (b * b - 4 * a * c) ** 0.5) / (2 * a), (-b + (b * b - 4 * a * c) ** 0.5) / (2 * a)))
    assert (round(low, 10), round(high, 10)) == (round(roots[0], 10), round(roots[1], 10))
    assert (round(low, 4), round(high, 4)) == (0.5216, 0.6096)
    assert wilson(0, 0) == (0.0, 0.0)


def _kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[k] * right[k] for k in left) / (n * n)
    return (observed - expected) / (1 - expected)


def test_blind_sample_reproduces_the_agreement_figures():
    text = resources.files("incident2chaos.data").joinpath("blind_sample.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    assert len(rows) == 45
    both = [r for r in rows if r["first_pass_in_scope"] == "yes"]
    assert len(both) == 44
    by_no = {r["corpus_no"]: r for r in corpus_rows()}
    trig = [(r["first_pass_trigger"], r["author_trigger"]) for r in both]
    fault = [(r["first_pass_fault"], r["author_fault"]) for r in both]
    inj = [(injectability(a, by_no[r["corpus_no"]]["source"]), injectability(b, by_no[r["corpus_no"]]["source"]))
           for r, (a, b) in zip(both, fault)]
    assert sum(a == b for a, b in trig) == 33 and round(_kappa(trig), 2) == 0.72
    assert sum(a == b for a, b in fault) == 39 and round(_kappa(fault), 3) == 0.875
    assert sum(a == b for a, b in inj) == 42 and round(_kappa(inj), 3) == 0.913


# The experiments

def _validator(schema):
    return jsonschema.Draft7Validator(schema)


def _unknown_fields(value, schema, path="", skip=("metadata",)):
    """Kubernetes drops unknown fields without an error, so check every key exists in the CRD schema."""
    found = []
    if isinstance(value, dict) and "properties" in schema:
        for key, item in value.items():
            if path == "" and key in skip:
                continue
            if key not in schema["properties"]:
                found.append(f"{path}.{key}")
            else:
                found += _unknown_fields(item, schema["properties"][key], f"{path}.{key}")
    elif isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            found += _unknown_fields(item, schema["items"], f"{path}[{i}]")
    return found


CM = json.loads((SCHEMAS / "chaos_mesh_crds.json").read_text())["schemas"]
LITMUS = json.loads((SCHEMAS / "litmus_chaosengine_crd.json").read_text())["schema"]


@pytest.mark.parametrize("fault", FAULTS)
def test_every_fault_class_except_f4_has_an_experiment(fault):
    recipes = [chaos_mesh(fault, "i2c-test", FULL_TARGET), litmus(fault, "i2c-test", FULL_TARGET)]
    if fault == "F4":
        assert recipes == [None, None]
    else:
        assert any(recipes), fault


@pytest.mark.parametrize("fault", FAULTS)
def test_chaos_mesh_manifests_validate_against_the_crds(fault):
    recipe = chaos_mesh(fault, "i2c-test", FULL_TARGET)
    if recipe is None:
        pytest.skip(f"no Chaos Mesh recipe for {fault}")
    for manifest in recipe.manifests:
        assert manifest["apiVersion"] == "chaos-mesh.org/v1alpha1"
        errors = list(_validator(CM[manifest["kind"]]).iter_errors(manifest))
        assert errors == [], [e.message for e in errors]
        assert _unknown_fields(manifest, CM[manifest["kind"]]) == []


@pytest.mark.parametrize("fault", FAULTS)
def test_litmus_manifests_validate_against_the_chaosengine_crd(fault):
    recipe = litmus(fault, "i2c-test", FULL_TARGET)
    if recipe is None:
        pytest.skip(f"no LitmusChaos recipe for {fault}")
    for manifest in recipe.manifests:
        if manifest["kind"] == "Secret":
            assert manifest["stringData"]["script.js"].startswith("import http")
            continue
        assert manifest["kind"] == "ChaosEngine"
        errors = list(_validator(LITMUS).iter_errors(manifest))
        assert errors == [], [e.message for e in errors]
        assert _unknown_fields(manifest, LITMUS) == []
        env = {e["name"]: e["value"] for e in manifest["spec"]["experiments"][0]["spec"]["components"]["env"]}
        assert env["TOTAL_CHAOS_DURATION"] == "60"
        assert all(isinstance(v, str) for v in env.values())


def test_names_are_valid_kubernetes_names():
    report = Report.from_mapping({"id": "A very long report id with Spaces and #anchors 2026-07-19T10:00Z " * 3,
                                  "title": "t", "url": "", "faults": FAULTS})
    for tool in ("chaos-mesh", "litmus"):
        for item in experiments(report, tool=tool, target=FULL_TARGET, all_faults=True):
            for manifest in item.manifests:
                name = manifest["metadata"]["name"]
                assert len(name) <= 63 and re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", name), name


def test_example_report_generates_and_parses():
    report = load_report(ROOT / "examples" / "aws-dynamodb-2025-10-19.yaml")
    assert report.primary_fault == "F9" and report.source == "AWS PES"
    items = experiments(report, tool="chaos-mesh", target=FULL_TARGET, all_faults=True)
    assert [i.fault for i in items] == ["F9", "F19", "F16", "F20", "F18"]
    assert [i.injectability for i in items] == ["A", "P", "A", "P", "P"]
    docs = [d for d in yaml.safe_load_all(render(report, items, "chaos-mesh")) if d]
    assert [d["kind"] for d in docs] == ["DNSChaos", "IOChaos", "NetworkChaos"]
    assert docs[0]["metadata"]["annotations"]["incident2chaos.io/report"] == "https://aws.amazon.com/message/101925/"


def test_report_from_corpus_and_out_of_scope():
    report = report_from_corpus("1")
    assert report.id == "101925" and report.primary_fault == "F9"
    with pytest.raises(ValueError):
        report_from_corpus("36")
    with pytest.raises(KeyError):
        report_from_corpus("no-such-report")


def test_not_injectable_and_not_stated():
    report = Report.from_mapping({"id": "x", "faults": ["F4", "F99"], "primary_fault": "F4"})
    items = experiments(report, all_faults=True)
    assert [(i.fault, i.injectability, i.manifests) for i in items] == [("F4", "N", []), ("F99", "NS", [])]


def test_bad_codes_are_rejected():
    with pytest.raises(ValueError):
        Report.from_mapping({"id": "x", "faults": ["F21"]})
    with pytest.raises(ValueError):
        Report.from_mapping({"id": "x", "faults": ["F1"], "trigger": "T14"})


# The command line

def test_cli_faults_generate_and_coverage(tmp_path, capsys):
    assert cli.main(["faults", "--triggers"]) == 0
    out = capsys.readouterr().out
    assert "F20" in out and "T99" in out and "A on AWS, P elsewhere" in out
    target = tmp_path / "exp.yaml"
    assert cli.main(["generate", "--report", str(ROOT / "examples" / "aws-dynamodb-2025-10-19.yaml"),
                     "--tool", "litmus", "--out", str(target)]) == 0
    docs = [d for d in yaml.safe_load_all(target.read_text()) if d]
    assert docs[0]["kind"] == "ChaosEngine" and docs[0]["spec"]["experiments"][0]["name"] == "pod-dns-error"
    capsys.readouterr()
    assert cli.main(["coverage", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["groups"][0]["A"] == 274 and data["stored_value_mismatches"] == []
    assert cli.main(["generate"]) == 2


def test_unknown_field_check_catches_a_typo():
    manifest = chaos_mesh("F9", "i2c-test", FULL_TARGET).manifests[0]
    manifest["spec"]["pattern"] = manifest["spec"].pop("patterns")
    assert _unknown_fields(manifest, CM["DNSChaos"]) == [".spec.pattern"]
