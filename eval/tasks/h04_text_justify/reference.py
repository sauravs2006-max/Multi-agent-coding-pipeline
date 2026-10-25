def justify(words, width):
    if any(len(w) > width for w in words):
        raise ValueError("a word is longer than the line width")
    lines = []
    i = 0
    while i < len(words):
        j = i
        length = 0
        while j < len(words) and length + len(words[j]) + (j - i) <= width:
            length += len(words[j])
            j += 1
        line_words = words[i:j]
        gaps = len(line_words) - 1
        if j == len(words) or gaps == 0:
            line = " ".join(line_words)
            lines.append(line + " " * (width - len(line)))
        else:
            spaces, extra = divmod(width - length, gaps)
            line = ""
            for k, word in enumerate(line_words[:-1]):
                line += word + " " * (spaces + (1 if k < extra else 0))
            lines.append(line + line_words[-1])
        i = j
    return lines
