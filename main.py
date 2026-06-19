import streamlit as st
import pandas as pd
from orchestrator import run_simulation

# 🔒 state 안전 초기화
if "nurses" not in st.session_state:
    st.session_state.nurses = [{"name": f"Nurse{i}"} for i in range(1, 21)]

if "rules" not in st.session_state:
    st.session_state.rules = {}

st.title("Nurse Scheduler")

tab1, tab2, tab3 = st.tabs(["Schedule", "Nurses", "Rules"])

# ======================
# SCHEDULE
# ======================
with tab1:

    if st.button("Run OR-Tools (10x)"):

        result = run_simulation(
            nurses=st.session_state.nurses,
            rules=st.session_state.rules,
            runs=10
        )

        if len(result) == 0:
            st.error("No schedule generated")
            st.stop()

        for i, r in enumerate(result):

            st.subheader(f"Rank {i+1} | Score {r['score']}")

            st.dataframe(pd.DataFrame(r["schedule"]))

# ======================
# NURSES
# ======================
with tab2:

    name = st.text_input("Nurse Name")

    if st.button("Add Nurse"):
        if name:
            st.session_state.nurses.append({"name": name})

    st.dataframe(pd.DataFrame(st.session_state.nurses))

# ======================
# RULES
# ======================
with tab3:

    st.write(st.session_state.rules)
