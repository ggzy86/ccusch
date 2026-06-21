import datetime as _dt

from ortools.sat.python import cp_model

try:
    import holidays as _holidays_lib
except ImportError:  # pip install holidays 안 돼있으면 공휴일 자동인식 없이 동작(에러 안 남)
    _holidays_lib = None

FTE_RATIO = {
    "full": 1.0, "0.8": 0.8, "0.6": 0.6, "0.4": 0.4, "0.2": 0.2,
    "bank": 0.3, "casual": 0.3,
}
CONTRACT_FTE_KEYS = {"full", "0.8", "0.6", "0.4", "0.2"}  # 계약시간 강제 적용 대상 (뱅크/캐주얼 제외)

# ---- 듀티 종류 ----
# D/E/N : 8시간 듀티 (07-15 / 15-23 / 23-07)
# LD    : 12시간 롱데이 (07-19) — D+E 합친 개념의 혼합듀티
# LN    : 12시간 롱나이트 (19-07) — E+N 합친 개념의 혼합듀티
SHIFTS = ["D", "E", "N", "LD", "LN"]
ALL_STATES = SHIFTS + ["OFF"]
ALL_STATES_SET = set(ALL_STATES)

NIGHT_TIER = {"N", "LN"}
DAY_TIER = {"D", "LD"}
DAY_EVE_TIER = ["D", "E", "LD"]
NIGHT_TIER_LIST = ["N", "LN"]

TIER = {"D": 1, "LD": 1, "E": 2, "N": 3, "LN": 3}

MIN_PER_SHIFT = {"D": 4, "E": 4, "N": 3}  # LD/LN은 최소인원 강제 없음
ABSOLUTE_MAX_CONSEC_DAYS = 6  # 룰북과 무관하게 항상 적용되는 절대 상한(어떤 듀티든 합쳐서)

SHIFT_HOURS = {"D": 8, "E": 8, "N": 8, "LD": 12, "LN": 12}
STANDARD_WEEKLY_HOURS = 38   # 풀타임 기준 주당 근무시간. 병원 정책에 맞게 조정 가능
DEFAULT_DAYS = 14            # 2주 스케줄 기본값

GROUP_OPTIONS = ["bedside", "leadership"]
DEFAULT_LEADERSHIP_PENALTY_WEIGHT = 10
DEFAULT_HOLIDAY_BANK_PENALTY_WEIGHT = 10  # 캐주얼은 이 값의 2배

WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]  # date.weekday(): 0=월 ... 6=일

# 스케줄표/Nurse 페이지 듀티 선택 UI가 공유하는 단일 색상 소스 (저채도 파스텔)
SHIFT_COLORS = {
    "D": "#7A9ED2",    # Day - 파랑
    "E": "#D2A87A",    # Evening - 주황
    "N": "#A496C6",    # Night - 보라
    "LD": "#77C591",   # Long Day(12h) - 초록
    "LN": "#B2774D",   # Long Night(12h) - 갈색
    "OFF": "#DA9090",  # Rest Day - 빨강
}

# 듀티 종료 ~ 다음날 듀티 시작까지의 휴식시간(시간 단위)
REST_HOURS_TABLE = {
    ("D", "D"): 16, ("D", "E"): 24, ("D", "N"): 32, ("D", "LD"): 16, ("D", "LN"): 28,
    ("E", "D"): 8,  ("E", "E"): 16, ("E", "N"): 24, ("E", "LD"): 8,  ("E", "LN"): 20,
    ("N", "D"): 0,  ("N", "E"): 8,  ("N", "N"): 16, ("N", "LD"): 0,  ("N", "LN"): 12,
    ("LD", "D"): 12, ("LD", "E"): 20, ("LD", "N"): 28, ("LD", "LD"): 12, ("LD", "LN"): 24,
    ("LN", "D"): 0,  ("LN", "E"): 8,  ("LN", "N"): 16, ("LN", "LD"): 0,  ("LN", "LN"): 12,
}


def required_hours(fte, days=DEFAULT_DAYS):
    """FTE/스케줄 기간에 따른 필요(계약) 근무시간. days=14면 2주 기준."""
    ratio = FTE_RATIO.get(fte, 1.0)
    weeks = days / 7
    return round(STANDARD_WEEKLY_HOURS * weeks * ratio)


