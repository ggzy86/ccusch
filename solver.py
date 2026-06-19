from ortools.sat.python import cp_model

def generate_schedule(nurses):

    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    model = cp_model.CpModel()

    days = 7
    shifts = ["D", "E", "N"]

    x = {}

    # 변수 생성
    for i in range(len(nurses)):
        for d in range(days):
            for s in shifts:
                x[(i, d, s)] = model.NewBoolVar(f"x_{i}_{d}_{s}")

    # 1. 간호사 하루 1 shift
    for i in range(len(nurses)):
        for d in range(days):
            model.Add(sum(x[(i, d, s)] for s in shifts) <= 1)

    # 2. 최소 staffing (핵심 안정화)
    # 👉 각 shift마다 최소 1명만 보장 (과도한 constraint 방지)
    for d in range(days):
        for s in shifts:
            model.Add(
                sum(x[(i, d, s)] for i in range(len(nurses))) >= 1
            )

    solver = cp_model.CpSolver()

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
