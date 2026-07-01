# shared.py
# Streamlit 멀티페이지 앱 — 공통 imports, session state, 사이드바, 헬퍼

import importlib
import sqlite3

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
    DB_PATH,
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


def _update_rpm_record(
    record_id: int,
    propeller_name: str,
    vessel_speed: float,
    propeller_diameter: float,
    rpm: float,
    shaft_power: float,
    thrust: float,
    rpm_min: float,
    rpm_max: float,
) -> bool:
    """저장된 RPM 기록 수정 (database.update_record 대신 app에서 직접 처리)"""
    try:
        result = calculate_all(
            vessel_speed, rpm, propeller_diameter,
            thrust, shaft_power, rpm_min, rpm_max,
        )
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE rpm_records SET
                propeller_name = ?, vessel_speed = ?, propeller_diameter = ?,
                rpm = ?, shaft_power = ?, thrust = ?,
                measured_efficiency = ?, model_efficiency = ?,
                optimal_rpm = ?, max_efficiency = ?, advance_ratio = ?
            WHERE id = ?
            """,
            (
                propeller_name,
                vessel_speed,
                propeller_diameter,
                rpm,
                shaft_power,
                thrust,
                result["measured_efficiency"],
                result["model_efficiency"],
                result["optimal_rpm"],
                result["max_efficiency"],
                result["advance_ratio"],
                record_id,
            ),
        )
        ok = cur.rowcount > 0
        conn.commit()
        conn.close()
        return ok
    except (sqlite3.Error, ValueError):
        return False


def init_session_state():
    """session_state 키 초기화 (앱 시작 시 1회 호출)"""
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
    if "rpm_confirmed" not in st.session_state:
        st.session_state.rpm_confirmed = False
    if "rpm_confirm_snapshot" not in st.session_state:
        st.session_state.rpm_confirm_snapshot = None
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
    st.session_state.rpm_confirmed = False
    st.session_state.rpm_confirm_snapshot = None


def _rpm_input_snapshot():
    return (
        st.session_state.form_propeller_name,
        st.session_state.form_vessel_speed,
        st.session_state.form_propeller_diameter,
        st.session_state.form_rpm,
        st.session_state.form_thrust,
        st.session_state.form_shaft_power,
        st.session_state.form_rpm_min,
        st.session_state.form_rpm_max,
    )


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
    st.session_state.rpm_confirmed = False


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


def _apply_voyage_reset():
    for k, v in _VOYAGE_RESET.items():
        st.session_state[k] = v
    st.session_state.voyage_saved = False
    st.session_state.voyage_last_snapshot = None
    st.session_state.voyage_decision = None
    st.session_state.voyage_confirmed = False


def process_pending_actions():
    """버튼 클릭 후 rerun 시, 위젯보다 먼저 처리"""
    if st.session_state._pending_reset:
        _apply_reset_values()
        st.session_state._pending_reset = False

    if st.session_state._pending_sample is not None:
        _apply_sample_case(st.session_state._pending_sample)
        st.session_state._pending_sample = None

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


def apply_theme():
    """커스텀 테마 CSS"""
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


def render_sidebar() -> dict:
    """사이드바 — 연습용 시나리오 + RPM 입력"""
    with st.sidebar:
        st.markdown("### 🧪 연습용 시나리오")
        st.caption("① 출항 확인 → ② RPM 불러오기 → **✅ ② RPM 확인** → 결과 확인")

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

        if st.session_state.rpm_confirmed:
            st.success("✅ ② RPM 확인 완료")
        elif st.button("✅ ② RPM 확인", key="sb_rpm_confirm", use_container_width=True):
            if _inputs_valid(
                st.session_state.form_propeller_name,
                st.session_state.form_vessel_speed,
                st.session_state.form_propeller_diameter,
                st.session_state.form_rpm,
                st.session_state.form_thrust,
                st.session_state.form_shaft_power,
                st.session_state.form_rpm_min,
                st.session_state.form_rpm_max,
            ):
                st.session_state.rpm_confirmed = True
                st.session_state.rpm_confirm_snapshot = _rpm_input_snapshot()
                st.session_state.saved = False
                st.rerun()
            else:
                st.error("② RPM 불러오기 후 입력값을 확인하거나, 아래에서 직접 입력해 주세요.")

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

        if st.session_state.rpm_confirmed:
            if st.button("🔄 RPM 다시 수정", key="rpm_unconfirm", use_container_width=True):
                st.session_state.rpm_confirmed = False
                st.session_state.rpm_confirm_snapshot = None
                st.session_state.saved = False
                st.rerun()

        if st.button("🔄 초기화", key="rpm_reset", use_container_width=True):
            st.session_state._pending_reset = True
            st.rerun()

        if st.session_state.rpm_confirmed and st.session_state.rpm_confirm_snapshot != (
            propeller_name, vessel_speed, propeller_diameter,
            rpm, thrust, shaft_power, rpm_min, rpm_max,
        ):
            st.session_state.rpm_confirmed = False
            st.session_state.rpm_confirm_snapshot = None
            st.session_state.saved = False

    return {
        "propeller_name": st.session_state.form_propeller_name,
        "vessel_speed": st.session_state.form_vessel_speed,
        "propeller_diameter": st.session_state.form_propeller_diameter,
        "rpm": st.session_state.form_rpm,
        "thrust": st.session_state.form_thrust,
        "shaft_power": st.session_state.form_shaft_power,
        "rpm_min": st.session_state.form_rpm_min,
        "rpm_max": st.session_state.form_rpm_max,
    }


def render_workflow_banner():
    """출항/RPM 확인 상태 안내 메시지"""
    if st.session_state.voyage_confirmed and st.session_state.rpm_confirmed:
        _dec = st.session_state.voyage_decision or "확인 완료"
        st.success(
            f"✅ ① 출항 확인 완료 ({_dec}) · ② RPM 확인 완료 — "
            "**② RPM 최적 효율** 탭에서 결과를 확인하세요."
        )
    elif st.session_state.voyage_confirmed:
        st.info("👈 사이드바 **✅ ② RPM 확인** 버튼을 눌러 주세요.")
    else:
        st.info("👈 먼저 **① 출항 조건** 탭에서 조건을 입력하고 **확인** 버튼을 눌러 주세요.")


def load_dashboard_data():
    """대시보드용 — 매번 DB에서 최신 기록 조회"""
    rpm_df = get_all_records()
    dep_df = get_all_departure_records()
    return rpm_df, dep_df, not rpm_df.empty, not dep_df.empty
