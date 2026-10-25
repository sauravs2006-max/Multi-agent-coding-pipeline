# Eval results

3 run(s) of 15 tasks.
Note: combined from eval_20261025_075240.json, eval_20261025_081956.json; left out run(s) 3.

## Summary

| metric | mean | min | max | stdev |
|---|---|---|---|---|
| pass_first_try | 0.889 | 0.867 | 0.933 | 0.038 |
| pass_within_3 | 0.955 | 0.933 | 1.0 | 0.039 |
| avg_iterations_to_pass | 1.397 | 1.36 | 1.47 | 0.064 |
| avg_iterations | 1.377 | 1.33 | 1.47 | 0.081 |
| false_approvals | 0.667 | 0 | 1 | 0.577 |
| false_rejections | 0.333 | 0 | 1 | 0.577 |
| rejected_correct_attempts | 3.667 | 2 | 6 | 2.082 |
| pipeline_errors | 0 | 0 | 0 | 0.0 |
| mean_wall_seconds | 15.6 | 13.9 | 17.7 | 1.931 |

## Per task

| task | difficulty | run 1 | run 2 | run 4 |
|---|---|---|---|---|
| e01_fizzbuzz | easy | pass (1 it, 6.0s) | pass (2 it, 30.1s) | pass (2 it, 22.1s) |
| e02_palindrome | easy | pass (1 it, 6.0s) | pass (1 it, 8.0s) | pass (1 it, 12.0s) |
| e03_second_largest | easy | pass (1 it, 6.0s) | pass (1 it, 12.0s) | pass (1 it, 6.0s) |
| e04_word_frequencies | easy | pass (1 it, 6.0s) | pass (1 it, 6.0s) | pass (1 it, 10.0s) |
| e05_flatten | easy | pass (1 it, 36.1s) | pass (1 it, 22.1s) | pass (1 it, 18.1s) |
| h01_expression_eval | hard | pass (3 it, 24.1s) | pass (3 it, 26.1s) | pass (2 it, 28.1s) |
| h02_shortest_path | hard | FAIL (1 it, 6.0s) | FAIL (1 it, 8.0s) | pass (3 it, 24.1s) |
| h03_sudoku | hard | pass (1 it, 8.0s) | pass (1 it, 20.1s) | pass (1 it, 14.0s) |
| h04_text_justify | hard | pass (3 it, 38.1s) | pass (1 it, 10.0s) | pass (2 it, 36.1s) |
| m01_roman | medium | pass (1 it, 10.0s) | pass (1 it, 10.0s) | pass (1 it, 8.0s) |
| m02_merge_intervals | medium | pass (1 it, 6.0s) | pass (1 it, 10.0s) | pass (1 it, 6.0s) |
| m03_lru_cache | medium | pass (2 it, 30.1s) | pass (2 it, 26.1s) | pass (2 it, 22.1s) |
| m04_parse_duration | medium | pass (1 it, 8.0s) | pass (1 it, 10.0s) | pass (2 it, 30.1s) |
| m05_balanced_brackets | medium | pass (1 it, 12.0s) | pass (1 it, 10.0s) | pass (1 it, 18.1s) |
| m06_top_k_words | medium | pass (1 it, 6.0s) | pass (2 it, 20.0s) | pass (1 it, 10.0s) |

## Failures

| run | task | reason |
|---|---|---|
| 1 | h02_shortest_path | AssertionError: shortest_path(..., 'A', 'C') distance inf, expected 0 |
| 2 | h02_shortest_path | AssertionError: shortest_path(..., 'A', 'C') distance inf, expected 0 |
