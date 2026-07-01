# 2. RPM 최적 효율
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from shared import (
    J_OPT,
    Decision,
    _get_diagnosis,
    _inputs_valid,
    _j_gauge_html,
    calculate_all,
    calculate_propeller_efficiency,
    draw_rpm_efficiency_curve,
    save_record,
)

if not st.session_state.voyage_confirmed:
    st.warning(
        "🔒 **1. 출항 조건** 페이지에서 기상·선박 정보를 입력한 뒤 "
        "**「확인하고 2. RPM으로 진행」** 버튼을 눌러 주세요."
    )
elif not st.session_state.rpm_confirmed:
    st.warning(
        "🔒 사이드바 **🧪 연습용 시나리오**에서 값을 불러온 뒤 "
        "**「✅ ② RPM 확인」** 버튼을 눌러 주세요."
    )
else:
    propeller_name = st.session_state.form_propeller_name
    vessel_speed = st.session_state.form_vessel_speed
    propeller_diameter = st.session_state.form_propeller_diameter
    thrust = st.session_state.form_thrust
    shaft_power = st.session_state.form_shaft_power
    rpm_min = st.session_state.form_rpm_min
    rpm_max = st.session_state.form_rpm_max
    rpm_val = st.session_state.form_rpm

    st.markdown("#### ⚓ 2. RPM 최적 효율")

    if st.session_state.voyage_decision == Decision.PROHIBITED.value:
        st.warning(
            "⚠️ 출항 판단 결과 **출항 불가**입니다. RPM 분석은 참고용이며, "
            "실제 운항은 선장·운항관리자 판단과 최신 기상정보를 따르세요."
        )
    elif st.session_state.voyage_decision == Decision.CONDITIONAL.value:
        st.info("ℹ️ 출항 조건: **조건부 가능** — 1. 출항 조건 페이지에서 사유를 확인하세요.")

    snapshot = (
        propeller_name, vessel_speed, propeller_diameter,
        rpm_val, thrust, shaft_power, rpm_min, rpm_max,
    )
    if st.session_state.last_snapshot != snapshot:
        st.session_state.saved = False
        st.session_state.last_snapshot = snapshot
        st.session_state.rpm_confirmed = False

    if not _inputs_valid(
        propeller_name, vessel_speed, propeller_diameter,
        rpm_val, thrust, shaft_power, rpm_min, rpm_max,
    ):
        st.info("👈 사이드바 **전체 불러오기** 또는 **② RPM**으로 샘플을 불러오세요.")
    else:
        try:
            result = calculate_all(
                vessel_speed, rpm_val, propeller_diameter,
                thrust, shaft_power, float(rpm_min), float(rpm_max),
            )
            measured_eff = result["measured_efficiency"]
            model_eff = result["model_efficiency"]
            optimal_rpm = result["optimal_rpm"]
            max_eff = result["max_efficiency"]
            J = result["advance_ratio"]
            optimal_J_eff = calculate_propeller_efficiency(
                vessel_speed, optimal_rpm, propeller_diameter
            )

            border_color, diag_title, diag_icon, diag_msg = _get_diagnosis(rpm_val, optimal_rpm)
            eff_ratio = model_eff / max_eff * 100 if max_eff > 0 else 0
            eff_gain = max_eff - model_eff

            chart_col, panel_col = st.columns([1.65, 1])

            with chart_col:
                st.markdown("##### RPM – 효율 곡선")
                fig_curve = draw_rpm_efficiency_curve(
                    vessel_speed, propeller_diameter,
                    float(rpm_min), float(rpm_max),
                    current_rpm=rpm_val, optimal_rpm=optimal_rpm,
                )
                st.pyplot(fig_curve, use_container_width=True)
                plt.close(fig_curve)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("실측 효율", f"{measured_eff:.1f} %")
                with c2:
                    st.metric("이론 효율", f"{model_eff:.1f} %", delta=f"최대 대비 {eff_ratio:.0f}%")
                with c3:
                    st.metric("최대 효율", f"{max_eff:.1f} %", delta=f"{optimal_rpm:.0f} RPM")

            with panel_col:
                st.markdown("##### 운항 진단")
                st.markdown(
                    f"""
                    <div class="diag-card" style="border-left-color:{border_color};">
                        <div class="diag-title">{diag_icon} {diag_title}</div>
                        <div class="diag-sub">{diag_msg}</div>
                        <div class="diag-big">{rpm_val:.0f} → {optimal_rpm:.0f} RPM</div>
                        <div class="diag-delta">효율 개선 여지 : +{eff_gain:.1f}%p (이론 기준)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(_j_gauge_html(J), unsafe_allow_html=True)

                st.markdown("##### 현재 vs 최적 비교")
                compare_df = pd.DataFrame({
                    "항목": ["RPM", "이론 효율 (%)", "진수비 J"],
                    "현재 운항": [f"{rpm_val:.0f}", f"{model_eff:.1f}", f"{J:.3f}"],
                    "최적 운항": [f"{optimal_rpm:.0f}", f"{optimal_J_eff:.1f}", f"{J_OPT:.3f}"],
                    "차이": [
                        f"{rpm_val - optimal_rpm:+.0f}",
                        f"{model_eff - optimal_J_eff:+.1f}%p",
                        f"{J - J_OPT:+.3f}",
                    ],
                })
                st.dataframe(compare_df, use_container_width=True, hide_index=True)

                st.progress(
                    min(1.0, eff_ratio / 100),
                    text=f"최대 효율 대비 현재 이론 효율 {eff_ratio:.0f}%",
                )

                with st.expander("계산 상세 보기"):
                    st.markdown(
                        f"""
                        - **실측** η = (추력 × 선속) / 축출력 = **{measured_eff:.2f}%**
                        - **이론** η = f(J), J = Va/(n·D) = **{J:.3f}**
                        - **스윕** {rpm_min}~{rpm_max} RPM → 최적 **{optimal_rpm:.0f} RPM**
                        """
                    )

                st.divider()

                if st.session_state.saved:
                    st.success("저장 완료 — **대시보드** 페이지에서 확인하세요.")
                    st.button("💾 저장됨", key="rpm_saved_btn", disabled=True, use_container_width=True)
                else:
                    if st.button("💾 이 결과 저장", key="rpm_save", use_container_width=True, type="primary"):
                        ok = save_record(
                            propeller_name=propeller_name,
                            vessel_speed=vessel_speed,
                            propeller_diameter=propeller_diameter,
                            rpm=float(rpm_val),
                            shaft_power=shaft_power,
                            thrust=thrust,
                            measured_efficiency=measured_eff,
                            model_efficiency=model_eff,
                            optimal_rpm=optimal_rpm,
                            max_efficiency=max_eff,
                            advance_ratio_val=J,
                        )
                        if ok:
                            st.session_state.saved = True
                            st.success("저장되었습니다! **대시보드** 페이지에서 확인하세요.")
                            st.rerun()
                        else:
                            st.error("저장 실패")

        except ValueError as e:
            st.error(f"계산 오류 : {e}")
