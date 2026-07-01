# app.py
# Streamlit 웹 앱의 메인 파일 (화면 구성 담당)
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
from database import create_database, save_record, get_all_records, delete_record
from calculator import calculate_all
from charts import (          # ← 새로 추가
    draw_fuel_bar_chart,
    draw_cost_bar_chart,
    draw_cost_trend_chart
)


# ──────────────────────────────────────────
# 앱 기본 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="선박 연료 비용 계산기",
    page_icon="🚢",
    layout="wide"
)

create_database()

# ──────────────────────────────────────────
# session_state 초기화
# ──────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result     = None
if "input_data" not in st.session_state:
    st.session_state.input_data = None
if "saved" not in st.session_state:
    st.session_state.saved      = False


# ──────────────────────────────────────────
# 제목
# ──────────────────────────────────────────
st.title("🚢 선박 연료 소비량 및 운항 비용 계산기")
st.markdown("운항 정보를 입력하면 **총 연료 소비량**과 **운항 비용**을 계산해 드립니다.")
st.divider()


# ──────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────
tab_calc, tab_history = st.tabs(["⚙️ 계산", "📋 기록 조회"])


# ════════════════════════════════════════════
# 탭 1 : 계산 화면 (Step 9와 동일)
# ════════════════════════════════════════════
with tab_calc:

    st.subheader("📋 운항 정보 입력")

    ship_name = st.text_input(
        label="선박명",
        placeholder="예 : 독도호",
        help="운항할 선박의 이름을 입력하세요."
    )

    col1, col2 = st.columns(2)

    with col1:
        distance = st.number_input(
            label="운항 거리 (km)",
            min_value=0.0, value=0.0, step=10.0,
            help="출발지에서 목적지까지의 거리를 입력하세요."
        )
        operation_hours = st.number_input(
            label="운항 시간 (hour)",
            min_value=0.0, value=0.0, step=1.0,
            help="총 운항에 걸리는 시간을 입력하세요."
        )
        fuel_price = st.number_input(
            label="연료 단가 (원/L)",
            min_value=0.0, value=0.0, step=100.0,
            help="연료 1리터당 가격을 입력하세요."
        )

    with col2:
        speed = st.number_input(
            label="평균 속도 (km/h)",
            min_value=0.0, value=0.0, step=1.0,
            help="운항 중 평균 속도를 입력하세요."
        )
        fuel_per_hour = st.number_input(
            label="시간당 연료 소비량 (L/h)",
            min_value=0.0, value=0.0, step=10.0,
            help="엔진이 1시간에 소비하는 연료량을 입력하세요."
        )

    st.divider()

    btn_col1, btn_col2 = st.columns([4, 1])

    with btn_col1:
        calculate_button = st.button(
            label="⚙️ 계산하기",
            use_container_width=True,
            type="primary"
        )
    with btn_col2:
        reset_button = st.button(
            label="🔄 초기화",
            use_container_width=True
        )

    if reset_button:
        st.session_state.result     = None
        st.session_state.input_data = None
        st.session_state.saved      = False
        st.rerun()

    if calculate_button:
        if not ship_name:
            st.warning("⚠️ 선박명을 입력해 주세요.")
        elif operation_hours <= 0:
            st.warning("⚠️ 운항 시간은 0보다 커야 합니다.")
        elif fuel_per_hour <= 0:
            st.warning("⚠️ 시간당 연료 소비량은 0보다 커야 합니다.")
        elif fuel_price <= 0:
            st.warning("⚠️ 연료 단가는 0보다 커야 합니다.")
        else:
            try:
                result = calculate_all(operation_hours, fuel_per_hour, fuel_price)
                st.session_state.result = result
                st.session_state.input_data = {
                    "ship_name"      : ship_name,
                    "distance"       : distance,
                    "speed"          : speed,
                    "operation_hours": operation_hours,
                    "fuel_per_hour"  : fuel_per_hour,
                    "fuel_price"     : fuel_price
                }
                st.session_state.saved = False
            except ValueError as e:
                st.error(f"❌ 계산 오류 : {e}")

    if st.session_state.result is not None:

        result     = st.session_state.result
        input_data = st.session_state.input_data
        total_fuel = result["total_fuel"]
        total_cost = result["total_cost"]

        st.divider()
        st.subheader("📊 계산 결과")

        metric_col1, metric_col2 = st.columns(2)

        with metric_col1:
            st.metric(
                label="⛽ 총 연료 소비량",
                value=f"{total_fuel:,.1f} L",
                delta=f"≈ {total_fuel / 1000:,.2f} 톤"
            )
        with metric_col2:
            st.metric(
                label="💰 총 운항 비용",
                value=f"{total_cost:,.0f} 원",
                delta=f"≈ {total_cost / 10000:,.1f} 만원"
            )

        st.info(
            f"""
            **📌 계산 상세 내역**

            - 운항 시간 **{input_data['operation_hours']:,.1f} h** ×
              시간당 연료 소비량 **{input_data['fuel_per_hour']:,.1f} L/h**
              = 총 연료 소비량 **{total_fuel:,.1f} L**

            - 총 연료 소비량 **{total_fuel:,.1f} L** ×
              연료 단가 **{input_data['fuel_price']:,.0f} 원/L**
              = 총 운항 비용 **{total_cost:,.0f} 원**
            """
        )

        st.divider()
        st.subheader("📋 입력값 요약")

        summary_col1, summary_col2 = st.columns(2)

        with summary_col1:
            st.write(f"- **선박명** : {input_data['ship_name']}")
            st.write(f"- **운항 거리** : {input_data['distance']:,.1f} km")
            st.write(f"- **평균 속도** : {input_data['speed']:,.1f} km/h")
        with summary_col2:
            st.write(f"- **운항 시간** : {input_data['operation_hours']:,.1f} hour")
            st.write(f"- **시간당 연료 소비량** : {input_data['fuel_per_hour']:,.1f} L/h")
            st.write(f"- **연료 단가** : {input_data['fuel_price']:,.0f} 원/L")

        st.divider()

        if st.session_state.saved:
            st.success("✅ 이미 저장된 결과입니다.")
            st.button("💾 저장 완료", disabled=True, use_container_width=True)
        else:
            save_button = st.button(
                label="💾 결과 저장하기",
                use_container_width=True
            )
            if save_button:
                success = save_record(
                    ship_name       = input_data["ship_name"],
                    distance        = input_data["distance"],
                    speed           = input_data["speed"],
                    operation_hours = input_data["operation_hours"],
                    fuel_per_hour   = input_data["fuel_per_hour"],
                    fuel_price      = input_data["fuel_price"],
                    total_fuel      = total_fuel,
                    total_cost      = total_cost
                )
                if success:
                    st.session_state.saved = True
                    st.success("✅ 결과가 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 저장에 실패했습니다. 다시 시도해 주세요.")


