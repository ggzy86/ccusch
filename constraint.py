def is_valid(schedule, rules):
    return len(schedule) > 0


def score(schedule, rules):
    # 간단 점수: 균형 조금만 반영
    d = sum(1 for s in schedule if s["shift"] == "D")
    e = sum(1 for s in schedule if s["shift"] == "E")
    n = sum(1 for s in schedule if s["shift"] == "N")

    balance = max(d, e, n) - min(d, e, n)
    return 100 - balance
