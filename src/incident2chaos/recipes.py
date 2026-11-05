"""Experiment recipes: one Chaos Mesh and one LitmusChaos experiment per fault class.

Chaos Mesh manifests use the field names of api/v1alpha1 at commit e636338c.
LitmusChaos manifests start from the upstream engine.yaml of each fault in
litmuschaos/chaos-charts at commit b2662c23 (Apache 2.0, see NOTICE), with the
target and the fault values filled in.
"""

import copy
from dataclasses import dataclass, field
from importlib import resources

import yaml

CHAOS_MESH_API = "chaos-mesh.org/v1alpha1"


@dataclass
class Target:
    """Where an experiment runs and what it hits."""

    namespace: str = "default"
    label: str = "app=my-service"
    dependency_label: str = ""
    node: str = ""
    zone: str = ""
    host: str = ""
    port: int = 80
    url: str = ""
    config_path: str = "/etc/config"
    data_path: str = "/data"
    duration_seconds: int = 60

    def label_pair(self, which="target"):
        """Split 'key=value' into a one-entry dict."""
        text = self.dependency_label if which == "dependency" and self.dependency_label else self.label
        key, _, value = text.partition("=")
        if not key or not value:
            raise ValueError(f"label must be key=value, got {text!r}")
        return {key: value}


@dataclass
class Recipe:
    """One experiment for one fault class in one tool."""

    fault: str
    tool: str
    summary: str
    manifests: list = field(default_factory=list)


def _pod_selector(target, which="target", mode="one", node_selectors=None):
    selector = {"namespaces": [target.namespace], "labelSelectors": target.label_pair(which)}
    if node_selectors:
        selector["nodeSelectors"] = node_selectors
    return {"selector": selector, "mode": mode}


def _cm(kind, name, target, spec):
    return {"apiVersion": CHAOS_MESH_API, "kind": kind,
            "metadata": {"name": name, "namespace": target.namespace}, "spec": spec}


def _duration(target):
    return f"{target.duration_seconds}s"


