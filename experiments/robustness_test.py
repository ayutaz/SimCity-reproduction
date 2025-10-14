"""
Robustness Test

3つの異なる乱数シードでシミュレーションを実行し、
結果の定性的一致と統計的有意性を検証する。
"""

import json
import sys
from pathlib import Path

import numpy as np
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.validation import EconomicPhenomenaValidator
from src.utils.logger import setup_logger


class RobustnessTest:
    """
    ロバストネステストクラス

    異なる乱数シードでシミュレーションを実行し、
    結果の再現性と安定性を検証する。
    """

    def __init__(self, simulation_results: list[dict]):
        """
        Args:
            simulation_results: 複数のシミュレーション結果のリスト
                各要素は validation.py で使用される形式
        """
        self.results = simulation_results
        self.num_runs = len(simulation_results)

    def test_qualitative_consistency(self) -> dict:
        """
        定性的一致の検証

        各シミュレーション実行で、7つの経済現象が
        同じ方向（正/負の相関）を示すかを確認

        Returns:
            {
                "phenomenon_name": {
                    "consistent": bool,
                    "values": [run1_value, run2_value, ...],
                    "expected_direction": str,
                    "success_rate": float,
                }
            }
        """
        logger.info("Testing qualitative consistency across runs...")

        validators = [EconomicPhenomenaValidator(r) for r in self.results]
        all_validations = [v.validate_all() for v in validators]

        consistency_results = {}

        # Phillips Curve: 負の相関
        phillips_values = [v["phillips_curve"]["correlation"] for v in all_validations]
        phillips_consistent = all(v < 0 for v in phillips_values)
        consistency_results["phillips_curve"] = {
            "consistent": phillips_consistent,
            "values": phillips_values,
            "expected_direction": "negative correlation",
            "success_rate": sum(1 for v in phillips_values if v < 0)
            / len(phillips_values),
        }

        # Okun's Law: 負の相関
        okun_values = [v["okuns_law"]["correlation"] for v in all_validations]
        okun_consistent = all(v < 0 for v in okun_values)
        consistency_results["okuns_law"] = {
            "consistent": okun_consistent,
            "values": okun_values,
            "expected_direction": "negative correlation",
            "success_rate": sum(1 for v in okun_values if v < 0) / len(okun_values),
        }

        # Beveridge Curve: 強い負の相関
        beveridge_values = [
            v["beveridge_curve"]["correlation"] for v in all_validations
        ]
        beveridge_consistent = all(v < -0.5 for v in beveridge_values)
        consistency_results["beveridge_curve"] = {
            "consistent": beveridge_consistent,
            "values": beveridge_values,
            "expected_direction": "strong negative correlation (< -0.5)",
            "success_rate": sum(1 for v in beveridge_values if v < -0.5)
            / len(beveridge_values),
        }

        # Price Elasticity: 必需品と贅沢品
        necessity_elasticities = [
            v["price_elasticity"]["necessities"]["mean_elasticity"]
            for v in all_validations
        ]
        luxury_elasticities = [
            v["price_elasticity"]["luxuries"]["mean_elasticity"]
            for v in all_validations
        ]
        necessity_consistent = all(-1 < e < 0 for e in necessity_elasticities)
        luxury_consistent = all(e < -1 for e in luxury_elasticities)
        consistency_results["price_elasticity"] = {
            "consistent": necessity_consistent and luxury_consistent,
            "necessities": {
                "values": necessity_elasticities,
                "expected": "-1 < E < 0",
                "consistent": necessity_consistent,
            },
            "luxuries": {
                "values": luxury_elasticities,
                "expected": "E < -1",
                "consistent": luxury_consistent,
            },
            "success_rate": (
                sum(1 for e in necessity_elasticities if -1 < e < 0)
                + sum(1 for e in luxury_elasticities if e < -1)
            )
            / (len(necessity_elasticities) + len(luxury_elasticities)),
        }

        # Engel's Law: 負の相関
        engel_values = [v["engels_law"]["correlation"] for v in all_validations]
        engel_consistent = all(v < 0 for v in engel_values)
        consistency_results["engels_law"] = {
            "consistent": engel_consistent,
            "values": engel_values,
            "expected_direction": "negative correlation",
            "success_rate": sum(1 for v in engel_values if v < 0) / len(engel_values),
        }

        # Investment Volatility: std(投資) > std(消費)
        investment_volatilities = [
            v["investment_volatility"]["valid"] for v in all_validations
        ]
        volatility_consistent = all(investment_volatilities)
        consistency_results["investment_volatility"] = {
            "consistent": volatility_consistent,
            "values": investment_volatilities,
            "expected_direction": "std(Investment) > std(Consumption)",
            "success_rate": sum(investment_volatilities) / len(investment_volatilities),
        }

        # Price Stickiness
        price_stickiness_values = [
            v["price_stickiness"]["valid"] for v in all_validations
        ]
        stickiness_consistent = all(price_stickiness_values)
        consistency_results["price_stickiness"] = {
            "consistent": stickiness_consistent,
            "values": price_stickiness_values,
            "expected_direction": "Price adjustment delay",
            "success_rate": sum(price_stickiness_values) / len(price_stickiness_values),
        }

        # Overall consistency
        all_consistent = all(
            r.get("consistent", False) for r in consistency_results.values()
        )

        logger.info(f"Qualitative consistency: {all_consistent}")
        logger.info(
            f"Consistent phenomena: {sum(1 for r in consistency_results.values() if r.get('consistent', False))}/7"
        )

        return {
            "overall_consistent": all_consistent,
            "phenomena": consistency_results,
            "num_runs": self.num_runs,
        }

    def test_statistical_significance(self) -> dict:
        """
        統計的有意性の検証

        複数実行の結果から、経済指標の統計的特性を検証

        Returns:
            {
                "indicator_name": {
                    "mean": float,
                    "std": float,
                    "min": float,
                    "max": float,
                    "cv": float,  # coefficient of variation
                }
            }
        """
        logger.info("Testing statistical significance...")

        # 各実行の最終ステップの指標を収集
        final_gdp = []
        final_unemployment = []
        final_inflation = []
        final_gini = []

        for result in self.results:
            history = result["history"]
            final_gdp.append(history["gdp"][-1])
            final_unemployment.append(history["unemployment_rate"][-1])
            final_inflation.append(history["inflation"][-1])
            final_gini.append(history["gini"][-1])

        def calc_stats(values: list) -> dict:
            """統計量を計算"""
            values_arr = np.array(values)
            mean_val = float(np.mean(values_arr))
            std_val = float(np.std(values_arr))
            return {
                "mean": mean_val,
                "std": std_val,
                "min": float(np.min(values_arr)),
                "max": float(np.max(values_arr)),
                "cv": abs(std_val / mean_val)
                if mean_val != 0
                else float("inf"),  # coefficient of variation
            }

        significance_results = {
            "gdp": calc_stats(final_gdp),
            "unemployment_rate": calc_stats(final_unemployment),
            "inflation": calc_stats(final_inflation),
            "gini_coefficient": calc_stats(final_gini),
        }

        # Coefficient of variation が小さいほど安定
        # 一般的に CV < 0.3 なら低変動、0.3-0.6なら中程度、>0.6なら高変動
        for indicator, stats_dict in significance_results.items():
            cv = stats_dict["cv"]
            if cv < 0.3:
                stability = "low variance (stable)"
            elif cv < 0.6:
                stability = "moderate variance"
            else:
                stability = "high variance (unstable)"
            stats_dict["stability"] = stability

            logger.info(
                f"{indicator}: mean={stats_dict['mean']:.4f}, cv={cv:.4f} ({stability})"
            )

        return significance_results

    def test_trend_consistency(self) -> dict:
        """
        トレンドの一致性を検証

        各実行でGDP、失業率などの時系列トレンドが一致するか確認

        Returns:
            {
                "indicator_name": {
                    "trend_directions": [run1_trend, run2_trend, ...],
                    "consistent": bool,
                    "correlation_matrix": [[...], ...],
                }
            }
        """
        logger.info("Testing trend consistency...")

        trend_results = {}

        # GDP トレンド
        gdp_series = [r["history"]["gdp"] for r in self.results]
        gdp_trends = [1 if s[-1] > s[0] else -1 for s in gdp_series]
        gdp_consistent = len(set(gdp_trends)) == 1

        # 相関行列を計算（異なる実行間の時系列相関）
        gdp_correlation_matrix = np.corrcoef(gdp_series).tolist()

        trend_results["gdp"] = {
            "trend_directions": gdp_trends,
            "consistent": gdp_consistent,
            "correlation_matrix": gdp_correlation_matrix,
            "mean_correlation": float(
                np.mean([c for row in gdp_correlation_matrix for c in row if c != 1.0])
            ),
        }

        # Unemployment トレンド
        unemployment_series = [r["history"]["unemployment_rate"] for r in self.results]
        unemployment_trends = [1 if s[-1] > s[0] else -1 for s in unemployment_series]
        unemployment_consistent = len(set(unemployment_trends)) == 1
        unemployment_correlation_matrix = np.corrcoef(unemployment_series).tolist()

        trend_results["unemployment_rate"] = {
            "trend_directions": unemployment_trends,
            "consistent": unemployment_consistent,
            "correlation_matrix": unemployment_correlation_matrix,
            "mean_correlation": float(
                np.mean(
                    [
                        c
                        for row in unemployment_correlation_matrix
                        for c in row
                        if c != 1.0
                    ]
                )
            ),
        }

        logger.info(f"GDP trend consistent: {gdp_consistent}")
        logger.info(f"Unemployment trend consistent: {unemployment_consistent}")

        return trend_results

    def generate_report(self, output_path: str = "robustness_report.json") -> dict:
        """
        ロバストネステストレポートを生成

        Args:
            output_path: 出力ファイルパス

        Returns:
            レポート辞書
        """
        logger.info("Generating robustness test report...")

        report = {
            "num_runs": self.num_runs,
            "seeds": [r["metadata"].get("seed", None) for r in self.results],
            "qualitative_consistency": self.test_qualitative_consistency(),
            "statistical_significance": self.test_statistical_significance(),
            "trend_consistency": self.test_trend_consistency(),
        }

        # Overall assessment
        qualitative_ok = report["qualitative_consistency"]["overall_consistent"]

        # Statistical significance: すべてのCVが<0.6なら安定
        significance = report["statistical_significance"]
        statistical_ok = all(s["cv"] < 0.6 for s in significance.values())

        # Trend consistency: GDP and unemploymentが一致すればOK
        trend_ok = (
            report["trend_consistency"]["gdp"]["consistent"]
            and report["trend_consistency"]["unemployment_rate"]["consistent"]
        )

        report["overall_assessment"] = {
            "qualitative_consistency": qualitative_ok,
            "statistical_stability": statistical_ok,
            "trend_consistency": trend_ok,
            "robust": qualitative_ok and statistical_ok and trend_ok,
        }

        # Save report
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Robustness test report saved to {output_file}")

        if report["overall_assessment"]["robust"]:
            logger.info("✅ Robustness test PASSED")
        else:
            logger.warning("⚠️ Robustness test FAILED")
            if not qualitative_ok:
                logger.warning("  - Qualitative consistency: FAILED")
            if not statistical_ok:
                logger.warning("  - Statistical stability: FAILED")
            if not trend_ok:
                logger.warning("  - Trend consistency: FAILED")

        return report


def run_robustness_test(
    simulation_data_paths: list[str],
    output_path: str = "experiments/results/robustness_report.json",
):
    """
    ロバストネステストを実行

    Args:
        simulation_data_paths: シミュレーション結果JSONファイルのパスリスト
        output_path: 出力レポートパス
    """
    setup_logger(log_level="INFO")

    logger.info(f"Loading {len(simulation_data_paths)} simulation results...")

    simulation_results = []
    for path in simulation_data_paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        simulation_results.append(data)
        logger.info(f"  Loaded: {path}")

    # Run robustness test
    tester = RobustnessTest(simulation_results)
    report = tester.generate_report(output_path)

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run robustness test")
    parser.add_argument(
        "simulation_files",
        nargs="+",
        help="Paths to simulation result JSON files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="experiments/results/robustness_report.json",
        help="Output report path",
    )

    args = parser.parse_args()

    run_robustness_test(
        simulation_data_paths=args.simulation_files,
        output_path=args.output,
    )
