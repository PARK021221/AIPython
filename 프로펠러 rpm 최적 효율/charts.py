# charts.py
# 프로펠러 RPM-효율 그래프를 그리는 함수를 담당하는 파일

import matplotlib.pyplot as plt
import pandas as pd

from calculator import sweep_rpm_efficiency


def set_korean_font():
    """matplotlib 한글 폰트 설정 (Windows: 맑은 고딕)"""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def draw_rpm_efficiency_curve(
    speed_knot: float,
    diameter_m: float,
    rpm_min: float,
    rpm_max: float,
    current_rpm: float = None,
    optimal_rpm: float = None,
) -> plt.Figure:
    """
    RPM 대비 프로펠러 효율 곡선 (꺾은선 차트).

    Args:
        speed_knot   : 선속 (knot)
        diameter_m   : 프로펠러 직경 (m)
        rpm_min/max  : RPM 탐색 범위
        current_rpm  : 현재 RPM (세로선 표시)
        optimal_rpm  : 최적 RPM (세로선 표시)
    """
    set_korean_font()

    sweep_data = sweep_rpm_efficiency(speed_knot, diameter_m, rpm_min, rpm_max)
    rpms = [d["rpm"] for d in sweep_data]
    effs = [d["efficiency"] for d in sweep_data]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0d1b2a")
    ax.set_facecolor("#1b2838")

    ax.plot(rpms, effs, color="#00b4d8", linewidth=2.5, label="이론 효율 곡선")
    ax.fill_between(rpms, effs, alpha=0.12, color="#00b4d8")

    if current_rpm is not None:
        ax.axvline(
            x=current_rpm, color="#ff9f1c", linestyle="--", linewidth=2,
            label=f"현재 RPM ({current_rpm:.0f})",
        )
        cur_eff = next(
            (e for r, e in zip(rpms, effs) if abs(r - current_rpm) < 0.5),
            None,
        )
        if cur_eff is not None:
            ax.scatter(
                [current_rpm], [cur_eff], color="#ff9f1c", s=120, zorder=5, edgecolors="white"
            )

    if optimal_rpm is not None:
        ax.axvline(
            x=optimal_rpm, color="#2ec4b6", linestyle="--", linewidth=2,
            label=f"최적 RPM ({optimal_rpm:.0f})",
        )

    ax.set_title("RPM – 효율 곡선", fontsize=15, fontweight="bold", pad=15, color="#e0e6ed")
    ax.set_xlabel("RPM", fontsize=11, color="#90a4ae")
    ax.set_ylabel("프로펠러 효율 (%)", fontsize=11, color="#90a4ae")
    ax.tick_params(colors="#90a4ae")
    for spine in ax.spines.values():
        spine.set_color("#2a3f5f")
    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#4a6080")
    ax.legend(loc="lower right", fontsize=9, facecolor="#1b2838", edgecolor="#2a3f5f", labelcolor="#e0e6ed")
    plt.tight_layout()

    return fig


def draw_rpm_deviation_scatter(df: pd.DataFrame) -> plt.Figure:
    """현재 RPM vs 최적 RPM 산점도 (대각선에서 멀수록 비효율)"""
    set_korean_font()

    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor("#0d1b2a")
    ax.set_facecolor("#1b2838")

    x = df["현재RPM"].values
    y = df["최적RPM"].values
    labels = df["프로펠러명"].values

    lim_min = min(x.min(), y.min()) * 0.9
    lim_max = max(x.max(), y.max()) * 1.1

    ax.plot([lim_min, lim_max], [lim_min, lim_max], "--", color="#4a6080", linewidth=1.5, label="이상선 (현재=최적)")
    ax.scatter(x, y, c="#00b4d8", s=100, alpha=0.85, edgecolors="white", linewidths=1, zorder=3)

    for xi, yi, name in zip(x, y, labels):
        ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(6, 6), fontsize=8, color="#e0e6ed")

    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)
    ax.set_title("RPM 편차 분석", fontsize=14, fontweight="bold", pad=12, color="#e0e6ed")
    ax.set_xlabel("현재 RPM", fontsize=10, color="#90a4ae")
    ax.set_ylabel("최적 RPM", fontsize=10, color="#90a4ae")
    ax.tick_params(colors="#90a4ae")
    for spine in ax.spines.values():
        spine.set_color("#2a3f5f")
    ax.legend(facecolor="#1b2838", edgecolor="#2a3f5f", labelcolor="#e0e6ed", fontsize=9)
    ax.grid(linestyle="--", alpha=0.2, color="#4a6080")
    plt.tight_layout()

    return fig


def draw_efficiency_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """프로펠러별 평균 최대 효율 비교 (가로 막대 차트)"""
    set_korean_font()

    eff_by_prop = (
        df.groupby("프로펠러명")["최대효율(%)"]
        .mean()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 4))

    bars = ax.barh(
        eff_by_prop.index,
        eff_by_prop.values,
        color="#4CAF50",
        alpha=0.8,
    )

    for bar, value in zip(bars, eff_by_prop.values):
        ax.text(
            value + max(eff_by_prop.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f} %",
            va="center",
            fontsize=9,
        )

    ax.set_title("프로펠러별 평균 최대 효율 비교", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("최대 효율 (%)", fontsize=10)
    ax.set_ylabel("프로펠러명", fontsize=10)
    plt.tight_layout()

    return fig


def draw_optimal_rpm_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """프로펠러별 평균 최적 RPM 비교 (가로 막대 차트)"""
    set_korean_font()

    rpm_by_prop = (
        df.groupby("프로펠러명")["최적RPM"]
        .mean()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 4))

    bars = ax.barh(
        rpm_by_prop.index,
        rpm_by_prop.values,
        color="#2196F3",
        alpha=0.8,
    )

    for bar, value in zip(bars, rpm_by_prop.values):
        ax.text(
            value + max(rpm_by_prop.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.0f} RPM",
            va="center",
            fontsize=9,
        )

    ax.set_title("프로펠러별 평균 최적 RPM 비교", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("최적 RPM", fontsize=10)
    ax.set_ylabel("프로펠러명", fontsize=10)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )
    plt.tight_layout()

    return fig


def draw_efficiency_trend_chart(df: pd.DataFrame) -> plt.Figure:
    """저장 순서에 따른 최대 효율 추이 (꺾은선 차트)"""
    set_korean_font()

    df_sorted = df.sort_values("번호").reset_index(drop=True)
    x_values = range(1, len(df_sorted) + 1)
    y_values = df_sorted["최대효율(%)"].values

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(
        x_values,
        y_values,
        marker="o",
        color="#FF5722",
        linewidth=2,
        markersize=8,
    )

    for x, y, name in zip(x_values, y_values, df_sorted["프로펠러명"]):
        ax.annotate(
            f"{name}\n{y:.1f}%",
            xy=(x, y),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_title("최대 효율 추이", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("저장 순번", fontsize=10)
    ax.set_ylabel("최대 효율 (%)", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    return fig
