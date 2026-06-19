from solver import generate_schedule
from constraint import is_valid, score

def run_simulation(n=10, nurses=None, rules=None):
    results = []

    for _ in range(n):
        s = generate_schedule(nurses, rules)

        if is_valid(s, rules):
            results.append((s, score(s, rules)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]
