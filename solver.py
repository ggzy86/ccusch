from ortools.sat.python import cp_model
import random

def generate_schedule(nurses, rules=None):

    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    model = cp_model.CpModel()

    days = 7
    shifts = ["D", "E", "N"]

    x = {}

    for i in range(len(nurses)):
        for d in range(days):
            for s in shifts:
                x[(i, d, s)] = model.NewBoolVar(f"x_{i}_{d}_{s}")

    # 하루 1 shift
    for i in range(len(nurses)):
        for d in range(days):
            model.Add(sum(x[(i, d, s)] for s in shifts) <= 1)

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = random.randint(1, 9999)

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    schedule = []

    for i, n in enumerate(nurses):
        for d in range(days):
            for s in shifts:
                if solver.Value(x[(i, d, s)]) == 1:
                    schedule.append({
                        "nurse": n["name"],
                        "day": d + 1,
                        "shift": s
                    })

    return schedule
