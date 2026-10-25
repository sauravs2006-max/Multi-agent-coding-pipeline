def second_largest(nums):
    distinct = sorted(set(nums), reverse=True)
    return distinct[1] if len(distinct) >= 2 else None
