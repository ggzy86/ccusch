from solver import generate_schedule
from constraint import score

def run_simulation(nurses, rules=None, runs=10):

    results = []

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        if not schedule:
            continue

        results.append({
            "schedule": schedule,
            "score": score(schedule, rules)
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:2]
