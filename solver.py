import random

SHIFTS = ["D", "E", "N"]

def generate_schedule(nurses, rules):
    schedule = []

    if not nurses:
        return schedule

    for nurse in nurses:
        name = nurse["name"] if isinstance(nurse, dict) else str(nurse)

        schedule.append({
            "nurse": name,
            "shift": random.choice(SHIFTS)
        })

    return schedule