def build_calendar(days, start_date):
    """start_date 기준으로 각 날짜의 요일(0=월~6=일)과 호주(VIC) 공휴일 여부를 계산.
    start_date가 없으면 weekday는 0(월)부터 시작한다고 가정하고 공휴일은 없음으로 처리."""
    if start_date is None:
        return list(range(days)), [d % 7 for d in range(days)], set()

    dates = [start_date + _dt.timedelta(days=d) for d in range(days)]
    weekday_of_day = [dt.weekday() for dt in dates]

    holiday_days = set()
    if _holidays_lib is not None:
        years = sorted({dt.year for dt in dates})
        try:
            au_hols = _holidays_lib.country_holidays("AU", subdiv="VIC", years=years)
        except Exception:
            au_hols = {}
        holiday_days = {d for d, dt in enumerate(dates) if dt in au_hols}

    return dates, weekday_of_day, holiday_days


def _get_rule(rules, rule_id):
    """같은 rule_id가 여러 개 있으면 가장 마지막(최신)으로 추가된 것을 사용.
    (wanted_shift처럼 여러 개를 동시에 써야 하는 룰은 이 함수를 쓰지 않고 직접 필터링한다.)"""
    if not rules:
        return None
    matches = [r for r in rules if isinstance(r, dict) and r.get("rule_id") == rule_id]
    return matches[-1] if matches else None


def _rule_param(rule, key, default):
    if not rule:
        return default
    try:
        val = rule.get("params", {}).get(key, default)
        return default if val is None else val
    except AttributeError:
        return default


def _rule_hardness(rule, default_weight=10, default_hard=True):
    """rule이 없으면 default_hard를 따른다. 있으면 rule의 type(hard/soft)을 따른다."""
    if not rule:
        return default_hard, default_weight
    is_hard = rule.get("type", "hard") != "soft"
    weight = rule.get("weight") or default_weight
    return is_hard, weight


def _classify_transition(today, nxt, ctx):
    """오늘(today) -> 내일(nxt) 전이가 어떤 룰에 의해 막히는지 판정.
    여러 룰이 동시에 막을 수 있는데, 그중 하나라도 hard면 전체를 hard로 처리하고,
    전부 soft면 soft 룰들의 weight를 합산한다.
    반환: None(허용) 또는 (hard: bool, weight: int)
    """
    if today == "OFF" or nxt == "OFF":
        return None

    reasons = []

    if REST_HOURS_TABLE[(today, nxt)] < ctx["min_rest_hours"]:
        reasons.append((ctx["rest_hard"], ctx["rest_weight"]))

    if ctx["block_n2d"] and today in NIGHT_TIER and nxt in DAY_TIER:
        reasons.append((ctx["n2d_hard"], ctx["n2d_weight"]))

    if ctx["block_n2e"] and today in NIGHT_TIER and nxt == "E":
        reasons.append((ctx["n2e_hard"], ctx["n2e_weight"]))

    if ctx["block_e2d"] and today == "E" and nxt in DAY_TIER:
        reasons.append((ctx["e2d_hard"], ctx["e2d_weight"]))

    if ctx["forward_only"] and TIER[nxt] < TIER[today]:
        reasons.append((ctx["forward_hard"], ctx["forward_weight"]))

    if not reasons:
        return None

    hard = any(h for h, _ in reasons)
    weight = sum(w for h, w in reasons if not h)
    if weight <= 0:
        weight = 10
    return hard, weight


