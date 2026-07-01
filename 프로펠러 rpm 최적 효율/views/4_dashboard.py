# 대시보드
import matplotlib.pyplot as plt
import streamlit as st

from shared import (
    _inputs_valid,
    _update_rpm_record,
    delete_departure_record,
    delete_record,
    draw_efficiency_bar_chart,
    draw_efficiency_trend_chart,
    draw_optimal_rpm_bar_chart,
    draw_rpm_deviation_scatter,
    load_dashboard_data,
)

_saved_df, _departure_df, _has_rpm_records, _has_departure_records = load_dashboard_data()

dash_header, dash_refresh = st.columns([4, 1])
with dash_header:
    st.markdown("#### 📊 운항 대시보드")
    st.caption("2. RPM **이 결과 저장** · 1. 출항 **판정 결과 저장** 한 기록이 여기에 모입니다.")
with dash_refresh:
    if st.button("🔄 새로고침", key="dash_refresh", use_container_width=True):
        st.rerun()

s1, s2 = st.columns(2)
with s1:
    st.metric("⚓ RPM 분석 기록", f"{len(_saved_df)}건")
with s2:
    st.metric("🌊 출항 판단 기록", f"{len(_departure_df)}건")

if not _has_rpm_records and not _has_departure_records:
    st.info(
        "📭 저장된 기록이 없습니다. "
        "**1. 출항 조건** 또는 **2. RPM 최적 효율** 페이지에서 결과를 저장해 보세요."
    )
