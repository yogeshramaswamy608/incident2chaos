"""Command line: incident2chaos faults | generate | coverage."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .codebook import CHAOS_MESH_COMMIT, CODEBOOK_VERSION, LITMUS_CHARTS_COMMIT, fault_classes, triggers
from .badge import badge_svg, reports_coverage
from .coverage import format_table, measure
from .generate import TOOLS, corpus_rows, experiments, load_report, render, report_from_corpus
from .recipes import Target


def cmd_faults(args):
    print(f"Codebook version {CODEBOOK_VERSION}; Chaos Mesh {CHAOS_MESH_COMMIT}; "
          f"LitmusChaos chaos-charts {LITMUS_CHARTS_COMMIT}")
    print("Injectability: A direct, P approximation only, N not injectable.\n")
    for code, item in fault_classes().items():
        rule = item["injectability"]
        inj = rule["default"] if len(rule) == 1 else "A on AWS, P elsewhere"
        print(f"{code:<4} {inj:<22} {item['name']}")
    if args.triggers:
        print()
        for code, item in triggers().items():
            print(f"{code:<4} {item['name']}")
    return 0


def _target(args):
    return Target(namespace=args.namespace, label=args.label, dependency_label=args.dependency_label or "",
                  node=args.node or "", zone=args.zone or "", host=args.host or "", port=args.port,
                  url=args.url or "", config_path=args.config_path, data_path=args.data_path,
                  duration_seconds=args.duration)


def cmd_generate(args):
    if bool(args.report) == bool(args.corpus_id):
        print("give exactly one of --report FILE or --corpus-id ID", file=sys.stderr)
        return 2
    report = load_report(args.report) if args.report else report_from_corpus(args.corpus_id, args.corpus)
    items = experiments(report, tool=args.tool, target=_target(args), all_faults=args.all_faults)
    text = render(report, items, args.tool)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        written = sum(len(i.manifests) for i in items)
        print(f"wrote {written} manifest(s) to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_coverage(args):
    rows = corpus_rows(args.corpus)
    result, mismatches = measure(rows, by=args.by)
    if args.json:
        print(json.dumps({"groups": result, "stored_value_mismatches": mismatches}, indent=1))
    else:
        print(format_table(result))
        if mismatches:
            print(f"\nWARNING: {len(mismatches)} report(s) whose stored injectability differs: {mismatches[:10]}")
    return 1 if mismatches else 0


def cmd_badge(args):
    result = reports_coverage(args.reports)
    if result["reports"] == 0:
        print(f"no coded reports (.yaml, .yml, .json) under {args.reports}", file=sys.stderr)
        return 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(badge_svg(result["A_share"]), encoding="utf-8")
    print(f"{result['A']} of {result['stated']} coded reports have a directly injectable primary fault "
          f"({100 * result['A_share']:.1f}%); badge written to {args.out}")
    if args.min_share is not None and result["A_share"] < args.min_share:
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="incident2chaos",
                                     description="Chaos experiments derived from real cloud incident reports.")
    parser.add_argument("--version", action="version", version=f"incident2chaos {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("faults", help="list the fault classes and what Chaos Mesh and LitmusChaos can inject")
    p.add_argument("--triggers", action="store_true", help="also list the trigger codes")
    p.set_defaults(func=cmd_faults)

    p = sub.add_parser("generate", help="write the chaos experiment for a coded incident report")
    p.add_argument("--report", help="a coded report, YAML or JSON (see examples/)")
    p.add_argument("--corpus-id", help="a report from the released corpus, by corpus_no or report_id")
    p.add_argument("--corpus", help="another corpus file with the same columns")
    p.add_argument("--tool", choices=sorted(TOOLS), default="chaos-mesh")
    p.add_argument("--all-faults", action="store_true", help="one experiment per listed fault, not only the primary")
    p.add_argument("--namespace", default="default")
    p.add_argument("--label", default="app=my-service", help="target pods, key=value")
    p.add_argument("--dependency-label", help="the dependency's pods, key=value (F7, F16, F20)")
    p.add_argument("--node", help="node to drain (LitmusChaos F2)")
    p.add_argument("--zone", help="zone whose pods fail (F3), default us-east-1a")
    p.add_argument("--host", help="hostname whose DNS lookups fail (F9); default all")
    p.add_argument("--port", type=int, default=80, help="HTTP port of the service (F14, F16, F20)")
    p.add_argument("--url", help="URL the load generator calls (F18, F20)")
    p.add_argument("--config-path", default="/etc/config", help="mounted configuration path (F15)")
    p.add_argument("--data-path", default="/data", help="mounted data volume (F12, F19)")
    p.add_argument("--duration", type=int, default=60, help="seconds")
    p.add_argument("--out", help="write to this file instead of standard output")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("coverage", help="rerun the study's coverage measurement on the corpus")
    p.add_argument("--corpus", help="another corpus file with the same columns")
    p.add_argument("--by", choices=["source", "year", "trigger"])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_coverage)

    p = sub.add_parser("badge", help="coverage of your own coded postmortems, written as an SVG badge")
    p.add_argument("--reports", required=True, help="folder of coded reports, YAML or JSON")
    p.add_argument("--out", default="chaos-coverage.svg", help="where to write the badge")
    p.add_argument("--min-share", type=float, help="fail when the directly injectable share is below this (0 to 1)")
    p.set_defaults(func=cmd_badge)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, KeyError) as error:
        print(f"incident2chaos: {error}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        sys.stderr.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
