from solver import generate_schedule

def run_simulation(nurses, rules=None, runs=10):

    print("\n===== RUN_SIMULATION START =====")
    print("nurses:", len(nurses) if nurses else 0)
    print("rules:", rules)
    print("runs:", runs)

    best_schedule = None
    best_score = -1

    for i in range(runs):

        print(f"\n--- RUN {i+1} START ---")

        try:
            schedule = generate_schedule(nurses, rules)

            print("schedule type:", type(schedule))
            print("schedule length:", len(schedule) if schedule else 0)

        except Exception as e:
            print("❌ generate_schedule ERROR:", str(e))
            continue

        # ✔ 안전 방어
        if schedule is None:
            print("schedule is None → skip")
            continue

        if not isinstance(schedule, list):
            print("schedule not list → skip")
            continue

        if len(schedule) == 0:
            print("empty schedule → skip")
            continue

        # ✔ 점수 (현재는 단순 feasibility 기반)
        score = len(schedule)
        print("score:", score)

        if score > best_score:
            best_score = score
            best_schedule = schedule

            print("🔥 NEW BEST FOUND")

    print("\n===== FINAL RESULT =====")

    if best_schedule is None:
        print("❌ NO VALID SCHEDULE FOUND")
        return []

    print("✅ BEST SCORE:", best_score)
    print("schedule sample:", best_schedule[:5])

    return best_schedule
