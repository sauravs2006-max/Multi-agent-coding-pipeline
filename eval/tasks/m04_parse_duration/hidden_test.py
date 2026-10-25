from solution import parse_duration

cases = {"1h30m15s": 5415, "45s": 45, "2h": 7200, "1h0m5s": 3605, "10m": 600, "0s": 0,
         "1h1s": 3601, "100m": 6000, "36h": 129600}
for text, want in cases.items():
    got = parse_duration(text)
    assert got == want, f"parse_duration({text!r}) gave {got!r}, expected {want}"
    assert isinstance(got, int), f"parse_duration({text!r}) should return an int"

for bad in ("", "30m1h", "1h1h", "5d", "h", "1.5h", "-5s", "1h 30m", "90", "1s1m", "m5", " 5s", "5S"):
    try:
        parse_duration(bad)
        raise AssertionError(f"parse_duration({bad!r}) should raise ValueError")
    except ValueError:
        pass
