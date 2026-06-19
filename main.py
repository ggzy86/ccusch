import streamlit as st

st.title("OR-Tools TEST")

try:
    from ortools.sat.python import cp_model

    st.success("OR-TOOLS IMPORT OK")

    # 아주 단순 테스트 모델
    model = cp_model.CpModel()

    x = model.NewBoolVar("x")
    y = model.NewBoolVar("y")

    model.Add(x + y <= 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    st.success("CP-SAT SOLVE OK")
    st.write("Status:", status)

except Exception as e:
    st.error("ERROR OCCURRED")
    st.exception(e)
