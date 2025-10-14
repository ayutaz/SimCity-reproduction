"""Tests for Economic Plots"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visualization.plots import EconomicPlots


class TestEconomicPlots:
    @pytest.fixture
    def plots(self):
        return EconomicPlots()

    @pytest.fixture
    def sample_time_series(self):
        """Generate sample time series data"""
        steps = 50
        gdp = 100 + np.cumsum(np.random.randn(steps) * 2)
        unemployment = 0.05 + np.random.randn(steps) * 0.01
        inflation = 0.02 + np.random.randn(steps) * 0.005

        return {
            "GDP": gdp.tolist(),
            "Unemployment Rate": unemployment.tolist(),
            "Inflation Rate": inflation.tolist(),
        }

    def test_initialization(self, plots):
        assert plots is not None

    def test_plot_time_series(self, plots, sample_time_series):
        """Test time series plotting"""
        fig = plots.plot_time_series(sample_time_series)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 3  # One for each indicator

        plt.close(fig)

    def test_plot_time_series_with_save(self, plots, sample_time_series, tmp_path):
        """Test time series plotting with file save"""
        save_path = tmp_path / "time_series.png"

        fig = plots.plot_time_series(sample_time_series, save_path=str(save_path))

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_phillips_curve(self, plots):
        """Test Phillips curve plotting"""
        # Generate data with negative correlation
        unemployment = np.linspace(0.03, 0.10, 30)
        inflation = 0.05 - 0.3 * unemployment + np.random.randn(30) * 0.005

        fig, stats = plots.plot_phillips_curve(
            unemployment.tolist(), inflation.tolist()
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "correlation" in stats
        assert "slope" in stats
        assert "r_squared" in stats

        # Check negative correlation (Phillips curve)
        assert stats["correlation"] < 0

        plt.close(fig)

    def test_plot_phillips_curve_with_save(self, plots, tmp_path):
        """Test Phillips curve with file save"""
        unemployment = np.linspace(0.03, 0.10, 30)
        inflation = 0.05 - 0.3 * unemployment + np.random.randn(30) * 0.005

        save_path = tmp_path / "phillips_curve.png"

        fig, stats = plots.plot_phillips_curve(
            unemployment.tolist(), inflation.tolist(), save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_okun_law(self, plots):
        """Test Okun's law plotting"""
        # Generate data with negative correlation
        unemployment_change = np.linspace(-0.02, 0.03, 30)
        gdp_growth = 0.03 - 2.0 * unemployment_change + np.random.randn(30) * 0.01

        fig, stats = plots.plot_okun_law(
            unemployment_change.tolist(), gdp_growth.tolist()
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "correlation" in stats
        assert "slope" in stats

        # Check negative correlation (Okun's law)
        assert stats["correlation"] < 0

        plt.close(fig)

    def test_plot_okun_law_with_save(self, plots, tmp_path):
        """Test Okun's law with file save"""
        unemployment_change = np.linspace(-0.02, 0.03, 30)
        gdp_growth = 0.03 - 2.0 * unemployment_change + np.random.randn(30) * 0.01

        save_path = tmp_path / "okun_law.png"

        fig, stats = plots.plot_okun_law(
            unemployment_change.tolist(), gdp_growth.tolist(), save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_beveridge_curve(self, plots):
        """Test Beveridge curve plotting"""
        # Generate data with negative correlation
        unemployment = np.linspace(0.03, 0.10, 30)
        vacancy = 0.08 - 0.5 * unemployment + np.random.randn(30) * 0.005

        fig, stats = plots.plot_beveridge_curve(unemployment.tolist(), vacancy.tolist())

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "correlation" in stats

        # Check negative correlation (Beveridge curve)
        assert stats["correlation"] < 0

        plt.close(fig)

    def test_plot_beveridge_curve_with_save(self, plots, tmp_path):
        """Test Beveridge curve with file save"""
        unemployment = np.linspace(0.03, 0.10, 30)
        vacancy = 0.08 - 0.5 * unemployment + np.random.randn(30) * 0.005

        save_path = tmp_path / "beveridge_curve.png"

        fig, stats = plots.plot_beveridge_curve(
            unemployment.tolist(), vacancy.tolist(), save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_engel_curve(self, plots):
        """Test Engel's law plotting"""
        # Generate data: food share decreases with income (log relationship)
        income = np.linspace(20000, 100000, 50)
        food_share = 0.5 - 0.08 * np.log(income / 20000) + np.random.randn(50) * 0.02

        fig, stats = plots.plot_engel_curve(income.tolist(), food_share.tolist())

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "slope" in stats
        assert "r_squared" in stats

        # Check negative slope (Engel's law)
        assert stats["slope"] < 0

        plt.close(fig)

    def test_plot_engel_curve_with_save(self, plots, tmp_path):
        """Test Engel curve with file save"""
        income = np.linspace(20000, 100000, 50)
        food_share = 0.5 - 0.08 * np.log(income / 20000) + np.random.randn(50) * 0.02

        save_path = tmp_path / "engel_curve.png"

        fig, stats = plots.plot_engel_curve(
            income.tolist(), food_share.tolist(), save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_price_elasticity_necessity(self, plots):
        """Test price elasticity for necessity goods (inelastic)"""
        # Inelastic: -1 < elasticity < 0
        prices = np.linspace(1.0, 3.0, 30)
        quantities = 100 * prices**-0.5 + np.random.randn(30) * 2  # Elasticity ≈ -0.5

        fig, stats = plots.plot_price_elasticity(
            prices.tolist(), quantities.tolist(), good_name="Food (Necessity)"
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "elasticity" in stats
        assert "elasticity_type" in stats

        # Check that it's inelastic
        assert -1 < stats["elasticity"] < 0
        assert "Inelastic" in stats["elasticity_type"]

        plt.close(fig)

    def test_plot_price_elasticity_luxury(self, plots):
        """Test price elasticity for luxury goods (elastic)"""
        # Elastic: elasticity < -1
        prices = np.linspace(1.0, 3.0, 30)
        quantities = 100 * prices**-2.0 + np.random.randn(30) * 2  # Elasticity ≈ -2.0

        fig, stats = plots.plot_price_elasticity(
            prices.tolist(), quantities.tolist(), good_name="Luxury Good"
        )

        assert fig is not None
        assert "elasticity" in stats

        # Check that it's elastic
        assert stats["elasticity"] < -1
        assert "Elastic" in stats["elasticity_type"]

        plt.close(fig)

    def test_plot_price_elasticity_with_save(self, plots, tmp_path):
        """Test price elasticity with file save"""
        prices = np.linspace(1.0, 3.0, 30)
        quantities = 100 * prices**-0.8 + np.random.randn(30) * 2

        save_path = tmp_path / "price_elasticity.png"

        fig, stats = plots.plot_price_elasticity(
            prices.tolist(), quantities.tolist(), save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_distribution(self, plots):
        """Test distribution plotting"""
        # Generate normal distribution data
        data = np.random.normal(50, 10, 1000).tolist()

        fig, stats = plots.plot_distribution(data, title="Income Distribution")

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats

        plt.close(fig)

    def test_plot_distribution_with_save(self, plots, tmp_path):
        """Test distribution plotting with file save"""
        data = np.random.normal(50, 10, 1000).tolist()

        save_path = tmp_path / "distribution.png"

        fig, stats = plots.plot_distribution(
            data, title="Income Distribution", save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_plot_comparison_bar(self, plots):
        """Test comparison bar plot"""
        data = {
            "Group A": [50, 52, 48, 51, 49],
            "Group B": [60, 62, 58, 61, 59],
            "Group C": [40, 42, 38, 41, 39],
        }

        fig = plots.plot_comparison(data, title="Group Comparison", plot_type="bar")

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        plt.close(fig)

    def test_plot_comparison_box(self, plots):
        """Test comparison box plot"""
        data = {
            "Group A": [50, 52, 48, 51, 49],
            "Group B": [60, 62, 58, 61, 59],
            "Group C": [40, 42, 38, 41, 39],
        }

        fig = plots.plot_comparison(data, title="Group Comparison", plot_type="box")

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        plt.close(fig)

    def test_plot_comparison_with_save(self, plots, tmp_path):
        """Test comparison plot with file save"""
        data = {
            "Group A": [50, 52, 48, 51, 49],
            "Group B": [60, 62, 58, 61, 59],
        }

        save_path = tmp_path / "comparison.png"

        fig = plots.plot_comparison(data, save_path=str(save_path))

        assert fig is not None
        assert save_path.exists()

        plt.close(fig)

    def test_close_all(self, plots):
        """Test closing all matplotlib figures"""
        # Generate some figures
        plots.plot_distribution([1, 2, 3, 4, 5])
        plots.plot_time_series({"test": [1, 2, 3]})

        # Close all
        EconomicPlots.close_all()

        # Verify the method doesn't error
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
