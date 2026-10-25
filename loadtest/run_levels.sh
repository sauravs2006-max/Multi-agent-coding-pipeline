#!/usr/bin/env bash
# Runs the locust scenario at a few user counts, one after another.
#   loadtest/run_levels.sh <label> <users>...    e.g. loadtest/run_levels.sh fake 1 5 10 20
# Expects the stack to be up already (make up, or FAKE_LLM=1 make up for an infra-only run).
set -euo pipefail

label=$1
shift
duration=${DURATION:-4m}
results=loadtest/results
mkdir -p "$results"

prometheus_query() {
  curl -s "http://localhost:9090/api/v1/query" --data-urlencode "query=$1"
}

for users in "$@"; do
  name="${label}_u${users}"
  echo "== $name: $users users for $duration"

  # snapshot cpu/memory halfway through, to see which container is the bottleneck
  (sleep 120 && docker stats --no-stream > "$results/${name}_docker_stats.txt") &

  docker compose --profile tools run --rm --no-deps loadtest --headless \
    -u "$users" -r "$users" -t "$duration" \
    --csv "results/$name" --html "results/$name.html" --only-summary > "$results/$name.log" 2>&1
  wait

  for q in 0.5 0.95; do
    prometheus_query "histogram_quantile($q, sum by (le, agent) (rate(pipeline_agent_duration_seconds_bucket[$duration])))" \
      > "$results/${name}_agents_p${q#0.}.json"
  done

  # users stop mid-task, so let the queue drain before the next level
  until [ "$(docker compose exec -T redis redis-cli llen celery | tr -d '\r')" = "0" ]; do sleep 2; done
  sleep 10
done
