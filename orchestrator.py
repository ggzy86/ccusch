from solver import generate_schedule
from constraint import score

def run_simulation(nurses, rules=None, runs=10):

    results = []

    # 🔒 입력 방어
    if not isinstance(nurses, list):
        return []

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        # 🔒 타입 고정
        if not isinstance(schedule, list):
            continue

        results.append({
            "schedule": schedule,
            "score": score(schedule, rules)
        })

    if len(results) == 0:
        return []

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:2]
