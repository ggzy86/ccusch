import datetime

import streamlit as st
import pandas as pd

import storage
from orchestrator import run_simulation, diagnose
from export import export_excel, export_pdf
from solver import SHIFT_HOURS, SHIFT_COLORS, WEEKDAY_LABELS, required_hours, build_calendar

REQUIRED_MIN = 11  # D4 + E4 + N3
SCHEDULE_DAYS = 14  # 2주 스케줄

HOUR_COL_WORKED = "총근무시간(h)"
HOUR_COL_REQUIRED = "총계약근무시간(h)"
SUMMARY_ROWS = {"D 인원수": "D", "E 인원수": "E", "N 인원수": "N"}

st.title("Nurse Scheduler (OR-Tools)")
st.write("Nurses:", len(st.session_state.nurses), f"(최소 필요: {REQUIRED_MIN}명)")

if len(st.session_state.nurses) < REQUIRED_MIN:
    st.warning(f"간호사가 {REQUIRED_MIN}명 미만이면 절대 못 풀림. Nurse 페이지에서 추가해줘.")

# ======================
# 스케줄 시작일 선택 (2주 스케줄, 호주 VIC 공휴일 자동 표시)
# ======================
col_a, col_b = st.columns([1, 2])
with col_a:
    start_date = st.date_input("스케줄 시작일", value=datetime.date.today())
with col_b:
    time_limit = st.slider("솔버 최대 탐색시간(초)", 5, 60, 30)

_, weekday_of_day, holiday_days = build_calendar(SCHEDULE_DAYS, start_date)
if holiday_days:
    holiday_strs = ", ".join(
        str(start_date + datetime.timedelta(days=d)) for d in sorted(holiday_days)
    )
    st.caption(f"🎉 이 기간 중 호주(VIC) 공휴일: {holiday_strs}")

if st.button("RUN SCHEDULE"):
    result = run_simulation(
        nurses=st.session_state.nurses,
        rules=st.session_state.rules,
        runs=1,
        days=SCHEDULE_DAYS,
        start_date=start_date,
        time_limit=time_limit,
    )
    if not result:
        st.session_state.last_result = None
        st.session_state.last_diagnosis = diagnose(
            st.session_state.nurses, st.session_state.rules,
            days=SCHEDULE_DAYS, start_date=start_date, time_limit=4,
        )
    else:
        st.session_state.last_result = result
        st.session_state.last_result_meta = {"start_date": start_date, "days": SCHEDULE_DAYS}
        st.session_state.last_diagnosis = None

if st.session_state.get("last_result") is None and st.session_state.get("last_diagnosis"):
    st.error("스케줄표가 만들어지지 않음 — 현재 조건으로는 풀이가 불가능함.")
    st.markdown("**👉 다음 조건들을 완화하면 풀릴 가능성이 있음 (자동 진단, 추정값):**")
    for s in st.session_state.last_diagnosis:
        st.markdown(f"- {s}")
    st.caption("※ 각 항목은 몇 초 안에 빠르게만 확인한 결과라 100% 정확하진 않음. 룰북에서 직접 완화/삭제해보고 다시 RUN 해줘.")

