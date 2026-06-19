import streamlit as st
import pandas as pd
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

tab1, tab2, tab3 = st.tabs(["Schedule", "Nurses", "Rules"])

# -------------------------
# SCHEDULE
# -------------------------
with tab1:

    st.subheader("OR-Tools Scheduler (Top 2)")

    if st.button("Run 10x Optimization"):

        result = run_simulation(
            nurses=state.nurses,
            rules=state.rules,
            runs=10
        )

        for idx, r in enumerate(result):

            st.markdown(f"## Result {idx+1} | Score: {r['score']}")

            df = pd.DataFrame(r["schedule"])

            st.dataframe(df)

# -------------------------
# NURSES
# -------------------------
with tab2:

    st.subheader("Nurses")

    name = st.text_input("Nurse Name", key="nurse")

    if st.button("Add Nurse"):
        if name:
            state.nurses.append({"name": name})

    st.dataframe(pd.DataFrame(state.nurses))

# -------------------------
# RULES (placeholder)
# -------------------------
with tab3:

    st.subheader("Rules")

    st.write(state.rules)
