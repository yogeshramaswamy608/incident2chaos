"""Second-model label check for paper 1 (see gpt_check/PLAN.md).

Reads gpt_check/run.json and runs one stage:
    probe   list the models the key can reach (no cost)
    pilot   label a fixed 10-report sample on each model in "models", to measure cost per report
    full    label every allowed report on "models"[0]
    second  label again on "models"[0], the 45 blind-sample reports first
Outputs go to gpt_check/out/<stage>/<model>/: labels.csv and calls.jsonl (one line per call).
No report text is written to disk; each call logs the text's URL, length and sha256 instead.
Spending stops before any call that would take the total of every calls.jsonl past the stage cap.
"""

import csv
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "out"
API = "https://api.openai.com/v1"
UA = "incident2chaos-study/1.0 (+https://github.com/yogeshramaswamy608/incident2chaos)"
MAX_CHARS = 40000
TRIGGERS = [f"T{i}" for i in range(1, 14)] + ["T99"]
FAULTS = [f"F{i}" for i in range(1, 21)] + ["F99"]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def system_prompt():
    """prompt.md, then codebook sections 1 to 3 and 6 (sections 4, 5 and 7 hold study results, left out)."""
    codebook = (REPO / "dataset" / "codebook.md").read_text(encoding="utf-8")
    parts = re.split(r"\n(?=\d\. )", codebook)
    keep = [p for p in parts if re.match(r"(1|2|3|6)\. ", p)]
    return (ROOT / "prompt.md").read_text(encoding="utf-8").strip() + "\n\n" + "\n\n".join(keep).strip()


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["in_scope", "trigger_primary", "trigger_secondary", "faults", "fault_primary",
                 "confidence", "evidence_trigger", "evidence_fault"],
    "properties": {
        "in_scope": {"type": "string", "enum": ["yes", "no"]},
        "trigger_primary": {"type": "string", "enum": TRIGGERS},
        "trigger_secondary": {"type": "string", "enum": TRIGGERS + [""]},
        "faults": {"type": "array", "items": {"type": "string", "enum": FAULTS}},
        "fault_primary": {"type": "string", "enum": FAULTS},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "evidence_trigger": {"type": "string"},
        "evidence_fault": {"type": "string"},
    },
}


# ---------- fetching ----------

def _clean(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "svg", "form"]):
        tag.decompose()
    return soup


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _github_section(soup, row):
    """One incident of a monthly GitHub availability report: its heading and the paragraphs up to the next heading."""
    body = soup.find("main") or soup
    title = row["title"]
    fragment = row["url"].split("#", 1)[1] if "#" in row["url"] else ""
    anchor = soup.find(id=fragment) if fragment else None
    if " – " not in title and anchor is None:
        return body.get_text(" ", strip=True)
    wanted = _norm(title.split(" – ", 1)[1]) if " – " in title else _norm(anchor.get_text())
    blocks = body.find_all(["h2", "h3", "h4", "p", "li"])

    def level(el):
        """Heading level: h2 2, h3 3, h4 4, a paragraph that is all bold 4.5; 0 for body text."""
        if el.name in ("h2", "h3", "h4"):
            return int(el.name[1])
        strong = el.find("strong") if el.name == "p" else None
        return 4.5 if strong and _norm(strong.get_text()) == _norm(el.get_text()) else 0

    start = None
    for i, el in enumerate(blocks):
        if level(el) and _norm(el.get_text()).startswith(wanted[:40]):
            start = i
            break
    if start is None:
        return ""
    top = level(blocks[start])
    out = [blocks[start].get_text(" ", strip=True)]
    for el in blocks[start + 1:]:
        if 0 < level(el) <= top:
            break
        out.append(el.get_text(" ", strip=True))
    return "\n".join(out)


def _azure_section(text, tracking_id):
    """One PIR of the Azure history page: from its date line to the date line of the next PIR."""
    key = f"Tracking ID: {tracking_id}"
    i = text.find(key)
    if i < 0:
        return ""
    head = list(re.finditer(r"\d{2}/\d{2}/\d{4}", text[max(0, i - 400):i]))
    start = max(0, i - 400) + head[-1].start() if head else max(0, i - 300)
    j = text.find("Tracking ID:", i + len(key))
    if j < 0:
        return text[start:]
    tail = list(re.finditer(r"\d{2}/\d{2}/\d{4}", text[i:j]))
    return text[start:i + tail[-1].start()] if tail else text[start:j]


