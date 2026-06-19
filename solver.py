from ortools.sat.python import cp_model

SHIFTS = ["D", "E", "N"]

def generate_schedule(nurses, rules=None):
    model = cp_model.CpModel()

    if not nurses:
        return []

    n = len(nurses)
    s = len(SHIFTS)

    x = {}

    for i in range(n):
        for j in range(s):
            x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")

    for i in range(n):
        model.Add(sum(x[(i, j)] for j in range(s)) == 1)

    if rules and "max_per_shift" in rules:
        for j in range(s):
            model.Add(
                sum(x[(i, j)] for i in range(n)) <= int(rules["max_per_shift"])
            )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return []

    schedule = []

    for i, nurse in enumerate(nurses):
        name = nurse["name"]

        for j, shift in enumerate(SHIFTS):
            if solver.Value(x[(i, j)]) == 1:
                schedule.append({
                    "nurse": name,
                    "shift": shift
                })

    return schedule
