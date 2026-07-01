# database.py
# 데이터베이스 생성, 저장, 조회 기능을 담당하는 파일

import sqlite3
import pandas as pd
import os
from datetime import datetime


# ──────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────
DB_FOLDER = "data"
DB_PATH   = os.path.join(DB_FOLDER, "ship_fuel.db")


def create_database():
    """
    데이터베이스와 테이블을 생성하는 함수.
    이미 존재하면 다시 만들지 않음 (IF NOT EXISTS).
    """
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    connection = sqlite3.connect(DB_PATH)
    cursor     = connection.cursor()

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS fuel_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_name        TEXT    NOT NULL,
            distance         REAL    NOT NULL,
            speed            REAL    NOT NULL,
            operation_hours  REAL    NOT NULL,
            fuel_per_hour    REAL    NOT NULL,
            fuel_price       REAL    NOT NULL,
            total_fuel       REAL    NOT NULL,
            total_cost       REAL    NOT NULL,
            created_at       TEXT    NOT NULL
        )
    """

    cursor.execute(create_table_sql)
    connection.commit()
    connection.close()


def save_record(
    ship_name      : str,
    distance       : float,
    speed          : float,
    operation_hours: float,
    fuel_per_hour  : float,
    fuel_price     : float,
    total_fuel     : float,
    total_cost     : float
) -> bool:
    """
    계산 결과를 데이터베이스에 저장하는 함수.

    Returns:
        bool: 저장 성공 시 True, 실패 시 False
    """
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = sqlite3.connect(DB_PATH)
        cursor     = connection.cursor()

        insert_sql = """
            INSERT INTO fuel_records (
                ship_name, distance, speed, operation_hours,
                fuel_per_hour, fuel_price, total_fuel, total_cost, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            ship_name, distance, speed, operation_hours,
            fuel_per_hour, fuel_price, total_fuel, total_cost, created_at
        )

        cursor.execute(insert_sql, values)
        connection.commit()
        connection.close()

        return True

    except sqlite3.Error as e:
        print(f"DB 저장 오류 : {e}")
        return False


def get_all_records() -> pd.DataFrame:
    """
    저장된 모든 기록을 불러오는 함수.
    최신 기록이 위에 오도록 내림차순 정렬합니다.

    Returns:
        pd.DataFrame: 전체 기록을 담은 데이터프레임.
                      데이터가 없으면 빈 데이터프레임 반환.
    """
    try:
        connection = sqlite3.connect(DB_PATH)

        # pandas의 read_sql_query() :
        # SQL 실행 결과를 바로 DataFrame으로 변환해줍니다.
        select_sql = """
            SELECT
                id              AS 번호,
                ship_name       AS 선박명,
                distance        AS '운항거리(km)',
                speed           AS '평균속도(km/h)',
                operation_hours AS '운항시간(h)',
                fuel_per_hour   AS '시간당연료(L/h)',
                fuel_price      AS '연료단가(원/L)',
                total_fuel      AS '총연료(L)',
                total_cost      AS '총비용(원)',
                created_at      AS 저장일시
            FROM fuel_records
            ORDER BY id DESC
        """

        # SQL 결과를 DataFrame으로 바로 읽어옴
        df = pd.read_sql_query(select_sql, connection)
        connection.close()

        return df

    except sqlite3.Error as e:
        print(f"DB 조회 오류 : {e}")
        # 오류 발생 시 빈 DataFrame 반환
        return pd.DataFrame()


def delete_record(record_id: int) -> bool:
    """
    특정 번호의 기록을 삭제하는 함수.

    Args:
        record_id (int): 삭제할 기록의 id

    Returns:
        bool: 삭제 성공 시 True, 실패 시 False
    """
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor     = connection.cursor()

        delete_sql = "DELETE FROM fuel_records WHERE id = ?"
        cursor.execute(delete_sql, (record_id,))  # 튜플로 전달 (쉼표 주의)

        connection.commit()
        connection.close()

        return True

    except sqlite3.Error as e:
        print(f"DB 삭제 오류 : {e}")
        return False


# ──────────────────────────────────────────
# 테스트 코드
# ──────────────────────────────────────────
if __name__ == "__main__":

    create_database()

    # 테스트 데이터 2건 저장
    save_record("독도호",   1500.0, 25.0, 60.0,  120.0, 1800.0, 7200.0,  12960000.0)
    save_record("한라산호", 800.0,  20.0, 40.0,   90.0, 1750.0, 3600.0,   6300000.0)

    # 전체 조회
    df = get_all_records()

    print("📋 전체 기록")
    print(df.to_string(index=False))
    print(f"\n총 {len(df)}건의 기록이 있습니다.")