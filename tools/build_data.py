"""Build the released data files from the author's working files.

Usage:
    python tools/build_data.py CODED_CSV INDEX_CSV CODEBOOK_MD BLIND_HUMAN_CSV MANUSCRIPT_DOCX OUT_DIR

Inputs are the author's working files for paper 1 (not in this repository).
Outputs, written to OUT_DIR:
    corpus.csv          one row per report: link, metadata, labels, paraphrased evidence
    blind_sample.csv    the 45-report blind agreement sample, both codings
    fault_classes.json  the 20 fault classes and their injectability, parsed from the codebook
    triggers.json       the 13 trigger codes, parsed from the codebook
No report text is copied; titles, dates and links come from the providers' index pages.
"""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path


def short_names(manuscript_docx):
    """Read the short fault-class names from Table 2 of the paper 1 manuscript (pandoc plain text)."""
    text = subprocess.run(["pandoc", str(manuscript_docx), "-t", "plain", "--wrap=none"],
                          capture_output=True, text=True, check=True).stdout
    table = text.split("Table 2.")[1].split("4.3 RQ3")[0]
    names = {}
    for line in table.splitlines():
        match = re.match(r"\s+(F\d+)\s{2,}(.+?)\s{2,}\d+\s", line)
        if match:
            names[match.group(1)] = match.group(2).strip()
    return names


def build_corpus(coded_csv, index_csv, out_dir):
    """Join the coded labels to the index (retrieval time) and write corpus.csv."""
    index_rows = list(csv.DictReader(open(index_csv, encoding="utf-8")))
    by_id = {(row["source"], row["report_id"]): row for row in index_rows}
    by_url_title = {(row["url"], row["title"]): row for row in index_rows}
    coded = list(csv.DictReader(open(coded_csv, encoding="utf-8")))
    fields = [
        "corpus_no", "source", "report_id", "title", "incident_date", "url", "retrieved_utc",
        "in_scope", "trigger_primary", "trigger_secondary", "faults", "fault_primary",
        "injectability_primary", "confidence", "evidence_trigger", "evidence_fault",
        "codebook_gap", "coded_by",
    ]
    out = []
    for row in coded:
        # Pilot rows carry no report_id in the working file; they are joined by link and title.
        ix = by_id.get((row["source"], row["report_id"])) or by_url_title[(row["url"], row["title"])]
        assert ix["source"] == row["source"] and ix["title"] == row["title"], row["corpus_no"]
        out_of_scope = row["trigger_primary"] == "OUT_OF_SCOPE"
        out.append({
            "corpus_no": row["corpus_no"],
            "source": row["source"],
            "report_id": row["report_id"] or ix["report_id"],
            "title": row["title"],
            "incident_date": row["incident_date"],
            "url": row["url"],
            "retrieved_utc": ix["retrieved_utc"],
            "in_scope": "no" if out_of_scope else "yes",
            "trigger_primary": "" if out_of_scope else row["trigger_primary"],
            "trigger_secondary": row["trigger_secondary"],
            "faults": row["faults"],
            "fault_primary": row["fault_primary"],
            "injectability_primary": row["injectability_primary"],
            "confidence": row["confidence"],
            "evidence_trigger": row["evidence_trigger"],
            "evidence_fault": row["evidence_fault"],
            "codebook_gap": row["codebook_gap"],
            "coded_by": row["coded_by"].replace("checked by Yogesh", "checked by the author"),
        })
    assert len(out) == len(index_rows) == len({(r["source"], r["report_id"]) for r in out})
    with open(Path(out_dir) / "corpus.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)
    return out


def build_blind(corpus, human_csv, out_dir):
    """Write the blind agreement sample with the first-pass and the author's codes."""
    by_no = {row["corpus_no"]: row for row in corpus}
    rows = []
    for human in csv.DictReader(open(human_csv, encoding="utf-8")):
        first = by_no[human["corpus_no"]]
        assert first["report_id"] == human["report_id"], human["corpus_no"]
        rows.append({
            "corpus_no": human["corpus_no"],
            "source": first["source"],
            "report_id": first["report_id"],
            "url": first["url"],
            "first_pass_in_scope": first["in_scope"],
            "first_pass_trigger": first["trigger_primary"],
            "first_pass_fault": first["fault_primary"],
            "author_trigger": human["his_trigger"],
            "author_fault": human["his_fault"],
        })
    with open(Path(out_dir) / "blind_sample.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def parse_codebook(codebook_md, names, out_dir):
    """Parse sections 2 and 3 of the codebook into triggers.json and fault_classes.json."""
    text = open(codebook_md, encoding="utf-8").read()
    sec2 = text.split("2. Trigger codes (T)")[1].split("3. Fault classes")[0]
    sec3 = text.split("3. Fault classes (F)")[1].split("4. What the pilot measures")[0]
    triggers = []
    for line in sec2.strip().splitlines():
        match = re.match(r"(T\d+) ([^:.]+)(?::|\.)\s*(.*)", line.strip())
        if match:
            triggers.append({"code": match.group(1), "name": match.group(2).strip(),
                             "definition": match.group(3).strip()})
    faults = []
    for line in sec3.strip().splitlines():
        match = re.match(r"(F\d+) (.+?)\. (A|P|N|A on AWS only|A in Chaos Mesh only)[\s(.]", line.strip() + " ")
        if not match:
            continue
        code, name, label = match.groups()
        if code == "F3":
            inj = {"AWS PES": "A", "default": "P"}
        else:
            inj = {"default": label[0]}
        faults.append({"code": code, "name": names[code], "injectability": inj,
                       "codebook_line": line.strip()})
    assert [t["code"] for t in triggers] == [f"T{i}" for i in range(1, 14)] + ["T99"], triggers
    assert [f["code"] for f in faults] == [f"F{i}" for i in range(1, 21)], [f["code"] for f in faults]
    json.dump(triggers, open(Path(out_dir) / "triggers.json", "w", encoding="utf-8"), indent=1)
    json.dump(faults, open(Path(out_dir) / "fault_classes.json", "w", encoding="utf-8"), indent=1)
    return triggers, faults


def main(argv):
    coded_csv, index_csv, codebook_md, human_csv, manuscript_docx, out_dir = argv[1:7]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    corpus = build_corpus(coded_csv, index_csv, out_dir)
    blind = build_blind(corpus, human_csv, out_dir)
    triggers, faults = parse_codebook(codebook_md, short_names(manuscript_docx), out_dir)
    print(f"corpus {len(corpus)}, blind {len(blind)}, triggers {len(triggers)}, faults {len(faults)}")


if __name__ == "__main__":
    main(sys.argv)
