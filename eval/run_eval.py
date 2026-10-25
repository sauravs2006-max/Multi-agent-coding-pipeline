"""Benchmark: send every task through the real API, then grade each attempt with hidden tests.

The hidden tests are never shown to the coder or the reviewer, so a pass here means the
code really does what the prompt asked, not that the pipeline liked its own tests.

    python eval/run_eval.py --runs 3
    python eval/run_eval.py --check-references   # sanity check the hidden tests in the sandbox
"""
import argparse
import json
import os
import statistics
import time
from datetime import datetime
from pathlib import Path

import httpx

TASKS_DIR = Path(__file__).parent / "tasks"
RESULTS_DIR = Path(__file__).parent / "results"
DIFFICULTY = {"e": "easy", "m": "medium", "h": "hard"}
HIDDEN_TEST_TIMEOUT = 20
TASK_TIMEOUT = 900  # tasks can sit in the queue behind the gemini rate limit
POLL_SECONDS = 2


def load_tasks(only=None):
    tasks = []
    for folder in sorted(p for p in TASKS_DIR.iterdir() if p.is_dir()):
        if only and folder.name not in only:
            continue
        tasks.append({
            "id": folder.name,
            "difficulty": DIFFICULTY[folder.name[0]],
            "prompt": (folder / "prompt.txt").read_text(encoding="utf-8").strip(),
            "hidden_test": (folder / "hidden_test.py").read_text(encoding="utf-8"),
            "reference": (folder / "reference.py").read_text(encoding="utf-8"),
        })
    return tasks


def run_hidden_test(client, sandbox_url, code, hidden_test):
    response = client.post(f"{sandbox_url}/run", json={"code": code, "tests": hidden_test, "timeout": HIDDEN_TEST_TIMEOUT},
                           timeout=HIDDEN_TEST_TIMEOUT + 30)
    response.raise_for_status()
    return response.json()


def last_line(text):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return lines[-1][:200] if lines else ""


def submit_and_wait(client, api_url, prompt):
    start = time.monotonic()
    response = client.post(f"{api_url}/tasks", json={"task_description": prompt})
    response.raise_for_status()
    task_id = response.json()["task_id"]
    while time.monotonic() - start < TASK_TIMEOUT:
        time.sleep(POLL_SECONDS)
        body = client.get(f"{api_url}/tasks/{task_id}").json()
        if body["status"] in ("done", "failed", "error"):
            return body, time.monotonic() - start
    return {"status": "timeout", "error": f"not finished after {TASK_TIMEOUT}s"}, time.monotonic() - start


def grade(client, sandbox_url, task, body, wall_seconds):
    result = {"task": task["id"], "difficulty": task["difficulty"], "status": body["status"],
              "wall_seconds": round(wall_seconds, 1)}
    if body["status"] in ("error", "timeout"):
        # the pipeline crashed (quota, gemini down...), there is no code to grade
        result.update(iterations=None, approved=False, attempt_passes=[], passed_first_try=False,
                      passed_final=False, failure=f"pipeline {body['status']}: {body.get('error', '')[:200]}")
        return result

    pipeline = body["result"]
    runs = [run_hidden_test(client, sandbox_url, code, task["hidden_test"]) for code in pipeline["code_history"]]
    passes = [run["exit_code"] == 0 for run in runs]
    failure = None
    if not passes[-1]:
        final = runs[-1]
        failure = "timed out" if final["timed_out"] else last_line(final["stderr"]) or f"exit code {final['exit_code']}"
    result.update(iterations=pipeline["iteration_count"], approved=pipeline["approved"], attempt_passes=passes,
                  passed_first_try=passes[0], passed_final=passes[-1], failure=failure)
    return result


def summarize(results):
    n = len(results)
    passed = [r for r in results if r["passed_final"]]
    finished = [r for r in results if r["iterations"] is not None]
    by_difficulty = {}
    for level in ("easy", "medium", "hard"):
        group = [r for r in results if r["difficulty"] == level]
        if group:
            by_difficulty[level] = round(sum(r["passed_final"] for r in group) / len(group), 3)
    return {
        "tasks": n,
        "pass_first_try": round(sum(r["passed_first_try"] for r in results) / n, 3),
        "pass_within_3": round(len(passed) / n, 3),
        "avg_iterations_to_pass": round(statistics.mean(r["iterations"] for r in passed), 2) if passed else None,
        "avg_iterations": round(statistics.mean(r["iterations"] for r in finished), 2) if finished else None,
        "pipeline_errors": n - len(finished),
        # approved by the reviewer but the hidden tests say it's wrong
        "false_approvals": sum(1 for r in results if r["approved"] and not r["passed_final"]),
        # the pipeline gave up on code that actually passes the hidden tests
        "false_rejections": sum(1 for r in results if r["status"] == "failed" and r["passed_final"]),
        # an earlier attempt already passed the hidden tests but the reviewer sent it back anyway
        "rejected_correct_attempts": sum(1 for r in results if any(r.get("attempt_passes", [])[:-1])),
        "pass_rate_by_difficulty": by_difficulty,
        "mean_wall_seconds": round(statistics.mean(r["wall_seconds"] for r in results), 1),
        "total_wall_seconds": round(sum(r["wall_seconds"] for r in results), 1),
    }


