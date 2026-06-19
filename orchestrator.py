from solver import generate_schedule
from constraint import is_valid, score

def run_simulation(n=10, nurses=None, rules=None):
    nurses = nurses or []
    results = []

    for _ in range(n):
        s = generate_schedule(nurses, rules)

        if is_valid(s, rules):
            results.append({
                "schedule": s,
                "score": score(s, rules)
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]
