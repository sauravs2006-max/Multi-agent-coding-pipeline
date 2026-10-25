import re
from collections import Counter


def word_frequencies(text):
    return dict(Counter(w.lower() for w in re.findall(r"[A-Za-z]+", text)))
