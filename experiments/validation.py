"""
Economic Phenomena Validation

180ステップ（15年）のシミュレーションを実行し、
7つの経済現象（論文Table 2相当）を検証する。
"""

import json
import sys
from pathlib import Path

import numpy as np
from loguru import logger
from scipy import stats

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.simulation import Simulation
from src.utils.config import SimCityConfig, load_config
from src.utils.logger import setup_logger


class EconomicPhenomenaValidator:
    """
    7つの経済現象を検証するクラス

    1. Phillips Curve: 失業率 vs インフレ率（r < 0）
    2. Okun's Law: 失業率変化 vs GDP成長率（r < 0）
    3. Beveridge Curve: 求人率 vs 失業率（r < -0.5）
    4. Price Elasticity: 価格 vs 需要量（必需品: -1<E<0, 贅沢品: E<-1）
    5. Engel's Law: 所得 vs 食料支出割合（負の相関）
    6. Investment Volatility: std(投資) > std(消費)
    7. Price Stickiness: 価格調整の遅延
    """

    def __init__(self, simulation_data: dict):
        """
        Args:
            simulation_data: シミュレーション結果データ
                {
                    "history": {
                        "gdp": [...],
                        "inflation": [...],
                        "unemployment_rate": [...],
                        "vacancy_rate": [...],
                        "gini": [...],
                        "consumption": [...],
                        "investment": [...],
                        "prices": {good_id: [...]},
                        "demands": {good_id: [...]},
                        "household_incomes": [[...], ...],  # 各ステップの世帯所得リスト
                        "food_expenditure_ratios": [[...], ...],  # 各ステップの食料支出割合
                    },
                    "metadata": {
                        "steps": int,
                        "households": int,
                        "firms": int,
                    }
                }
        """
        self.data = simulation_data
        self.history = simulation_data["history"]
        self.metadata = simulation_data["metadata"]
        self.results = {}

    def validate_phillips_curve(self) -> dict:
        """
        Phillips Curve検証: 失業率とインフレ率の負の相関

        Returns:
            {
                "correlation": float,
                "p_value": float,
                "valid": bool (r < 0 and p < 0.05),
            }
        """
        logger.info("Validating Phillips Curve...")

        unemployment = np.array(self.history["unemployment_rate"])
        inflation = np.array(self.history["inflation"])

        # 相関係数とp値を計算
        correlation, p_value = stats.pearsonr(unemployment, inflation)

        valid = correlation < 0 and p_value < 0.05

        result = {
            "phenomenon": "Phillips Curve",
            "correlation": float(correlation),
            "p_value": float(p_value),
            "valid": bool(valid),
            "expected": "r < 0 (negative correlation)",
            "description": "Unemployment rate vs Inflation rate",
        }

        logger.info(
            f"Phillips Curve: r={correlation:.4f}, p={p_value:.4f}, "
            f"valid={valid}"
        )

        return result

    def validate_okuns_law(self) -> dict:
        """
        Okun's Law検証: 失業率変化とGDP成長率の負の相関

        Returns:
            {
                "correlation": float,
                "p_value": float,
                "valid": bool (r < 0 and p < 0.05),
            }
        """
        logger.info("Validating Okun's Law...")

        gdp = np.array(self.history["gdp"])
        unemployment = np.array(self.history["unemployment_rate"])

        # GDP成長率を計算
        gdp_growth = np.diff(gdp) / gdp[:-1] * 100  # %

        # 失業率変化を計算
        unemployment_change = np.diff(unemployment)

        # 相関係数とp値を計算
        correlation, p_value = stats.pearsonr(unemployment_change, gdp_growth)

        valid = correlation < 0 and p_value < 0.05

        result = {
            "phenomenon": "Okun's Law",
            "correlation": float(correlation),
            "p_value": float(p_value),
            "valid": bool(valid),
            "expected": "r < 0 (negative correlation)",
            "description": "Unemployment change vs GDP growth rate",
        }

        logger.info(
            f"Okun's Law: r={correlation:.4f}, p={p_value:.4f}, valid={valid}"
        )

        return result

    def validate_beveridge_curve(self) -> dict:
        """
        Beveridge Curve検証: 求人率と失業率の強い負の相関

        Returns:
            {
                "correlation": float,
                "p_value": float,
                "valid": bool (r < -0.5 and p < 0.05),
            }
        """
        logger.info("Validating Beveridge Curve...")

        unemployment = np.array(self.history["unemployment_rate"])
        vacancy = np.array(self.history["vacancy_rate"])

        # 相関係数とp値を計算
        correlation, p_value = stats.pearsonr(unemployment, vacancy)

        valid = correlation < -0.5 and p_value < 0.05

        result = {
            "phenomenon": "Beveridge Curve",
            "correlation": float(correlation),
            "p_value": float(p_value),
            "valid": bool(valid),
            "expected": "r < -0.5 (strong negative correlation)",
            "description": "Unemployment rate vs Vacancy rate",
        }

        logger.info(
            f"Beveridge Curve: r={correlation:.4f}, p={p_value:.4f}, "
            f"valid={valid}"
        )

        return result

    def validate_price_elasticity(self) -> dict:
        """
        Price Elasticity検証: 需要の価格弾力性

        必需品: -1 < E < 0
        贅沢品: E < -1

        Returns:
            {
                "necessities": {"mean_elasticity": float, "valid": bool},
                "luxuries": {"mean_elasticity": float, "valid": bool},
            }
        """
        logger.info("Validating Price Elasticity...")

        from src.data.goods_types import GOODS

        necessities = [g for g in GOODS if g.is_necessity]
        luxuries = [g for g in GOODS if not g.is_necessity]

        def calculate_elasticity(good_id: str) -> float:
            """価格弾力性を計算"""
            if good_id not in self.history["prices"]:
                return 0.0

            prices = np.array(self.history["prices"][good_id])
            demands = np.array(self.history["demands"][good_id])

            # 価格変化率と需要変化率を計算
            price_change = np.diff(prices) / prices[:-1]
            demand_change = np.diff(demands) / (demands[:-1] + 1e-9)  # ゼロ除算回避

            # 弾力性 = (需要変化率) / (価格変化率)
            # ゼロ除算とnanを除外
            elasticities = []
            for pc, dc in zip(price_change, demand_change):
                if abs(pc) > 1e-6 and not np.isnan(dc):
                    elasticities.append(dc / pc)

            if len(elasticities) == 0:
                return 0.0

            return float(np.mean(elasticities))

        # 必需品の弾力性
        necessity_elasticities = [
            calculate_elasticity(g.good_id) for g in necessities
        ]
        necessity_elasticities = [e for e in necessity_elasticities if e != 0.0]
        mean_necessity_elasticity = (
            np.mean(necessity_elasticities) if necessity_elasticities else 0.0
        )
        necessity_valid = -1 < mean_necessity_elasticity < 0

        # 贅沢品の弾力性
        luxury_elasticities = [calculate_elasticity(g.good_id) for g in luxuries]
        luxury_elasticities = [e for e in luxury_elasticities if e != 0.0]
        mean_luxury_elasticity = (
            np.mean(luxury_elasticities) if luxury_elasticities else 0.0
        )
        luxury_valid = mean_luxury_elasticity < -1

        result = {
            "phenomenon": "Price Elasticity",
            "necessities": {
                "mean_elasticity": float(mean_necessity_elasticity),
                "valid": bool(necessity_valid),
                "expected": "-1 < E < 0",
            },
            "luxuries": {
                "mean_elasticity": float(mean_luxury_elasticity),
                "valid": bool(luxury_valid),
                "expected": "E < -1",
            },
            "valid": bool(necessity_valid and luxury_valid),
            "description": "Price change vs Demand change",
        }

        logger.info(
            f"Price Elasticity: Necessities E={mean_necessity_elasticity:.4f}, "
            f"Luxuries E={mean_luxury_elasticity:.4f}"
        )

        return result

    def validate_engels_law(self) -> dict:
        """
        Engel's Law検証: 所得上昇に伴う食料支出割合の減少

        Returns:
            {
                "correlation": float,
                "p_value": float,
                "valid": bool (r < 0 and p < 0.05),
            }
        """
        logger.info("Validating Engel's Law...")

        # 各ステップの世帯ごとの所得と食料支出割合を取得
        incomes = []
        food_ratios = []

        for step_incomes, step_ratios in zip(
            self.history["household_incomes"], self.history["food_expenditure_ratios"]
        ):
            incomes.extend(step_incomes)
            food_ratios.extend(step_ratios)

        incomes = np.array(incomes)
        food_ratios = np.array(food_ratios)

        # 相関係数とp値を計算
        correlation, p_value = stats.pearsonr(incomes, food_ratios)

        valid = correlation < 0 and p_value < 0.05

        result = {
            "phenomenon": "Engel's Law",
            "correlation": float(correlation),
            "p_value": float(p_value),
            "valid": bool(valid),
            "expected": "r < 0 (negative correlation)",
            "description": "Income vs Food expenditure ratio",
        }

        logger.info(
            f"Engel's Law: r={correlation:.4f}, p={p_value:.4f}, valid={valid}"
        )

        return result

    def validate_investment_volatility(self) -> dict:
        """
        Investment Volatility検証: 投資のボラティリティ > 消費のボラティリティ

        Returns:
            {
                "investment_std": float,
                "consumption_std": float,
                "valid": bool (investment_std > consumption_std),
            }
        """
        logger.info("Validating Investment Volatility...")

        consumption = np.array(self.history["consumption"])
        investment = np.array(self.history["investment"])

        # 標準偏差を計算
        consumption_std = np.std(consumption)
        investment_std = np.std(investment)

        valid = investment_std > consumption_std

        result = {
            "phenomenon": "Investment Volatility",
            "investment_std": float(investment_std),
            "consumption_std": float(consumption_std),
            "ratio": float(investment_std / (consumption_std + 1e-9)),
            "valid": bool(valid),
            "expected": "std(Investment) > std(Consumption)",
            "description": "Volatility comparison",
        }

        logger.info(
            f"Investment Volatility: std(I)={investment_std:.4f}, "
            f"std(C)={consumption_std:.4f}, valid={valid}"
        )

        return result

    def validate_price_stickiness(self) -> dict:
        """
        Price Stickiness検証: 価格調整の遅延

        価格変化の頻度が需要変化の頻度より低いことを確認

        Returns:
            {
                "price_change_frequency": float,
                "demand_change_frequency": float,
                "valid": bool,
            }
        """
        logger.info("Validating Price Stickiness...")

        from src.data.goods_types import GOODS

        price_change_frequencies = []
        demand_change_frequencies = []

        for good in GOODS:
            good_id = good.good_id
            if good_id not in self.history["prices"]:
                continue

            prices = np.array(self.history["prices"][good_id])
            demands = np.array(self.history["demands"][good_id])

            # 価格変化の頻度（変化した回数 / 総ステップ数）
            price_changes = np.abs(np.diff(prices)) > 1e-6
            price_change_freq = np.sum(price_changes) / len(price_changes)

            # 需要変化の頻度
            demand_changes = np.abs(np.diff(demands)) > 1e-6
            demand_change_freq = np.sum(demand_changes) / len(demand_changes)

            price_change_frequencies.append(price_change_freq)
            demand_change_frequencies.append(demand_change_freq)

        mean_price_change_freq = np.mean(price_change_frequencies)
        mean_demand_change_freq = np.mean(demand_change_frequencies)

        # 価格変化頻度が需要変化頻度より低ければ粘着性あり
        valid = mean_price_change_freq < mean_demand_change_freq

        result = {
            "phenomenon": "Price Stickiness",
            "price_change_frequency": float(mean_price_change_freq),
            "demand_change_frequency": float(mean_demand_change_freq),
            "valid": bool(valid),
            "expected": "Price change frequency < Demand change frequency",
            "description": "Price adjustment delay",
        }

        logger.info(
            f"Price Stickiness: price_freq={mean_price_change_freq:.4f}, "
            f"demand_freq={mean_demand_change_freq:.4f}, valid={valid}"
        )

        return result

    def validate_all(self) -> dict:
        """
        すべての経済現象を検証

        Returns:
            {
                "phillips_curve": {...},
                "okuns_law": {...},
                "beveridge_curve": {...},
                "price_elasticity": {...},
                "engels_law": {...},
                "investment_volatility": {...},
                "price_stickiness": {...},
                "summary": {
                    "total": 7,
                    "valid": int,
                    "invalid": int,
                }
            }
        """
        logger.info("=" * 60)
        logger.info("Starting Economic Phenomena Validation")
        logger.info("=" * 60)

        results = {
            "phillips_curve": self.validate_phillips_curve(),
            "okuns_law": self.validate_okuns_law(),
            "beveridge_curve": self.validate_beveridge_curve(),
            "price_elasticity": self.validate_price_elasticity(),
            "engels_law": self.validate_engels_law(),
            "investment_volatility": self.validate_investment_volatility(),
            "price_stickiness": self.validate_price_stickiness(),
        }

        # サマリーを計算
        valid_count = sum(1 for r in results.values() if r.get("valid", False))
        invalid_count = 7 - valid_count

        results["summary"] = {
            "total": 7,
            "valid": valid_count,
            "invalid": invalid_count,
            "success_rate": valid_count / 7,
        }

        logger.info("=" * 60)
        logger.info(f"Validation Summary: {valid_count}/7 phenomena validated")
        logger.info("=" * 60)

        return results

    def generate_report(self, output_path: str = "validation_report.json"):
        """
        検証レポートをJSON形式で保存

        Args:
            output_path: 出力ファイルパス
        """
        results = self.validate_all()

        report = {
            "metadata": self.metadata,
            "validation_results": results,
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Validation report saved to {output_file}")

        return report


def run_validation_experiment(
    config_path: str = "config/simulation_config.yaml",
    steps: int = 180,
    output_dir: str = "experiments/results",
):
    """
    検証実験を実行

    Args:
        config_path: 設定ファイルパス
        steps: シミュレーションステップ数（デフォルト: 180 = 15年）
        output_dir: 結果出力ディレクトリ
    """
    setup_logger(log_level="INFO")

    logger.info(f"Starting validation experiment: {steps} steps")

    # 設定を読み込み
    config = load_config(config_path)

    # TODO: 実際のシミュレーション実行
    # NOTE: LLM API呼び出しが必要なため、ここでは省略
    # 実際の実行は別のスクリプトで行い、結果データを読み込む形にする

    logger.warning(
        "Actual simulation with LLM is not implemented yet. "
        "Please run simulation separately and load the result data."
    )

    # サンプルデータ構造を示す
    sample_data = {
        "history": {
            "gdp": [100 + i * 2 for i in range(steps)],
            "inflation": [0.02 + np.random.randn() * 0.01 for _ in range(steps)],
            "unemployment_rate": [
                0.05 + np.random.randn() * 0.01 for _ in range(steps)
            ],
            "vacancy_rate": [0.03 + np.random.randn() * 0.01 for _ in range(steps)],
            "gini": [0.35 + np.random.randn() * 0.02 for _ in range(steps)],
            "consumption": [80 + i * 1.5 for i in range(steps)],
            "investment": [20 + i * 0.5 + np.random.randn() * 5 for i in range(steps)],
            "prices": {},
            "demands": {},
            "household_incomes": [
                [40000 + np.random.randn() * 5000 for _ in range(200)]
                for _ in range(steps)
            ],
            "food_expenditure_ratios": [
                [0.15 + np.random.randn() * 0.05 for _ in range(200)]
                for _ in range(steps)
            ],
        },
        "metadata": {"steps": steps, "households": 200, "firms": 44},
    }

    logger.info(
        "To run actual validation, please load simulation result data and use:"
    )
    logger.info("  validator = EconomicPhenomenaValidator(simulation_data)")
    logger.info("  report = validator.generate_report('validation_report.json')")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run economic phenomena validation")
    parser.add_argument(
        "--steps",
        type=int,
        default=180,
        help="Number of simulation steps (default: 180 = 15 years)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/simulation_config.yaml",
        help="Path to simulation config file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="experiments/results",
        help="Output directory for results",
    )

    args = parser.parse_args()

    run_validation_experiment(
        config_path=args.config, steps=args.steps, output_dir=args.output
    )