_PAGES = {}


def fetch_report(row, session):
    """Return (status, text). status is 'ok', 'empty' or 'http <code>'; two tries. A page shared by
    several reports (a monthly GitHub report) is fetched once per run."""
    url = row["url"].split("#")[0]
    status, text = "empty", ""
    for attempt in range(2):
        html = _PAGES.get(url) if attempt == 0 else None
        if html is None:
            try:
                resp = session.get(url, timeout=60)
            except requests.RequestException as exc:
                status, text = f"error {type(exc).__name__}", ""
                time.sleep(5)
                continue
            if resp.status_code != 200:
                status, text = f"http {resp.status_code}", ""
                time.sleep(5)
                continue
            html = _PAGES[url] = resp.text
        soup = _clean(html)
        source = row["source"]
        if source.startswith("GitHub"):
            text = _github_section(soup, row)
        elif source.startswith("Microsoft Azure"):
            text = _azure_section(soup.get_text(" ", strip=True), row["report_id"])
        else:
            main = soup.find("main") or soup.find("article") or soup
            text = main.get_text(" ", strip=True)
        status = "ok" if len(text) >= 300 else "empty"
        if status == "ok":
            break
        time.sleep(5)
    return status, text[:MAX_CHARS]


# ---------- the model ----------

def call_model(cfg, model, system, user, key):
    body = {
        "model": model,
        "input": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "text": {"format": {"type": "json_schema", "name": "labels", "schema": SCHEMA, "strict": True}},
        "max_output_tokens": cfg.get("max_output_tokens", 8000),
        "store": False,
    }
    if cfg.get("reasoning_effort"):
        body["reasoning"] = {"effort": cfg["reasoning_effort"]}
    if cfg.get("service_tier"):
        body["service_tier"] = cfg["service_tier"]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(6):
        resp = requests.post(f"{API}/responses", headers=headers, json=body, timeout=900)
        if resp.status_code == 200:
            return resp.json()
        err = resp.text[:500]
        if "credit_balance_exhausted" in err or "insufficient_quota" in err:
            raise SystemExit(f"Credit exhausted: {err}")
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(300, 15 * 2 ** attempt))
            continue
        raise SystemExit(f"API error {resp.status_code}: {err}")
    raise SystemExit("API kept failing after six tries")


def parse_reply(reply):
    for item in reply.get("output", []):
        for part in item.get("content", []) or []:
            if part.get("type") == "output_text":
                return json.loads(part["text"])
    raise ValueError("no output_text in reply")


def cost_of(usage, price):
    """Dollars for one call from its usage and the prices per million tokens in run.json."""
    cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
    fresh = usage.get("input_tokens", 0) - cached
    out = usage.get("output_tokens", 0)
    return (fresh * price["input"] + cached * price.get("cached_input", price["input"]) + out * price["output"]) / 1e6


