import streamlit as st

st.title("📋 룰북 관리")

SHIFT_CHOICES = ["D", "E", "N", "LD", "LN", "OFF"]

# param_specs의 type: "int" | "nurse" | "day" | "shift_choice"
RULE_CATALOG = {
    "min_rest_between_shifts": {
        "label": "모든 듀티 사이 최소 휴식시간(시간)",
        "desc": "어떤 듀티든 끝난 뒤 다음 듀티 시작까지 보장할 최소 휴식시간. 기본 10시간.",
        "param_specs": [{"key": "hours", "label": "최소 휴식시간(시간)", "type": "int", "default": 10}],
    },
    "min_rest_after_night_block": {
        "label": "연속 나이트(N/LN) 종료 후 최소 휴식시간(시간)",
        "desc": "2개 이상 연속된 나이트 듀티가 끝난 직후 보장할 최소 오프 시간. 기본 48시간(=2일).",
        "param_specs": [{"key": "hours", "label": "최소 휴식시간(시간)", "type": "int", "default": 48}],
    },
    "max_consecutive_nights": {
        "label": "나이트(N/LN) 최대 연속 근무일",
        "desc": "N 또는 LN을 합쳐서 며칠까지 연속으로 일할 수 있는지. 기본 4일.",
        "param_specs": [{"key": "max_days", "label": "최대 연속일수", "type": "int", "default": 4}],
    },
    "max_consecutive_day_evening": {
        "label": "데이/이브닝(D/E/LD) 최대 연속 근무일",
        "desc": "D, E, LD를 합쳐서 며칠까지 연속으로 일할 수 있는지. 기본 6일.",
        "param_specs": [{"key": "max_days", "label": "최대 연속일수", "type": "int", "default": 6}],
    },
    "no_night_to_day": {
        "label": "나이트 다음날 데이 금지",
        "desc": "N/LN 다음날 D/LD 배정 금지.",
        "param_specs": [],
    },
    "no_night_to_evening": {
        "label": "나이트 다음날 이브닝 금지",
        "desc": "N/LN 다음날 E 배정 금지.",
        "param_specs": [],
    },
    "no_evening_to_day": {
        "label": "이브닝 다음날 데이 금지",
        "desc": "E 다음날 D/LD 배정 금지.",
        "param_specs": [],
    },
    "forward_rotation_only": {
        "label": "혼합듀티 Forward Rotation 강제",
        "desc": "D/LD → E → N/LN 방향(정방향)만 허용, 역행 전이는 전부 금지.",
        "param_specs": [],
    },
    "cluster_off_days": {
        "label": "휴무 몰아주기 (단독 1일 오프 패널티/금지)",
        "desc": "오프가 시작되면 최소 N일은 연속으로 쉬도록. 미등록 시 적용 안 함(선택 규칙).",
        "param_specs": [{"key": "min_block", "label": "최소 연속 오프 블록(일)", "type": "int", "default": 2}],
    },
    "leadership_overlap_penalty": {
        "label": "리더십 중복배치 패널티 가중치",
        "desc": "듀티당 리더십 1명 필수는 항상 적용됨. 이 룰은 2명 이상 몰릴 때의 패널티 강도(soft) "
        "또는 절대 금지(hard) 여부만 조정.",
        "param_specs": [],
    },
    "holiday_staffing_priority": {
        "label": "공휴일 배치 우선순위 (풀타임/파트타임 우선, 뱅크/캐주얼 패널티)",
        "desc": "공휴일에 뱅크가 들어가면 패널티, 캐주얼이 들어가면 그 2배 패널티. "
        "등록 안 해도 기본 soft(가중치 10/20)로 항상 적용됨. hard로 바꾸면 뱅크/캐주얼 공휴일 배치 자체를 금지.",
        "param_specs": [],
    },
    "wanted_shift": {
        "label": "희망 근무 요청 (이름+날짜+근무)",
        "desc": "특정 간호사의 특정 날짜에 원하는 근무를 직접 지정. 여러 개 등록 가능.",
        "param_specs": [
            {"key": "nurse_name", "label": "간호사", "type": "nurse"},
            {"key": "day", "label": "날짜(1~28일차)", "type": "day"},
            {"key": "shift", "label": "희망 근무", "type": "shift_choice"},
        ],
    },
}

DEFAULT_WEIGHTS = {
    "min_rest_between_shifts": 10, "min_rest_after_night_block": 10,
    "max_consecutive_nights": 10, "max_consecutive_day_evening": 10,
    "no_night_to_day": 10, "no_night_to_evening": 10, "no_evening_to_day": 10,
    "forward_rotation_only": 10, "cluster_off_days": 10,
    "leadership_overlap_penalty": 10, "holiday_staffing_priority": 10, "wanted_shift": 10,
}


def render_param_input(spec):
    key, label, ptype = spec["key"], spec["label"], spec["type"]
    if ptype == "int":
        return st.number_input(label, value=spec.get("default", 1), step=1)
    if ptype == "nurse":
        names = [n["name"] for n in st.session_state.nurses]
        if not names:
            st.warning("Nurse 페이지에서 간호사를 먼저 등록해줘.")
            return None
        return st.selectbox(label, names)
    if ptype == "day":
        return st.number_input(label, min_value=1, max_value=28, value=1, step=1)
    if ptype == "shift_choice":
        return st.selectbox(label, SHIFT_CHOICES)
    return None


