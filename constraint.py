def score(schedule, rules=None):

    if not schedule:
        return 0

    score = 100

    # shift balance scoring
    d = sum(1 for s in schedule if s["shift"] == "D")
    e = sum(1 for s in schedule if s["shift"] == "E")
    n = sum(1 for s in schedule if s["shift"] == "N")

    # fairness penalty
    diff = max(d, e, n) - min(d, e, n)
    score -= diff * 2

    return score
