"""선박 출항 가능 여부를 판단하는 간단한 의사결정 보조 도구."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOWED = "출항 가능"
    CONDITIONAL = "조건부 가능"
    PROHIBITED = "출항 불가"


@dataclass(frozen=True)
class VoyageConditions:
    wind_speed_ms: float
    wave_height_m: float
    visibility_km: float
    vessel_length_m: float
    engine_ok: bool = True
    navigation_ok: bool = True
    lifesaving_ok: bool = True
    crew_ready: bool = True
    weather_warning: bool = False


@dataclass(frozen=True)
class Limits:
    max_wind_speed_ms: float = 14.0
    caution_wind_speed_ms: float = 10.0
    max_wave_height_m: float = 3.0
    caution_wave_height_m: float = 2.0
    min_visibility_km: float = 0.5
    caution_visibility_km: float = 1.0
    min_vessel_length_m: float = 1.0


@dataclass(frozen=True)
class Result:
    decision: Decision
    reasons: list[str]


def assess_voyage(c: VoyageConditions, limits: Limits = Limits()) -> Result:
    """입력 조건을 평가한다. 실제 법정 출항통제 기준을 대신하지 않는다."""
    if c.wind_speed_ms < 0 or c.wave_height_m < 0 or c.visibility_km < 0:
        raise ValueError("풍속, 파고, 시정은 0 이상이어야 합니다.")
    if c.vessel_length_m < limits.min_vessel_length_m:
        raise ValueError("선박 길이가 유효하지 않습니다.")

    prohibited: list[str] = []
    caution: list[str] = []

    equipment = {
        "기관 상태 불량": c.engine_ok,
        "항해 장비 상태 불량": c.navigation_ok,
        "구명·안전 장비 상태 불량": c.lifesaving_ok,
        "필수 승무원 미확보 또는 승무원 준비 미완료": c.crew_ready,
    }
    prohibited.extend(reason for reason, ok in equipment.items() if not ok)

    if c.weather_warning:
        prohibited.append("기상특보 발효")
    if c.wind_speed_ms > limits.max_wind_speed_ms:
        prohibited.append(f"풍속 초과 ({c.wind_speed_ms:g} > {limits.max_wind_speed_ms:g} m/s)")
    elif c.wind_speed_ms >= limits.caution_wind_speed_ms:
        caution.append(f"강한 바람 ({c.wind_speed_ms:g} m/s)")
    if c.wave_height_m > limits.max_wave_height_m:
        prohibited.append(f"파고 초과 ({c.wave_height_m:g} > {limits.max_wave_height_m:g} m)")
    elif c.wave_height_m >= limits.caution_wave_height_m:
        caution.append(f"높은 파고 ({c.wave_height_m:g} m)")
    if c.visibility_km < limits.min_visibility_km:
        prohibited.append(f"시정 부족 ({c.visibility_km:g} < {limits.min_visibility_km:g} km)")
    elif c.visibility_km <= limits.caution_visibility_km:
        caution.append(f"낮은 시정 ({c.visibility_km:g} km)")

    if prohibited:
        return Result(Decision.PROHIBITED, prohibited)
    if caution:
        return Result(Decision.CONDITIONAL, caution)
    return Result(Decision.ALLOWED, ["설정된 모든 기준 충족"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="선박 출항 가능 여부 판단(의사결정 보조용)")
    parser.add_argument("--wind", type=float, required=True, help="풍속(m/s)")
    parser.add_argument("--wave", type=float, required=True, help="파고(m)")
    parser.add_argument("--visibility", type=float, required=True, help="시정(km)")
    parser.add_argument("--length", type=float, required=True, help="선박 길이(m)")
    parser.add_argument("--engine-fault", action="store_true", help="기관 이상")
    parser.add_argument("--navigation-fault", action="store_true", help="항해 장비 이상")
    parser.add_argument("--lifesaving-fault", action="store_true", help="구명 장비 이상")
    parser.add_argument("--crew-not-ready", action="store_true", help="승무원 준비 미완료")
    parser.add_argument("--weather-warning", action="store_true", help="기상특보 발효")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conditions = VoyageConditions(
        wind_speed_ms=args.wind,
        wave_height_m=args.wave,
        visibility_km=args.visibility,
        vessel_length_m=args.length,
        engine_ok=not args.engine_fault,
        navigation_ok=not args.navigation_fault,
        lifesaving_ok=not args.lifesaving_fault,
        crew_ready=not args.crew_not_ready,
        weather_warning=args.weather_warning,
    )
    try:
        result = assess_voyage(conditions)
    except ValueError as exc:
        print(f"입력 오류: {exc}")
        return 2

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"판정: {result.decision.value}")
        print("사유: " + "; ".join(result.reasons))
        print("주의: 실제 출항은 최신 기상정보, 관할 법규 및 선장/운항관리자의 승인을 따르세요.")
    return 1 if result.decision == Decision.PROHIBITED else 0


if __name__ == "__main__":
    raise SystemExit(main())