def spread(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"mean": round(statistics.mean(values), 3), "min": min(values), "max": max(values),
            "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0}


def write_markdown(path, runs, aggregate):
    lines = ["# Eval results", "", f"{len(runs)} run(s) of {runs[0]['summary']['tasks']} tasks.", "",
             "## Summary", "", "| metric | mean | min | max | stdev |", "|---|---|---|---|---|"]
    for name, stats in aggregate.items():
        if stats:
            lines.append(f"| {name} | {stats['mean']} | {stats['min']} | {stats['max']} | {stats['stdev']} |")
    lines += ["", "## Per task", "", "| task | difficulty | " + " | ".join(f"run {i + 1}" for i in range(len(runs))) + " |",
              "|---|---|" + "---|" * len(runs)]
    for i, row in enumerate(runs[0]["results"]):
        cells = []
        for run in runs:
            r = run["results"][i]
            if r["iterations"] is None:
                cells.append(r["status"])
            else:
                mark = "pass" if r["passed_final"] else "FAIL"
                cells.append(f"{mark} ({r['iterations']} it, {r['wall_seconds']}s)")
        lines.append(f"| {row['task']} | {row['difficulty']} | " + " | ".join(cells) + " |")
    failures = [(i + 1, r) for i, run in enumerate(runs) for r in run["results"] if r["failure"]]
    if failures:
        lines += ["", "## Failures", "", "| run | task | reason |", "|---|---|---|"]
        for run_number, r in failures:
            lines.append(f"| {run_number} | {r['task']} | {r['failure'].replace('|', '/')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_references(client, sandbox_url, tasks):
    ok = True
    for task in tasks:
        run = run_hidden_test(client, sandbox_url, task["reference"], task["hidden_test"])
        status = "ok" if run["exit_code"] == 0 else f"FAILED: {last_line(run['stderr'])}"
        ok = ok and run["exit_code"] == 0
        print(f"{task['id']:<24} {status}")
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--tasks", help="comma separated task ids, default all")
    parser.add_argument("--api", default=os.getenv("API_URL", "http://localhost:8000"))
    parser.add_argument("--sandbox", default=os.getenv("SANDBOX_URL", "http://localhost:8080"))
    parser.add_argument("--check-references", action="store_true")
    args = parser.parse_args()

    tasks = load_tasks(args.tasks.split(",") if args.tasks else None)
    client = httpx.Client(timeout=30)

    if args.check_references:
        raise SystemExit(0 if check_references(client, args.sandbox, tasks) else 1)

    runs = []
    for run_number in range(1, args.runs + 1):
        results = []
        for task in tasks:
            body, wall = submit_and_wait(client, args.api, task["prompt"])
            result = grade(client, args.sandbox, task, body, wall)
            results.append(result)
            outcome = "pass" if result["passed_final"] else "FAIL"
            print(f"run {run_number} {task['id']:<24} {outcome:<4} iterations={result['iterations']} "
                  f"{result['wall_seconds']:>6}s {result['failure'] or ''}", flush=True)
        runs.append({"run": run_number, "results": results, "summary": summarize(results)})
        print(f"run {run_number} summary: {json.dumps(runs[-1]['summary'])}", flush=True)

    metrics = ["pass_first_try", "pass_within_3", "avg_iterations_to_pass", "avg_iterations",
               "false_approvals", "false_rejections", "rejected_correct_attempts", "pipeline_errors",
               "mean_wall_seconds"]
    aggregate = {m: spread([run["summary"][m] for run in runs]) for m in metrics}

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = {"started": stamp, "model": os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"), "runs": runs,
           "aggregate": aggregate}
    (RESULTS_DIR / f"eval_{stamp}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    write_markdown(RESULTS_DIR / f"eval_{stamp}.md", runs, aggregate)
    print(f"saved eval/results/eval_{stamp}.json and .md")


if __name__ == "__main__":
    main()
