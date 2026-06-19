def score(schedule, rules=None):

    if not isinstance(schedule, list):
        return 0

    if len(schedule) == 0:
        return 0

    d = sum(1 for x in schedule if x["shift"] == "D")
    e = sum(1 for x in schedule if x["shift"] == "E")
    n = sum(1 for x in schedule if x["shift"] == "N")

    return max(0, 100 - abs(d - e) - abs(e - n))
