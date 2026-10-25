# Eval results

4 run(s) of 15 tasks.
Note: combined from eval_20261025_075240.json, eval_20261025_081956.json.

## Summary

| metric | mean | min | max | stdev |
|---|---|---|---|---|
| pass_first_try | 0.767 | 0.4 | 0.933 | 0.246 |
| pass_within_3 | 0.817 | 0.4 | 1.0 | 0.279 |
| avg_iterations_to_pass | 1.423 | 1.36 | 1.5 | 0.073 |
| avg_iterations | 1.407 | 1.33 | 1.5 | 0.09 |
| false_approvals | 0.5 | 0 | 1 | 0.577 |
| false_rejections | 0.25 | 0 | 1 | 0.5 |
| rejected_correct_attempts | 3.25 | 2 | 6 | 1.893 |
| pipeline_errors | 2.25 | 0 | 9 | 4.5 |
| mean_wall_seconds | 14.2 | 10.0 | 17.7 | 3.214 |

## Per task

| task | difficulty | run 1 | run 2 | run 3 | run 4 |
|---|---|---|---|---|---|
| e01_fizzbuzz | easy | pass (1 it, 6.0s) | pass (2 it, 30.1s) | pass (2 it, 24.1s) | pass (2 it, 22.1s) |
| e02_palindrome | easy | pass (1 it, 6.0s) | pass (1 it, 8.0s) | pass (1 it, 10.0s) | pass (1 it, 12.0s) |
| e03_second_largest | easy | pass (1 it, 6.0s) | pass (1 it, 12.0s) | pass (1 it, 10.0s) | pass (1 it, 6.0s) |
| e04_word_frequencies | easy | pass (1 it, 6.0s) | pass (1 it, 6.0s) | pass (1 it, 8.0s) | pass (1 it, 10.0s) |
| e05_flatten | easy | pass (1 it, 36.1s) | pass (1 it, 22.1s) | pass (1 it, 20.1s) | pass (1 it, 18.1s) |
| h01_expression_eval | hard | pass (3 it, 24.1s) | pass (3 it, 26.1s) | pass (3 it, 30.1s) | pass (2 it, 28.1s) |
| h02_shortest_path | hard | FAIL (1 it, 6.0s) | FAIL (1 it, 8.0s) | error | pass (3 it, 24.1s) |
| h03_sudoku | hard | pass (1 it, 8.0s) | pass (1 it, 20.1s) | error | pass (1 it, 14.0s) |
| h04_text_justify | hard | pass (3 it, 38.1s) | pass (1 it, 10.0s) | error | pass (2 it, 36.1s) |
| m01_roman | medium | pass (1 it, 10.0s) | pass (1 it, 10.0s) | error | pass (1 it, 8.0s) |
| m02_merge_intervals | medium | pass (1 it, 6.0s) | pass (1 it, 10.0s) | error | pass (1 it, 6.0s) |
| m03_lru_cache | medium | pass (2 it, 30.1s) | pass (2 it, 26.1s) | error | pass (2 it, 22.1s) |
| m04_parse_duration | medium | pass (1 it, 8.0s) | pass (1 it, 10.0s) | error | pass (2 it, 30.1s) |
| m05_balanced_brackets | medium | pass (1 it, 12.0s) | pass (1 it, 10.0s) | error | pass (1 it, 18.1s) |
| m06_top_k_words | medium | pass (1 it, 6.0s) | pass (2 it, 20.0s) | error | pass (1 it, 10.0s) |

## Failures

| run | task | reason |
|---|---|---|
| 1 | h02_shortest_path | AssertionError: shortest_path(..., 'A', 'C') distance inf, expected 0 |
| 2 | h02_shortest_path | AssertionError: shortest_path(..., 'A', 'C') distance inf, expected 0 |
| 3 | h02_shortest_path | pipeline error: gemini failed after 3 attempts: [Errno -2] Name or service not known |
| 3 | h03_sudoku | pipeline error: circuit open, gemini failing (retry in 26s) |
| 3 | h04_text_justify | pipeline error: circuit open, gemini failing (retry in 25s) |
| 3 | m01_roman | pipeline error: circuit open, gemini failing (retry in 23s) |
| 3 | m02_merge_intervals | pipeline error: circuit open, gemini failing (retry in 21s) |
| 3 | m03_lru_cache | pipeline error: circuit open, gemini failing (retry in 19s) |
| 3 | m04_parse_duration | pipeline error: circuit open, gemini failing (retry in 17s) |
| 3 | m05_balanced_brackets | pipeline error: circuit open, gemini failing (retry in 15s) |
| 3 | m06_top_k_words | pipeline error: circuit open, gemini failing (retry in 13s) |
