def is_valid(schedule, rules=None):
    return True


def score(schedule, rules=None):
    if not schedule:
        return 0

    d = sum(1 for s in schedule if s["shift"] == "D")
    e = sum(1 for s in schedule if s["shift"] == "E")
    n = sum(1 for s in schedule if s["shift"] == "N")

    return 100 - max(d, e, n)
