import streamlit as st
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

if st.button("Generate"):
    result = run_simulation(
        nurses=state.nurses,
        rules=state.rules
    )

    st.write(result)
