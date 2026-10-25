VALUES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def int_to_roman(n):
    if not 1 <= n <= 3999:
        raise ValueError("out of range")
    out = []
    for value, symbol in VALUES:
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


def roman_to_int(s):
    letters = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not s or any(c not in letters for c in s):
        raise ValueError(f"not a roman numeral: {s!r}")
    total = 0
    for i, c in enumerate(s):
        value = letters[c]
        if i + 1 < len(s) and letters[s[i + 1]] > value:
            total -= value
        else:
            total += value
    if not 1 <= total <= 3999 or int_to_roman(total) != s:
        raise ValueError(f"not canonical: {s!r}")
    return total
