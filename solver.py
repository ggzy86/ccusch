from ortools.sat.python import cp_model
import random

SHIFTS = ["D", "E", "N"]

def generate_schedule(nurses, rules=None):

    model = cp_model.CpModel()

    n = len(nurses)
    d = 7  # 1주 기준 (일단 MVP)

    x = {}

    # decision variable: nurse x day x shift
    for i in range(n):
        for day in range(d):
            for s in SHIFTS:
                x[(i, day, s)] = model.NewBoolVar(f"x_{i}_{day}_{s}")

    # 하루 1 shift
    for i in range(n):
        for day in range(d):
            model.Add(sum(x[(i, day, s)] for s in SHIFTS) <= 1)

    # shift coverage (최소 인원)
    for day in range(d):
        model.Add(sum(x[(i, day, "D")] for i in range(n)) >= 1)
        model.Add(sum(x[(i, day, "E")] for i in range(n)) >= 1)
        model.Add(sum(x[(i, day, "N")] for i in range(n)) >= 1)

    solver = cp_model.CpSolver()

    # 약간 랜덤성 넣어서 10번 다른 해 나오게
    solver.parameters.random_seed = random.randint(1, 9999)

    status = solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return []

    schedule = []

    for i, nurse in enumerate(nurses):
        for day in range(d):
            for s in SHIFTS:
                if solver.Value(x[(i, day, s)]) == 1:
                    schedule.append({
                        "nurse": nurse["name"],
                        "day": day + 1,
                        "shift": s
                    })

    return schedule
