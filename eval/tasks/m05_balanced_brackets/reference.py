PAIRS = {")": "(", "]": "[", "}": "{"}


def is_balanced(s):
    stack = []
    for c in s:
        if c in "([{":
            stack.append(c)
        elif c in PAIRS:
            if not stack or stack.pop() != PAIRS[c]:
                return False
    return not stack
