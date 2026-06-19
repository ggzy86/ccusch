import streamlit as st
import pandas as pd
from orchestrator import run_simulation
import inspect

# =========================
# STATE INIT
# =========================
if "nurses" not in st.session_state:
    st.session_state.nurses = [{"name": f"Nurse{i}"} for i in range(1, 21)]

st.title("Nurse Scheduler")

# =========================
# 🔍 DEBUG (이거 중요)
# =========================
st.write("RUN_SIM FILE:", inspect.getfile(run_simulation))

# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["Schedule", "Nurses"])

# =========================
# SCHEDULE
# =========================
with tab1:

    if st.button("Run OR-Tools (10x)"):

        result = run_simulation(
            nurses=st.session_state.nurses,
            runs=10
        )

        if not isinstance(result, list) or len(result) == 0:
            st.error("No schedule generated")
            st.stop()

        for i, r in enumerate(result):

            st.subheader(f"Rank {i+1} | Score {r['score']}")

            st.dataframe(pd.DataFrame(r["schedule"]))

# =========================
# NURSES
# =========================
with tab2:

    name = st.text_input("Nurse Name")

    if st.button("Add Nurse"):
        if name:
            st.session_state.nurses.append({"name": name})

    st.dataframe(pd.DataFrame(st.session_state.nurses))
