from solution import top_k_frequent

words = ["i", "love", "leetcode", "i", "love", "coding"]
assert top_k_frequent(words, 2) == ["i", "love"], top_k_frequent(words, 2)
assert top_k_frequent(words, 3) == ["i", "love", "coding"], top_k_frequent(words, 3)

words = ["the", "day", "is", "sunny", "the", "the", "the", "sunny", "is", "is"]
assert top_k_frequent(words, 4) == ["the", "is", "sunny", "day"], top_k_frequent(words, 4)

assert top_k_frequent(["b", "a", "c"], 2) == ["a", "b"]
assert top_k_frequent(["x"], 5) == ["x"]
assert top_k_frequent(["a", "b"], 0) == []
assert top_k_frequent([], 3) == []
assert top_k_frequent(["A", "a", "a"], 2) == ["a", "A"]

try:
    top_k_frequent(["a"], -1)
    raise AssertionError("k < 0 should raise ValueError")
except ValueError:
    pass
