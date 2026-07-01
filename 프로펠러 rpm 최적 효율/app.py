# app.py
# Streamlit 웹 앱 — 프로펠러 RPM 최적 효율 시뮬레이터

import importlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from calculator import J_OPT, calculate_all, calculate_propeller_efficiency
from charts import (
    draw_efficiency_bar_chart,
    draw_efficiency_trend_chart,
    draw_optimal_rpm_bar_chart,
    draw_rpm_deviation_scatter,
    draw_rpm_efficiency_curve,
)
from database import (
    create_database,
    delete_departure_record,
    delete_record,
    get_all_departure_records,
    get_all_records,
    save_departure_record,
    save_record,
)
import test_samples as _test_samples_mod
importlib.reload(_test_samples_mod)
RPM_CASES = _test_samples_mod.RPM_CASES
get_rpm_case_by_label = _test_samples_mod.get_rpm_case_by_label
from voyage_checker import Decision, VoyageConditions, assess_voyage

# label별 기상 기본값 (구버전 샘플에 wind 키가 없을 때 대비)
_VOYAGE_WEATHER_BY_LABEL = {
    "FP-4500 · 일반 운항": (5.0, 1.0, 5.0),
    "CP-3800 · 저속 화물선": (10.0, 1.8, 2.0),
    "FP-5200 · 고속 운항": (6.0, 1.2, 4.0),
    "FP-4500 · RPM 과다": (14.0, 2.5, 1.0),
    "FP-4500 · RPM 부족": (8.0, 1.5, 0.9),
}


def _voyage_fields_from_rpm(case: dict) -> dict:
    """① 출항 조건 입력값 — RPM 샘플과 동일 시나리오"""
    label = case.get("label", "")
    wind, wave, vis = _VOYAGE_WEATHER_BY_LABEL.get(label, (5.0, 1.0, 5.0))
    diameter = float(case.get("propeller_diameter", 4.5))
    return {
        "vessel_name": case.get("propeller_name", ""),
        "wind": case.get("wind", wind),
        "wave": case.get("wave", wave),
        "visibility": case.get("visibility", vis),
        "length": round(diameter * 11),
    }


def _rpm_case_preview(case: dict) -> dict:
    return calculate_all(
        case["vessel_speed"],
        case["rpm"],
        case["propeller_diameter"],
        case["thrust"],
        case["shaft_power"],
        case["rpm_min"],
        case["rpm_max"],
    )


# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="선박 운항 분석 시스템",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

create_database()

