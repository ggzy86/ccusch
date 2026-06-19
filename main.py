import streamlit as st
from orchestrator import run_simulation

if "nurses" not in st.session_state:
    st.session_state.nurses = [{"name": f"Nurse{i:02d}"} for i in range(1, 21)]

if "rules" not in st.session_state:
    st.session_state.rules = {}

st.title("Scheduler")

if st.button("RUN"):

    result = run_simulation(
        nurses=st.session_state.nurses,
        rules=st.session_state.rules,
        runs=10
    )

    st.write(result)