def chaos_mesh(fault, name, target):
    """Return the Chaos Mesh recipe for a fault class, or None when the tool has none."""
    d = _duration(target)
    pod = _pod_selector(target)
    if fault == "F1":
        return Recipe(fault, "chaos-mesh", "PodChaos pod-kill on one target pod",
                      [_cm("PodChaos", name, target, {**pod, "action": "pod-kill"})])
    if fault == "F2":
        return Recipe(fault, "chaos-mesh", "PodChaos pod-failure on every target pod, standing in for the lost node; "
                      "for a cloud VM use AWSChaos ec2-stop, GCPChaos node-stop or AzureChaos vm-stop",
                      [_cm("PodChaos", name, target, {**_pod_selector(target, mode="all"),
                                                      "action": "pod-failure", "duration": d})])
    if fault == "F3":
        zone = target.zone or "us-east-1a"
        return Recipe(fault, "chaos-mesh", f"PodChaos pod-failure on every target pod in zone {zone}",
                      [_cm("PodChaos", name, target, {**_pod_selector(
                          target, mode="all", node_selectors={"topology.kubernetes.io/zone": zone}),
                          "action": "pod-failure", "duration": d})])
    if fault == "F5":
        return Recipe(fault, "chaos-mesh", "NetworkChaos delay of 200 ms",
                      [_cm("NetworkChaos", name, target, {**pod, "action": "delay", "duration": d,
                                                          "delay": {"latency": "200ms", "jitter": "50ms",
                                                                    "correlation": "0"}})])
    if fault == "F6":
        return Recipe(fault, "chaos-mesh", "NetworkChaos loss of 25 percent of packets",
                      [_cm("NetworkChaos", name, target, {**pod, "action": "loss", "duration": d,
                                                          "loss": {"loss": "25", "correlation": "0"}})])
    if fault in ("F7", "F16"):
        which = "dependency" if target.dependency_label else "target"
        summary = ("NetworkChaos partition between the target and its dependency" if fault == "F16"
                   else "NetworkChaos partition between the target and the selected peer")
        spec = {**pod, "action": "partition", "duration": d, "direction": "both",
                "target": _pod_selector(target, which=which, mode="all")}
        return Recipe(fault, "chaos-mesh", summary, [_cm("NetworkChaos", name, target, spec)])
    if fault == "F8":
        return Recipe(fault, "chaos-mesh", "NetworkChaos bandwidth limit of 1 mbps",
                      [_cm("NetworkChaos", name, target, {**pod, "action": "bandwidth", "duration": d,
                                                          "bandwidth": {"rate": "1mbps", "limit": 20971520,
                                                                        "buffer": 10000}})])
    if fault == "F9":
        patterns = [target.host] if target.host else ["*"]
        return Recipe(fault, "chaos-mesh", f"DNSChaos error for {', '.join(patterns)}",
                      [_cm("DNSChaos", name, target, {**pod, "action": "error", "duration": d,
                                                      "patterns": patterns})])
    if fault == "F10":
        return Recipe(fault, "chaos-mesh", "StressChaos CPU, one worker at 100 percent load",
                      [_cm("StressChaos", name, target, {**pod, "duration": d,
                                                         "stressors": {"cpu": {"workers": 1, "load": 100}}})])
    if fault == "F11":
        return Recipe(fault, "chaos-mesh", "StressChaos memory, one worker holding 256MB",
                      [_cm("StressChaos", name, target, {**pod, "duration": d,
                                                         "stressors": {"memory": {"workers": 1, "size": "256MB"}}})])
    if fault == "F12":
        return Recipe(fault, "chaos-mesh", f"IOChaos fault, error 5 (EIO) on half of the I/O under {target.data_path}",
                      [_cm("IOChaos", name, target, {**pod, "action": "fault", "duration": d,
                                                     "volumePath": target.data_path,
                                                     "path": f"{target.data_path}/**/*",
                                                     "errno": 5, "percent": 50})])
    if fault == "F13":
        return Recipe(fault, "chaos-mesh", "TimeChaos clock moved back 10 minutes",
                      [_cm("TimeChaos", name, target, {**pod, "duration": d, "timeOffset": "-10m"})])
    if fault == "F14":
        return Recipe(fault, "chaos-mesh", f"HTTPChaos replacing responses on port {target.port} with status 503",
                      [_cm("HTTPChaos", name, target, {**pod, "target": "Response", "port": target.port,
                                                       "path": "*", "duration": d,
                                                       "replace": {"code": 503}})])
    if fault == "F15":
        return Recipe(fault, "chaos-mesh", f"Approximation: IOChaos mistake corrupting reads of the configuration "
                      f"under {target.config_path}",
                      [_cm("IOChaos", name, target, {**pod, "action": "mistake", "duration": d,
                                                     "volumePath": target.config_path,
                                                     "path": f"{target.config_path}/**/*", "percent": 100,
                                                     "methods": ["read"],
                                                     "mistake": {"filling": "random", "maxOccurrences": 1,
                                                                 "maxLength": 10}})])
    if fault == "F17":
        return Recipe(fault, "chaos-mesh", "Approximation: TimeChaos clock moved 90 days ahead, past a "
                      "certificate's or token's expiry",
                      [_cm("TimeChaos", name, target, {**pod, "duration": d, "timeOffset": "2160h"})])
    if fault == "F19":
        return Recipe(fault, "chaos-mesh", f"Approximation: IOChaos mistake corrupting reads of data under "
                      f"{target.data_path}",
                      [_cm("IOChaos", name, target, {**pod, "action": "mistake", "duration": d,
                                                     "volumePath": target.data_path,
                                                     "path": f"{target.data_path}/**/*", "percent": 10,
                                                     "methods": ["read"],
                                                     "mistake": {"filling": "zero", "maxOccurrences": 1,
                                                                 "maxLength": 100}})])
    return None


def _litmus_template(fault_name):
    text = resources.files("incident2chaos.templates.litmus").joinpath(f"{fault_name}.yaml").read_text(
        encoding="utf-8")
    return [doc for doc in yaml.safe_load_all(text) if doc][0]


def _litmus(fault_name, name, target, env, which="target", appinfo=True):
    engine = copy.deepcopy(_litmus_template(fault_name))
    engine["metadata"] = {"name": name, "namespace": target.namespace}
    if appinfo:
        key, value = next(iter(target.label_pair(which).items()))
        engine["spec"]["appinfo"] = {"appns": target.namespace, "applabel": f"{key}={value}",
                                     "appkind": "deployment"}
    values = {"TOTAL_CHAOS_DURATION": str(target.duration_seconds), **{k: str(v) for k, v in env.items()}}
    entries = engine["spec"]["experiments"][0]["spec"]["components"]["env"]
    present = {entry["name"] for entry in entries}
    for entry in entries:
        if entry["name"] in values:
            entry["value"] = values[entry["name"]]
    for key, value in values.items():
        if key not in present:
            entries.append({"name": key, "value": value})
    return engine


