from solver import generate_schedule

def run_simulation(nurses, rules=None, runs=10):

    best_schedule = None
    best_score = -1

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        # ✔ 타입 강제 방어
        if not isinstance(schedule, list):
            continue

        if len(schedule) == 0:
            continue

        score = len(schedule)

        if score > best_score:
            best_score = score
            best_schedule = schedule

    if not isinstance(best_schedule, list) or len(best_schedule) == 0:
        return []

    return best_schedule
