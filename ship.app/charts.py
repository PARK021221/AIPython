# charts.py
# 그래프를 그리는 함수를 담당하는 파일

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd


def set_korean_font():
    """
    matplotlib에서 한글이 깨지지 않도록 폰트를 설정하는 함수.
    Windows 환경에서는 'Malgun Gothic'(맑은 고딕)을 사용합니다.
    """
    plt.rcParams["font.family"]     = "Malgun Gothic"  # 맑은 고딕
    plt.rcParams["axes.unicode_minus"] = False          # 마이너스 기호 깨짐 방지


def draw_fuel_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """
    선박별 총 연료 소비량을 비교하는 가로 막대 차트를 그리는 함수.

    Args:
        df (pd.DataFrame): get_all_records()가 반환한 데이터프레임

    Returns:
        plt.Figure: 그려진 그래프 객체 (st.pyplot()에 전달)
    """
    set_korean_font()

    # 선박별 평균 연료 소비량 계산
    # 같은 선박이 여러 번 저장된 경우 평균값을 사용
    fuel_by_ship = (
        df.groupby("선박명")["총연료(L)"]
        .mean()
        .sort_values(ascending=True)  # 큰 값이 위에 오도록 오름차순 (가로 막대)
    )

    # 그래프 크기 설정 (가로 8인치, 세로 4인치)
    fig, ax = plt.subplots(figsize=(8, 4))

    # 가로 막대 차트 (barh : horizontal bar)
    bars = ax.barh(
        fuel_by_ship.index,   # y축 : 선박명
        fuel_by_ship.values,  # x축 : 연료 소비량
        color="#2196F3",      # 파란색
        alpha=0.8             # 투명도 (0: 완전 투명, 1: 불투명)
    )

    # 각 막대 끝에 숫자 표시
    for bar, value in zip(bars, fuel_by_ship.values):
        ax.text(
            value + max(fuel_by_ship.values) * 0.01,  # x 위치 (막대 끝 + 여백)
            bar.get_y() + bar.get_height() / 2,        # y 위치 (막대 중앙)
            f"{value:,.1f} L",                         # 표시할 텍스트
            va="center",                               # 세로 중앙 정렬
            fontsize=9
        )

    # 축 및 제목 설정
    ax.set_title("선박별 평균 연료 소비량 비교", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("총 연료 소비량 (L)", fontsize=10)
    ax.set_ylabel("선박명", fontsize=10)

    # x축 숫자에 천 단위 콤마 적용
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    # 그래프 여백 자동 조정
    plt.tight_layout()

    return fig


def draw_cost_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """
    선박별 총 운항 비용을 비교하는 가로 막대 차트를 그리는 함수.

    Args:
        df (pd.DataFrame): get_all_records()가 반환한 데이터프레임

    Returns:
        plt.Figure: 그려진 그래프 객체
    """
    set_korean_font()

    # 선박별 평균 운항 비용 계산
    cost_by_ship = (
        df.groupby("선박명")["총비용(원)"]
        .mean()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 4))

    bars = ax.barh(
        cost_by_ship.index,
        cost_by_ship.values,
        color="#4CAF50",   # 초록색
        alpha=0.8
    )

    # 각 막대 끝에 만원 단위로 숫자 표시
    for bar, value in zip(bars, cost_by_ship.values):
        ax.text(
            value + max(cost_by_ship.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value / 10000:,.0f} 만원",
            va="center",
            fontsize=9
        )

    ax.set_title("선박별 평균 운항 비용 비교", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("총 운항 비용 (원)", fontsize=10)
    ax.set_ylabel("선박명", fontsize=10)

    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    plt.tight_layout()

    return fig


def draw_cost_trend_chart(df: pd.DataFrame) -> plt.Figure:
    """
    저장 순서에 따른 운항 비용 추이를 꺾은선 차트로 그리는 함수.

    Args:
        df (pd.DataFrame): get_all_records()가 반환한 데이터프레임

    Returns:
        plt.Figure: 그려진 그래프 객체
    """
    set_korean_font()

    # 저장 순서대로 정렬 (번호 오름차순)
    df_sorted = df.sort_values("번호").reset_index(drop=True)

    # x축 : 저장 순번 (1, 2, 3...)
    x_values = range(1, len(df_sorted) + 1)
    # y축 : 총 비용
    y_values = df_sorted["총비용(원)"].values

    fig, ax = plt.subplots(figsize=(8, 4))

    # 꺾은선 차트
    ax.plot(
        x_values,
        y_values,
        marker="o",        # 데이터 포인트에 동그라미 표시
        color="#FF5722",   # 주황색
        linewidth=2,       # 선 두께
        markersize=8       # 동그라미 크기
    )

    # 각 점 위에 선박명과 비용 표시
    for i, (x, y, name) in enumerate(
        zip(x_values, y_values, df_sorted["선박명"])
    ):
        ax.annotate(
            f"{name}\n{y / 10000:,.0f}만원",  # 표시할 텍스트
            xy=(x, y),                          # 텍스트를 붙일 데이터 좌표
            xytext=(0, 12),                     # 텍스트 위치 (데이터 좌표 기준 오프셋)
            textcoords="offset points",         # 오프셋 단위 (포인트)
            ha="center",                        # 가로 중앙 정렬
            fontsize=8
        )

    # 데이터가 1개일 때 x축 눈금이 소수점으로 표시되는 문제 방지
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    ax.set_title("운항 비용 추이", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("저장 순번", fontsize=10)
    ax.set_ylabel("총 운항 비용 (원)", fontsize=10)

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: f"{y:,.0f}")
    )

    # 배경 격자선 추가 (읽기 편하게)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()

    return fig