def spent_so_far():
    total = 0.0
    for path in OUT.glob("**/calls.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                total += json.loads(line).get("cost_usd", 0.0)
    return total


# ---------- stages ----------

def allowed_rows(cfg):
    rows = list(csv.DictReader(open(REPO / "dataset" / "corpus.csv", encoding="utf-8")))
    excluded = set(cfg.get("exclude_sources", []))
    return [r for r in rows if r["source"] not in excluded]


def pilot_sample(rows, n=10, seed=20261123):
    by_source = {}
    for r in rows:
        by_source.setdefault(r["source"], []).append(r)
    rng = random.Random(seed)
    order = sorted(by_source)
    picks = []
    while len(picks) < n and any(by_source.values()):
        for s in order:
            if by_source[s] and len(picks) < n:
                picks.append(by_source[s].pop(rng.randrange(len(by_source[s]))))
    return picks


def stage_rows(cfg, stage):
    rows = allowed_rows(cfg)
    if stage == "pilot":
        return pilot_sample(rows)
    if stage == "second":
        blind = {r["corpus_no"] for r in csv.DictReader(open(REPO / "dataset" / "blind_sample.csv", encoding="utf-8"))}
        return [r for r in rows if r["corpus_no"] in blind] + [r for r in rows if r["corpus_no"] not in blind]
    return rows


LABEL_FIELDS = ["corpus_no", "source", "report_id", "fetch_status", "in_scope", "trigger_primary",
                "trigger_secondary", "faults", "fault_primary", "confidence", "evidence_trigger", "evidence_fault"]


def run_stage(cfg, stage, model, key):
    out_dir = OUT / stage / model
    out_dir.mkdir(parents=True, exist_ok=True)
    labels_path, calls_path = out_dir / "labels.csv", out_dir / "calls.jsonl"
    done = set()
    if labels_path.exists():
        done = {r["corpus_no"] for r in csv.DictReader(open(labels_path, encoding="utf-8"))}
    new_file = not labels_path.exists()
    system = system_prompt()
    system_sha = sha(system)
    cap = cfg["caps_usd"][stage]
    price = cfg["prices_per_million"][model]
    est = cfg.get("estimate_per_report_usd", {}).get(model, 0.10)
    session = requests.Session()
    session.headers["User-Agent"] = UA
    with open(labels_path, "a", encoding="utf-8", newline="") as lf, open(calls_path, "a", encoding="utf-8") as cf:
        writer = csv.DictWriter(lf, fieldnames=LABEL_FIELDS)
        if new_file:
            writer.writeheader()
        for row in stage_rows(cfg, stage):
            if row["corpus_no"] in done:
                continue
            spent = spent_so_far()
            if spent + 2 * est > cap:
                print(f"Stopping: ${spent:.2f} spent, cap ${cap:.2f} for stage {stage}.")
                break
            fetched_at = now()
            status, text = fetch_report(row, session)
            record = {"corpus_no": row["corpus_no"], "source": row["source"], "report_id": row["report_id"],
                      "fetch_status": status}
            log = {"corpus_no": row["corpus_no"], "stage": stage, "model": model, "url": row["url"],
                   "fetched_utc": fetched_at, "fetch_status": status, "text_chars": len(text),
                   "text_sha256": sha(text) if text else "", "system_prompt_sha256": system_sha,
                   "settings": {k: cfg.get(k) for k in ("reasoning_effort", "service_tier", "max_output_tokens")}}
            if status == "ok":
                user = f"Title: {row['title']}\nIncident date: {row['incident_date']}\nURL: {row['url']}\n\nReport text:\n{text}"
                log["called_utc"] = now()
                reply = call_model(cfg, model, system, user, key)
                usage = reply.get("usage", {})
                log.update({"snapshot": reply.get("model"), "response_id": reply.get("id"), "usage": usage,
                            "cost_usd": round(cost_of(usage, price), 6), "status": reply.get("status")})
                try:
                    labels = parse_reply(reply)
                    log["reply"] = labels
                    record.update({k: (";".join(v) if isinstance(v, list) else v) for k, v in labels.items()})
                except (ValueError, json.JSONDecodeError) as exc:
                    log["parse_error"] = str(exc)
            cf.write(json.dumps(log, ensure_ascii=False) + "\n")
            cf.flush()
            writer.writerow({k: record.get(k, "") for k in LABEL_FIELDS})
            lf.flush()
            time.sleep(cfg.get("pause_seconds", 2))
    print(f"Stage {stage} on {model}: total spent across all stages ${spent_so_far():.4f}")


def probe(key):
    resp = requests.get(f"{API}/models", headers={"Authorization": f"Bearer {key}"}, timeout=60)
    OUT.mkdir(parents=True, exist_ok=True)
    if resp.status_code != 200:
        raise SystemExit(f"Key check failed: HTTP {resp.status_code} {resp.text[:300]}")
    ids = sorted(m["id"] for m in resp.json().get("data", []))
    (OUT / "models.json").write_text(json.dumps({"read_utc": now(), "models": ids}, indent=1) + "\n", encoding="utf-8")
    print(f"Key works; {len(ids)} models listed in gpt_check/out/models.json")


def main():
    cfg = json.loads((ROOT / "run.json").read_text(encoding="utf-8"))
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set as a repository secret; nothing was called.")
    stage = cfg["stage"]
    if stage == "probe":
        return probe(key)
    if stage not in ("pilot", "full", "second"):
        raise SystemExit(f"Unknown stage {stage}")
    models = cfg["models"] if stage == "pilot" else cfg["models"][:1]
    for model in models:
        if model not in cfg.get("prices_per_million", {}):
            raise SystemExit(f"No price for {model} in run.json; nothing was called.")
    for model in models:
        run_stage(cfg, stage, model, key)


if __name__ == "__main__":
    sys.exit(main())
