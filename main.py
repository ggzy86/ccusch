import streamlit as st

st.set_page_config(page_title="Nurse Scheduler", layout="wide")

# ======================
# 전역 세션 상태 초기화 (모든 페이지에서 공유됨)
# ======================
if "nurses" not in st.session_state:
    # 최소 4(D)+4(E)+3(N)=11명 필요, 휴무가 실제로 생기려면 그보다 넉넉해야 함
    st.session_state.nurses = [
        {
            "id": i,
            "name": f"Nurse{i:02d}",
            "fte": "full",
            "group": "leadership" if i <= 3 else "bedside",  # 기본 3명을 리더십으로 지정
            "available_shifts": ["D", "E", "N", "LD", "LN"],
        }
        for i in range(1, 16)
    ]

if "rules" not in st.session_state:
    st.session_state.rules = []

if "next_nurse_id" not in st.session_state:
    st.session_state.next_nurse_id = len(st.session_state.nurses) + 1

if "next_rule_id" not in st.session_state:
    st.session_state.next_rule_id = 1

# ======================
# 페이지 라우팅
# ======================
main_page = st.Page("page_main.py", title="메인", icon="🏠", default=True)
nurse_page = st.Page("page_nurse.py", title="Nurse", icon="👩‍⚕️")
rulebook_page = st.Page("page_rulebook.py", title="룰북", icon="📋")

pg = st.navigation([main_page, nurse_page, rulebook_page])
pg.run()
