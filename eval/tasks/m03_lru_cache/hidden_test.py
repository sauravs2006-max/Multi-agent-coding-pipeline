import time

from solution import LRUCache

cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1
cache.put(3, 3)  # evicts 2, because 1 was just used
assert cache.get(2) == -1, "key 2 should have been evicted"
cache.put(4, 4)  # evicts 1
assert cache.get(1) == -1, "key 1 should have been evicted"
assert cache.get(3) == 3
assert cache.get(4) == 4

cache = LRUCache(2)
cache.put("a", 1)
cache.put("b", 2)
cache.put("a", 10)  # update counts as use, so b is now the oldest
cache.put("c", 3)
assert cache.get("b") == -1, "update should count as use"
assert cache.get("a") == 10
assert cache.get("c") == 3

cache = LRUCache(1)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == -1
assert cache.get(2) == 2
assert cache.get(99) == -1

for bad in (0, -3):
    try:
        LRUCache(bad)
        raise AssertionError(f"LRUCache({bad}) should raise ValueError")
    except ValueError:
        pass

start = time.perf_counter()
cache = LRUCache(1000)
for i in range(200_000):
    cache.put(i, i)
    cache.get(i - 500)
took = time.perf_counter() - start
assert took < 5, f"200k operations took {took:.1f}s, not O(1)"
