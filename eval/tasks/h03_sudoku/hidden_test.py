import copy

from solution import solve_sudoku

puzzle = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]
solution = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

original = copy.deepcopy(puzzle)
got = solve_sudoku(puzzle)
assert got is not None, "returned None for a solvable puzzle"
assert [list(row) for row in got] == solution, "wrong solution"
assert puzzle == original, "input board was modified"

assert [list(row) for row in solve_sudoku(copy.deepcopy(solution))] == solution, "already solved board"

broken = copy.deepcopy(puzzle)
broken[0][2] = 5  # row 0 now has two 5s
assert solve_sudoku(broken) is None, "givens break the rules, should be None"

# no duplicates, but the top-left cell can't be anything: 2-9 are in its row, 1 is in its column
stuck = [[0] * 9 for _ in range(9)]
stuck[0] = [0, 2, 3, 4, 5, 6, 7, 8, 9]
stuck[1][0] = 1
assert solve_sudoku(stuck) is None, "unsolvable board should be None"
