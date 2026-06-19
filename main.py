import streamlit as st
import pandas as pd
from orchestrator import run_simulation
import state

st.title("Nurse Scheduler")

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["Schedule", "Nurses", "Rule Book"])

# =========================
# TAB 1 - SCHEDULE
# =========================
with tab1:

    st.subheader("Generate Schedule")

    days = st.number_input("Days", min_value=1, max_value=30, value=3)

    if st.button("Generate"):

        result = run_simulation(
            nurses=state.nurses,
            rules=state.rules
        )

        rows = []

        for day in range(days):
            for r in result:
                for s in r["schedule"]:
                    rows.append({
                        "day": day + 1,
                        "nurse": s["nurse"],
                        "shift": s["shift"],
                        "score": r["score"]
                    })

        st.dataframe(pd.DataFrame(rows))


# =========================
# TAB 2 - NURSES
# =========================
with tab2:

    st.subheader("Nurse Manager")

    name = st.text_input("Nurse Name", key="nurse_input")

    if st.button("Add Nurse"):
        if name.strip():
            state.nurses.append({"name": name.strip()})
            st.session_state.nurse_input = ""

    st.write("Total Nurses:", len(state.nurses))

    st.dataframe(pd.DataFrame(state.nurses))


# =========================
# TAB 3 - RULE BOOK
# =========================
with tab3:

    st.subheader("Rule Book")

    rule_key = st.text_input("Rule Name", key="rule_key")
    rule_value = st.text_input("Rule Value", key="rule_value")

    if st.button("Add Rule"):
        if rule_key.strip() and rule_value.strip():
            state.rules[rule_key.strip()] = rule_value.strip()
            st.session_state.rule_key = ""
            st.session_state.rule_value = ""

    st.write("Total Rules:", len(state.rules))

    # RULE TABLE VIEW
    rule_df = pd.DataFrame([
        {"rule": k, "value": v}
        for k, v in state.rules.items()
    ])

    st.dataframe(rule_df)
