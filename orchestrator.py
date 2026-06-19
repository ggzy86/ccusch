from solver import generate_schedule
import random

def run_simulation(nurses, rules=None, runs=10):  # ← 핵심 수정

    best_schedule = None
    best_score = -1

    for _ in range(runs):

        schedule = generate_schedule(nurses, rules)

        if not schedule:
            continue

        # 아주 단순 점수 (임시)
        score = len(schedule)

        if score > best_score:
            best_score = score
            best_schedule = schedule

    if best_schedule is None:
        return []

    return best_schedule
