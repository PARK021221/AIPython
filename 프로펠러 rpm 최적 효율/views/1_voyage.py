# 1. 출항 조건
import streamlit as st
import pandas as pd

from shared import (
    Decision,
    VoyageConditions,
    _voyage_conditions_valid,
    _voyage_style,
    assess_voyage,
    delete_departure_record,
    get_all_departure_records,
    save_departure_record,
)

st.markdown("#### 🌊 1. 출항 조건")
st.markdown(
    "풍속·파고·시정·선박 상태를 입력하면 **자동 판정**됩니다. "
    "결과를 확인한 뒤 **「확인하고 2. RPM으로 진행」** 을 눌러 다음 페이지로 넘어가세요."
)
st.caption("교육용 예시 기준입니다. 실제 출항은 관할 법규와 선장 판단을 따르세요.")

inp_col, res_col = st.columns([1, 1])

with inp_col:
    st.markdown("##### 기상·해상 조건")
    voy_vessel_name = st.text_input(
        "선박명 (저장 시 필요)",
        key="voy_vessel_name",
        placeholder="예 : 해양호",
    )

    wcol1, wcol2 = st.columns(2)
    with wcol1:
        voy_wind = st.number_input("풍속 (m/s)", min_value=0.0, step=0.5, key="voy_wind")
        voy_wave = st.number_input("파고 (m)", min_value=0.0, step=0.1, format="%.1f", key="voy_wave")
    with wcol2:
        voy_visibility = st.number_input("시정 (km)", min_value=0.0, step=0.1, format="%.1f", key="voy_visibility")
        voy_length = st.number_input("선박 길이 (m)", min_value=0.0, step=1.0, key="voy_length")

    st.markdown("##### 선박·운항 상태")
    voy_engine_ok = st.checkbox("기관 상태 양호", key="voy_engine_ok")
    voy_navigation_ok = st.checkbox("항해 장비 상태 양호", key="voy_navigation_ok")
    voy_lifesaving_ok = st.checkbox("구명·안전 장비 상태 양호", key="voy_lifesaving_ok")
    voy_crew_ready = st.checkbox("승무원 준비 완료", key="voy_crew_ready")
    voy_weather_warning = st.checkbox("기상특보 발효", key="voy_weather_warning")

    if st.button("🔄 입력 초기화", key="voy_reset", use_container_width=True):
        st.session_state._pending_voyage_reset = True
        st.rerun()

voy_snapshot = (
    voy_vessel_name, voy_wind, voy_wave, voy_visibility, voy_length,
    voy_engine_ok, voy_navigation_ok, voy_lifesaving_ok,
    voy_crew_ready, voy_weather_warning,
)
if st.session_state.voyage_last_snapshot != voy_snapshot:
    st.session_state.voyage_saved = False
    st.session_state.voyage_last_snapshot = voy_snapshot
    st.session_state.voyage_confirmed = False
    st.session_state.voyage_decision = None

