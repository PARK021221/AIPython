# app.py — 선박 운항 분석 시스템 (멀티페이지)
import streamlit as st

st.set_page_config(
    page_title="선박 운항 분석 시스템",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

import shared

shared.create_database()
shared.init_session_state()
shared.process_pending_actions()
shared.apply_theme()
shared.render_sidebar()

st.markdown('<p class="hero-caption">Vessel Operation Workflow</p>', unsafe_allow_html=True)
st.title("선박 운항 분석 시스템")
st.markdown(
    "**1. 출항 조건** → **2. RPM 최적 효율** → **3. 운항 속도** 순서로 분석합니다. "
    "왼쪽 메뉴에서 페이지를 선택하세요."
)
shared.render_workflow_banner()

pg = st.navigation(
    {
        "운항 분석": [
            st.Page("views/1_voyage.py", title="1. 출항 조건", icon="🌊", default=True),
            st.Page("views/2_rpm.py", title="2. RPM 최적 효율", icon="⚓"),
            st.Page("views/3_speed.py", title="3. 운항 속도", icon="🚢"),
        ],
        "기록": [
            st.Page("views/4_dashboard.py", title="대시보드", icon="📊"),
        ],
    }
)
pg.run()