def generate_schedule(
    nurses,
    rules=None,
    days=DEFAULT_DAYS,
    start_date=None,
    holiday_days=None,
    weekday_of_day=None,
    time_limit=30,
    skip_leadership=False,
    disable_contracted_hours=False,
    disable_absolute_cap=False,
):
    """간호사/룰북을 받아 CP-SAT으로 스케줄을 생성.
    start_date가 주어지면 실제 달력(요일, 호주 VIC 공휴일)을 자동 계산해서
    '가능한 요일' 제약과 '공휴일 배치 우선순위' 룰에 사용한다.
    diagnose_infeasibility()에서 내부적으로 일부 제약을 끄기 위해
    skip_leadership / disable_contracted_hours / disable_absolute_cap 플래그를 쓴다."""
    if not isinstance(nurses, list) or len(nurses) == 0:
        return []

    rules = rules if isinstance(rules, list) else []

    n_nurses = len(nurses)

    if n_nurses < sum(MIN_PER_SHIFT.values()):
        return []

    if weekday_of_day is None or holiday_days is None:
        _, auto_weekday, auto_holiday = build_calendar(days, start_date)
        if weekday_of_day is None:
            weekday_of_day = auto_weekday
        if holiday_days is None:
            holiday_days = auto_holiday

    model = cp_model.CpModel()
    objective_penalties = []  # soft 룰 위반/충족에 대한 가중 항목들 (목적함수에 더해짐)

    # y[i,d,state]: 그날의 상태 (D/E/N/LD/LN/OFF 중 정확히 1개)
    y = {}
    for i in range(n_nurses):
        for d in range(days):
            for st_ in ALL_STATES:
                y[(i, d, st_)] = model.NewBoolVar(f"y_{i}_{d}_{st_}")
            model.AddExactlyOne(y[(i, d, st_)] for st_ in ALL_STATES)

    x = {(i, d, s): y[(i, d, s)] for i in range(n_nurses) for d in range(days) for s in SHIFTS}

    # ---- Hard: shift별 최소 인원 (D/E/N만. LD/LN은 강제 최소인원 없음) ----
    for d in range(days):
        for s in SHIFTS:
            if s in MIN_PER_SHIFT:
                model.Add(sum(x[(i, d, s)] for i in range(n_nurses)) >= MIN_PER_SHIFT[s])

    # ---- Hard: 간호사 프로필의 '가능 듀티'(available_shifts) ----
    for i, n in enumerate(nurses):
        avail = n.get("available_shifts")
        if avail is None:
            avail = SHIFTS
        if isinstance(avail, list):
            for s in SHIFTS:
                if s not in avail:
                    for d in range(days):
                        model.Add(x[(i, d, s)] == 0)

    # ---- Hard: 간호사 프로필의 '가능한 요일'(available_weekdays) ----
    # 미지정(None)이면 전부 가능으로 간주(하위호환). 지정돼 있으면 그 요일이 아닌 날은 무조건 OFF.
    for i, n in enumerate(nurses):
        avail_wd = n.get("available_weekdays")
        if isinstance(avail_wd, list) and len(avail_wd) > 0:
            avail_wd_set = set(avail_wd)
            for d in range(days):
                if weekday_of_day[d] not in avail_wd_set:
                    model.Add(y[(i, d, "OFF")] == 1)

    # ======================================================================
    # 룰북: 듀티 간 전이 제약
    # ======================================================================
    rule_min_rest = _get_rule(rules, "min_rest_between_shifts")
    rule_n2d = _get_rule(rules, "no_night_to_day")
    rule_n2e = _get_rule(rules, "no_night_to_evening")
    rule_e2d = _get_rule(rules, "no_evening_to_day")
    rule_forward = _get_rule(rules, "forward_rotation_only")

    rest_hard, rest_weight = _rule_hardness(rule_min_rest, default_hard=True)
    n2d_hard, n2d_weight = _rule_hardness(rule_n2d, default_hard=True)
    n2e_hard, n2e_weight = _rule_hardness(rule_n2e, default_hard=True)
    e2d_hard, e2d_weight = _rule_hardness(rule_e2d, default_hard=True)
    forward_hard, forward_weight = _rule_hardness(rule_forward, default_hard=True)

    ctx = {
        "min_rest_hours": _rule_param(rule_min_rest, "hours", 10),
        "rest_hard": rest_hard, "rest_weight": rest_weight,
        "block_n2d": rule_n2d is not None, "n2d_hard": n2d_hard, "n2d_weight": n2d_weight,
        "block_n2e": rule_n2e is not None, "n2e_hard": n2e_hard, "n2e_weight": n2e_weight,
        "block_e2d": rule_e2d is not None, "e2d_hard": e2d_hard, "e2d_weight": e2d_weight,
        "forward_only": rule_forward is not None, "forward_hard": forward_hard, "forward_weight": forward_weight,
    }

    for i in range(n_nurses):
        for d in range(days - 1):
            for st_today in ALL_STATES:
                for st_next in ALL_STATES:
                    verdict = _classify_transition(st_today, st_next, ctx)
                    if verdict is None:
                        continue
                    hard, weight = verdict
                    if hard:
                        model.Add(y[(i, d, st_today)] + y[(i, d + 1, st_next)] <= 1)
                    else:
                        viol = model.NewBoolVar(f"trans_viol_{i}_{d}_{st_today}_{st_next}")
                        model.Add(y[(i, d, st_today)] + y[(i, d + 1, st_next)] <= 1 + viol)
                        objective_penalties.append(-weight * viol)

    # ======================================================================
    # 룰북: min_rest_after_night_block — 연속 나이트(N/LN) 블록 종료 후 최소 휴식시간(기본 48h=2일)
    # ======================================================================
    rule_post_night = _get_rule(rules, "min_rest_after_night_block")
    post_night_hours = _rule_param(rule_post_night, "hours", 48)
    try:
        post_night_days = max(1, round(float(post_night_hours) / 24))
    except (TypeError, ValueError):
        post_night_days = 2
    post_night_hard, post_night_weight = _rule_hardness(rule_post_night, default_hard=True)

    night_var = {}
    for i in range(n_nurses):
        for d in range(days):
            nv = model.NewBoolVar(f"nighttier_{i}_{d}")
            model.Add(nv == x[(i, d, "N")] + x[(i, d, "LN")])
            night_var[(i, d)] = nv

    for i in range(n_nurses):
        for d in range(days - 1):
            block_end = model.NewBoolVar(f"night_end_{i}_{d}")
            model.Add(night_var[(i, d)] == 1).OnlyEnforceIf(block_end)
            model.Add(night_var[(i, d + 1)] == 0).OnlyEnforceIf(block_end)
            model.AddBoolOr([night_var[(i, d)].Not(), night_var[(i, d + 1)], block_end])
            for offset in range(2, 2 + post_night_days):
                req_day = d + offset
                if req_day >= days:
                    continue
                if post_night_hard:
                    model.Add(y[(i, req_day, "OFF")] == 1).OnlyEnforceIf(block_end)
                else:
                    viol = model.NewBoolVar(f"postnight_viol_{i}_{d}_{offset}")
                    model.Add(y[(i, req_day, "OFF")] + viol >= 1).OnlyEnforceIf(block_end)
                    objective_penalties.append(-post_night_weight * viol)

    # ======================================================================
    # 룰북: max_consecutive_nights (N/LN 묶음, 기본 4) /
    #       max_consecutive_day_evening (D/E/LD 묶음, 기본 6)
    # ======================================================================
    rule_max_n = _get_rule(rules, "max_consecutive_nights")
    max_nights = max(0, int(_rule_param(rule_max_n, "max_days", 4)))
    nights_hard, nights_weight = _rule_hardness(rule_max_n, default_hard=True)

    for i in range(n_nurses):
        for d in range(days - max_nights):
            window = [x[(i, dd, s)] for dd in range(d, d + max_nights + 1) for s in NIGHT_TIER_LIST]
            if nights_hard:
                model.Add(sum(window) <= max_nights)
            else:
                slack = model.NewIntVar(0, len(window), f"night_slack_{i}_{d}")
                model.Add(sum(window) <= max_nights + slack)
                objective_penalties.append(-nights_weight * slack)

    rule_max_de = _get_rule(rules, "max_consecutive_day_evening")
    max_de = max(0, int(_rule_param(rule_max_de, "max_days", 6)))
    de_hard, de_weight = _rule_hardness(rule_max_de, default_hard=True)

    for i in range(n_nurses):
        for d in range(days - max_de):
            window = [x[(i, dd, s)] for dd in range(d, d + max_de + 1) for s in DAY_EVE_TIER]
            if de_hard:
                model.Add(sum(window) <= max_de)
            else:
                slack = model.NewIntVar(0, len(window), f"de_slack_{i}_{d}")
                model.Add(sum(window) <= max_de + slack)
                objective_penalties.append(-de_weight * slack)

    # ---- Hard, 항상 적용 (룰북과 무관): 듀티 종류 섞여도 총 연속근무일은 절대 6일 초과 불가 ----
    if not disable_absolute_cap:
        for i in range(n_nurses):
            for d in range(days - ABSOLUTE_MAX_CONSEC_DAYS):
                window = [
                    x[(i, dd, s)]
                    for dd in range(d, d + ABSOLUTE_MAX_CONSEC_DAYS + 1)
                    for s in SHIFTS
                ]
                model.Add(sum(window) <= ABSOLUTE_MAX_CONSEC_DAYS)

    # ======================================================================
    # 룰북: cluster_off_days — 단독(1일) 오프 패널티/최소 연속오프 블록 강제 (선택 룰, 기본 OFF)
    # ======================================================================
    rule_cluster = _get_rule(rules, "cluster_off_days")
    if rule_cluster is not None:
        min_block = max(1, int(_rule_param(rule_cluster, "min_block", 2)))
        cluster_hard, cluster_weight = _rule_hardness(rule_cluster, default_hard=False)

        if min_block >= 2:
            for i in range(n_nurses):
                for d in range(days):
                    if d == 0:
                        block_start = y[(i, 0, "OFF")]
                    else:
                        block_start = model.NewBoolVar(f"offstart_{i}_{d}")
                        model.Add(y[(i, d, "OFF")] == 1).OnlyEnforceIf(block_start)
                        model.Add(y[(i, d - 1, "OFF")] == 0).OnlyEnforceIf(block_start)
                        model.AddBoolOr([y[(i, d, "OFF")].Not(), y[(i, d - 1, "OFF")], block_start])
                    for offset in range(1, min_block):
                        req_day = d + offset
                        if req_day >= days:
                            continue
                        if cluster_hard:
                            model.Add(y[(i, req_day, "OFF")] == 1).OnlyEnforceIf(block_start)
                        else:
                            viol = model.NewBoolVar(f"cluster_viol_{i}_{d}_{offset}")
                            model.Add(y[(i, req_day, "OFF")] + viol >= 1).OnlyEnforceIf(block_start)
                            objective_penalties.append(-cluster_weight * viol)

    # ======================================================================
    # 리더십/베드사이드: 듀티에 사람이 배치되면 리더십 최소 1명 보장(구조적, 항상 적용,
    # leadership 그룹 간호사가 0명이면 스킵). 2명 이상 몰리면 leadership_overlap_penalty로 패널티.
    # ======================================================================
    leadership_idx = [i for i, n in enumerate(nurses) if n.get("group") == "leadership"]

    rule_lead_overlap = _get_rule(rules, "leadership_overlap_penalty")
    lead_hard, lead_weight = _rule_hardness(
        rule_lead_overlap, default_weight=DEFAULT_LEADERSHIP_PENALTY_WEIGHT, default_hard=False
    )

    if leadership_idx and not skip_leadership:
        for d in range(days):
            for s in SHIFTS:
                total_expr = sum(x[(i, d, s)] for i in range(n_nurses))
                lead_expr = sum(x[(i, d, s)] for i in leadership_idx)

                staffed = model.NewBoolVar(f"staffed_{d}_{s}")
                model.Add(total_expr >= 1).OnlyEnforceIf(staffed)
                model.Add(total_expr == 0).OnlyEnforceIf(staffed.Not())
                model.Add(lead_expr >= 1).OnlyEnforceIf(staffed)

                if lead_hard:
                    model.Add(lead_expr <= 1)
                else:
                    over = model.NewBoolVar(f"leadover_{d}_{s}")
                    model.Add(lead_expr >= 2).OnlyEnforceIf(over)
                    model.Add(lead_expr <= 1).OnlyEnforceIf(over.Not())
                    overflow = model.NewIntVar(0, n_nurses, f"leadoverflow_{d}_{s}")
                    model.Add(overflow == 0).OnlyEnforceIf(over.Not())
                    model.Add(overflow == lead_expr).OnlyEnforceIf(over)
                    objective_penalties.append(-lead_weight * overflow)

    # ======================================================================
    # 룰북: holiday_staffing_priority — 공휴일은 풀타임/파트타임 우선, 뱅크/캐주얼 배치 패널티
    # (캐주얼은 뱅크의 2배). 기본 soft(가중치 10/20)로 항상 적용, 룰 등록시 가중치/hard 조정 가능.
    # ======================================================================
    rule_holiday = _get_rule(rules, "holiday_staffing_priority")
    holiday_hard, holiday_bank_weight = _rule_hardness(
        rule_holiday, default_weight=DEFAULT_HOLIDAY_BANK_PENALTY_WEIGHT, default_hard=False
    )
    holiday_casual_weight = holiday_bank_weight * 2

    if holiday_days:
        for i, n in enumerate(nurses):
            fte = n.get("fte", "full")
            if fte not in ("bank", "casual"):
                continue
            weight = holiday_casual_weight if fte == "casual" else holiday_bank_weight
            for d in holiday_days:
                if d < 0 or d >= days:
                    continue
                working_expr = sum(x[(i, d, s)] for s in SHIFTS)
                if holiday_hard:
                    model.Add(working_expr == 0)
                else:
                    objective_penalties.append(-weight * working_expr)

    # ======================================================================
    # 룰북: wanted_shift — 간호사 이름 + 날짜 + 희망 근무 (여러 개 동시 등록 가능)
    # ======================================================================
    wanted_rules = [r for r in rules if isinstance(r, dict) and r.get("rule_id") == "wanted_shift"]
    name_to_idx = {n["name"]: i for i, n in enumerate(nurses)}

    for r in wanted_rules:
        params = r.get("params", {}) or {}
        name = params.get("nurse_name")
        day = params.get("day")
        shift = params.get("shift")
        if name not in name_to_idx or shift not in ALL_STATES:
            continue
        try:
            d = int(day) - 1
        except (TypeError, ValueError):
            continue
        if d < 0 or d >= days:
            continue
        i = name_to_idx[name]
        hard, weight = _rule_hardness(r, default_hard=False)
        if hard:
            model.Add(y[(i, d, shift)] == 1)
        else:
            objective_penalties.append(weight * y[(i, d, shift)])

    # ---- Hard, 항상 적용: 풀타임/파트타임은 계약 근무시간을 반드시 다 채워야 함 (뱅크/캐주얼 제외) ----
    total_hours_vars = []
    for i, n in enumerate(nurses):
        hours_expr = sum(x[(i, d, s)] * SHIFT_HOURS[s] for d in range(days) for s in SHIFTS)
        hrs = model.NewIntVar(0, days * 12, f"hours_{i}")
        model.Add(hrs == hours_expr)
        total_hours_vars.append(hrs)

        fte = n.get("fte", "full")
        if not disable_contracted_hours and fte in CONTRACT_FTE_KEYS:
            model.Add(hrs >= required_hours(fte, days))

    # ---- Hard: FTE 기반 최대 근무일수(시프트 개수 상한, 대략치) ----
    total_shifts = []
    for i, n in enumerate(nurses):
        ratio = FTE_RATIO.get(n.get("fte", "full"), 1.0)
        cap = max(1, round(days * ratio * 0.75))
        t = model.NewIntVar(0, days, f"total_{i}")
        model.Add(t == sum(x[(i, d, s)] for d in range(days) for s in SHIFTS))
        model.Add(t <= cap)
        total_shifts.append(t)

    # ---- 목표 함수 ----
    max_load = model.NewIntVar(0, days, "max_load")
    model.AddMaxEquality(max_load, total_shifts)

    PREF_CAP = 10
    pref_terms = []
    no_pref_bonus_terms = []
    for i, n in enumerate(nurses):
        pref = n.get("preferred_shift")
        if pref in SHIFTS:
            raw_match = sum(x[(i, d, pref)] for d in range(days))
            capped = model.NewIntVar(0, PREF_CAP, f"pref_capped_{i}")
            model.Add(capped <= raw_match)
            pref_terms.append(capped)
        else:
            no_pref_bonus_terms.append(days - total_shifts[i])

    LOAD_WEIGHT = 10
    PREF_WEIGHT = 3
    NO_PREF_WEIGHT = 1

    objective_terms = [-LOAD_WEIGHT * max_load]
    if pref_terms:
        objective_terms.append(PREF_WEIGHT * sum(pref_terms))
    if no_pref_bonus_terms:
        objective_terms.append(NO_PREF_WEIGHT * sum(no_pref_bonus_terms))
    if objective_penalties:
        objective_terms.append(sum(objective_penalties))

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)

    print("STATUS:", solver.StatusName(status))  # 디버깅용, 그대로 둠

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    schedule = []
    for i, n in enumerate(nurses):
        for d in range(days):
            for st_ in ALL_STATES:
                if solver.Value(y[(i, d, st_)]) == 1:
                    schedule.append({"nurse": n["name"], "day": d + 1, "shift": st_})
                    break

    return schedule