# ════════════════════════════════════════════
# 탭 2 : 기록 조회 + 그래프
# ════════════════════════════════════════════
with tab_history:

    st.subheader("📋 운항 기록 조회")

    if st.button("🔄 목록 새로고침", key="refresh_btn"):
        st.rerun()

    df = get_all_records()

    if df.empty:
        st.info("📭 저장된 기록이 없습니다. 계산 탭에서 결과를 저장해 보세요.")

    else:
        # ── 요약 통계 ──────────────────────────
        st.subheader("📈 요약 통계")

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric(label="📁 총 기록 수",    value=f"{len(df)} 건")
        with stat_col2:
            st.metric(label="⛽ 평균 연료 소비량", value=f"{df['총연료(L)'].mean():,.1f} L")
        with stat_col3:
            st.metric(label="💰 평균 운항 비용",  value=f"{df['총비용(원)'].mean():,.0f} 원")
        with stat_col4:
            st.metric(label="💳 누적 총 비용",   value=f"{df['총비용(원)'].sum():,.0f} 원")

        st.divider()

        # ── 그래프 영역 ────────────────────────
        st.subheader("📊 데이터 시각화")

        # 그래프가 2개 이상의 데이터가 있을 때만 의미 있음
        # 1건일 때도 표시하되 안내 메시지 추가
        if len(df) == 1:
            st.caption("💡 데이터가 2건 이상이면 비교 그래프가 더욱 유용합니다.")

        # 그래프 1, 2 : 나란히 배치
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**⛽ 선박별 연료 소비량**")
            try:
                fig_fuel = draw_fuel_bar_chart(df)
                # st.pyplot() : matplotlib Figure를 Streamlit에 표시
                st.pyplot(fig_fuel)
                # 메모리 절약 : 표시 후 Figure 객체 닫기
                plt.close(fig_fuel)
            except Exception as e:
                st.error(f"그래프 오류 : {e}")

        with chart_col2:
            st.markdown("**💰 선박별 운항 비용**")
            try:
                fig_cost = draw_cost_bar_chart(df)
                st.pyplot(fig_cost)
                plt.close(fig_cost)
            except Exception as e:
                st.error(f"그래프 오류 : {e}")

        # 그래프 3 : 전체 너비 사용
        st.markdown("**📈 운항 비용 추이**")
        try:
            fig_trend = draw_cost_trend_chart(df)
            st.pyplot(fig_trend)
            plt.close(fig_trend)
        except Exception as e:
            st.error(f"그래프 오류 : {e}")

        st.divider()

        # ── 전체 기록 표 ───────────────────────
        st.subheader("📄 전체 기록")

        styled_df = df.style.format({
            "운항거리(km)"   : "{:,.1f}",
            "평균속도(km/h)" : "{:,.1f}",
            "운항시간(h)"    : "{:,.1f}",
            "시간당연료(L/h)": "{:,.1f}",
            "연료단가(원/L)" : "{:,.0f}",
            "총연료(L)"      : "{:,.1f}",
            "총비용(원)"     : "{:,.0f}"
        })

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        # ── 개별 기록 삭제 ─────────────────────
        st.divider()
        st.subheader("🗑️ 기록 삭제")

        record_ids  = df["번호"].tolist()
        selected_id = st.selectbox(
            label="삭제할 기록 번호를 선택하세요",
            options=record_ids,
            help="선택한 번호의 기록이 영구 삭제됩니다."
        )

        selected_row = df[df["번호"] == selected_id].iloc[0]
        st.write(
            f"선택된 기록 : **{selected_row['선박명']}** | "
            f"총 연료 {selected_row['총연료(L)']:,.1f} L | "
            f"총 비용 {selected_row['총비용(원)']:,.0f} 원 | "
            f"저장일시 {selected_row['저장일시']}"
        )

        if st.button(label="🗑️ 선택한 기록 삭제", type="primary"):
            success = delete_record(selected_id)
            if success:
                st.success(f"✅ 번호 {selected_id} 기록이 삭제되었습니다.")
                st.rerun()
            else:
                st.error("❌ 삭제에 실패했습니다.")