import streamlit as st
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

# --------------------
# Nurses
# --------------------
st.subheader("Nurses")

name = st.text_input("Nurse Name", key="nurse_input")

if st.button("Add Nurse"):
    if name.strip():
        state.nurses.append({"name": name})
        st.success("Added")

st.write(state.nurses)


# --------------------
# Rules
# --------------------
st.subheader("Rules")

rule_key = st.text_input("Rule Key", key="rule_key")
rule_value = st.text_input("Rule Value", key="rule_value")

if st.button("Add Rule"):
    if rule_key.strip():
        state.rules[rule_key] = rule_value
        st.success("Added")

st.write(state.rules)


# --------------------
# Generate
# --------------------
st.subheader("Scheduler")

if st.button("Generate"):
    result = run_simulation(
        nurses=state.nurses,
        rules=state.rules
    )

    st.write(result)