def format_params(rule):
    spec_list = RULE_CATALOG.get(rule["rule_id"], {}).get("param_specs", [])
    if not spec_list:
        return ""
    parts = [f"{spec['label']}={rule['params'].get(spec['key'])}" for spec in spec_list]
    return " · ".join(parts)


with st.form("add_rule_form", clear_on_submit=True):
    rule_id = st.selectbox(
        "규칙 종류", list(RULE_CATALOG.keys()), format_func=lambda k: RULE_CATALOG[k]["label"]
    )
    st.caption(RULE_CATALOG[rule_id]["desc"])

    rule_type = st.radio("타입", ["hard", "soft"], horizontal=True)
    weight = (
        st.number_input("점수 가중치 (soft일 때만)", value=DEFAULT_WEIGHTS.get(rule_id, 10), step=1)
        if rule_type == "soft"
        else None
    )

    params = {}
    for spec in RULE_CATALOG[rule_id]["param_specs"]:
        params[spec["key"]] = render_param_input(spec)

    submitted = st.form_submit_button("규칙 추가")
    if submitted:
        # nurse 타입 파라미터가 없는데(간호사 미등록) 제출된 경우는 무시
        missing_required = any(
            params.get(spec["key"]) is None
            for spec in RULE_CATALOG[rule_id]["param_specs"]
            if spec["type"] == "nurse"
        )
        if missing_required:
            st.error("간호사를 먼저 등록한 뒤 다시 시도해줘.")
        else:
            st.session_state.rules.append(
                {
                    "id": st.session_state.next_rule_id,
                    "rule_id": rule_id,
                    "type": rule_type,
                    "params": params,
                    "weight": weight,
                }
            )
            st.session_state.next_rule_id += 1
            st.rerun()

st.divider()
st.subheader(f"등록된 규칙 {len(st.session_state.rules)}개")

for rule in list(st.session_state.rules):
    cols = st.columns([4, 2, 1])
    with cols[0]:
        param_str = format_params(rule)
        suffix = f" — {param_str}" if param_str else ""
        st.write(f"**{RULE_CATALOG[rule['rule_id']]['label']}**{suffix}")
    with cols[1]:
        tag = "🔒 hard" if rule["type"] == "hard" else f"🟡 soft (가중치 {rule['weight']})"
        st.write(tag)
    with cols[2]:
        if st.button("삭제", key=f"delrule_{rule['id']}"):
            st.session_state.rules = [r for r in st.session_state.rules if r["id"] != rule["id"]]
            st.rerun()

st.divider()
st.success("✅ 등록된 규칙은 RUN SCHEDULE 실행 시 solver.py에서 실제 CP-SAT 제약/패널티로 적용됨.")

st.subheader("📌 적용된 규칙 모음")
hard_tab, soft_tab = st.tabs([
    f"🔒 Hard ({sum(1 for r in st.session_state.rules if r['type'] == 'hard')})",
    f"🟡 Soft ({sum(1 for r in st.session_state.rules if r['type'] == 'soft')})",
])

with hard_tab:
    hard_rules = [r for r in st.session_state.rules if r["type"] == "hard"]
    if not hard_rules:
        st.caption(
            "등록된 hard 규칙 없음 (룰북 등록과 무관하게 항상 자동 적용되는 안전장치/구조적 규칙들:\n"
            "・ 모든 듀티 사이 최소 휴식 10시간\n"
            "・ 나이트 종료 후 최소 48시간 휴식\n"
            "・ 나이트 최대 연속 4일 / 데이·이브 최대 연속 6일\n"
            "・ 듀티 종류 무관 총 연속근무일 절대 6일 초과 금지\n"
            "・ 풀타임/파트타임은 계약 근무시간을 반드시 다 채움(뱅크/캐주얼 제외)\n"
            "・ 듀티당 리더십 1명 필수(리더십 그룹 0명이면 비활성)\n"
            "・ 공휴일 뱅크/캐주얼 배치는 기본 soft 패널티로 항상 적용)"
        )
    for r in hard_rules:
        param_str = format_params(r)
        st.write(f"- **{RULE_CATALOG[r['rule_id']]['label']}**" + (f" — {param_str}" if param_str else ""))

with soft_tab:
    soft_rules = [r for r in st.session_state.rules if r["type"] == "soft"]
    if not soft_rules:
        st.caption(
            "등록된 soft 규칙 없음 (다음 2개는 등록 안 해도 기본 soft로 항상 적용됨: "
            "리더십 중복배치 패널티(가중치 10), 공휴일 뱅크/캐주얼 배치 패널티(가중치 10/캐주얼은 20))."
        )
    for r in soft_rules:
        param_str = format_params(r)
        st.write(
            f"- **{RULE_CATALOG[r['rule_id']]['label']}** (가중치 {r['weight']})"
            + (f" — {param_str}" if param_str else "")
        )
