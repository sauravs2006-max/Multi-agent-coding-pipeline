from solution import word_frequencies

cases = [
    ("Hello, hello world!", {"hello": 2, "world": 1}),
    ("", {}),
    ("123 !!!", {}),
    ("Don't stop", {"don": 1, "t": 1, "stop": 1}),
    ("a-b a", {"a": 2, "b": 1}),
    ("CamelCase", {"camelcase": 1}),
    ("one1two2three", {"one": 1, "two": 1, "three": 1}),
    ("  spaced   out  ", {"spaced": 1, "out": 1}),
]
for text, want in cases:
    got = word_frequencies(text)
    assert dict(got) == want, f"word_frequencies({text!r}) gave {got!r}, expected {want!r}"
