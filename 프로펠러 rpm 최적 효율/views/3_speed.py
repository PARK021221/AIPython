# 3. 운항 속도
import streamlit as st

st.markdown("#### 🚢 3. 운항 속도")

if not st.session_state.voyage_confirmed:
    st.warning("🔒 **1. 출항 조건** 페이지에서 **확인**을 완료한 뒤 이용할 수 있습니다.")
elif not st.session_state.rpm_confirmed:
    st.warning("🔒 사이드바 **✅ ② RPM 확인** 을 완료한 뒤 이용할 수 있습니다.")
else:
    st.caption("1. 출항 조건 · 2. RPM 최적 효율 확인 후 운항 속도를 분석합니다.")

    st.info(
        "🚧 **운항 속도** 기능은 준비 중입니다.\n\n"
        "파일을 추가해 주시면 이 페이지에서 **선속·연료·운항 효율** 등을 분석할 수 있도록 연결하겠습니다."
    )

    st.markdown("##### 예정 워크플로")
    st.markdown(
        """
        1. **1. 출항 조건** — 기상·선박 상태로 출항 가능 여부 확인
        2. **2. RPM 최적 효율** — 프로펠러 RPM·효율 최적화
        3. **3. 운항 속도** — 목적지까지 경제 속도·ETA 분석 *(준비 중)*
        """
    )
