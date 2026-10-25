from solution import is_palindrome

cases = {
    "A man, a plan, a canal: Panama": True,
    "race a car": False,
    "": True,
    "   ": True,
    "No 'x' in Nixon": True,
    "0P": False,
    "ab_a": True,
    "Was it a car or a cat I saw?": True,
    "12321": True,
    "123": False,
    "Aa": True,
    "ab": False,
}
for text, want in cases.items():
    got = is_palindrome(text)
    assert got is want, f"is_palindrome({text!r}) gave {got!r}, expected {want}"
