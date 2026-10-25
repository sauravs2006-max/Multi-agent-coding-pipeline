import copy

from solution import merge_intervals

cases = [
    ([[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 6], [8, 10], [15, 18]]),
    ([[1, 4], [4, 5]], [[1, 5]]),
    ([], []),
    ([[5, 6], [1, 2]], [[1, 2], [5, 6]]),
    ([[1, 10], [2, 3]], [[1, 10]]),
    ([[1, 1]], [[1, 1]]),
    ([[3, 5], [1, 2], [2, 3]], [[1, 5]]),
    ([[-5, -1], [-2, 0], [2, 3]], [[-5, 0], [2, 3]]),
]
for intervals, want in cases:
    before = copy.deepcopy(intervals)
    got = merge_intervals(intervals)
    assert [list(x) for x in got] == want, f"merge_intervals({before}) gave {got}, expected {want}"
    assert intervals == before, "input was modified"
