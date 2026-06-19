from solver import generate_schedule

def run_simulation(nurses, rules=None, runs=10):

    best_schedule = None
    best_score = -1

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        # ✔ 방어코드 (핵심)
        if schedule is None or len(schedule) == 0:
            continue

        score = len(schedule)

        if score > best_score:
            best_score = score
            best_schedule = schedule

    # ✔ 최종 방어
    if best_schedule is None or len(best_schedule) == 0:
        return []

    return best_schedule
