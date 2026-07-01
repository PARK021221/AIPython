# calculator.py
# 프로펠러 효율 및 최적 RPM 계산 함수를 담당하는 파일

# 진수비(J) 기반 이론 효율 모델 상수
J_OPT = 0.65       # 최적 진수비
J_WIDTH = 0.25     # 효율 곡선 폭
ETA_MAX = 68.0     # 최대 프로펠러 효율 (%)


def knot_to_mps(speed_knot: float) -> float:
    """노트(knot)를 m/s로 변환"""
    return speed_knot * 0.514444


def advance_ratio(speed_knot: float, rpm: float, diameter_m: float) -> float:
    """
    진수비 J = Va / (n * D) 계산
    Va : 선속 (m/s), n : 회전수 (rev/s), D : 직경 (m)
    """
    if speed_knot <= 0:
        raise ValueError("선속은 0보다 커야 합니다.")
    if rpm <= 0:
        raise ValueError("RPM은 0보다 커야 합니다.")
    if diameter_m <= 0:
        raise ValueError("프로펠러 직경은 0보다 커야 합니다.")

    va = knot_to_mps(speed_knot)
    n = rpm / 60.0
    return va / (n * diameter_m)


def efficiency_from_advance_ratio(J: float) -> float:
    """진수비에 따른 이론 프로펠러 효율 (%)"""
    eta = ETA_MAX * max(0.0, 1.0 - ((J - J_OPT) / J_WIDTH) ** 2)
    return min(eta, ETA_MAX)


def calculate_propeller_efficiency(
    speed_knot: float,
    rpm: float,
    diameter_m: float,
) -> float:
    """
    현재 운항 조건에서의 이론 프로펠러 효율 (%) 계산.

    Args:
        speed_knot  (float): 선속 (knot)
        rpm         (float): 현재 RPM
        diameter_m  (float): 프로펠러 직경 (m)

    Returns:
        float: 프로펠러 효율 (%)
    """
    J = advance_ratio(speed_knot, rpm, diameter_m)
    return efficiency_from_advance_ratio(J)


def calculate_measured_efficiency(
    thrust_kn: float,
    speed_knot: float,
    shaft_power_kw: float,
) -> float:
    """
    실측값 기반 프로펠러 효율 (%) 계산.
    η = (추력 × 선속) / 축출력 × 100

    Args:
        thrust_kn      (float): 추력 (kN)
        speed_knot     (float): 선속 (knot)
        shaft_power_kw (float): 축 출력 (kW)

    Returns:
        float: 실측 프로펠러 효율 (%)
    """
    if thrust_kn <= 0:
        raise ValueError("추력은 0보다 커야 합니다.")
    if speed_knot <= 0:
        raise ValueError("선속은 0보다 커야 합니다.")
    if shaft_power_kw <= 0:
        raise ValueError("축 출력은 0보다 커야 합니다.")

    va = knot_to_mps(speed_knot)
    # 추력(kN→N) × 선속(m/s) / 출력(kW→W)
    efficiency = (thrust_kn * 1000 * va) / (shaft_power_kw * 1000) * 100
    return efficiency


def find_optimal_rpm(
    speed_knot: float,
    diameter_m: float,
    rpm_min: float,
    rpm_max: float,
) -> tuple[float, float]:
    """
    RPM 구간을 스윕하여 최대 효율이 되는 최적 RPM 탐색.

    Args:
        speed_knot  (float): 선속 (knot)
        diameter_m  (float): 프로펠러 직경 (m)
        rpm_min     (float): 탐색 최소 RPM
        rpm_max     (float): 탐색 최대 RPM

    Returns:
        tuple: (최적 RPM, 최대 효율 %)
    """
    if rpm_min <= 0 or rpm_max <= 0:
        raise ValueError("RPM 범위는 0보다 커야 합니다.")
    if rpm_min >= rpm_max:
        raise ValueError("RPM 최솟값은 최댓값보다 작아야 합니다.")

    best_rpm = rpm_min
    best_eff = 0.0

    for rpm in range(int(rpm_min), int(rpm_max) + 1):
        eff = calculate_propeller_efficiency(speed_knot, float(rpm), diameter_m)
        if eff > best_eff:
            best_eff = eff
            best_rpm = float(rpm)

    return best_rpm, best_eff


def sweep_rpm_efficiency(
    speed_knot: float,
    diameter_m: float,
    rpm_min: float,
    rpm_max: float,
) -> list[dict]:
    """RPM 구간별 효율 데이터 생성 (그래프용)"""
    data = []
    for rpm in range(int(rpm_min), int(rpm_max) + 1):
        eff = calculate_propeller_efficiency(speed_knot, float(rpm), diameter_m)
        data.append({"rpm": float(rpm), "efficiency": eff})
    return data


def calculate_all(
    speed_knot: float,
    rpm: float,
    diameter_m: float,
    thrust_kn: float,
    shaft_power_kw: float,
    rpm_min: float,
    rpm_max: float,
) -> dict:
    """
    실측 효율, 이론 효율, 최적 RPM을 한 번에 계산.

    Returns:
        dict: measured_efficiency, model_efficiency, optimal_rpm, max_efficiency, advance_ratio
    """
    measured = calculate_measured_efficiency(thrust_kn, speed_knot, shaft_power_kw)
    model = calculate_propeller_efficiency(speed_knot, rpm, diameter_m)
    optimal_rpm, max_eff = find_optimal_rpm(speed_knot, diameter_m, rpm_min, rpm_max)
    J = advance_ratio(speed_knot, rpm, diameter_m)

    return {
        "measured_efficiency": measured,
        "model_efficiency": model,
        "optimal_rpm": optimal_rpm,
        "max_efficiency": max_eff,
        "advance_ratio": J,
    }


if __name__ == "__main__":
    test_speed = 12.0
    test_rpm = 95.0
    test_diameter = 4.5
    test_thrust = 320.0
    test_power = 4500.0
    test_rpm_min = 60.0
    test_rpm_max = 140.0

    result = calculate_all(
        test_speed, test_rpm, test_diameter,
        test_thrust, test_power, test_rpm_min, test_rpm_max,
    )

    print("=" * 45)
    print("  프로펠러 RPM 최적 효율 계산 테스트")
    print("=" * 45)
    print(f"  선속                 : {test_speed} knot")
    print(f"  현재 RPM             : {test_rpm} RPM")
    print(f"  프로펠러 직경        : {test_diameter} m")
    print(f"  추력                 : {test_thrust} kN")
    print(f"  축 출력              : {test_power} kW")
    print("-" * 45)
    print(f"  실측 효율            : {result['measured_efficiency']:.2f} %")
    print(f"  이론 효율 (현재 RPM) : {result['model_efficiency']:.2f} %")
    print(f"  진수비 J             : {result['advance_ratio']:.3f}")
    print(f"  최적 RPM             : {result['optimal_rpm']:.0f} RPM")
    print(f"  최대 효율            : {result['max_efficiency']:.2f} %")
    print("=" * 45)
