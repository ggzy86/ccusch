import streamlit as st
import pandas as pd
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

# ------------------
# Nurses
# ------------------
st.subheader("Nurses")

name = st.text_input("Nurse Name", key="nurse_input")

if st.button("Add Nurse"):
    if name.strip():
        state.nurses.append({"name": name.strip()})
        st.session_state.nurse_input = ""

st.write(state.nurses)

# ------------------
# Rules
# ------------------
st.subheader("Rules")

rule_key = st.text_input("Rule Key", key="rule_key")
rule_value = st.text_input("Rule Value", key="rule_value")

if st.button("Add Rule"):
    if rule_key.strip() and rule_value.strip():
        state.rules[rule_key.strip()] = rule_value.strip()
        st.session_state.rule_key = ""
        st.session_state.rule_value = ""

st.write(state.rules)

# ------------------
# Scheduler (TABLE OUTPUT)
# ------------------
st.subheader("Schedule")

if st.button("Generate"):

    result = run_simulation(
        nurses=state.nurses,
        rules=state.rules
    )

    rows = []

    for r in result:
        for s in r["schedule"]:
            rows.append({
                "nurse": s["nurse"],
                "shift": s["shift"],
                "score": r["score"]
            })

    df = pd.DataFrame(rows)

    st.dataframe(df)