# ──────────────────────────────────────────
# 커스텀 테마 CSS
# ──────────────────────────────────────────
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0a1628 0%, #0d2137 50%, #0a1628 100%); }
    [data-testid="stSidebar"] {
        background: #f5f7fa;
        border-right: 1px solid #dde3ea;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: #1a1a1a !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }
    h1, h2, h3, h4 { color: #e8f1f8 !important; }
    p, label, .stMarkdown { color: #b0bec5; }
    div[data-testid="stMetric"] {
        background: #132337; border: 1px solid #1e3a5f; border-radius: 10px; padding: 12px;
    }
    div[data-testid="stMetric"] label { color: #78909c !important; font-size: 0.8rem; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .diag-card {
        background: #132337; border-radius: 12px; padding: 20px 22px;
        border-left: 5px solid VAR_BORDER; margin-bottom: 16px;
    }
    .diag-title { font-size: 1.15rem; font-weight: 700; color: #e8f1f8; margin-bottom: 6px; }
    .diag-sub { font-size: 0.88rem; color: #90a4ae; margin-bottom: 14px; }
    .diag-big { font-size: 2rem; font-weight: 800; color: #00b4d8; line-height: 1.2; }
    .diag-delta { font-size: 0.95rem; color: #2ec4b6; margin-top: 8px; }
    .j-bar-wrap {
        background: #1b2838; border-radius: 8px; height: 28px; position: relative;
        margin: 8px 0 4px; overflow: hidden;
    }
    .j-opt-zone {
        position: absolute; top: 0; height: 100%;
        background: rgba(46, 196, 182, 0.25); border-left: 1px solid #2ec4b6; border-right: 1px solid #2ec4b6;
    }
    .j-marker {
        position: absolute; top: 2px; width: 4px; height: 24px;
        background: #ff9f1c; border-radius: 2px; transform: translateX(-2px);
    }
    .hero-caption { color: #607d8b; font-size: 0.82rem; letter-spacing: 0.04em; text-transform: uppercase; }
    .record-card {
        background: #132337; border: 1px solid #1e3a5f; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 10px;
    }
    .record-card h4 { margin: 0 0 8px; color: #00b4d8 !important; }
    .record-card p { margin: 2px 0; font-size: 0.85rem; color: #90a4ae; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────
# session_state
# ──────────────────────────────────────────
_RESET_VALUES = {
    "form_propeller_name": "",
    "form_vessel_speed": 0.0,
    "form_propeller_diameter": 0.0,
    "form_thrust": 0.0,
    "form_shaft_power": 0.0,
    "form_rpm_min": 0,
    "form_rpm_max": 0,
    "form_rpm": 0,
}

for _k, _v in _RESET_VALUES.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if "saved" not in st.session_state:
    st.session_state.saved = False
if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = None
if "_pending_reset" not in st.session_state:
    st.session_state._pending_reset = False
if "_pending_sample" not in st.session_state:
    st.session_state._pending_sample = None
if "sample_pick" not in st.session_state:
    st.session_state.sample_pick = RPM_CASES[0]["label"]
elif st.session_state.sample_pick not in {c["label"] for c in RPM_CASES}:
    st.session_state.sample_pick = RPM_CASES[0]["label"]

_VOYAGE_RESET = {
    "voy_vessel_name": "",
    "voy_wind": 0.0,
    "voy_wave": 0.0,
    "voy_visibility": 0.0,
    "voy_length": 0.0,
    "voy_engine_ok": True,
    "voy_navigation_ok": True,
    "voy_lifesaving_ok": True,
    "voy_crew_ready": True,
    "voy_weather_warning": False,
}
for _vk, _vv in _VOYAGE_RESET.items():
    if _vk not in st.session_state:
        st.session_state[_vk] = _vv

if "voyage_saved" not in st.session_state:
    st.session_state.voyage_saved = False
if "voyage_last_snapshot" not in st.session_state:
    st.session_state.voyage_last_snapshot = None
if "voyage_decision" not in st.session_state:
    st.session_state.voyage_decision = None
if "voyage_confirmed" not in st.session_state:
    st.session_state.voyage_confirmed = False
if "_pending_voyage_reset" not in st.session_state:
    st.session_state._pending_voyage_reset = False
if "_pending_voyage_sample" not in st.session_state:
    st.session_state._pending_voyage_sample = None


def _apply_reset_values():
    """위젯 생성 전에만 호출 — 초기화(전부 0, 프로펠러명 빈칸)"""
    for k, v in _RESET_VALUES.items():
        st.session_state[k] = v
    st.session_state.saved = False
    st.session_state.last_snapshot = None


def _apply_sample_case(case: dict):
    """위젯 생성 전에만 호출 — RPM 샘플 적용"""
    st.session_state.sample_pick = case["label"]
    st.session_state.form_propeller_name = case["propeller_name"]
    st.session_state.form_vessel_speed = case["vessel_speed"]
    st.session_state.form_propeller_diameter = case["propeller_diameter"]
    st.session_state.form_thrust = case["thrust"]
    st.session_state.form_shaft_power = case["shaft_power"]
    st.session_state.form_rpm_min = int(case["rpm_min"])
    st.session_state.form_rpm_max = int(case["rpm_max"])
    st.session_state.form_rpm = int(case["rpm"])
    st.session_state.saved = False


def _apply_voyage_sample(case: dict):
    """위젯 생성 전에만 호출 — 출항 샘플 적용 (RPM 샘플과 동일 시나리오)"""
    st.session_state.sample_pick = case["label"]
    voy = _voyage_fields_from_rpm(case)
    st.session_state.voy_vessel_name = voy["vessel_name"]
    st.session_state.voy_wind = voy["wind"]
    st.session_state.voy_wave = voy["wave"]
    st.session_state.voy_visibility = voy["visibility"]
    st.session_state.voy_length = float(voy["length"])
    st.session_state.voyage_saved = False
    st.session_state.voyage_decision = None
    st.session_state.voyage_confirmed = False
if st.session_state._pending_reset:
    _apply_reset_values()
    st.session_state._pending_reset = False

if st.session_state._pending_sample is not None:
    _apply_sample_case(st.session_state._pending_sample)
    st.session_state._pending_sample = None


def _apply_voyage_reset():
    for k, v in _VOYAGE_RESET.items():
        st.session_state[k] = v
    st.session_state.voyage_saved = False
    st.session_state.voyage_last_snapshot = None
    st.session_state.voyage_decision = None
    st.session_state.voyage_confirmed = False


if st.session_state._pending_voyage_reset:
    _apply_voyage_reset()
    st.session_state._pending_voyage_reset = False

if st.session_state._pending_voyage_sample is not None:
    _apply_voyage_sample(st.session_state._pending_voyage_sample)
    st.session_state._pending_voyage_sample = None


def _get_diagnosis(rpm: float, optimal_rpm: float) -> tuple[str, str, str, str]:
    """상태 색상, 제목, 아이콘, 메시지 반환"""
    diff = rpm - optimal_rpm
    abs_diff = abs(diff)

    if abs_diff <= 5:
        return "#2ec4b6", "최적 운항 구간", "🟢", f"현재 RPM이 최적값({optimal_rpm:.0f})에 근접합니다."
    if abs_diff <= 20:
        direction = "올리" if diff < 0 else "낮추"
        return "#ff9f1c", "RPM 조정 권장", "🟡", f"RPM을 {abs_diff:.0f} 정도 {direction}면 효율이 개선됩니다."
    direction = "올리" if diff < 0 else "낮추"
    return "#e63946", "RPM 재조정 필요", "🔴", f"최적 RPM과 {abs_diff:.0f} RPM 차이 — {direction}세요."


def _j_gauge_html(J: float, j_low: float = 0.55, j_high: float = 0.75) -> str:
    """진수비 J 시각화 HTML"""
    j_min, j_max = 0.30, 1.20
    pct = max(0, min(100, (J - j_min) / (j_max - j_min) * 100))
    opt_l = (j_low - j_min) / (j_max - j_min) * 100
    opt_w = (j_high - j_low) / (j_max - j_min) * 100
    in_zone = j_low <= J <= j_high
    zone_text = "최적 구간 내" if in_zone else "최적 구간 밖"
    zone_color = "#2ec4b6" if in_zone else "#ff9f1c"

    return f"""
    <div style="background:#132337;border-radius:10px;padding:14px 16px;border:1px solid #1e3a5f;margin-bottom:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#78909c;font-size:0.82rem;">진수비 J (Advance Ratio)</span>
            <span style="color:{zone_color};font-size:0.82rem;font-weight:600;">{zone_text}</span>
        </div>
        <div style="font-size:1.6rem;font-weight:700;color:#e8f1f8;margin:4px 0 10px;">{J:.3f}</div>
        <div class="j-bar-wrap">
            <div class="j-opt-zone" style="left:{opt_l:.1f}%;width:{opt_w:.1f}%;"></div>
            <div class="j-marker" style="left:{pct:.1f}%;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:#607d8b;">
            <span>{j_min}</span><span style="color:#2ec4b6;">최적 {j_low}~{j_high}</span><span>{j_max}</span>
        </div>
    </div>
    """


def _inputs_valid(name, speed, dia, rpm, thrust, power, rmin, rmax) -> bool:
    return bool(
        name and speed > 0 and dia > 0 and rpm > 0 and thrust > 0
        and power > 0 and rmin > 0 and rmax > 0 and rmin < rmax
    )


def _voyage_conditions_valid(wind, wave, vis, length) -> bool:
    """기상·선박 치수만 있으면 자동 판정 가능 (선박명은 저장 시에만 필요)"""
    return length >= 1.0 and wind >= 0 and wave >= 0 and vis >= 0


def _voyage_style(decision: Decision) -> tuple[str, str]:
    if decision == Decision.ALLOWED:
        return "#2ec4b6", "🟢"
    if decision == Decision.CONDITIONAL:
        return "#ff9f1c", "🟡"
    return "#e63946", "🔴"


# ──────────────────────────────────────────
# 사이드바 — 연습용 시나리오 + RPM 입력
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧪 연습용 시나리오")
    st.caption("① 출항 조건 입력 → **확인** 후 ② RPM 순서로 테스트하세요.")

    rpm_labels = [c["label"] for c in RPM_CASES]
    st.selectbox("시나리오", rpm_labels, key="sample_pick")
    _picked = get_rpm_case_by_label(st.session_state.sample_pick)
    _voy = _voyage_fields_from_rpm(_picked)
    _rpm_prev = _rpm_case_preview(_picked)

    st.caption(_picked["description"])
    st.markdown(
        f"**① 출항** · {_voy['vessel_name']} · 풍 {_voy['wind']:g}m/s · "
        f"파고 {_voy['wave']:g}m · 시정 {_voy['visibility']:g}km · {_voy['length']:g}m"
    )
    st.markdown(
        f"**② RPM** · {_picked['vessel_speed']:g}kn · RPM {_picked['rpm']:g} · "
        f"직경 {_picked['propeller_diameter']:g}m · 최적 **{_rpm_prev['optimal_rpm']:.0f}**"
    )

    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("① 출항", key="sb_voy_load", use_container_width=True):
            st.session_state._pending_voyage_sample = _picked
            st.rerun()
    with bcol2:
        if st.button("② RPM", key="sb_rpm_load", use_container_width=True):
            st.session_state._pending_sample = _picked
            st.rerun()
    if st.button("전체 불러오기 (①+②)", key="sb_load_all", use_container_width=True, type="primary"):
        st.session_state._pending_voyage_sample = _picked
        st.session_state._pending_sample = _picked
        st.rerun()

    st.divider()
    st.markdown("### ⚓ ② RPM 입력")
    st.caption("값을 입력하면 효율·최적 RPM이 **자동 계산**됩니다.")

    propeller_name = st.text_input("프로펠러명", key="form_propeller_name")
    vessel_speed = st.number_input("선속 (knot)", min_value=0.0, step=0.5, key="form_vessel_speed")
    propeller_diameter = st.number_input(
        "직경 (m)", min_value=0.0, step=0.1, format="%.1f", key="form_propeller_diameter"
    )
    thrust = st.number_input("추력 (kN)", min_value=0.0, step=10.0, key="form_thrust")
    shaft_power = st.number_input("축 출력 (kW)", min_value=0.0, step=100.0, key="form_shaft_power")

    st.markdown("##### RPM 탐색 범위")
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        rpm_min = st.number_input("최소", min_value=0, step=5, key="form_rpm_min")
    with rcol2:
        rpm_max = st.number_input("최대", min_value=0, step=5, key="form_rpm_max")

    # RPM 슬라이더 — 범위가 유효하지 않으면 0~100 기본 슬라이더
    if int(rpm_max) > int(rpm_min):
        _rmin = int(rpm_min)
        _rmax = int(rpm_max)
        _rpm_val = max(_rmin, min(_rmax, int(st.session_state.form_rpm)))
    else:
        _rmin = 0
        _rmax = 100
        _rpm_val = 0

    rpm = st.slider(
        "현재 RPM",
        min_value=_rmin,
        max_value=_rmax,
        value=_rpm_val,
        key="form_rpm",
    )

    st.divider()

    if st.button("🔄 초기화", key="rpm_reset", use_container_width=True):
        st.session_state._pending_reset = True
        st.rerun()


# ──────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────
st.markdown('<p class="hero-caption">Vessel Operation Workflow</p>', unsafe_allow_html=True)
st.title("선박 운항 분석 시스템")
st.markdown(
    "**① 출항 조건 확인** → **② RPM 최적 효율** → **③ 운항 속도** 순서로 분석합니다."
)

if st.session_state.voyage_confirmed:
    _dec = st.session_state.voyage_decision or "확인 완료"
    st.success(f"✅ ① 출항 조건 확인 완료 ({_dec}) — ② RPM 최적 효율 탭으로 진행하세요.")
else:
    st.info("👈 먼저 **① 출항 조건** 탭에서 조건을 입력하고 **확인** 버튼을 눌러 주세요.")

_saved_df = get_all_records()
_departure_df = get_all_departure_records()
_has_rpm_records = not _saved_df.empty
_has_departure_records = not _departure_df.empty

_tab_labels = [
    "① 🌊 출항 조건",
    "② ⚓ RPM 최적 효율",
    "③ 🚢 운항 속도",
    "📊 운항 대시보드",
]
_tabs = st.tabs(_tab_labels)
voyage_panel = _tabs[0]
sim_panel = _tabs[1]
speed_panel = _tabs[2]
tab_dash = _tabs[3]


# ════════════════════════════════════════════
# ② RPM 시뮬레이션
# ════════════════════════════════════════════
with sim_panel:

    if not st.session_state.voyage_confirmed:
        st.warning(
            "🔒 **① 출항 조건** 탭에서 기상·선박 정보를 입력한 뒤 "
            "**「확인하고 ② RPM으로 진행」** 버튼을 눌러 주세요."
        )
    else:
        if st.session_state.voyage_decision == Decision.PROHIBITED.value:
            st.warning(
                "⚠️ 출항 판단 결과 **출항 불가**입니다. RPM 분석은 참고용이며, "
                "실제 운항은 선장·운항관리자 판단과 최신 기상정보를 따르세요."
            )
        elif st.session_state.voyage_decision == Decision.CONDITIONAL.value:
            st.info("ℹ️ 출항 조건: **조건부 가능** — ① 출항 조건 탭에서 사유를 확인하세요.")

        snapshot = (
            propeller_name, vessel_speed, propeller_diameter,
            rpm, thrust, shaft_power, rpm_min, rpm_max,
        )
        if st.session_state.last_snapshot != snapshot:
            st.session_state.saved = False
            st.session_state.last_snapshot = snapshot

        if not _inputs_valid(
            propeller_name, vessel_speed, propeller_diameter,
            rpm, thrust, shaft_power, rpm_min, rpm_max,
        ):
            st.info("👈 사이드바 **전체 불러오기** 또는 **② RPM**으로 샘플을 불러오세요.")
        else:
            try:
                result = calculate_all(
                    vessel_speed, rpm, propeller_diameter,
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

                border_color, diag_title, diag_icon, diag_msg = _get_diagnosis(rpm, optimal_rpm)
                eff_ratio = model_eff / max_eff * 100 if max_eff > 0 else 0
                eff_gain = max_eff - model_eff

                chart_col, panel_col = st.columns([1.65, 1])

                with chart_col:
                    st.markdown("#### RPM – 효율 곡선")
                    fig_curve = draw_rpm_efficiency_curve(
                        vessel_speed, propeller_diameter,
                        float(rpm_min), float(rpm_max),
                        current_rpm=rpm, optimal_rpm=optimal_rpm,
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
                    st.markdown("#### 운항 진단")
                    st.markdown(
                        f"""
                        <div class="diag-card" style="border-left-color:{border_color};">
                            <div class="diag-title">{diag_icon} {diag_title}</div>
                            <div class="diag-sub">{diag_msg}</div>
                            <div class="diag-big">{rpm:.0f} → {optimal_rpm:.0f} RPM</div>
                            <div class="diag-delta">효율 개선 여지 : +{eff_gain:.1f}%p (이론 기준)</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(_j_gauge_html(J), unsafe_allow_html=True)

                    st.markdown("##### 현재 vs 최적 비교")
                    compare_df = pd.DataFrame({
                        "항목": ["RPM", "이론 효율 (%)", "진수비 J"],
                        "현재 운항": [
                            f"{rpm:.0f}",
                            f"{model_eff:.1f}",
                            f"{J:.3f}",
                        ],
                        "최적 운항": [
                            f"{optimal_rpm:.0f}",
                            f"{optimal_J_eff:.1f}",
                            f"{J_OPT:.3f}",
                        ],
                        "차이": [
                            f"{rpm - optimal_rpm:+.0f}",
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
                        st.success("저장 완료된 분석입니다.")
                        st.button("💾 저장됨", key="rpm_saved_btn", disabled=True, use_container_width=True)
                    else:
                        if st.button("💾 이 결과 저장", key="rpm_save", use_container_width=True, type="primary"):
                            ok = save_record(
                                propeller_name=propeller_name,
                                vessel_speed=vessel_speed,
                                propeller_diameter=propeller_diameter,
                                rpm=float(rpm),
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
                                st.success("저장되었습니다!")
                                st.rerun()
                            else:
                                st.error("저장 실패")

            except ValueError as e:
                st.error(f"계산 오류 : {e}")


# ════════════════════════════════════════════
# ① 출항 판단
# ════════════════════════════════════════════
with voyage_panel:

    st.markdown("#### 🌊 ① 출항 조건 점검")
    st.markdown(
        "풍속·파고·시정·선박 상태를 입력하면 **자동 판정**됩니다. "
        "결과를 확인한 뒤 **「확인하고 ② RPM으로 진행」** 을 눌러 다음 단계로 넘어가세요."
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
                    st.success("✅ 출항 가능 — 확인 후 ② RPM으로 진행할 수 있습니다.")
                elif vresult.decision == Decision.CONDITIONAL:
                    st.warning("⚠️ 조건부 가능 — 사유를 검토한 뒤 확인 버튼을 눌러 주세요.")
                else:
                    st.error("🚫 출항 불가 — 판정을 확인한 뒤, 참고용으로 ② RPM 분석이 가능합니다.")

                st.divider()
                if st.session_state.voyage_confirmed:
                    st.success("✅ 확인 완료 — **② RPM 최적 효율** 탭으로 이동하세요.")
                    if st.button("🔄 출항 조건 다시 입력", key="voy_unconfirm", use_container_width=True):
                        st.session_state.voyage_confirmed = False
                        st.rerun()
                elif st.button(
                    "✅ 확인하고 ② RPM으로 진행",
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
                            st.success("저장되었습니다!")
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


# ════════════════════════════════════════════
# ③ 운항 속도 (준비 중)
# ════════════════════════════════════════════
with speed_panel:

    if not st.session_state.voyage_confirmed:
        st.warning("🔒 **① 출항 조건** 탭에서 **확인**을 완료한 뒤 이용할 수 있습니다.")
    else:
        st.markdown("#### 🚢 운항 속도 분석")
        st.caption("① 출항 조건 · ② RPM 최적 효율 확인 후 운항 속도를 분석합니다.")

        st.info(
            "🚧 **운항 속도** 기능은 준비 중입니다.\n\n"
            "파일을 추가해 주시면 이 탭에서 **선속·연료·운항 효율** 등을 분석할 수 있도록 연결하겠습니다."
        )

        st.markdown("##### 예정 워크플로")
        st.markdown(
            """
            1. **① 출항 조건** — 기상·선박 상태로 출항 가능 여부 확인
            2. **② RPM 최적 효율** — 프로펠러 RPM·효율 최적화
            3. **③ 운항 속도** — 목적지까지 경제 속도·ETA 분석 *(준비 중)*
            """
        )


# ════════════════════════════════════════════
# 운항 대시보드
# ════════════════════════════════════════════
with tab_dash:

    dash_header, dash_refresh = st.columns([4, 1])
    with dash_header:
        st.markdown("#### 운항 대시보드")
    with dash_refresh:
        if st.button("🔄 새로고침", key="dash_refresh", use_container_width=True):
            st.rerun()

    if not _has_rpm_records and not _has_departure_records:
        st.info(
            "📭 저장된 기록이 없습니다. "
            "**① 출항 조건** 또는 **② RPM 최적 효율** 탭에서 결과를 저장해 보세요."
        )
    else:
        st.markdown("##### ⚓ RPM 분석 기록")
        if not _has_rpm_records:
            st.caption("저장된 RPM 분석 기록이 없습니다.")
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
