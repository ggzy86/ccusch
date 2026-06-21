from solver import generate_schedule, diagnose_infeasibility


def run_simulation(nurses, rules=None, runs=1, **solver_kwargs):
    """runs=1이 기본값. 예전엔 10번 돌려서 '제일 긴 스케줄'을 골랐는데, 매일 모든 간호사가
    정확히 1개 상태를 갖는 구조라 스케줄 길이가 항상 동일해서 10번 돌리는 의미가 없었음.
    이제는 1번만 돌리고, solver_kwargs로 days/start_date/holiday_days/weekday_of_day/
    time_limit 등을 그대로 generate_schedule에 전달한다."""

    print("ORCHESTRATOR START")

    best = None
    best_score = -1

    try:
        runs = int(runs)
    except (TypeError, ValueError):
        runs = 1
    runs = max(1, runs)

    for i in range(runs):
        print("run:", i + 1)

        schedule = generate_schedule(nurses, rules, **solver_kwargs)

        print("type:", type(schedule))

        if not isinstance(schedule, list) or len(schedule) == 0:
            continue

        score = len(schedule)
        if score > best_score:
            best_score = score
            best = schedule

    return best if best else []


def diagnose(nurses, rules=None, **solver_kwargs):
    """RUN SCHEDULE이 실패했을 때 호출 — 어떤 조건을 완화하면 풀릴지 후보를 알려준다."""
    return diagnose_infeasibility(nurses, rules, **solver_kwargs)