with res_col:
    st.markdown("##### 자동 판정 결과")

    if not _voyage_conditions_valid(voy_wind, voy_wave, voy_visibility, voy_length):
        st.info(
            "왼쪽에 **선박명·풍속·파고·시정·선박 길이** 를 입력하거나, "
            "사이드바 **전체 불러오기** 또는 **① 출항**을 사용하면 "
            "이곳에 **출항 가능 / 조건부 / 출항 불가** 가 자동으로 표시됩니다."
        )
    else:
        try:
            conditions = VoyageConditions(
                wind_speed_ms=voy_wind,
                wave_height_m=voy_wave,
                visibility_km=voy_visibility,
                vessel_length_m=voy_length,
                engine_ok=voy_engine_ok,
                navigation_ok=voy_navigation_ok,
                lifesaving_ok=voy_lifesaving_ok,
                crew_ready=voy_crew_ready,
                weather_warning=voy_weather_warning,
            )
            vresult = assess_voyage(conditions)
            st.session_state.voyage_decision = vresult.decision.value

            border, icon = _voyage_style(vresult.decision)
            reasons_html = "".join(f"<li>{r}</li>" for r in vresult.reasons)
            display_name = voy_vessel_name.strip() or "선박명 미입력"

            st.markdown(
                f"""
                <div class="diag-card" style="border-left-color:{border};">
                    <div class="diag-title">{icon} {vresult.decision.value}</div>
                    <div class="diag-sub">입력 조건 기반 자동 판정</div>
                    <div class="diag-big">{display_name}</div>
                    <div class="diag-delta">
                        풍 {voy_wind:g} m/s · 파고 {voy_wave:g} m · 시정 {voy_visibility:g} km
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("##### 판정 사유")
            st.markdown(f"<ul style='color:#b0bec5;'>{reasons_html}</ul>", unsafe_allow_html=True)

            limits_df = pd.DataFrame({
                "항목": ["풍속", "파고", "시정"],
                "현재": [f"{voy_wind:g} m/s", f"{voy_wave:g} m", f"{voy_visibility:g} km"],
                "주의 기준": ["≥ 10 m/s", "≥ 2 m", "≤ 1 km"],
                "금지 기준": ["> 14 m/s", "> 3 m", "< 0.5 km"],
            })
            st.dataframe(limits_df, use_container_width=True, hide_index=True)

            st.caption(
                "실제 출항은 최신 기상정보, 관할 법규 및 선장/운항관리자의 승인을 따르세요."
            )

            if vresult.decision == Decision.ALLOWED:
                st.success("✅ 출항 가능 — 확인 후 **2. RPM 최적 효율** 페이지로 진행할 수 있습니다.")
            elif vresult.decision == Decision.CONDITIONAL:
                st.warning("⚠️ 조건부 가능 — 사유를 검토한 뒤 확인 버튼을 눌러 주세요.")
            else:
                st.error("🚫 출항 불가 — 판정을 확인한 뒤, 참고용으로 RPM 분석이 가능합니다.")

            st.divider()
            if st.session_state.voyage_confirmed:
                st.success("✅ 확인 완료 — 왼쪽 메뉴 **2. RPM 최적 효율** 페이지로 이동하세요.")
                if st.button("🔄 출항 조건 다시 입력", key="voy_unconfirm", use_container_width=True):
                    st.session_state.voyage_confirmed = False
                    st.rerun()
            elif st.button(
                "✅ 확인하고 2. RPM으로 진행",
                key="voy_confirm",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.voyage_confirmed = True
                st.session_state.voyage_decision = vresult.decision.value
                st.rerun()

            st.divider()
            if st.session_state.voyage_saved:
                st.success("판정 결과가 저장되었습니다.")
                st.button("💾 저장됨", key="voy_saved_btn", disabled=True, use_container_width=True)
            else:
                if not voy_vessel_name.strip():
                    st.warning("판정 결과를 저장하려면 선박명을 입력해 주세요.")
                elif st.button("💾 판정 결과 저장", key="voy_save", use_container_width=True, type="primary"):
                    ok = save_departure_record(
                        vessel_name=voy_vessel_name.strip(),
                        wind_speed_ms=voy_wind,
                        wave_height_m=voy_wave,
                        visibility_km=voy_visibility,
                        vessel_length_m=voy_length,
                        decision=vresult.decision.value,
                        reasons=vresult.reasons,
                    )
                    if ok:
                        st.session_state.voyage_saved = True
                        st.success("저장되었습니다! **대시보드** 페이지에서 확인하세요.")
                        st.rerun()
                    else:
                        st.error("저장 실패")

        except ValueError as e:
            st.error(f"입력 오류 : {e}")

dep_df = get_all_departure_records()
if not dep_df.empty:
    with st.expander(f"📋 저장된 출항 판단 기록 ({len(dep_df)}건)"):
        st.dataframe(
            dep_df.style.format({
                "풍속(m/s)": "{:,.1f}",
                "파고(m)": "{:,.1f}",
                "시정(km)": "{:,.1f}",
                "선박길이(m)": "{:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
        dep_ids = dep_df["번호"].tolist()
        del_id = st.selectbox("삭제할 기록", dep_ids, key="voy_del_pick")
        if st.button("🗑️ 출항 기록 삭제", key="voy_del_btn"):
            if delete_departure_record(del_id):
                st.success(f"#{del_id} 삭제 완료")
                st.rerun()
