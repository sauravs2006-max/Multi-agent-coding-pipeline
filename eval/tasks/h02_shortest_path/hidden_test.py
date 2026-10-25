import math

from solution import shortest_path


def check(graph, start, end, want_distance, want_path=None):
    distance, path = shortest_path(graph, start, end)
    assert math.isclose(distance, want_distance) if want_distance != math.inf else distance == math.inf, \
        f"shortest_path(..., {start!r}, {end!r}) distance {distance!r}, expected {want_distance!r}"
    if want_path is not None:
        assert list(path) == want_path, f"path {path!r}, expected {want_path!r}"
    if want_distance != math.inf:
        assert path[0] == start and path[-1] == end, f"path {path!r} doesn't go from {start} to {end}"
        cost = sum(graph[a][b] for a, b in zip(path, path[1:]))
        assert math.isclose(cost, distance), f"path {path!r} costs {cost}, not {distance}"


graph = {"A": {"B": 1, "C": 4}, "B": {"C": 2, "D": 5}, "C": {"D": 1}, "D": {}}
check(graph, "A", "D", 4, ["A", "B", "C", "D"])
check(graph, "A", "A", 0, ["A"])
check(graph, "D", "A", math.inf, [])
check(graph, "A", "E", math.inf, [])
check(graph, "E", "E", 0, ["E"])
check({"A": {"B": 1}}, "B", "A", math.inf, [])
check({"A": {"B": 0}, "B": {"C": 0}}, "A", "C", 0, ["A", "B", "C"])
check({"A": {"B": 0.5, "C": 2}, "B": {"C": 0.5}}, "A", "C", 1.0, ["A", "B", "C"])
check({"S": {"A": 1, "T": 10}, "A": {"B": 1}, "B": {"T": 1}}, "S", "T", 3, ["S", "A", "B", "T"])
check({1: {2: 7, 3: 9, 6: 14}, 2: {3: 10, 4: 15}, 3: {4: 11, 6: 2}, 4: {5: 6}, 6: {5: 9}}, 1, 5, 20, [1, 3, 6, 5])

# 40x40 grid, moving right or down costs 1, so the corner is 78 away by many equal paths
grid = {}
for r in range(40):
    for c in range(40):
        grid[(r, c)] = {}
        if r + 1 < 40:
            grid[(r, c)][(r + 1, c)] = 1
        if c + 1 < 40:
            grid[(r, c)][(r, c + 1)] = 1
check(grid, (0, 0), (39, 39), 78)
