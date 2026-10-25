from prometheus_client import Counter, Gauge, Histogram

# LLM calls take seconds, so the default buckets (mostly under 1s) are useless here
AGENT_BUCKETS = (0.25, 0.5, 1, 2, 4, 8, 16, 32, 64)

AGENT_LATENCY = Histogram(
    "pipeline_agent_duration_seconds", "Time spent in each agent node", ["agent"], buckets=AGENT_BUCKETS
)
AGENT_RUNS = Counter("pipeline_agent_runs_total", "Agent node runs", ["agent", "outcome"])

PIPELINE_RUNS = Counter("pipeline_runs_total", "Finished pipeline runs", ["status"])
PIPELINE_DURATION = Histogram(
    "pipeline_duration_seconds", "End to end pipeline time", buckets=(2, 5, 10, 20, 40, 80, 160, 320)
)
PIPELINE_ITERATIONS = Histogram("pipeline_iterations", "Coder iterations per finished run", buckets=(1, 2, 3))

LLM_CALLS = Counter("llm_calls_total", "ask_json calls", ["outcome"])
LLM_ATTEMPTS = Counter("llm_attempts_total", "Requests sent to Gemini, by result", ["result"])
LLM_RETRIES = Counter("llm_retries_total", "Gemini attempts that failed and were retried")
CIRCUIT_OPEN = Gauge("llm_circuit_open", "1 while the circuit breaker is open")

SANDBOX_RUNS = Counter("sandbox_runs_total", "Sandbox runs by result", ["result"])

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "API request time", ["method", "path", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)

# create every known label combination at 0 up front. a series that first shows
# up already at 1 has no earlier sample, so increase() would miss that first event
for agent in ("planner", "coder", "tester", "reviewer"):
    AGENT_LATENCY.labels(agent)
    for outcome in ("success", "error"):
        AGENT_RUNS.labels(agent, outcome)
for status in ("done", "failed", "error"):
    PIPELINE_RUNS.labels(status)
for outcome in ("success", "failed"):
    LLM_CALLS.labels(outcome)
for result in ("ok", "rate_limited", "server_error", "timeout", "bad_json", "client_error"):
    LLM_ATTEMPTS.labels(result)
for result in ("passed", "failed", "timeout", "killed", "no_tests"):
    SANDBOX_RUNS.labels(result)
