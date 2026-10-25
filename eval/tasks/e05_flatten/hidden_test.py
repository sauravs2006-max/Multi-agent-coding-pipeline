from solution import flatten

cases = [
    ([1, [2, [3, [4]]], 5], [1, 2, 3, 4, 5]),
    ([], []),
    ([[], [[]]], []),
    ([1, (2, 3), [4]], [1, (2, 3), 4]),
    (["ab", ["cd"]], ["ab", "cd"]),
    ([None, [False, [0]]], [None, False, 0]),
]
for nested, want in cases:
    got = flatten(nested)
    assert got == want, f"flatten({nested!r}) gave {got!r}, expected {want!r}"

deep = [1]
for _ in range(100):
    deep = [deep]
assert flatten(deep) == [1], "failed on 100 levels of nesting"

original = [1, [2, 3]]
flatten(original)
assert original == [1, [2, 3]], "input was modified"