def diagnose_infeasibility(nurses, rules=None, days=DEFAULT_DAYS, start_date=None, time_limit=4):
    """RUN SCHEDULE이 실패했을 때 어떤 조건을 완화하면 풀릴 가능성이 있는지 빠르게(짧은 time_limit)
    하나씩 꺼보면서 확인. 100% 정확한 진단은 아니고(시간 제한 안에서의 추정), 참고용 힌트.
    """
    rules = rules if isinstance(rules, list) else []

    if not isinstance(nurses, list) or len(nurses) == 0:
        return ["간호사가 한 명도 없음 — Nurse 페이지에서 간호사를 추가해줘."]
    if len(nurses) < sum(MIN_PER_SHIFT.values()):
        return [
            f"간호사 수가 너무 적음(현재 {len(nurses)}명, 최소 {sum(MIN_PER_SHIFT.values())}명 필요) — "
            "Nurse 페이지에서 간호사를 더 추가해줘."
        ]

    def without(rule_id):
        return [r for r in rules if r.get("rule_id") != rule_id]

    def replaced(rule_id, params, rule_type="soft", weight=1):
        nr = without(rule_id)
        nr.append({"id": -1, "rule_id": rule_id, "type": rule_type, "params": params, "weight": weight})
        return nr

    candidates = [
        ("'모든 듀티 사이 최소 휴식시간'을 완화", replaced("min_rest_between_shifts", {"hours": 0}, "hard")),
        ("'나이트 후 최소 휴식시간'을 완화", replaced("min_rest_after_night_block", {"hours": 0}, "hard")),
        ("'나이트 최대연속일수' 제한을 완화", replaced("max_consecutive_nights", {"max_days": days}, "hard")),
        ("'데이/이브 최대연속일수' 제한을 완화", replaced("max_consecutive_day_evening", {"max_days": days}, "hard")),
        ("'나이트 다음날 데이 금지' 규칙을 제거", without("no_night_to_day")),
        ("'나이트 다음날 이브닝 금지' 규칙을 제거", without("no_night_to_evening")),
        ("'이브닝 다음날 데이 금지' 규칙을 제거", without("no_evening_to_day")),
        ("'Forward Rotation 강제' 규칙을 제거", without("forward_rotation_only")),
        ("'휴무 몰아주기' 규칙을 제거", without("cluster_off_days")),
        ("'공휴일 뱅크/캐주얼 배치 금지(hard)'를 soft로 변경", replaced("holiday_staffing_priority", {}, "soft", 1)),
        ("'리더십 중복배치 금지(hard)'를 soft로 변경", replaced("leadership_overlap_penalty", {}, "soft", 1)),
    ]

    suggestions = []
    for desc, cand_rules in candidates:
        try:
            sched = generate_schedule(nurses, cand_rules, days=days, start_date=start_date, time_limit=time_limit)
        except Exception:
            continue
        if sched:
            suggestions.append(desc)

    structural_checks = [
        ("듀티당 '리더십 1명 필수' 조건을 일시 해제 — 리더십 그룹 인원을 늘리는 걸 고려",
         {"skip_leadership": True}),
        ("'풀타임/파트타임 계약시간 무조건 채우기' 조건을 일시 해제 — 계약시간 충족이 빡빡한 상태",
         {"disable_contracted_hours": True}),
        ("'절대 최대연속근무 6일' 제한을 일시 해제", {"disable_absolute_cap": True}),
    ]
    for desc, kwargs in structural_checks:
        try:
            sched = generate_schedule(nurses, rules, days=days, start_date=start_date, time_limit=time_limit, **kwargs)
        except Exception:
            continue
        if sched:
            suggestions.append(desc)

    if not suggestions:
        suggestions.append(
            "개별 조건을 하나씩 풀어봐도 안 풀림 — 간호사 수를 늘리거나, 여러 조건을 동시에 완화해야 할 가능성이 높음."
        )

    return suggestions