def _k6_secret(name, target):
    url = target.url or "http://{}.{}.svc.cluster.local/".format(
        next(iter(target.label_pair().values())), target.namespace)
    script = ("import http from 'k6/http';\n"
              "export const options = { vus: 200, duration: '%ds' };\n"
              "export default function () { http.get('%s'); }\n") % (target.duration_seconds, url)
    return {"apiVersion": "v1", "kind": "Secret",
            "metadata": {"name": f"{name}-k6", "namespace": target.namespace},
            "type": "Opaque", "stringData": {"script.js": script}}


def litmus(fault, name, target):
    """Return the LitmusChaos recipe for a fault class, or None when the catalog has none."""
    if fault == "F1":
        return Recipe(fault, "litmus", "pod-delete on the target pods",
                      [_litmus("pod-delete", name, target, {"CHAOS_INTERVAL": 10})])
    if fault == "F2":
        engine = _litmus("node-drain", name, target, {"TARGET_NODE": target.node}, appinfo=False)
        note = "node-drain of node " + (target.node or "(set TARGET_NODE to the node to drain)")
        return Recipe(fault, "litmus", note, [engine])
    if fault == "F5":
        return Recipe(fault, "litmus", "pod-network-latency of 200 ms",
                      [_litmus("pod-network-latency", name, target, {"NETWORK_LATENCY": 200, "JITTER": 50})])
    if fault == "F6":
        return Recipe(fault, "litmus", "pod-network-loss of 25 percent of packets",
                      [_litmus("pod-network-loss", name, target, {"NETWORK_PACKET_LOSS_PERCENTAGE": 25})])
    if fault in ("F7", "F16"):
        if fault == "F16":
            return Recipe(fault, "litmus", f"pod-http-status-code 503 on the dependency's port {target.port}",
                          [_litmus("pod-http-status-code", name, target,
                                   {"STATUS_CODE": 503, "TARGET_SERVICE_PORT": target.port},
                                   which="dependency")])
        return Recipe(fault, "litmus", "pod-network-partition of the target pods",
                      [_litmus("pod-network-partition", name, target, {"POLICY_TYPES": "all"})])
    if fault == "F8":
        return Recipe(fault, "litmus", "pod-network-rate-limit to 1mbit",
                      [_litmus("pod-network-rate-limit", name, target, {"NETWORK_BANDWIDTH": "1mbit"})])
    if fault == "F9":
        hosts = f'["{target.host}"]' if target.host else ""
        return Recipe(fault, "litmus", "pod-dns-error for " + (target.host or "every hostname"),
                      [_litmus("pod-dns-error", name, target, {"TARGET_HOSTNAMES": hosts})])
    if fault == "F10":
        return Recipe(fault, "litmus", "pod-cpu-hog on one core",
                      [_litmus("pod-cpu-hog", name, target, {"CPU_CORES": 1})])
    if fault == "F11":
        return Recipe(fault, "litmus", "pod-memory-hog of 500 MB",
                      [_litmus("pod-memory-hog", name, target, {"MEMORY_CONSUMPTION": 500})])
    if fault == "F12":
        return Recipe(fault, "litmus", "disk-fill to 80 percent of the ephemeral storage limit",
                      [_litmus("disk-fill", name, target, {"FILL_PERCENTAGE": 80})])
    if fault == "F14":
        return Recipe(fault, "litmus", f"pod-http-status-code 503 on port {target.port}",
                      [_litmus("pod-http-status-code", name, target,
                               {"STATUS_CODE": 503, "TARGET_SERVICE_PORT": target.port})])
    if fault in ("F18", "F20"):
        secret = _k6_secret(name, target)
        load = _litmus("k6-loadgen", name, target, {"SCRIPT_SECRET_NAME": secret["metadata"]["name"],
                                                    "SCRIPT_SECRET_KEY": "script.js"}, appinfo=False)
        if fault == "F18":
            return Recipe(fault, "litmus", "Approximation: k6-loadgen, 200 virtual users against the service's "
                          "limit", [secret, load])
        dep = _litmus("pod-http-status-code", f"{name}-dep", target,
                      {"STATUS_CODE": 503, "TARGET_SERVICE_PORT": target.port},
                      which="dependency" if target.dependency_label else "target")
        return Recipe(fault, "litmus", "Approximation: k6-loadgen, 200 virtual users, together with "
                      "pod-http-status-code 503 on the dependency, so clients retry", [secret, load, dep])
    return None
