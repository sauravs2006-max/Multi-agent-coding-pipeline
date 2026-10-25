from solution import fizzbuzz

expected = ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]
assert fizzbuzz(15) == expected, f"fizzbuzz(15) gave {fizzbuzz(15)}"
assert fizzbuzz(0) == [], "fizzbuzz(0) should be []"
assert fizzbuzz(1) == ["1"]
assert len(fizzbuzz(100)) == 100
assert fizzbuzz(100)[-1] == "Buzz"
assert fizzbuzz(90)[-1] == "FizzBuzz"

try:
    fizzbuzz(-1)
    raise AssertionError("fizzbuzz(-1) should raise ValueError")
except ValueError:
    pass