else:
    st.markdown("##### ⚓ RPM 분석 기록")
    if not _has_rpm_records:
        st.info(
            "저장된 RPM 분석이 없습니다.\n\n"
            "1. **1. 출항 조건** → 확인 완료\n"
            "2. 사이드바 **② RPM 불러오기** → **✅ ② RPM 확인**\n"
            "3. **2. RPM 최적 효율** 페이지에서 **💾 이 결과 저장**\n"
            "4. 이 **대시보드** 페이지에서 기록 확인"
        )
    else:
        df = _saved_df.copy()
        df["RPM편차"] = df["현재RPM"] - df["최적RPM"]
        df["효율갭"] = df["최대효율(%)"] - df["이론효율(%)"]

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("RPM 분석", f"{len(df)}건")
        with k2:
            st.metric("평균 RPM 편차", f"{df['RPM편차'].abs().mean():.1f}")
        with k3:
            st.metric("평균 효율 갭", f"{df['효율갭'].mean():.1f}%p")
        with k4:
            near_opt = (df["RPM편차"].abs() <= 5).sum()
            st.metric("최적 근접", f"{near_opt}/{len(df)}건")

        scatter_col, trend_col = st.columns(2)

        with scatter_col:
            st.markdown("**RPM 편차 분석**")
            try:
                fig_sc = draw_rpm_deviation_scatter(df)
                st.pyplot(fig_sc, use_container_width=True)
                plt.close(fig_sc)
            except Exception as ex:
                st.error(str(ex))

        with trend_col:
            st.markdown("**최대 효율 추이**")
            try:
                fig_tr = draw_efficiency_trend_chart(df)
                st.pyplot(fig_tr, use_container_width=True)
                plt.close(fig_tr)
            except Exception as ex:
                st.error(str(ex))

        with st.expander("프로펠러별 비교 차트"):
            bc1, bc2 = st.columns(2)
            with bc1:
                fig_b1 = draw_efficiency_bar_chart(df)
                st.pyplot(fig_b1, use_container_width=True)
                plt.close(fig_b1)
            with bc2:
                fig_b2 = draw_optimal_rpm_bar_chart(df)
                st.pyplot(fig_b2, use_container_width=True)
                plt.close(fig_b2)

        for _, row in df.iterrows():
            diff = row["현재RPM"] - row["최적RPM"]
            if abs(diff) <= 5:
                badge, bcolor = "최적", "#2ec4b6"
            elif abs(diff) <= 20:
                badge, bcolor = "조정권장", "#ff9f1c"
            else:
                badge, bcolor = "재조정", "#e63946"

            st.markdown(
                f"""
                <div class="record-card">
                    <h4>{row['프로펠러명']}
                        <span style="font-size:0.7rem;background:{bcolor}22;color:{bcolor};
                        padding:2px 8px;border-radius:4px;margin-left:8px;">{badge}</span>
                    </h4>
                    <p>선속 {row['선속(knot)']:.1f} kn · RPM {row['현재RPM']:.0f} → 최적 {row['최적RPM']:.0f}
                       (편차 {diff:+.0f})</p>
                    <p>실측 {row['실측효율(%)']:.1f}% · 이론 {row['이론효율(%)']:.1f}%
                       · 최대 {row['최대효율(%)']:.1f}% · J={row['진수비J']:.3f}</p>
                    <p style="color:#607d8b;">{row['저장일시']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("✏️ RPM 기록 수정", expanded=False):
            edit_id = st.selectbox(
                "수정할 기록",
                df["번호"].tolist(),
                format_func=lambda x: f"#{x} {df.loc[df['번호']==x, '프로펠러명'].iloc[0]}",
                key="dash_rpm_edit_id",
            )
            edit_row = df.loc[df["번호"] == edit_id].iloc[0]
            _cur_rpm = float(edit_row["현재RPM"])
            with st.form("rpm_edit_form", clear_on_submit=False):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_name = st.text_input("프로펠러명", value=str(edit_row["프로펠러명"]))
                    e_speed = st.number_input("선속 (knot)", value=float(edit_row["선속(knot)"]), step=0.5)
                    e_dia = st.number_input("직경 (m)", value=float(edit_row["직경(m)"]), step=0.1)
                    e_rpm = st.number_input("현재 RPM", value=_cur_rpm, step=1.0)
                with ec2:
                    e_thrust = st.number_input("추력 (kN)", value=float(edit_row["추력(kN)"]), step=10.0)
                    e_power = st.number_input("축 출력 (kW)", value=float(edit_row["축출력(kW)"]), step=100.0)
                    e_rmin = st.number_input("RPM 최소", value=max(1, int(_cur_rpm - 40)), step=5)
                    e_rmax = st.number_input("RPM 최대", value=int(_cur_rpm + 40), step=5)
                if st.form_submit_button("💾 수정 저장", type="primary", use_container_width=True):
                    if _inputs_valid(e_name, e_speed, e_dia, e_rpm, e_thrust, e_power, e_rmin, e_rmax):
                        if _update_rpm_record(
                            int(edit_id), e_name, e_speed, e_dia, e_rpm,
                            e_power, e_thrust, float(e_rmin), float(e_rmax),
                        ):
                            st.success(f"#{edit_id} 수정 완료")
                            st.rerun()
                        else:
                            st.error("수정 실패")
                    else:
                        st.error("입력값을 확인해 주세요.")

        with st.expander("RPM 전체 표 / 삭제"):
            styled = df.drop(columns=["RPM편차", "효율갭"], errors="ignore").style.format({
                "선속(knot)": "{:,.1f}",
                "직경(m)": "{:,.1f}",
                "현재RPM": "{:,.0f}",
                "축출력(kW)": "{:,.0f}",
                "추력(kN)": "{:,.1f}",
                "실측효율(%)": "{:,.1f}",
                "이론효율(%)": "{:,.1f}",
                "최적RPM": "{:,.0f}",
                "최대효율(%)": "{:,.1f}",
                "진수비J": "{:,.3f}",
            })
            st.dataframe(styled, use_container_width=True, hide_index=True)

            record_ids = df["번호"].tolist()
            sel_id = st.selectbox("삭제할 RPM 기록", record_ids, key="dash_rpm_del")
            if st.button("🗑️ RPM 기록 삭제", type="primary", key="dash_rpm_del_btn"):
                if delete_record(sel_id):
                    st.success(f"#{sel_id} 삭제 완료")
                    st.rerun()
                else:
                    st.error("삭제 실패")

    st.divider()
    st.markdown("##### 🌊 출항 판단 기록")

    if not _has_departure_records:
        st.caption("저장된 출항 판단 기록이 없습니다.")
    else:
        dep_df = _departure_df.copy()
        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric("출항 판단", f"{len(dep_df)}건")
        with d2:
            allowed = (dep_df["판정"] == "출항 가능").sum()
            st.metric("출항 가능", f"{allowed}건")
        with d3:
            prohibited = (dep_df["판정"] == "출항 불가").sum()
            st.metric("출항 불가", f"{prohibited}건")

        for _, row in dep_df.iterrows():
            decision = row["판정"]
            if decision == "출항 가능":
                badge, bcolor = "출항가능", "#2ec4b6"
            elif decision == "조건부 가능":
                badge, bcolor = "조건부", "#ff9f1c"
            else:
                badge, bcolor = "출항불가", "#e63946"

            st.markdown(
                f"""
                <div class="record-card">
                    <h4>{row['선박명']}
                        <span style="font-size:0.7rem;background:{bcolor}22;color:{bcolor};
                        padding:2px 8px;border-radius:4px;margin-left:8px;">{badge}</span>
                    </h4>
                    <p>풍 {row['풍속(m/s)']:.1f} m/s · 파고 {row['파고(m)']:.1f} m · 시정 {row['시정(km)']:.1f} km</p>
                    <p>선박 길이 {row['선박길이(m)']:.0f} m · {row['사유']}</p>
                    <p style="color:#607d8b;">{row['저장일시']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("출항 판단 전체 표 / 삭제"):
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
            dep_sel = st.selectbox("삭제할 출항 기록", dep_ids, key="dash_dep_del")
            if st.button("🗑️ 출항 기록 삭제", type="primary", key="dash_dep_del_btn"):
                if delete_departure_record(dep_sel):
                    st.success(f"#{dep_sel} 삭제 완료")
                    st.rerun()
                else:
                    st.error("삭제 실패")
