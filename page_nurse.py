import streamlit as st

from solver import SHIFT_COLORS, WEEKDAY_LABELS

st.title("👩‍⚕️ Nurse 관리")

FTE_OPTIONS = ["full", "0.8", "0.6", "0.4", "0.2", "bank", "casual"]
SHIFT_OPTIONS = ["D", "E", "N", "LD", "LN"]
GROUP_OPTIONS = ["bedside", "leadership"]
GROUP_LABELS = {"bedside": "베드사이드(Bedside)", "leadership": "리더십(Leadership)"}
PREF_NONE = "(선호 없음)"


def shift_color_picker(label, selected, key_prefix, help_text=None):
    """st.multiselect 대신 듀티마다 스케줄표와 동일한 색 막대를 박은 체크박스 묶음.
    (multiselect 태그는 색이 전부 동일해서 스케줄표 색상과 안 맞는 문제 때문에 이 방식으로 대체)"""
    st.write(label)
    if help_text:
        st.caption(help_text)
    cols = st.columns(len(SHIFT_OPTIONS))
    chosen = []
    for col, s in zip(cols, SHIFT_OPTIONS):
        with col:
            st.markdown(
                f"<div style='width:100%;height:8px;border-radius:4px;"
                f"background:{SHIFT_COLORS[s]};margin-bottom:4px;'></div>",
                unsafe_allow_html=True,
            )
            checked = st.checkbox(s, value=s in selected, key=f"{key_prefix}_{s}")
            if checked:
                chosen.append(s)
    return chosen


def weekday_picker(label, selected, key_prefix):
    st.write(label)
    cols = st.columns(7)
    chosen = []
    for idx, (col, wd_label) in enumerate(zip(cols, WEEKDAY_LABELS)):
        with col:
            checked = st.checkbox(wd_label, value=idx in selected, key=f"{key_prefix}_{idx}")
            if checked:
                chosen.append(idx)
    return chosen


def preferred_shift_picker(label, current, key):
    options = [PREF_NONE] + SHIFT_OPTIONS
    idx = options.index(current) if current in options else 0
    labels = {PREF_NONE: PREF_NONE}
    for s in SHIFT_OPTIONS:
        labels[s] = f"{s}"
    choice = st.selectbox(label, options, index=idx, format_func=lambda o: labels[o], key=key)
    if choice != PREF_NONE:
        st.markdown(
            f"<div style='width:60px;height:6px;border-radius:3px;background:{SHIFT_COLORS[choice]};'></div>",
            unsafe_allow_html=True,
        )
    return None if choice == PREF_NONE else choice


# ---- 추가 ----
with st.form("add_nurse_form", clear_on_submit=True):
    name = st.text_input("이름")
    fte = st.selectbox("근무형태(FTE)", FTE_OPTIONS)
    group = st.radio(
        "그룹", GROUP_OPTIONS, format_func=lambda g: GROUP_LABELS[g], horizontal=True,
        help="각 듀티에는 leadership 그룹에서 최소 1명이 배치됨. bedside는 인원 보충용.",
    )
    available = shift_color_picker(
        "가능 듀티 (hard — 이 듀티만 배정 가능)", SHIFT_OPTIONS, "add_avail",
        help_text="색 막대는 스케줄표 색상과 동일함.",
    )
    available_weekdays = weekday_picker(
        "가능한 요일 (hard — 체크 안 한 요일은 항상 OFF)", set(range(7)), "add_wd"
    )
    preferred = preferred_shift_picker("선호 듀티 (soft — 가능하면 이 듀티를 우선 배정)", PREF_NONE, "add_pref")

    submitted = st.form_submit_button("추가")
    if submitted and name:
        st.session_state.nurses.append(
            {
                "id": st.session_state.next_nurse_id,
                "name": name,
                "fte": fte,
                "group": group,
                "available_shifts": [s for s in SHIFT_OPTIONS if s in available],
                "available_weekdays": sorted(available_weekdays),
                "preferred_shift": preferred,
            }
        )
        st.session_state.next_nurse_id += 1
        st.rerun()

st.divider()
st.subheader(f"전체 {len(st.session_state.nurses)}명")
st.caption("듀티 색상은 스케줄표와 동일: 🟦D ・ 🟧E ・ 🟪N ・ 🟩LD(12h) ・ 🟫LN(12h)")

leader_count = sum(1 for n in st.session_state.nurses if n.get("group") == "leadership")
if leader_count == 0:
    st.info("ℹ️ 현재 리더십(Leadership) 그룹 간호사가 0명임 — '듀티당 리더십 1명 필수' 규칙이 적용되지 않음.")

# ---- 목록 / 수정 / 삭제 ----
for nurse in list(st.session_state.nurses):
    with st.container(border=True):
        top_cols = st.columns([2, 1, 1.4, 1])
        with top_cols[0]:
            new_name = st.text_input("이름", value=nurse["name"], key=f"name_{nurse['id']}")
        with top_cols[1]:
            new_fte = st.selectbox(
                "FTE", FTE_OPTIONS, index=FTE_OPTIONS.index(nurse.get("fte", "full")),
                key=f"fte_{nurse['id']}",
            )
        with top_cols[2]:
            new_group = st.selectbox(
                "그룹", GROUP_OPTIONS, index=GROUP_OPTIONS.index(nurse.get("group", "bedside")),
                format_func=lambda g: GROUP_LABELS[g], key=f"group_{nurse['id']}",
            )
        with top_cols[3]:
            st.write("")
            delete_clicked = st.button("삭제", key=f"del_{nurse['id']}")

        new_available = shift_color_picker(
            "가능 듀티 (hard)", nurse.get("available_shifts", SHIFT_OPTIONS), f"avail_{nurse['id']}"
        )
        new_weekdays = weekday_picker(
            "가능한 요일 (hard)",
            set(nurse.get("available_weekdays", list(range(7))) or []),
            f"wd_{nurse['id']}",
        )
        new_preferred = preferred_shift_picker(
            "선호 듀티 (soft)",
            nurse.get("preferred_shift") or PREF_NONE,
            f"pref_{nurse['id']}",
        )

        if delete_clicked:
            st.session_state.nurses = [n for n in st.session_state.nurses if n["id"] != nurse["id"]]
            st.rerun()

        new_available_sorted = [s for s in SHIFT_OPTIONS if s in new_available]
        new_weekdays_sorted = sorted(new_weekdays)
        if (
            new_name != nurse["name"]
            or new_fte != nurse.get("fte")
            or new_group != nurse.get("group", "bedside")
            or new_available_sorted != nurse.get("available_shifts", SHIFT_OPTIONS)
            or new_weekdays_sorted != sorted(nurse.get("available_weekdays", list(range(7))) or [])
            or new_preferred != nurse.get("preferred_shift")
        ):
            nurse["name"] = new_name
            nurse["fte"] = new_fte
            nurse["group"] = new_group
            nurse["available_shifts"] = new_available_sorted
            nurse["available_weekdays"] = new_weekdays_sorted
            nurse["preferred_shift"] = new_preferred

        if not new_available_sorted:
            st.caption(f"⚠️ {new_name}: 가능 듀티가 없음 — 항상 OFF로만 배정됨")
        if not new_weekdays_sorted:
            st.caption(f"⚠️ {new_name}: 가능한 요일이 없음 — 항상 OFF로만 배정됨")
