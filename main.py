import streamlit as st
from orchestrator import run_simulation

# ---------------- SESSION ----------------
if "nurses" not in st.session_state:
    st.session_state.nurses = [{"name": f"Nurse{i:02d}"} for i in range(1, 21)]

if "rules" not in st.session_state:
    st.session_state.rules = {}

# ---------------- UI ----------------
st.title("Nurse Scheduler (OR-Tools)")

st.write("Nurses:", len(st.session_state.nurses))

# 버튼
if st.button("Run OR-Tools (10x)"):

    result = run_simulation(
        nurses=st.session_state.nurses,
        rules=st.session_state.rules,
        runs=10
    )

    if not result:
        st.error("No schedule generated")
        st.stop()

    st.success("Schedule generated")

    st.write("Sample output:")
    st.write(result[:20])
