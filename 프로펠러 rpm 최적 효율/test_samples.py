# 테스트용 샘플 데이터 — RPM_CASES가 ① 출항·② RPM 공통 원본
from calculator import calculate_all

# ── 통합 샘플 (② RPM + ① 출항 입력값) ──────────────────────────────
RPM_CASES = [
    {
        "label": "FP-4500 · 일반 운항",
        "description": "12kn / RPM 95 — 최적 RPM보다 낮아 효율 개선 여지 있음",
        "propeller_name": "FP-4500",
        "vessel_speed": 12.0,
        "rpm": 95.0,
        "propeller_diameter": 4.5,
        "thrust": 320.0,
        "shaft_power": 4500.0,
        "rpm_min": 60.0,
        "rpm_max": 140.0,
        "wind": 5.0,
        "wave": 1.0,
        "visibility": 5.0,
    },
    {
        "label": "CP-3800 · 저속 화물선",
        "description": "8kn / RPM 72 — 저속·대형 화물선 운항 예시",
        "propeller_name": "CP-3800",
        "vessel_speed": 8.0,
        "rpm": 72.0,
        "propeller_diameter": 3.8,
        "thrust": 180.0,
        "shaft_power": 2800.0,
        "rpm_min": 50.0,
        "rpm_max": 120.0,
        "wind": 10.0,
        "wave": 1.8,
        "visibility": 2.0,
    },
    {
        "label": "FP-5200 · 고속 운항",
        "description": "16kn / RPM 110 — 고속 운항·대출력 조건",
        "propeller_name": "FP-5200",
        "vessel_speed": 16.0,
        "rpm": 110.0,
        "propeller_diameter": 5.2,
        "thrust": 420.0,
        "shaft_power": 6200.0,
        "rpm_min": 80.0,
        "rpm_max": 160.0,
        "wind": 6.0,
        "wave": 1.2,
        "visibility": 4.0,
    },
    {
        "label": "FP-4500 · RPM 과다",
        "description": "12kn / RPM 130 — 진수비 과다, 이론 효율 저하 구간",
        "propeller_name": "FP-4500",
        "vessel_speed": 12.0,
        "rpm": 130.0,
        "propeller_diameter": 4.5,
        "thrust": 380.0,
        "shaft_power": 5200.0,
        "rpm_min": 60.0,
        "rpm_max": 140.0,
        "wind": 14.0,
        "wave": 2.5,
        "visibility": 1.0,
    },
    {
        "label": "FP-4500 · RPM 부족",
        "description": "12kn / RPM 70 — RPM 부족, 최적 대비 큰 편차",
        "propeller_name": "FP-4500",
        "vessel_speed": 12.0,
        "rpm": 70.0,
        "propeller_diameter": 4.5,
        "thrust": 250.0,
        "shaft_power": 3800.0,
        "rpm_min": 60.0,
        "rpm_max": 140.0,
        "wind": 8.0,
        "wave": 1.5,
        "visibility": 0.9,
    },
]

# 하위 호환
CASES = RPM_CASES


def get_rpm_case_by_label(label: str) -> dict:
    for case in RPM_CASES:
        if case["label"] == label:
            return case
    return RPM_CASES[0]


def voyage_fields_from_rpm(case: dict) -> dict:
    """① 출항 조건 입력값 — 선박명·치수는 RPM 샘플에서, 기상은 같은 샘플의 wind/wave/visibility"""
    diameter = float(case.get("propeller_diameter", 4.5))
    return {
        "vessel_name": case.get("propeller_name", ""),
        "wind": case.get("wind", 5.0),
        "wave": case.get("wave", 1.0),
        "visibility": case.get("visibility", 5.0),
        "length": round(diameter * 11),
    }


def apply_rpm_case_to_session(case: dict, session_state) -> None:
    """② RPM 입력값 적용"""
    session_state.sample_pick = case["label"]
    session_state.form_propeller_name = case["propeller_name"]
    session_state.form_vessel_speed = case["vessel_speed"]
    session_state.form_propeller_diameter = case["propeller_diameter"]
    session_state.form_thrust = case["thrust"]
    session_state.form_shaft_power = case["shaft_power"]
    session_state.form_rpm_min = int(case["rpm_min"])
    session_state.form_rpm_max = int(case["rpm_max"])
    session_state.form_rpm = int(case["rpm"])


def apply_voyage_from_rpm(case: dict, session_state) -> None:
    """① 출항 조건 입력값 적용 (RPM 샘플과 동일 시나리오)"""
    session_state.sample_pick = case["label"]
    voy = voyage_fields_from_rpm(case)
    session_state.voy_vessel_name = voy["vessel_name"]
    session_state.voy_wind = voy["wind"]
    session_state.voy_wave = voy["wave"]
    session_state.voy_visibility = voy["visibility"]
    session_state.voy_length = float(voy["length"])


def rpm_case_preview(case: dict) -> dict:
    """선택한 RPM 시나리오의 예상 계산 결과 (사이드바 미리보기용)"""
    return calculate_all(
        case["vessel_speed"],
        case["rpm"],
        case["propeller_diameter"],
        case["thrust"],
        case["shaft_power"],
        case["rpm_min"],
        case["rpm_max"],
    )


if __name__ == "__main__":
    print("=" * 70)
    print("  RPM 최적 효율 - 테스트 샘플 예상 결과")
    print("=" * 70)

    for case in RPM_CASES:
        r = calculate_all(
            case["vessel_speed"],
            case["rpm"],
            case["propeller_diameter"],
            case["thrust"],
            case["shaft_power"],
            case["rpm_min"],
            case["rpm_max"],
        )
        voy = voyage_fields_from_rpm(case)
        print(f"\n[{case['label']}]")
        print(f"  {case['description']}")
        print(
            f"  출항: {voy['vessel_name']} | 풍 {voy['wind']} | 파고 {voy['wave']} | "
            f"시정 {voy['visibility']} | 길이 {voy['length']}m"
        )
        print(
            f"  RPM: 실측 {r['measured_efficiency']:.1f}% | 이론 {r['model_efficiency']:.1f}% | "
            f"최적 {r['optimal_rpm']:.0f} | 최대 {r['max_efficiency']:.1f}%"
        )
