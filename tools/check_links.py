"""Open every link of the corpus and list the rows whose link does not open the report it names.

Usage:
    python tools/check_links.py CORPUS_CSV OUT_DIR
    python tools/check_links.py CORPUS_CSV OUT_DIR --rejudge

CORPUS_CSV is corpus.csv. OUT_DIR is a new, empty directory. One GET goes to each distinct
address of the url column, with redirects followed. A row's link passes when the answer is
HTTP 200, the last address is on the provider's own site, and the page returned holds the
report the row names:
    AWS PES                        the page holds the row's title
    Microsoft Azure PIR            the history results hold the row's tracking id
    Google Cloud incident report   an incident page that holds the row's title
    Cloudflare blog post-mortem    the page holds the row's title
    GitHub availability report     the address ends in the report's slug and the page heading
                                   is the report the row's title names
A page holds a title when the title is in its text, its title element or its og:title. The
title element alone is not the test: on four AWS pages and one Cloudflare page it differs
from the title on the provider's index, which is the title the corpus holds.
Thirteen rows hold the source, the identifier and the date in place of a title. The two Azure
rows among them are judged by the tracking id alone, and the eleven Google Cloud rows by the
date the incident page says the incident began.
A site never receives the part of an address after "#", so the check judges the page a browser
is given for the address. A request that gets no HTTP answer, an answer of 429 or 5xx, or an
Azure history page with no review in it is sent up to two more times, so that one passing
answer does not fail a link. Requests to one site are at least one second apart, and each
carries a User-Agent that names this tool.
Outputs:
    OUT_DIR/link_check.csv   one line per corpus row: the address, the answer and the verdict
    OUT_DIR/pages/           each page as returned, named by the SHA-256 of its address
With --rejudge nothing is fetched: the verdicts of OUT_DIR/link_check.csv are worked out again
from the pages a run saved there.
"""

import csv
import hashlib
import html
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

HOSTS = {
    "AWS PES": "aws.amazon.com",
    "Microsoft Azure PIR": "azure.status.microsoft",
    "Google Cloud incident report": "status.cloud.google.com",
    "Cloudflare blog post-mortem": "blog.cloudflare.com",
    "GitHub availability report": "github.blog",
}
USER_AGENT = "incident2chaos-check-links (https://github.com/yogeshramaswamy608/incident2chaos)"
TRIES = 3
PAUSE_BETWEEN_TRIES = 10
PAUSE_PER_HOST = 1.0
TIMEOUT = 60
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―"), "-")
QUOTES = {ord("‘"): "'", ord("’"): "'", ord("“"): '"', ord("”"): '"', 0xA0: " "}


def norm(text):
    """Text as compared: entities resolved, dashes and quotes made plain, spaces single, lower case."""
    text = html.unescape(text).translate(DASHES).translate(QUOTES)
    return re.sub(r"\s+", " ", text).strip().casefold()


