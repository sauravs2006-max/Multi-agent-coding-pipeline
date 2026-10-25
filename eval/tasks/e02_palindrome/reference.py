def is_palindrome(s):
    chars = [c.lower() for c in s if c.isalnum()]
    return chars == chars[::-1]
