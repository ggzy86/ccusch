from solver import generate_schedule

def run_simulation(nurses, rules=None, runs=10):

    print("\n===== ORCHESTRATOR START =====")
    print("nurses:", len(nurses) if nurses else 0)
    print("runs:", runs)

    # runs 안전 보정
    try:
        runs = int(runs)
    except:
        runs = 10

    best_schedule = None
    best_score = -1

    for i in range(runs):

        print(f"\n--- SIM {i+1} ---")

        schedule = None

        try:
            schedule = generate_schedule(nurses, rules)
        except Exception as e:
            print("SOLVER ERROR:", e)
            continue

        print("type:", type(schedule))
        print("len:", len(schedule) if schedule else 0)

        if not schedule or not isinstance(schedule, list):
            continue

        score = len(schedule)

        if score > best_score:
            best_score = score
            best_schedule = schedule
            print("NEW BEST SCORE:", best_score)

    print("\n===== FINAL =====")

    if best_schedule is None:
        print("NO SCHEDULE FOUND")
        return []

    print("BEST SCORE:", best_score)

    return best_schedule
