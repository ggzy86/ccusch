from ortools.sat.python import cp_model

def generate_schedule(nurses):

    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    model = cp_model.CpModel()

    days = 7
    shifts = ["D", "E", "N"]

    x = {}
    off = {}

    # ======================
    # 변수 생성
    # ======================
    for i in range(len(nurses)):
        for d in range(days):

            off[(i, d)] = model.NewBoolVar(f"off_{i}_{d}")

            for s in shifts:
                x[(i, d, s)] = model.NewBoolVar(f"x_{i}_{d}_{s}")

    # ======================
    # 1. 하루에 반드시 1개 상태만
    # (D/E/N/OFF 중 하나)
    # ======================
    for i in range(len(nurses)):
        for d in range(days):
            model.Add(
                sum(x[(i, d, s)] for s in shifts) + off[(i, d)] == 1
            )

    # ======================
    # 2. shift당 최소 인원 (임시 안정형)
    # ======================
    for d in range(days):
        for s in shifts:
            model.Add(
                sum(x[(i, d, s)] for i in range(len(nurses))) >= 1
            )

    # ======================
    # solver
    # ======================
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    schedule = []

    for i, n in enumerate(nurses):
        for d in range(days):

            if solver.Value(off[(i, d)]) == 1:
                continue

            for s in shifts:
                if solver.Value(x[(i, d, s)]) == 1:
                    schedule.append({
                        "nurse": n["name"],
                        "day": d + 1,
                        "shift": s
                    })

    return schedule
