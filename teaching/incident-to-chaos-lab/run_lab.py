"""Runs every command of the lab handout (README.md) as a student would, and checks the results.

Usage: python3 run_lab.py [--parts 0,1,2,3] [--keep DIR]
Part 4 needs Docker, kind, kubectl and Helm; the workflow lab-check runs it on a GitHub runner.
Between Part 1 and Part 2 the script writes the published coding of the three reports into coded/,
the files a student writes by hand. Exits 1 if a command fails or an expected result is missing.
"""

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

# The published coding of the three reports: rows P42, P39 and P41 of the corpus (pilot rows, checked by the author).
KEY = {
    "r1": ("What came first, the CNAME or the A record?",
           "https://blog.cloudflare.com/cname-a-record-order-dns-standards/", "T1", "F9"),
    "r2": ("Cloudflare service outage June 12, 2025",
           "https://blog.cloudflare.com/cloudflare-service-outage-june-12-2025/", "T10", "F16"),
    "r3": ("A deep dive into Cloudflare's September 12, 2025 dashboard and API outage",
           "https://blog.cloudflare.com/deep-dive-into-cloudflares-sept-12-dashboard-and-api-outage/", "T1", "F20"),
}

# Text each part must print, in the answer key of INSTRUCTOR.md.
EXPECT = {
    0: ["incident2chaos 0.1.2", "F4   N", "F20  P"],
    1: ["# trigger: T1\n\n# F9 DNS resolution failure: injectability A (direct)",
        "# trigger: T10\n\n# F16 Internal dependency unavailable: injectability A (direct)",
        "# trigger: T1\n\n# F20 Overload or retry storm: injectability P (approximation only)"],
    2: ["wrote 1 manifest(s) to r1-chaos-mesh.yaml", "wrote 1 manifest(s) to r2-chaos-mesh.yaml",
        "wrote 0 manifest(s) to r3-chaos-mesh.yaml", "wrote 3 manifest(s) to r3-litmus.yaml"],
    3: ["All                                497      491   274   208   2   7  56.6% (52.2-61.0)",
        "T11                                 13       13     1    12   0   0  7.7% (1.4-33.3)",
        "T5                                  37       37     9    28   0   0  24.3% (13.4-40.1)",
        "2 of 3 coded reports have a directly injectable primary fault (66.7%)"],
    4: ["lookup worked", "lookup failed"],
}

# Files Part 2 writes, with text each must hold.
FILES = {
    2: {"r1-chaos-mesh.yaml": ["kind: DNSChaos", "- '*'"],
        "r2-chaos-mesh.yaml": ["kind: NetworkChaos", "action: partition", "app: orders-db"],
        "r3-chaos-mesh.yaml": ["The chaos-mesh catalog has no fault for this class; try --tool litmus."],
        "r3-litmus.yaml": ["k6-loadgen", "pod-http-status-code", "incident2chaos.io/report: https://blog.cloudflare.com/deep-dive"]},
}


def blocks(readme):
    """The bash blocks of each part, in order: each follows a line <!-- part: N -->."""
    out = {}
    for part, body in re.findall(r"<!-- part: (\d+) -->\n```bash\n(.*?)```", readme, re.S):
        out.setdefault(int(part), []).append(body)
    return out


def write_key(work):
    (work / "coded").mkdir(exist_ok=True)
    for name, (title, url, trigger, fault) in KEY.items():
        (work / "coded" / f"{name}.yaml").write_text(
            f"id: {name}\ntitle: \"{title}\"\nurl: {url}\nsource: Cloudflare blog post-mortem\n"
            f"trigger: {trigger}\nfaults: [{fault}]\nprimary_fault: {fault}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="0,1,2,3")
    ap.add_argument("--keep", help="run in this folder and keep it")
    args = ap.parse_args()
    parts = [int(p) for p in args.parts.split(",")]
    code = blocks((HERE / "README.md").read_text(encoding="utf-8"))
    work = pathlib.Path(args.keep or tempfile.mkdtemp(prefix="lab-"))
    work.mkdir(parents=True, exist_ok=True)
    failures = 0
    for part in parts:
        if part == 2:
            write_key(work)
        # One shell per part, so the virtual environment of Part 0 stays active; set -e stops at the first failing command.
        script = "set -e\n" + ("" if part == 0 else ". lab/bin/activate\n") + "\n".join(code[part])
        run = subprocess.run(["bash", "-c", script], cwd=work, capture_output=True, text=True)
        text = run.stdout + run.stderr
        ok = run.returncode == 0
        missing = [e for e in EXPECT.get(part, []) if e not in text]
        for name, needles in FILES.get(part, {}).items():
            body = (work / name).read_text(encoding="utf-8") if (work / name).exists() else ""
            missing += [f"{name}: {n}" for n in needles if n not in body]
        if part == 4 and ok and text.find("lookup worked") > text.find("lookup failed"):
            missing.append("lookup failed came before lookup worked")
        status = "PASS" if ok and not missing else "FAIL"
        failures += status == "FAIL"
        print(f"part {part}: {status}" + ("" if ok else f" (exit {run.returncode})"))
        for m in missing:
            print(f"  missing: {m!r}")
        if status == "FAIL":
            print(text[-3000:])
    print(f"work folder: {work}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
