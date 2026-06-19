import streamlit as st
import pandas as pd
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

tab1, tab2, tab3 = st.tabs(["Schedule", "Nurses", "Rules"])

# =========================
# SCHEDULE
# =========================
with tab1:

    st.subheader("Schedule")

    if st.button("Run Optimization"):

        result = run_simulation(
            nurses=state.nurses,
            rules=state.rules,
            runs=10
        )

        # 🔒 최종 방어
        if not isinstance(result, list) or len(result) == 0:
            st.error("No valid schedule generated")
            st.stop()

        for i, r in enumerate(result):

            st.markdown(f"## Rank {i+1} | Score {r.get('score',0)}")

            schedule = r.get("schedule", [])

            if not isinstance(schedule, list):
                continue

            df = pd.DataFrame(schedule)
            st.dataframe(df)


# =========================
# NURSES
# =========================
with tab2:

    st.subheader("Nurses")

    name = st.text_input("Nurse Name")

    if st.button("Add Nurse"):
        if name:
            state.nurses.append({"name": name})

    st.dataframe(pd.DataFrame(state.nurses))


# =========================
# RULES
# =========================
with tab3:

    st.subheader("Rules")

    st.write(state.rules)