def visible(page):
    """The page without scripts, styles and tags."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    return norm(re.sub(r"(?s)<[^>]+>", " ", page))


def tag_text(page, tag):
    """The text of the first TAG element of the page that has any."""
    for match in re.finditer(r"(?is)<%s\b[^>]*>(.*?)</%s>" % (tag, tag), page):
        text = norm(re.sub(r"(?s)<[^>]+>", " ", match.group(1)))
        if text:
            return text
    return ""


def holds_title(page, title):
    """Whether the page holds the title: in its text, its title element or its og:title."""
    tagged = [tag_text(page, "title")]
    for meta in re.findall(r"(?is)<meta\b[^>]*>", page):
        if re.search(r"""(?i)property=["']og:title["']""", meta):
            content = re.search(r"""(?is)content=(["'])(.*?)\1""", meta)
            if content:
                tagged.append(norm(content.group(2)))
    return title in visible(page) or any(title in text for text in tagged)


def title_is_replaced(row):
    return bool(re.fullmatch(re.escape(row["source"] + " " + row["report_id"]) + r", \d{4}-\d{2}-\d{2}",
                             row["title"]))


def azure_results(page):
    """The part of an Azure history page that lists reviews."""
    start = page.find('id="history-results-container"')
    return page[start:] if start >= 0 else ""


def azure_holds(page, tracking_id):
    results = azure_results(page)
    return ("incident-history-collapse-" + tracking_id + '"') in results or bool(
        re.search(r"Tracking ID:?\s*" + re.escape(tracking_id) + r"(?![A-Za-z0-9_-])", results))


def holds_report(row, page, final_url):
    """(True or False, the rule applied) for one row and the page its link returned."""
    source = row["source"]
    title = norm(row["title"])
    if source == "AWS PES":
        return holds_title(page, title), "page holds the row's title"
    if source == "Microsoft Azure PIR":
        return azure_holds(page, row["report_id"]), "history results hold the tracking id"
    if source == "Google Cloud incident report":
        if not tag_text(page, "title").startswith("incident details"):
            return False, "an incident page"
        if title_is_replaced(row):
            return ("incident began at " + row["incident_date"]) in visible(page), \
                "incident page says the incident began on the row's date"
        return holds_title(page, title), "incident page holds the row's title"
    if source == "Cloudflare blog post-mortem":
        return holds_title(page, title), "page holds the row's title"
    if source == "GitHub availability report":
        slug = row["report_id"].split("#")[0]
        heading = norm(row["title"].split(" – ")[0])
        ok = urlsplit(final_url).path.rstrip("/").endswith("/" + slug) and tag_text(page, "h1") == heading
        return ok, "address ends in the report's slug and the heading is the report's title"
    raise ValueError("unknown source: " + source)


def judge(row, status, final_url, page):
    """(PASS or FAIL, the reason) for one row, the answer to its link and the page returned."""
    host = HOSTS[row["source"]]
    if status != 200:
        return "FAIL", "no HTTP answer" if status is None else "HTTP %d" % status
    if urlsplit(final_url).hostname != host:
        return "FAIL", "ends on %s, not on %s" % (urlsplit(final_url).hostname, host)
    ok, rule = holds_report(row, page, final_url)
    return ("PASS", rule) if ok else ("FAIL", "not met: " + rule)


class Chain(urllib.request.HTTPRedirectHandler):
    """Follows redirects and keeps each answer on the way."""

    def __init__(self):
        self.steps = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.steps.append("%d -> %s" % (code, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    """One GET with redirects followed: (status or None, final address, body, redirect steps, error)."""
    chain = Chain()
    opener = urllib.request.build_opener(chain)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
    try:
        with opener.open(request, timeout=TIMEOUT) as answer:
            return answer.status, answer.geturl(), answer.read(), chain.steps, ""
    except urllib.error.HTTPError as error:
        return error.code, error.geturl(), error.read(), chain.steps, ""
    except Exception as error:  # no HTTP answer: DNS, TLS, timeout, connection reset
        return None, url, b"", chain.steps, "%s: %s" % (type(error).__name__, error)


def check_address(url, rows, pages_dir):
    """Open one address (up to TRIES times for the conditions in the module text) and judge its rows."""
    source = rows[0]["source"]
    for attempt in range(1, TRIES + 1):
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        status, final_url, body, steps, error = fetch(url)
        page = body.decode("utf-8", errors="replace")
        on_host = urlsplit(final_url).hostname == HOSTS[source]
        empty_azure = (source == "Microsoft Azure PIR" and status == 200 and on_host
                       and "incident-history-collapse-" not in azure_results(page)
                       and "Tracking ID" not in azure_results(page))
        transient = status is None or status == 429 or status >= 500 or empty_azure
        if not transient or attempt == TRIES:
            break
        time.sleep(PAUSE_BETWEEN_TRIES)
    name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16] + ".html"
    (pages_dir / name).write_bytes(body)
    results = []
    for row in rows:
        verdict, why = judge(row, status, final_url, page)
        results.append({
            "corpus_no": row["corpus_no"], "source": source, "report_id": row["report_id"], "url": url,
            "checked_utc": when, "tries": attempt, "status": "" if status is None else status,
            "redirects": " | ".join(steps), "final_url": final_url, "bytes": len(body),
            "page_sha256": hashlib.sha256(body).hexdigest(), "page_file": name,
            "verdict": verdict, "reason": why, "error": error,
        })
    return results


def report(ordered, addresses):
    failed = [item for item in ordered if item["verdict"] == "FAIL"]
    print("%d rows, %d addresses, %d rows pass, %d rows fail" % (
        len(ordered), addresses, len(ordered) - len(failed), len(failed)))
    for item in failed:
        print("FAIL  %-5s %-28s %s  (%s)" % (item["corpus_no"], item["source"], item["url"], item["reason"]))
    return 1 if failed else 0


def rejudge(corpus, out_dir):
    """Work the verdicts out again from the pages a run saved, without a request."""
    with open(out_dir / "link_check.csv", newline="", encoding="utf-8") as handle:
        ordered = list(csv.DictReader(handle))
    by_no = {row["corpus_no"]: row for row in corpus}
    for item in ordered:
        row = by_no[item["corpus_no"]]
        if row["url"] != item["url"]:
            raise SystemExit("row %s: the corpus holds another address than the saved check" % item["corpus_no"])
        page = (out_dir / "pages" / item["page_file"]).read_bytes().decode("utf-8", errors="replace")
        status = int(item["status"]) if item["status"] else None
        item["verdict"], item["reason"] = judge(row, status, item["final_url"], page)
    with open(out_dir / "link_check.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]))
        writer.writeheader()
        writer.writerows(ordered)
    return report(ordered, len({item["url"] for item in ordered}))


def main(corpus_csv, out_dir, saved=False):
    out_dir = Path(out_dir)
    with open(corpus_csv, newline="", encoding="utf-8") as handle:
        corpus = list(csv.DictReader(handle))
    if saved:
        return rejudge(corpus, out_dir)
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True)
    by_url = {}
    for row in corpus:
        by_url.setdefault(row["url"], []).append(row)
    for url, rows in by_url.items():
        if len({row["source"] for row in rows}) != 1:
            raise SystemExit("one address under two sources: " + url)
    by_host = {}
    for url in by_url:
        by_host.setdefault(urlsplit(url).hostname, []).append(url)
    results, lock = {}, threading.Lock()

    def work(urls):
        for url in urls:
            checked = check_address(url, by_url[url], pages_dir)
            with lock:
                for item in checked:
                    results[item["corpus_no"]] = item
            time.sleep(PAUSE_PER_HOST)

    threads = [threading.Thread(target=work, args=(urls,)) for urls in by_host.values()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    ordered = [results[row["corpus_no"]] for row in corpus]
    with open(out_dir / "link_check.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]))
        writer.writeheader()
        writer.writerows(ordered)
    return report(ordered, len(by_url))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or sys.argv[3:] not in ([], ["--rejudge"]):
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2], saved=len(sys.argv) == 4))
