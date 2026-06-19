import streamlit as st
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

# =========================
# 1. Nurses 관리
# =========================
st.subheader("Nurses")

name = st.text_input("Add Nurse Name")

if st.button("Add Nurse"):
    state.nurses.append({"name": name})
    st.success(f"Added {name}")

st.write(state.nurses)


# =========================
# 2. Rules 관리
# =========================
st.subheader("Rules")

rule_key = st.text_input("Rule Key")
rule_value = st.text_input("Rule Value")

if st.button("Add Rule"):
    state.rules[rule_key] = rule_value
    st.success(f"Added rule {rule_key}")

st.write(state.rules)


# =========================
# 3. Schedule Generator
# =========================
st.subheader("Scheduler")

if st.button("Generate 10 Schedules"):
    result = run_simulation(
        nurses=state.nurses,
        rules=state.rules
    )

    st.write(result)