if st.session_state.get("last_result"):
    result = st.session_state.last_result
    meta = st.session_state.get("last_result_meta") or {"start_date": start_date, "days": SCHEDULE_DAYS}
    sched_days = meta["days"]
    sched_start = meta["start_date"]
    dates, sched_weekday_of_day, sched_holidays = build_calendar(sched_days, sched_start)

    nurses = st.session_state.nurses
    nurse_names = [n["name"] for n in nurses]
    leadership_names = {n["name"] for n in nurses if n.get("group") == "leadership"}
    days = sorted(set(r["day"] for r in result))

    # ---- long → wide 피벗 (간호사 x 일자, 컬럼은 아직 정수 day) ----
    grid = pd.DataFrame(index=nurse_names, columns=days)
    for r in result:
        grid.loc[r["nurse"], r["day"]] = r["shift"]
    grid = grid.fillna("OFF")

    # ---- 가로 마지막칸: 총근무시간 / 총계약근무시간 (LD/LN=12h 정확히 반영) ----
    for n in nurses:
        name = n["name"]
        if name not in grid.index:
            continue
        worked_hours = sum(SHIFT_HOURS.get(v, 0) for v in grid.loc[name, days])
        grid.loc[name, HOUR_COL_WORKED] = int(worked_hours)
        grid.loc[name, HOUR_COL_REQUIRED] = required_hours(n.get("fte", "full"), sched_days)

    # ---- 일별 세로 마지막칸: D/E/N 듀티별 인원수 (아직 정수 day 컬럼 기준으로 집계) ----
    summary_df = pd.DataFrame(index=list(SUMMARY_ROWS.keys()), columns=grid.columns)
    for label, shift in SUMMARY_ROWS.items():
        for d in days:
            summary_df.loc[label, d] = int((grid[d] == shift).sum())
        summary_df.loc[label, HOUR_COL_WORKED] = ""
        summary_df.loc[label, HOUR_COL_REQUIRED] = ""

    grid = pd.concat([grid, summary_df])

    # ---- 정수 day 컬럼 -> 실제 날짜 라벨로 교체 (호주 공휴일은 🎉 표시) ----
    def day_label(d):
        idx = d - 1
        if dates and idx < len(dates):
            dt = dates[idx]
            wd = WEEKDAY_LABELS[sched_weekday_of_day[idx]]
            mark = "🎉" if idx in sched_holidays else ""
            return f"{dt.month}/{dt.day}({wd}){mark}"
        return str(d)

    grid = grid.rename(columns={d: day_label(d) for d in days})

    def color_shift(val):
        bg = SHIFT_COLORS.get(val)
        return f"background-color: {bg}" if bg else ""

    def style_row(row):
        is_leader = row.name in leadership_names
        styles = []
        for val in row:
            parts = []
            bg = SHIFT_COLORS.get(val)
            if bg:
                parts.append(f"background-color: {bg}")
            if is_leader and val in SHIFT_COLORS and val != "OFF":
                parts.append("text-decoration: underline")
                parts.append("font-weight: 700")
            styles.append("; ".join(parts))
        return styles

    def index_style(label):
        return "text-decoration: underline; font-weight: 700" if label in leadership_names else ""

    styled = grid.style.apply(style_row, axis=1)
    try:
        styled = styled.map_index(index_style, axis=0)
    except AttributeError:
        try:
            styled = styled.applymap_index(index_style, axis=0)
        except AttributeError:
            pass  # 구버전 pandas — 인덱스(이름) 밑줄만 생략, 셀 밑줄/배경색은 정상 표시

    st.markdown(
        "🟦 D ・ 🟧 E ・ 🟪 N ・ 🟩 LD(롱데이 12h) ・ 🟫 LN(롱나이트 12h) ・ 🟥 OFF "
        "・ <u>밑줄</u> = 리더십 그룹(이름 밑줄) / 해당 듀티 근무중인 리더십(듀티 밑줄)",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**📊 시간 구분:** `{HOUR_COL_WORKED}` = 이번 2주간 실제로 배정된 근무시간 합계(LD/LN은 12h로 계산) "
        f"&nbsp;|&nbsp; `{HOUR_COL_REQUIRED}` = FTE 기준으로 반드시 채워야 하는 계약 근무시간 "
        "(풀타임/파트타임은 이 값을 반드시 채우도록 강제됨, 뱅크/캐주얼은 강제 없음)"
    )
    st.caption("마지막 3행 = 일자별 듀티 인원수")

    row_height = 33
    table_height = (len(grid) + 1) * row_height + 3
    column_config = {col: st.column_config.Column(width="small") for col in grid.columns}

    st.dataframe(styled, use_container_width=True, height=table_height, column_config=column_config)
    st.caption(
        "※ 표 내부에는 더 이상 자체 스크롤바가 없음. 화면(창)이 표 전체 너비보다 좁으면 "
        "브라우저 자체 가로 스크롤이 생길 수 있는데, 창을 최대화하거나 줌아웃(Ctrl/Cmd + -)하면 한눈에 들어옴."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Excel 다운로드",
            data=export_excel(grid),
            file_name="nurse_schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        st.download_button(
            "📥 PDF 다운로드",
            data=export_pdf(grid),
            file_name="nurse_schedule.pdf",
            mime="application/pdf",
        )

# ======================
# 저장 / 불러오기 (간호사 정보 + 마지막 스케줄 + 룰북을 로컬 파일에 보관)
# ======================
st.divider()
with st.expander("💾 저장 / 불러오기"):
    st.caption("간호사 정보 + 마지막에 생성된 스케줄 + 룰북을 통째로 저장. 앱을 껐다 켜도 불러올 수 있음 "
               "(같은 폴더의 schedule_snapshots.json 파일에 저장됨).")

    save_name = st.text_input("저장할 이름", key="save_name_input")
    if st.button("💾 현재 상태 저장"):
        ok, msg = storage.save_snapshot(
            save_name,
            st.session_state.nurses,
            st.session_state.rules,
            st.session_state.get("last_result"),
            meta=st.session_state.get("last_result_meta"),
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    snapshots = storage.list_snapshots()
    if snapshots:
        names = [f"{name} ({saved_at})" for name, saved_at in snapshots]
        idx = st.selectbox("불러올 스냅샷 선택", range(len(names)), format_func=lambda i: names[i])
        chosen_name = snapshots[idx][0]

        load_col, del_col = st.columns(2)
        with load_col:
            if st.button("📂 불러오기"):
                snap = storage.load_snapshot(chosen_name)
                if snap:
                    st.session_state.nurses = snap.get("nurses", [])
                    st.session_state.rules = snap.get("rules", [])
                    st.session_state.last_result = snap.get("last_result")
                    st.session_state.last_result_meta = snap.get("meta")
                    st.session_state.next_nurse_id = (
                        max([n.get("id", 0) for n in st.session_state.nurses], default=0) + 1
                    )
                    st.session_state.next_rule_id = (
                        max([r.get("id", 0) for r in st.session_state.rules], default=0) + 1
                    )
                    st.success(f"'{chosen_name}' 불러옴")
                    st.rerun()
                else:
                    st.error("불러오기 실패")
        with del_col:
            if st.button("🗑️ 삭제"):
                storage.delete_snapshot(chosen_name)
                st.rerun()
    else:
        st.caption("저장된 스냅샷 없음.")
