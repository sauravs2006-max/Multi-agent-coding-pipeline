import heapq
import itertools
import math


def shortest_path(graph, start, end):
    if start == end:
        return 0, [start]
    counter = itertools.count()  # tie breaker, nodes don't have to be comparable
    best = {start: 0}
    previous = {}
    heap = [(0, next(counter), start)]
    while heap:
        distance, _, node = heapq.heappop(heap)
        if node == end:
            path = [end]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return distance, path[::-1]
        if distance > best.get(node, math.inf):
            continue
        for neighbour, weight in graph.get(node, {}).items():
            new_distance = distance + weight
            if new_distance < best.get(neighbour, math.inf):
                best[neighbour] = new_distance
                previous[neighbour] = node
                heapq.heappush(heap, (new_distance, next(counter), neighbour))
    return math.inf, []
