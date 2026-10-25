def _tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
        elif c in "+-*/()":
            tokens.append(c)
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
                j += 1
            try:
                tokens.append(float(expr[i:j]))
            except ValueError:
                raise ValueError(f"bad number {expr[i:j]!r}") from None
            i = j
        else:
            raise ValueError(f"unexpected character {c!r}")
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self):
        token = self.peek()
        self.pos += 1
        return token

    def expression(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            if self.take() == "+":
                value += self.term()
            else:
                value -= self.term()
        return value

    def term(self):
        value = self.factor()
        while self.peek() in ("*", "/"):
            if self.take() == "*":
                value *= self.factor()
            else:
                value /= self.factor()
        return value

    def factor(self):
        token = self.take()
        if token == "-":
            return -self.factor()
        if token == "(":
            value = self.expression()
            if self.take() != ")":
                raise ValueError("missing )")
            return value
        if isinstance(token, float):
            return token
        raise ValueError(f"unexpected {token!r}")


def evaluate(expr):
    parser = _Parser(_tokenize(expr))
    value = parser.expression()
    if parser.peek() is not None:
        raise ValueError(f"unexpected {parser.peek()!r}")
    return value
