from collections import Counter


def top_k_frequent(words, k):
    if k < 0:
        raise ValueError("k must not be negative")
    counts = Counter(words)
    return sorted(counts, key=lambda w: (-counts[w], w))[:k]
