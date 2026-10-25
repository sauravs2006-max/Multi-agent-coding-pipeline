from solution import int_to_roman, roman_to_int

assert int_to_roman(1994) == "MCMXCIV", int_to_roman(1994)
assert int_to_roman(3999) == "MMMCMXCIX"
assert int_to_roman(4) == "IV"
assert int_to_roman(58) == "LVIII"
assert roman_to_int("LVIII") == 58
assert roman_to_int("MCMXCIV") == 1994

for n in range(1, 4000):
    assert roman_to_int(int_to_roman(n)) == n, f"round trip failed for {n}"

for bad in (0, 4000, -5):
    try:
        int_to_roman(bad)
        raise AssertionError(f"int_to_roman({bad}) should raise ValueError")
    except ValueError:
        pass

for bad in ("", "IIII", "VV", "IC", "IIX", "mcm", "ABC", "MMMM", "XM", "VX", "CMM"):
    try:
        roman_to_int(bad)
        raise AssertionError(f"roman_to_int({bad!r}) should raise ValueError")
    except ValueError:
        pass
