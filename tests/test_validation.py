"""Tests for Economic Phenomena Validation"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.validation import EconomicPhenomenaValidator


class TestEconomicPhenomenaValidator:
    """Test EconomicPhenomenaValidator"""

    @pytest.fixture
    def sample_data(self):
        """Create sample simulation data for testing"""
        steps = 50

        # Generate synthetic data that satisfies economic phenomena
        np.random.seed(42)

        # Phillips Curve: negative correlation between unemployment and inflation
        unemployment = np.linspace(0.05, 0.10, steps) + np.random.randn(steps) * 0.005
        inflation = -unemployment * 2 + 0.25 + np.random.randn(steps) * 0.01

        # Okun's Law: negative correlation between unemployment change and GDP growth
        gdp = 1000 + np.cumsum(np.random.randn(steps) * 10)

        # Beveridge Curve: strong negative correlation
        vacancy = -unemployment * 2 + 0.20 + np.random.randn(steps) * 0.005

        # Investment Volatility: investment more volatile than consumption
        consumption = 800 + np.arange(steps) * 2 + np.random.randn(steps) * 5
        investment = (
            200 + np.arange(steps) * 0.5 + np.random.randn(steps) * 30
        )  # Increased volatility

        # Engel's Law: negative correlation between income and food expenditure ratio
        household_incomes = []
        food_expenditure_ratios = []
        for _ in range(steps):
            incomes = np.random.lognormal(10.5, 0.5, 200)
            # Higher income -> lower food ratio
            food_ratios = 0.30 - incomes / 100000 + np.random.randn(200) * 0.05
            food_ratios = np.clip(food_ratios, 0.05, 0.50)
            household_incomes.append(incomes.tolist())
            food_expenditure_ratios.append(food_ratios.tolist())

        # Price Elasticity: prices and demands for goods
        from src.data.goods_types import GOODS

        prices = {}
        demands = {}
        for good in GOODS[:10]:  # Test with first 10 goods
            base_price = 50.0
            price_series = base_price + np.random.randn(steps) * 5
            prices[good.good_id] = price_series.tolist()

            # Demand inversely related to price
            if good.is_necessity:
                # Inelastic: -1 < E < 0
                elasticity = -0.5
            else:
                # Elastic: E < -1
                elasticity = -1.5

            demand_series = 100 * (price_series / base_price) ** elasticity
            demands[good.good_id] = demand_series.tolist()

        data = {
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
            "metadata": {"steps": steps, "households": 200, "firms": 44},
        }

        return data

    def test_validator_initialization(self, sample_data):
        """Test validator initialization"""
        validator = EconomicPhenomenaValidator(sample_data)

        assert validator.data == sample_data
        assert validator.history == sample_data["history"]
        assert validator.metadata == sample_data["metadata"]

    def test_phillips_curve_validation(self, sample_data):
        """Test Phillips Curve validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_phillips_curve()

        assert "correlation" in result
        assert "p_value" in result
        assert "valid" in result
        assert result["phenomenon"] == "Phillips Curve"

        # Our synthetic data has negative correlation
        assert result["correlation"] < 0

    def test_okuns_law_validation(self, sample_data):
        """Test Okun's Law validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_okuns_law()

        assert "correlation" in result
        assert "p_value" in result
        assert "valid" in result
        assert result["phenomenon"] == "Okun's Law"

    def test_beveridge_curve_validation(self, sample_data):
        """Test Beveridge Curve validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_beveridge_curve()

        assert "correlation" in result
        assert "p_value" in result
        assert "valid" in result
        assert result["phenomenon"] == "Beveridge Curve"

        # Strong negative correlation
        assert result["correlation"] < -0.5
        assert result["valid"] is True

    def test_price_elasticity_validation(self, sample_data):
        """Test Price Elasticity validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_price_elasticity()

        assert "necessities" in result
        assert "luxuries" in result
        assert "valid" in result
        assert result["phenomenon"] == "Price Elasticity"

        # Check structure
        assert "mean_elasticity" in result["necessities"]
        assert "valid" in result["necessities"]
        assert "mean_elasticity" in result["luxuries"]
        assert "valid" in result["luxuries"]

    def test_engels_law_validation(self, sample_data):
        """Test Engel's Law validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_engels_law()

        assert "correlation" in result
        assert "p_value" in result
        assert "valid" in result
        assert result["phenomenon"] == "Engel's Law"

        # Negative correlation
        assert result["correlation"] < 0

    def test_investment_volatility_validation(self, sample_data):
        """Test Investment Volatility validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_investment_volatility()

        assert "investment_std" in result
        assert "consumption_std" in result
        assert "valid" in result
        assert result["phenomenon"] == "Investment Volatility"

        # Investment more volatile
        assert result["investment_std"] > result["consumption_std"]
        assert result["valid"] is True

    def test_price_stickiness_validation(self, sample_data):
        """Test Price Stickiness validation"""
        validator = EconomicPhenomenaValidator(sample_data)
        result = validator.validate_price_stickiness()

        assert "price_change_frequency" in result
        assert "demand_change_frequency" in result
        assert "valid" in result
        assert result["phenomenon"] == "Price Stickiness"

    def test_validate_all(self, sample_data):
        """Test validating all phenomena at once"""
        validator = EconomicPhenomenaValidator(sample_data)
        results = validator.validate_all()

        # Check all phenomena are present (now 10 phenomena)
        assert "phillips_curve" in results
        assert "okuns_law" in results
        assert "beveridge_curve" in results
        assert "price_elasticity" in results
        assert "engels_law" in results
        assert "investment_volatility" in results
        assert "price_stickiness" in results
        assert "wage_price_spiral" in results
        assert "capital_accumulation" in results
        assert "consumption_smoothing" in results
        assert "summary" in results

        # Check summary
        summary = results["summary"]
        assert summary["total"] == 10
        assert "valid" in summary
        assert "invalid" in summary
        assert "success_rate" in summary
        assert summary["valid"] + summary["invalid"] == 10

    def test_generate_report(self, sample_data, tmp_path):
        """Test generating validation report"""
        validator = EconomicPhenomenaValidator(sample_data)

        output_path = tmp_path / "test_report.json"
        report = validator.generate_report(str(output_path))

        # Check report structure
        assert "metadata" in report
        assert "validation_results" in report

        # Check file was created
        assert output_path.exists()

        # Check file content
        import json

        with open(output_path, encoding="utf-8") as f:
            loaded_report = json.load(f)

        assert loaded_report == report


class TestValidationWithEdgeCases:
    """Test validation with edge cases"""

    def test_empty_history(self):
        """Test with minimal/empty history"""
        data = {
            "history": {
                "gdp": [100, 110],
                "inflation": [0.02, 0.03],
                "unemployment_rate": [0.05, 0.06],
                "vacancy_rate": [0.03, 0.02],
                "gini": [0.35, 0.36],
                "consumption": [80, 85],
                "investment": [20, 22],
                "prices": {},
                "demands": {},
                "household_incomes": [[40000] * 10, [42000] * 10],
                "food_expenditure_ratios": [[0.15] * 10, [0.14] * 10],
            },
            "metadata": {"steps": 2, "households": 10, "firms": 5},
        }

        validator = EconomicPhenomenaValidator(data)

        # Should not crash with minimal data
        result = validator.validate_phillips_curve()
        assert "correlation" in result

    def test_constant_values(self):
        """Test with constant values (no variance)"""
        steps = 20
        data = {
            "history": {
                "gdp": [100] * steps,
                "inflation": [0.02] * steps,
                "unemployment_rate": [0.05] * steps,
                "vacancy_rate": [0.03] * steps,
                "gini": [0.35] * steps,
                "consumption": [80] * steps,
                "investment": [20] * steps,
                "prices": {},
                "demands": {},
                "household_incomes": [[40000] * 10 for _ in range(steps)],
                "food_expenditure_ratios": [[0.15] * 10 for _ in range(steps)],
            },
            "metadata": {"steps": steps, "households": 10, "firms": 5},
        }

        validator = EconomicPhenomenaValidator(data)

        # Should handle constant values gracefully
        # Correlation will be undefined (nan) or 0
        result = validator.validate_phillips_curve()
        assert "correlation" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
