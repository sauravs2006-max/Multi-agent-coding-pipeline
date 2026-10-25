from solution import is_balanced

cases = {
    "": True, "()": True, "([]{})": True, "a(b)c": True, "{[()()]}": True, "no brackets": True,
    "(]": False, "((": False, ")(": False, "([)]": False, "}": False, "(": False,
    "[(])": False, "((a)": False, "{[]}()": True, "x)(": False,
}
for text, want in cases.items():
    got = is_balanced(text)
    assert got is want, f"is_balanced({text!r}) gave {got!r}, expected {want}"

assert is_balanced("(" * 5000 + ")" * 5000) is True
assert is_balanced("(" * 5000 + ")" * 4999) is False
