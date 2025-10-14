"""
Economic Plots for SimCity Simulation

経済グラフ生成:
- 時系列プロット（GDP、失業率、インフレ等）
- フィリップス曲線
- オークンの法則
- ベバリッジ曲線
- エンゲルの法則
- 価格弾力性
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from scipy import stats


class EconomicPlots:
    """
    経済グラフ生成クラス

    シミュレーション結果から経済現象を可視化
    - マクロ経済指標の時系列
    - 経済法則の検証グラフ
    """

    def __init__(self):
        """EconomicPlotsの初期化"""
        logger.info("EconomicPlots initialized")

    def plot_time_series(
        self,
        data: dict[str, list[float]],
        title: str = "Economic Indicators Over Time",
        figsize: tuple[int, int] = (12, 8),
        save_path: str | None = None,
    ) -> plt.Figure:
        """
        複数指標の時系列プロット

        Args:
            data: {指標名: [値のリスト]} の辞書
            title: グラフタイトル
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figure
        """
        num_indicators = len(data)
        fig, axes = plt.subplots(num_indicators, 1, figsize=figsize, sharex=True)

        if num_indicators == 1:
            axes = [axes]

        for ax, (indicator, values) in zip(axes, data.items(), strict=False):
            steps = range(len(values))
            ax.plot(steps, values, linewidth=2)
            ax.set_ylabel(indicator)
            ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel("Time Step")
        fig.suptitle(title, fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Time series plot saved to {save_path}")

        return fig

    def plot_phillips_curve(
        self,
        unemployment_rate: list[float],
        inflation_rate: list[float],
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        フィリップス曲線をプロット

        Args:
            unemployment_rate: 失業率のリスト
            inflation_rate: インフレ率のリスト
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 相関係数を計算
        correlation = np.corrcoef(unemployment_rate, inflation_rate)[0, 1]

        # 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            unemployment_rate, inflation_rate
        )

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # 散布図
        ax.scatter(unemployment_rate, inflation_rate, alpha=0.6, s=50)

        # 回帰直線
        x_line = np.array([min(unemployment_rate), max(unemployment_rate)])
        y_line = slope * x_line + intercept
        ax.plot(
            x_line,
            y_line,
            "r--",
            linewidth=2,
            label=f"Fit: y={slope:.3f}x+{intercept:.3f}",
        )

        ax.set_xlabel("Unemployment Rate")
        ax.set_ylabel("Inflation Rate")
        ax.set_title(
            f"Phillips Curve (correlation={correlation:.3f})",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Phillips curve saved to {save_path}")

        stats_info = {
            "correlation": correlation,
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_value**2,
            "p_value": p_value,
        }

        return fig, stats_info

    def plot_okun_law(
        self,
        unemployment_change: list[float],
        gdp_growth: list[float],
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        オークンの法則をプロット

        Args:
            unemployment_change: 失業率の変化量
            gdp_growth: GDP成長率
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 相関係数を計算
        correlation = np.corrcoef(unemployment_change, gdp_growth)[0, 1]

        # 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            unemployment_change, gdp_growth
        )

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # 散布図
        ax.scatter(unemployment_change, gdp_growth, alpha=0.6, s=50)

        # 回帰直線
        x_line = np.array([min(unemployment_change), max(unemployment_change)])
        y_line = slope * x_line + intercept
        ax.plot(
            x_line,
            y_line,
            "r--",
            linewidth=2,
            label=f"Fit: y={slope:.3f}x+{intercept:.3f}",
        )

        ax.set_xlabel("Change in Unemployment Rate")
        ax.set_ylabel("GDP Growth Rate")
        ax.set_title(
            f"Okun's Law (correlation={correlation:.3f})",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Okun's law plot saved to {save_path}")

        stats_info = {
            "correlation": correlation,
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_value**2,
            "p_value": p_value,
        }

        return fig, stats_info

    def plot_beveridge_curve(
        self,
        unemployment_rate: list[float],
        vacancy_rate: list[float],
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        ベバリッジ曲線をプロット

        Args:
            unemployment_rate: 失業率のリスト
            vacancy_rate: 求人率のリスト
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 相関係数を計算
        correlation = np.corrcoef(unemployment_rate, vacancy_rate)[0, 1]

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # 時系列順にグラデーション表示
        n_points = len(unemployment_rate)
        colors = plt.cm.viridis(np.linspace(0, 1, n_points))

        for i in range(n_points - 1):
            ax.plot(
                unemployment_rate[i : i + 2],
                vacancy_rate[i : i + 2],
                color=colors[i],
                linewidth=2,
                alpha=0.7,
            )

        # 散布図（終点を強調）
        ax.scatter(
            unemployment_rate,
            vacancy_rate,
            c=range(n_points),
            cmap="viridis",
            s=50,
            alpha=0.6,
        )

        ax.set_xlabel("Unemployment Rate")
        ax.set_ylabel("Vacancy Rate")
        ax.set_title(
            f"Beveridge Curve (correlation={correlation:.3f})",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)

        # カラーバー（時間軸）
        sm = plt.cm.ScalarMappable(
            cmap="viridis", norm=plt.Normalize(vmin=0, vmax=n_points - 1)
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label("Time Step")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Beveridge curve saved to {save_path}")

        stats_info = {
            "correlation": correlation,
        }

        return fig, stats_info

    def plot_engel_curve(
        self,
        income: list[float],
        food_share: list[float],
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        エンゲルの法則をプロット（所得と食料支出割合）

        Args:
            income: 所得のリスト
            food_share: 食料支出割合のリスト
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 対数回帰
        log_income = np.log(income)
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            log_income, food_share
        )

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # 散布図
        ax.scatter(income, food_share, alpha=0.6, s=50)

        # 回帰曲線（対数スケール）
        x_line = np.linspace(min(income), max(income), 100)
        y_line = slope * np.log(x_line) + intercept
        ax.plot(x_line, y_line, "r--", linewidth=2, label="Log fit")

        ax.set_xlabel("Income")
        ax.set_ylabel("Food Expenditure Share")
        ax.set_title("Engel's Law", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Engel curve saved to {save_path}")

        stats_info = {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_value**2,
            "p_value": p_value,
        }

        return fig, stats_info

    def plot_price_elasticity(
        self,
        prices: list[float],
        quantities: list[float],
        good_name: str = "Good",
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        価格弾力性をプロット

        Args:
            prices: 価格のリスト
            quantities: 需要量のリスト
            good_name: 財の名前
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 対数スケールで線形回帰（弾力性を求めるため）
        log_prices = np.log(prices)
        log_quantities = np.log(quantities)

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            log_prices, log_quantities
        )

        # 価格弾力性 = slope
        elasticity = slope

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # 散布図
        ax.scatter(prices, quantities, alpha=0.6, s=50)

        # 回帰曲線
        x_line = np.linspace(min(prices), max(prices), 100)
        y_line = np.exp(intercept) * x_line**slope
        ax.plot(x_line, y_line, "r--", linewidth=2, label=f"Elasticity={elasticity:.3f}")

        ax.set_xlabel("Price")
        ax.set_ylabel("Quantity Demanded")
        ax.set_title(f"Price Elasticity: {good_name}", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()

        # 弾力性の解釈をテキストで追加
        if elasticity < -1:
            elasticity_type = "Elastic (luxury)"
        elif -1 <= elasticity < 0:
            elasticity_type = "Inelastic (necessity)"
        else:
            elasticity_type = "Unusual (positive)"

        ax.text(
            0.05,
            0.95,
            f"Type: {elasticity_type}",
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Price elasticity plot saved to {save_path}")

        stats_info = {
            "elasticity": elasticity,
            "r_squared": r_value**2,
            "p_value": p_value,
            "elasticity_type": elasticity_type,
        }

        return fig, stats_info

    def plot_distribution(
        self,
        data: list[float],
        title: str = "Distribution",
        xlabel: str = "Value",
        bins: int = 30,
        figsize: tuple[int, int] = (8, 6),
        save_path: str | None = None,
    ) -> tuple[plt.Figure, dict[str, Any]]:
        """
        分布のヒストグラムをプロット

        Args:
            data: データのリスト
            title: グラフタイトル
            xlabel: X軸ラベル
            bins: ビン数
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figureと統計情報
        """
        # 統計量を計算
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)

        # プロット
        fig, ax = plt.subplots(figsize=figsize)

        # ヒストグラム
        ax.hist(data, bins=bins, alpha=0.7, edgecolor="black")

        # 平均値と中央値のライン
        ax.axvline(
            mean_val, color="red", linestyle="--", linewidth=2, label=f"Mean={mean_val:.2f}"
        )
        ax.axvline(
            median_val,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Median={median_val:.2f}",
        )

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Frequency")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Distribution plot saved to {save_path}")

        stats_info = {
            "mean": mean_val,
            "median": median_val,
            "std": std_val,
            "min": float(np.min(data)),
            "max": float(np.max(data)),
        }

        return fig, stats_info

    def plot_comparison(
        self,
        data_dict: dict[str, list[float]],
        title: str = "Comparison",
        xlabel: str = "Category",
        ylabel: str = "Value",
        plot_type: str = "bar",
        figsize: tuple[int, int] = (10, 6),
        save_path: str | None = None,
    ) -> plt.Figure:
        """
        複数データの比較プロット

        Args:
            data_dict: {ラベル: [値のリスト]} の辞書
            title: グラフタイトル
            xlabel: X軸ラベル
            ylabel: Y軸ラベル
            plot_type: プロットタイプ ("bar" or "box")
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        if plot_type == "bar":
            # 平均値の棒グラフ
            labels = list(data_dict.keys())
            means = [np.mean(values) for values in data_dict.values()]
            stds = [np.std(values) for values in data_dict.values()]

            x_pos = np.arange(len(labels))
            ax.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=45, ha="right")

        elif plot_type == "box":
            # ボックスプロット
            data_list = list(data_dict.values())
            labels = list(data_dict.keys())
            ax.boxplot(data_list, tick_labels=labels)
            ax.set_xticklabels(labels, rotation=45, ha="right")

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Comparison plot saved to {save_path}")

        return fig

    @staticmethod
    def close_all():
        """全てのMatplotlib図を閉じる"""
        plt.close("all")
        logger.debug("All matplotlib figures closed")
