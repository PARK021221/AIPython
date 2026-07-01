# database.py
# 데이터베이스 생성, 저장, 조회 기능을 담당하는 파일

import sqlite3
import os
from datetime import datetime

import pandas as pd

DB_FOLDER = "data"
DB_PATH = os.path.join(DB_FOLDER, "propeller_rpm.db")


def create_database():
    """데이터베이스와 테이블을 생성하는 함수."""
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS rpm_records (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            propeller_name      TEXT    NOT NULL,
            vessel_speed        REAL    NOT NULL,
            propeller_diameter  REAL    NOT NULL,
            rpm                 REAL    NOT NULL,
            shaft_power         REAL    NOT NULL,
            thrust              REAL    NOT NULL,
            measured_efficiency REAL    NOT NULL,
            model_efficiency    REAL    NOT NULL,
            optimal_rpm         REAL    NOT NULL,
            max_efficiency      REAL    NOT NULL,
            advance_ratio       REAL    NOT NULL,
            created_at          TEXT    NOT NULL
        )
    """

    cursor.execute(create_table_sql)

    departure_table_sql = """
        CREATE TABLE IF NOT EXISTS departure_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            vessel_name      TEXT    NOT NULL,
            wind_speed_ms    REAL    NOT NULL,
            wave_height_m    REAL    NOT NULL,
            visibility_km    REAL    NOT NULL,
            vessel_length_m  REAL    NOT NULL,
            decision         TEXT    NOT NULL,
            reasons          TEXT    NOT NULL,
            created_at       TEXT    NOT NULL
        )
    """
    cursor.execute(departure_table_sql)

    connection.commit()
    connection.close()


def save_record(
    propeller_name: str,
    vessel_speed: float,
    propeller_diameter: float,
    rpm: float,
    shaft_power: float,
    thrust: float,
    measured_efficiency: float,
    model_efficiency: float,
    optimal_rpm: float,
    max_efficiency: float,
    advance_ratio_val: float,
) -> bool:
    """계산 결과를 데이터베이스에 저장."""
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        insert_sql = """
            INSERT INTO rpm_records (
                propeller_name, vessel_speed, propeller_diameter,
                rpm, shaft_power, thrust,
                measured_efficiency, model_efficiency,
                optimal_rpm, max_efficiency, advance_ratio, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            propeller_name,
            vessel_speed,
            propeller_diameter,
            rpm,
            shaft_power,
            thrust,
            measured_efficiency,
            model_efficiency,
            optimal_rpm,
            max_efficiency,
            advance_ratio_val,
            created_at,
        )

        cursor.execute(insert_sql, values)
        connection.commit()
        connection.close()
        return True

    except sqlite3.Error as e:
        print(f"DB 저장 오류 : {e}")
        return False


def get_all_records() -> pd.DataFrame:
    """저장된 모든 기록을 불러옴."""
    try:
        connection = sqlite3.connect(DB_PATH)

        select_sql = """
            SELECT
                id                  AS 번호,
                propeller_name      AS 프로펠러명,
                vessel_speed        AS '선속(knot)',
                propeller_diameter  AS '직경(m)',
                rpm                 AS '현재RPM',
                shaft_power         AS '축출력(kW)',
                thrust              AS '추력(kN)',
                measured_efficiency AS '실측효율(%)',
                model_efficiency    AS '이론효율(%)',
                optimal_rpm         AS '최적RPM',
                max_efficiency      AS '최대효율(%)',
                advance_ratio       AS '진수비J',
                created_at          AS 저장일시
            FROM rpm_records
            ORDER BY id DESC
        """

        df = pd.read_sql_query(select_sql, connection)
        connection.close()
        return df

    except sqlite3.Error as e:
        print(f"DB 조회 오류 : {e}")
        return pd.DataFrame()


def delete_record(record_id: int) -> bool:
    """특정 번호의 기록을 삭제."""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        delete_sql = "DELETE FROM rpm_records WHERE id = ?"
        cursor.execute(delete_sql, (record_id,))

        connection.commit()
        connection.close()
        return True

    except sqlite3.Error as e:
        print(f"DB 삭제 오류 : {e}")
        return False


def save_departure_record(
    vessel_name: str,
    wind_speed_ms: float,
    wave_height_m: float,
    visibility_km: float,
    vessel_length_m: float,
    decision: str,
    reasons: list[str],
) -> bool:
    """출항 판단 결과를 데이터베이스에 저장."""
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reasons_text = " | ".join(reasons)

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        insert_sql = """
            INSERT INTO departure_records (
                vessel_name, wind_speed_ms, wave_height_m, visibility_km,
                vessel_length_m, decision, reasons, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(
            insert_sql,
            (
                vessel_name,
                wind_speed_ms,
                wave_height_m,
                visibility_km,
                vessel_length_m,
                decision,
                reasons_text,
                created_at,
            ),
        )
        connection.commit()
        connection.close()
        return True

    except sqlite3.Error as e:
        print(f"DB 저장 오류 : {e}")
        return False


def get_all_departure_records() -> pd.DataFrame:
    """저장된 출항 판단 기록을 불러옴."""
    try:
        connection = sqlite3.connect(DB_PATH)
        select_sql = """
            SELECT
                id              AS 번호,
                vessel_name     AS 선박명,
                wind_speed_ms   AS '풍속(m/s)',
                wave_height_m   AS '파고(m)',
                visibility_km   AS '시정(km)',
                vessel_length_m AS '선박길이(m)',
                decision        AS 판정,
                reasons         AS 사유,
                created_at      AS 저장일시
            FROM departure_records
            ORDER BY id DESC
        """
        df = pd.read_sql_query(select_sql, connection)
        connection.close()
        return df

    except sqlite3.Error as e:
        print(f"DB 조회 오류 : {e}")
        return pd.DataFrame()


def delete_departure_record(record_id: int) -> bool:
    """출항 판단 기록 삭제."""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM departure_records WHERE id = ?", (record_id,))
        connection.commit()
        connection.close()
        return True
    except sqlite3.Error as e:
        print(f"DB 삭제 오류 : {e}")
        return False


if __name__ == "__main__":
    create_database()
    print("DB ready (table only, no sample data)")
