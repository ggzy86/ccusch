from ortools.sat.python import cp_model

def generate_schedule(nurses, rules=None):
    """
    OR-Tools schedule generator (Streamlit compatible)
    rules는 아직 미사용 (placeholder)
    """

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

    # 하루 1 shift max
    for i in range(len(nurses)):
        for d in range(days):
            model.Add(sum(x[(i, d, s)] for s in shifts) <= 1)

    # 하루 최소 커버 (아주 기본 constraint)
    for d in range(days):
        model.Add(sum(x[(i, d, s)] for i in range(len(nurses)) for s in shifts) >= 1)

    solver = cp_model.CpSolver()

    status = solver.Solve(model)

    print("STATUS:", solver.StatusName(status))

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
