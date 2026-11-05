"""End-to-end run on a real cluster: apply each generated experiment and check its result.

Chaos Mesh: every experiment is applied and must reach AllInjected=True, then is deleted.
LitmusChaos: every ChaosEngine and Secret must be accepted by the API server (server-side dry run)
with the ChaosEngine resource definition installed.
Writes e2e-result.txt and exits 1 on any failure.
"""

import json
import subprocess
import sys
import time

import yaml

from incident2chaos.generate import experiments, load_report
from incident2chaos.recipes import Target

TARGET = Target(namespace="shop", label="app=my-service", dependency_label="app=orders-db", zone="us-east-1a",
                host="example.com", port=80, url="http://my-service.shop.svc.cluster.local/",
                config_path="/etc/config", data_path="/data", duration_seconds=30)
PLURAL = {"PodChaos": "podchaos", "NetworkChaos": "networkchaos", "DNSChaos": "dnschaos",
          "StressChaos": "stresschaos", "IOChaos": "iochaos", "HTTPChaos": "httpchaos", "TimeChaos": "timechaos"}


def kubectl(args, data=None):
    return subprocess.run(["kubectl", *args], input=data, capture_output=True, text=True)


def injected(kind, name):
    out = kubectl(["get", PLURAL[kind], name, "-n", "shop", "-o", "json"])
    if out.returncode != 0:
        return None, out.stderr.strip()
    conditions = json.loads(out.stdout).get("status", {}).get("conditions", [])
    state = {c["type"]: c["status"] for c in conditions}
    return state.get("AllInjected") == "True", json.dumps(state)


def main():
    report = load_report(sys.argv[1])
    lines, failed = [], 0
    for item in experiments(report, tool="chaos-mesh", target=TARGET, all_faults=True):
        for manifest in item.manifests:
            kind, name = manifest["kind"], manifest["metadata"]["name"]
            applied = kubectl(["apply", "-f", "-"], yaml.safe_dump(manifest))
            ok, detail = False, applied.stderr.strip()
            if applied.returncode == 0:
                for _ in range(24):
                    ok, detail = injected(kind, name)
                    if ok:
                        break
                    time.sleep(5)
            kubectl(["delete", PLURAL[kind], name, "-n", "shop", "--wait=true", "--timeout=120s"])
            failed += not ok
            lines.append(f"chaos-mesh {item.fault} {kind} {name}: {'INJECTED' if ok else 'FAILED ' + detail}")
            time.sleep(5)
        if not item.manifests:
            lines.append(f"chaos-mesh {item.fault}: no experiment ({item.summary})")
    for item in experiments(report, tool="litmus", target=TARGET, all_faults=True):
        for manifest in item.manifests:
            out = kubectl(["apply", "--dry-run=server", "-f", "-"], yaml.safe_dump(manifest))
            ok = out.returncode == 0
            failed += not ok
            lines.append(f"litmus {item.fault} {manifest['kind']} {manifest['metadata']['name']}: "
                         + ("ACCEPTED" if ok else "REJECTED " + out.stderr.strip()))
        if not item.manifests:
            lines.append(f"litmus {item.fault}: no experiment ({item.summary})")
    lines.append(f"failures: {failed}")
    text = "\n".join(lines)
    open("e2e-result.txt", "w").write(text + "\n")
    print(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
