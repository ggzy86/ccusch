from solver import generate_schedule

def run_simulation(nurses, rules=None, runs=10):

    print("ORCHESTRATOR START")

    best = None
    best_score = -1

    # runs 안전 보장
    try:
        runs = int(runs)
    except:
        runs = 10

    for i in range(runs):

        print("run:", i+1)

        schedule = generate_schedule(nurses, rules)

        print("type:", type(schedule))

        if not isinstance(schedule, list):
            continue

        if len(schedule) == 0:
            continue

        score = len(schedule)

        if score > best_score:
            best_score = score
            best = schedule

    return best if best else []
