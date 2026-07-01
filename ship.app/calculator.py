# calculator.py
# 연료 소비량 및 운항 비용 계산 함수를 담당하는 파일


def calculate_fuel_consumption(operation_hours: float, fuel_per_hour: float) -> float:
    """
    총 연료 소비량을 계산하는 함수.

    Args:
        operation_hours (float): 운항 시간 (hour)
        fuel_per_hour   (float): 시간당 연료 소비량 (L/h)

    Returns:
        float: 총 연료 소비량 (L)

    Raises:
        ValueError: 입력값이 0 이하일 때 오류 발생
    """
    if operation_hours <= 0:
        raise ValueError("운항 시간은 0보다 커야 합니다.")
    if fuel_per_hour <= 0:
        raise ValueError("시간당 연료 소비량은 0보다 커야 합니다.")

    total_fuel = operation_hours * fuel_per_hour

    return total_fuel


def calculate_total_cost(total_fuel: float, fuel_price: float) -> float:
    """
    총 운항 비용을 계산하는 함수.

    Args:
        total_fuel  (float): 총 연료 소비량 (L)
        fuel_price  (float): 연료 단가 (원/L)

    Returns:
        float: 총 운항 비용 (원)

    Raises:
        ValueError: 입력값이 0 이하일 때 오류 발생
    """
    if total_fuel <= 0:
        raise ValueError("총 연료 소비량은 0보다 커야 합니다.")
    if fuel_price <= 0:
        raise ValueError("연료 단가는 0보다 커야 합니다.")

    # 총 비용 계산
    total_cost = total_fuel * fuel_price

    return total_cost


def calculate_all(
    operation_hours: float,
    fuel_per_hour: float,
    fuel_price: float
) -> dict:
    """
    연료 소비량과 총 비용을 한 번에 계산하여 딕셔너리로 반환하는 함수.
    app.py에서 이 함수 하나만 호출하면 모든 결과를 받을 수 있습니다.

    Args:
        operation_hours (float): 운항 시간 (hour)
        fuel_per_hour   (float): 시간당 연료 소비량 (L/h)
        fuel_price      (float): 연료 단가 (원/L)

    Returns:
        dict: {
            "total_fuel" : 총 연료 소비량 (L),
            "total_cost" : 총 운항 비용 (원)
        }
    """
    # Step 5에서 만든 함수로 연료 소비량 계산
    total_fuel = calculate_fuel_consumption(operation_hours, fuel_per_hour)

    # 위에서 만든 함수로 총 비용 계산
    total_cost = calculate_total_cost(total_fuel, fuel_price)

    # 결과를 딕셔너리로 묶어서 반환
    return {
        "total_fuel": total_fuel,
        "total_cost": total_cost
    }


# ──────────────────────────────────────────
# 테스트 코드 : 이 파일을 직접 실행할 때만 동작
# ──────────────────────────────────────────
if __name__ == "__main__":

    # 테스트용 예시값
    test_hours      = 60.0    # 운항 시간 60시간
    test_fuel_rate  = 120.0   # 시간당 연료 소비량 120 L/h
    test_price      = 1800.0  # 연료 단가 1,800 원/L

    # calculate_all() 로 한 번에 계산
    result = calculate_all(test_hours, test_fuel_rate, test_price)

    print("=" * 45)
    print("  운항 비용 계산 테스트")
    print("=" * 45)
    print(f"  운항 시간            : {test_hours} hour")
    print(f"  시간당 연료 소비량   : {test_fuel_rate} L/h")
    print(f"  연료 단가            : {test_price:,.0f} 원/L")
    print("-" * 45)
    print(f"  총 연료 소비량       : {result['total_fuel']:,.1f} L")
    print(f"  총 운항 비용         : {result['total_cost']:,.0f} 원")
    print("=" * 45)

    # 예외 처리 테스트
    print("\n[예외 처리 테스트]")
    try:
        calculate_total_cost(0, 1800.0)
    except ValueError as e:
        print(f"✅ 예외 정상 발생 : {e}")