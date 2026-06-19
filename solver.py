from ortools.sat.python import cp_model

SHIFTS = ["D", "E", "N"]

def generate_schedule(nurses, rules):
    model = cp_model.CpModel()

    num_nurses = len(nurses)
    num_shifts = len(SHIFTS)

    # decision variable: nurse x shift (binary)
    x = {}

    for i in range(num_nurses):
        for j in range(num_shifts):
            x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")

    # constraint 1: each nurse gets exactly 1 shift
    for i in range(num_nurses):
        model.Add(sum(x[(i, j)] for j in range(num_shifts)) == 1)

    # constraint 2: shift balance (optional)
    if "max_per_shift" in rules:
        for j in range(num_shifts):
            model.Add(
                sum(x[(i, j)] for i in range(num_nurses)) <= rules["max_per_shift"]
            )

    # objective: balance (minimize difference)
    shift_counts = []
    for j in range(num_shifts):
        shift_counts.append(sum(x[(i, j)] for i in range(num_nurses)))

    max_shift = model.NewIntVar(0, num_nurses, "max_shift")
    min_shift = model.NewIntVar(0, num_nurses, "min_shift")

    model.AddMaxEquality(max_shift, shift_counts)
    model.AddMinEquality(min_shift, shift_counts)

    model.Minimize(max_shift - min_shift)

    # solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return []

    schedule = []

    for i, nurse in enumerate(nurses):
        for j, shift in enumerate(SHIFTS):
            if solver.Value(x[(i, j)]) == 1:
                name = nurse["name"] if isinstance(nurse, dict) else str(nurse)
                schedule.append({
                    "nurse": name,
                    "shift": shift
                })

    return schedule
