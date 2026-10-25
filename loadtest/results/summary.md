# Load test results

Raw locust output (CSV, HTML, logs) is in this folder.

### fake

| users | tasks done | tasks/min | end-to-end P50 / P95 (s) | queue wait P50 / P95 (s) | processing P50 / P95 (s) | POST /tasks P95 (ms) | GET P95 (ms) | failures |
|---|---|---|---|---|---|---|---|---|
| 1 | 34 | 8.5 | 5.6 / 5.6 | 0.5 / 0.5 | 5.1 / 5.1 | 12 | 8 | 0/511 |
| 5 | 44 | 11.1 | 25.0 / 26.0 | 20.0 / 20.0 | 5.1 / 5.6 | 130 | 8 | 0/2411 |
| 10 | 45 | 11.3 | 51.0 / 52.0 | 46.0 / 47.0 | 5.1 / 5.6 | 260 | 10 | 0/4778 |
| 20 | 45 | 11.3 | 103.0 / 105.0 | 98.0 / 99.0 | 5.1 / 5.6 | 450 | 12 | 0/9481 |

Per-agent latency from Prometheus, P50 / P95 in seconds:

| users | planner | coder | tester | reviewer |
|---|---|---|---|---|
| 1 | 1.50 / 1.95 | 1.50 / 1.95 | 0.75 / 0.98 | 1.50 / 1.95 |
| 5 | 1.50 / 1.95 | 1.50 / 1.95 | 0.76 / 1.00 | 1.50 / 1.95 |
| 10 | 1.50 / 1.95 | 1.50 / 1.95 | 0.76 / 0.99 | 1.50 / 1.95 |
| 20 | 1.50 / 1.95 | 1.50 / 1.95 | 0.75 / 0.97 | 1.50 / 1.95 |

### fake_4workers

| users | tasks done | tasks/min | end-to-end P50 / P95 (s) | queue wait P50 / P95 (s) | processing P50 / P95 (s) | POST /tasks P95 (ms) | GET P95 (ms) | failures |
|---|---|---|---|---|---|---|---|---|
| 20 | 177 | 44.4 | 25.0 / 26.0 | 20.0 / 21.0 | 5.1 / 5.6 | 330 | 11 | 0/9623 |

Per-agent latency from Prometheus, P50 / P95 in seconds:

| users | planner | coder | tester | reviewer |
|---|---|---|---|---|
| 20 | 1.50 / 1.95 | 1.50 / 1.95 | 0.79 / 1.63 | 1.50 / 1.95 |
