import re

PATTERN = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(s):
    match = PATTERN.fullmatch(s)
    if not s or not match:
        raise ValueError(f"bad duration: {s!r}")
    hours, minutes, seconds = (int(part) if part else 0 for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds
