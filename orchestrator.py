from solver import generate_schedule
from constraint import score

def run_simulation(nurses, rules=None, runs=10):

    results = []

    if not isinstance(nurses, list):
        return []

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        if not isinstance(schedule, list) or len(schedule) == 0:
            continue

        results.append({
            "schedule": schedule,
            "score": score(schedule, rules)
        })

    if len(results) == 0:
        return []

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:2]
