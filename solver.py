from ortools.sat.python import cp_model

def generate_schedule(nurses, rules=None):  # ✔ 핵심: orchestrator랑 시그니처 맞춤

    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    model = cp_model.CpModel()

    days = 7
    shifts = ["D", "E", "N"]

    x = {}
    off = {}

    # =========================
    # 변수 생성
    # =========================
    for i in range(len(nurses)):
        for d in range(days):

            off[(i, d)] = model.NewBoolVar(f"off_{i}_{d}")

            for s in shifts:
                x[(i, d, s)] = model.NewBoolVar(f"x_{i}_{d}_{s}")

    # =========================
    # 하루에 하나만 (근무 or OFF)
    # =========================
    for i in range(len(nurses)):
        for d in range(days):
            model.Add(
                sum(x[(i, d, s)] for s in shifts) + off[(i, d)] == 1
            )

    # =========================
    # shift 최소 인원 (안정 버전)
    # =========================
    for d in range(days):
        for s in shifts:
            model.Add(
                sum(x[(i, d, s)] for i in range(len(nurses))) >= 1
            )

    # =========================
    # solver
    # =========================
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2

    status = solver.Solve(model)

    # =========================
    # DEBUG (여기서 바로 확인)
    # =========================
    print("STATUS:", solver.StatusName(status))
    print("OBJECTIVE:", solver.ObjectiveValue())

    # =========================
    # 결과
    # =========================
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
