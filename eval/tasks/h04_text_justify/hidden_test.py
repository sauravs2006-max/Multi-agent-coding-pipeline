from solution import justify

cases = [
    (["This", "is", "an", "example", "of", "text", "justification."], 16,
     ["This    is    an", "example  of text", "justification.  "]),
    (["What", "must", "be", "acknowledgment", "shall", "be"], 16,
     ["What   must   be", "acknowledgment  ", "shall be        "]),
    (["Science", "is", "what", "we", "understand", "well", "enough", "to", "explain", "to", "a",
      "computer.", "Art", "is", "everything", "else", "we", "do"], 20,
     ["Science  is  what we", "understand      well", "enough to explain to", "a  computer.  Art is",
      "everything  else  we", "do                  "]),
    (["hello"], 5, ["hello"]),
    (["a", "b", "c"], 1, ["a", "b", "c"]),
    ([], 10, []),
    (["a", "b", "c", "d"], 3, ["a b", "c d"]),
    (["ab", "c", "d", "e"], 6, ["ab c d", "e     "]),
]
for words, width, want in cases:
    got = justify(list(words), width)
    assert got == want, f"justify({words}, {width}) gave {got!r}, expected {want!r}"

text = ("the quick brown fox jumps over the lazy dog and keeps on running far away "
        "into the woods where nobody can find it anymore").split()
for width in range(9, 40):
    lines = justify(text, width)
    assert all(len(line) == width for line in lines), f"width {width}: a line has the wrong length"
    assert " ".join(" ".join(lines).split()) == " ".join(text), f"width {width}: words changed or reordered"

try:
    justify(["toolongword"], 5)
    raise AssertionError("a word longer than width should raise ValueError")
except ValueError:
    pass
