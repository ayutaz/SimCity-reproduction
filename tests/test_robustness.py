"""Tests for Robustness Test"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.robustness_test import RobustnessTest


class TestRobustnessTest:
    """Test RobustnessTest"""

    @pytest.fixture
    def sample_runs(self):
        """Create sample simulation runs with different seeds"""
        np.random.seed(42)

        runs = []
        for seed in [42, 123, 456]:
            np.random.seed(seed)
            steps = 50

            # Generate data with same qualitative properties but different values
            unemployment = (
                np.linspace(0.05, 0.10, steps) + np.random.randn(steps) * 0.005
            )
            inflation = -unemployment * 2 + 0.25 + np.random.randn(steps) * 0.01
            gdp = 1000 + np.cumsum(np.random.randn(steps) * 10)
            vacancy = -unemployment * 2 + 0.20 + np.random.randn(steps) * 0.005

            consumption = 800 + np.arange(steps) * 2 + np.random.randn(steps) * 5
            investment = 200 + np.arange(steps) * 0.5 + np.random.randn(steps) * 30

            household_incomes = []
            food_expenditure_ratios = []
            for _ in range(steps):
                incomes = np.random.lognormal(10.5, 0.5, 200)
                food_ratios = 0.30 - incomes / 100000 + np.random.randn(200) * 0.05
                food_ratios = np.clip(food_ratios, 0.05, 0.50)
                household_incomes.append(incomes.tolist())
                food_expenditure_ratios.append(food_ratios.tolist())

            # Price elasticity data
            from src.data.goods_types import GOODS

            prices = {}
            demands = {}
            for good in GOODS[:10]:
                base_price = 50.0
                price_series = base_price + np.random.randn(steps) * 5
                prices[good.good_id] = price_series.tolist()

                if good.is_necessity:
                    elasticity = -0.5
                else:
                    elasticity = -1.5

                demand_series = 100 * (price_series / base_price) ** elasticity
                demands[good.good_id] = demand_series.tolist()

            run_data = {
                "history": {
                    "gdp": gdp.tolist(),
                    "inflation": inflation.tolist(),
                    "unemployment_rate": unemployment.tolist(),
                    "vacancy_rate": vacancy.tolist(),
                    "gini": (0.35 + np.random.randn(steps) * 0.02).tolist(),
                    "consumption": consumption.tolist(),
                    "investment": investment.tolist(),
                    "prices": prices,
                    "demands": demands,
                    "household_incomes": household_incomes,
                    "food_expenditure_ratios": food_expenditure_ratios,
                },
                "metadata": {
                    "steps": steps,
                    "households": 200,
                    "firms": 44,
                    "seed": seed,
                },
            }

            runs.append(run_data)

        return runs

    def test_initialization(self, sample_runs):
        """Test RobustnessTest initialization"""
        tester = RobustnessTest(sample_runs)

        assert tester.num_runs == 3
        assert len(tester.results) == 3

    def test_qualitative_consistency(self, sample_runs):
        """Test qualitative consistency check"""
        tester = RobustnessTest(sample_runs)
        result = tester.test_qualitative_consistency()

        assert "overall_consistent" in result
        assert "phenomena" in result
        assert "num_runs" in result

        # Check all 7 phenomena are tested
        phenomena = result["phenomena"]
        assert "phillips_curve" in phenomena
        assert "okuns_law" in phenomena
        assert "beveridge_curve" in phenomena
        assert "price_elasticity" in phenomena
        assert "engels_law" in phenomena
        assert "investment_volatility" in phenomena
        assert "price_stickiness" in phenomena

        # Each phenomenon should have consistency info
        for name, info in phenomena.items():
            if name != "price_elasticity":
                assert "consistent" in info
                assert "values" in info
                assert "expected_direction" in info
                assert "success_rate" in info

    def test_statistical_significance(self, sample_runs):
        """Test statistical significance check"""
        tester = RobustnessTest(sample_runs)
        result = tester.test_statistical_significance()

        # Check key indicators
        assert "gdp" in result
        assert "unemployment_rate" in result
        assert "inflation" in result
        assert "gini_coefficient" in result

        # Each indicator should have statistics
        for _indicator, stats in result.items():
            assert "mean" in stats
            assert "std" in stats
            assert "min" in stats
            assert "max" in stats
            assert "cv" in stats  # coefficient of variation
            assert "stability" in stats

    def test_trend_consistency(self, sample_runs):
        """Test trend consistency check"""
        tester = RobustnessTest(sample_runs)
        result = tester.test_trend_consistency()

        # Check GDP and unemployment trends
        assert "gdp" in result
        assert "unemployment_rate" in result

        for _indicator, info in result.items():
            assert "trend_directions" in info
            assert "consistent" in info
            assert "correlation_matrix" in info
            assert "mean_correlation" in info

    def test_generate_report(self, sample_runs, tmp_path):
        """Test report generation"""
        tester = RobustnessTest(sample_runs)

        output_path = tmp_path / "test_robustness_report.json"
        report = tester.generate_report(str(output_path))

        # Check report structure
        assert "num_runs" in report
        assert "seeds" in report
        assert "qualitative_consistency" in report
        assert "statistical_significance" in report
        assert "trend_consistency" in report
        assert "overall_assessment" in report

        # Check overall assessment
        assessment = report["overall_assessment"]
        assert "qualitative_consistency" in assessment
        assert "statistical_stability" in assessment
        assert "trend_consistency" in assessment
        assert "robust" in assessment

        # Check file was created
        assert output_path.exists()

        # Check file content
        import json

        with open(output_path, encoding="utf-8") as f:
            loaded_report = json.load(f)

        assert loaded_report == report

    def test_with_two_runs(self):
        """Test with minimum number of runs (2)"""
        np.random.seed(42)

        runs = []
        for seed in [42, 123]:
            np.random.seed(seed)
            steps = 20

            runs.append(
                {
                    "history": {
                        "gdp": (1000 + np.cumsum(np.random.randn(steps) * 10)).tolist(),
                        "inflation": (0.02 + np.random.randn(steps) * 0.01).tolist(),
                        "unemployment_rate": (
                            0.05 + np.random.randn(steps) * 0.01
                        ).tolist(),
                        "vacancy_rate": (0.03 + np.random.randn(steps) * 0.01).tolist(),
                        "gini": (0.35 + np.random.randn(steps) * 0.02).tolist(),
                        "consumption": (800 + np.arange(steps) * 2).tolist(),
                        "investment": (200 + np.arange(steps) * 0.5).tolist(),
                        "prices": {},
                        "demands": {},
                        "household_incomes": [[40000] * 10 for _ in range(steps)],
                        "food_expenditure_ratios": [[0.15] * 10 for _ in range(steps)],
                    },
                    "metadata": {
                        "steps": steps,
                        "households": 10,
                        "firms": 5,
                        "seed": seed,
                    },
                }
            )

        tester = RobustnessTest(runs)

        # Should not crash with 2 runs
        consistency = tester.test_qualitative_consistency()
        assert consistency["num_runs"] == 2

        significance = tester.test_statistical_significance()
        assert "gdp" in significance

        trends = tester.test_trend_consistency()
        assert "gdp" in trends


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
