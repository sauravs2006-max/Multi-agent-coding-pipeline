import copy


def _candidates(board, r, c):
    used = set(board[r]) | {board[i][c] for i in range(9)}
    br, bc = 3 * (r // 3), 3 * (c // 3)
    used |= {board[i][j] for i in range(br, br + 3) for j in range(bc, bc + 3)}
    return [d for d in range(1, 10) if d not in used]


def _givens_ok(board):
    for r in range(9):
        for c in range(9):
            value = board[r][c]
            if value:
                board[r][c] = 0
                ok = value in _candidates(board, r, c)
                board[r][c] = value
                if not ok:
                    return False
    return True


def _solve(board):
    # fill the cell with the fewest options first, so dead ends show up early
    best = None
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                options = _candidates(board, r, c)
                if best is None or len(options) < len(best[2]):
                    best = (r, c, options)
    if best is None:
        return True
    r, c, options = best
    for d in options:
        board[r][c] = d
        if _solve(board):
            return True
    board[r][c] = 0
    return False


def solve_sudoku(board):
    work = copy.deepcopy(board)
    if not _givens_ok(work):
        return None
    return work if _solve(work) else None
