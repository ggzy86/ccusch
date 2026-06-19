from ortools.sat.python import cp_model
import random

SHIFTS = ["D", "E", "N"]

def generate_schedule(nurses, rules=None):

    # 🔒 입력 방어
    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    model = cp_model.CpModel()

    n = len(nurses)
    days = 7

    x = {}

    for i in range(n):
        for d in range(days):
            for s in SHIFTS:
                x[(i, d, s)] = model.NewBoolVar(f"x_{i}_{d}_{s}")

    # 하루 1 shift
    for i in range(n):
        for d in range(days):
            model.Add(sum(x[(i, d, s)] for s in SHIFTS) <= 1)

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = random.randint(1, 9999)

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    schedule = []

    for i, nurse in enumerate(nurses):
        for d in range(days):
            for s in SHIFTS:
                if solver.Value(x[(i, d, s)]) == 1:
                    schedule.append({
                        "nurse": nurse.get("name", f"Nurse{i}"),
                        "day": d + 1,
                        "shift": s
                    })

    return schedule
