"""Turns the locust CSVs and prometheus snapshots in loadtest/results into summary.md."""
import csv
import json
import re
import sys
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
AGENTS = ("planner", "coder", "tester", "reviewer")


def stats_rows(name):
    with open(RESULTS / f"{name}_stats.csv", encoding="utf-8") as f:
        return {row["Name"]: row for row in csv.DictReader(f)}


def seconds(row, column):
    return f"{float(row[column]) / 1000:.1f}" if row and row[column] not in ("", "N/A") else "-"


def agent_latency(name, quantile):
    path = RESULTS / f"{name}_agents_p{quantile}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))["data"]["result"]
    return {r["metric"]["agent"]: float(r["value"][1]) for r in data if r["value"][1] != "NaN"}


def summarize(label):
    names = sorted({p.name.split("_stats.csv")[0] for p in RESULTS.glob(f"{label}_u*_stats.csv")},
                   key=lambda n: int(re.search(r"_u(\d+)$", n).group(1)))
    lines = [f"### {label}", "",
             "| users | tasks done | tasks/min | end-to-end P50 / P95 (s) | queue wait P50 / P95 (s) "
             "| processing P50 / P95 (s) | POST /tasks P95 (ms) | GET P95 (ms) | failures |",
             "|---|---|---|---|---|---|---|---|---|"]
    agent_lines = ["", "Per-agent latency from Prometheus, P50 / P95 in seconds:", "",
                   "| users | " + " | ".join(AGENTS) + " |", "|---|" + "---|" * len(AGENTS)]
    for name in names:
        users = re.search(r"_u(\d+)$", name).group(1)
        rows = stats_rows(name)
        e2e, queue, processing = rows.get("end to end"), rows.get("queue wait"), rows.get("processing")
        post, get, total = rows.get("POST /tasks"), rows.get("GET /tasks/[id]"), rows.get("Aggregated")
        done = int(e2e["Request Count"]) if e2e else 0
        per_min = float(e2e["Requests/s"]) * 60 if e2e else 0
        failures = f"{int(total['Failure Count'])}/{int(total['Request Count'])}" if total else "-"
        lines.append(
            f"| {users} | {done} | {per_min:.1f} | {seconds(e2e, '50%')} / {seconds(e2e, '95%')} "
            f"| {seconds(queue, '50%')} / {seconds(queue, '95%')} | {seconds(processing, '50%')} / {seconds(processing, '95%')} "
            f"| {post['95%'] if post else '-'} | {get['95%'] if get else '-'} | {failures} |")
        p50, p95 = agent_latency(name, "5"), agent_latency(name, "95")
        cells = [f"{p50[a]:.2f} / {p95[a]:.2f}" if a in p50 and a in p95 else "-" for a in AGENTS]
        agent_lines.append(f"| {users} | " + " | ".join(cells) + " |")
    return lines + agent_lines


if __name__ == "__main__":
    labels = sys.argv[1:] or sorted({p.name.rsplit("_u", 1)[0] for p in RESULTS.glob("*_u*_stats.csv")})
    out = ["# Load test results", "", "Raw locust output (CSV, HTML, logs) is in this folder.", ""]
    for label in labels:
        out += summarize(label) + [""]
    (RESULTS / "summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
