from solution import second_largest

cases = [
    ([1, 2, 3], 2),
    ([3, 3, 2], 2),
    ([5], None),
    ([], None),
    ([2, 2], None),
    ([-1, -5, -3], -3),
    ([10, 10, 9, 8], 9),
    ([7, 1, 7, 1], 1),
    ([0, -1], -1),
]
for nums, want in cases:
    got = second_largest(list(nums))
    assert got == want, f"second_largest({nums}) gave {got!r}, expected {want!r}"

data = [4, 1, 3]
second_largest(data)
assert data == [4, 1, 3], "input list was modified"
