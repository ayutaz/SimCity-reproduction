"""Tests for Dashboard"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visualization.dashboard import SimCityDashboard


class TestDashboard:
    @pytest.fixture
    def dashboard(self):
        return SimCityDashboard()

    def test_initialization(self, dashboard):
        """Test dashboard initialization"""
        assert dashboard is not None
        assert dashboard.map_generator is not None
        assert dashboard.plots is not None

    def test_create_demo_city_map(self, dashboard):
        """Test demo city map creation"""
        city_map = dashboard._create_demo_city_map(grid_size=20)

        assert city_map is not None
        assert city_map.grid_size == 20
        assert len(city_map.buildings) > 0

        # Check that different building types exist
        stats = city_map.get_statistics()
        assert stats["total_buildings"] > 0

    def test_generate_demo_time_series(self, dashboard):
        """Test demo time series generation"""
        time_series = dashboard._generate_demo_time_series(steps=50)

        assert "GDP" in time_series
        assert "Unemployment Rate" in time_series
        assert "Inflation Rate" in time_series
        assert "Interest Rate" in time_series
        assert "Wages" in time_series

        # Check data length
        for _key, values in time_series.items():
            assert len(values) == 50

        # Check data ranges
        assert all(0.01 <= v <= 0.15 for v in time_series["Unemployment Rate"])
        assert all(-0.02 <= v <= 0.10 for v in time_series["Inflation Rate"])
        assert all(0.0 <= v <= 0.10 for v in time_series["Interest Rate"])

    def test_create_multiple_city_maps(self, dashboard):
        """Test creating multiple city maps with different sizes"""
        sizes = [20, 30, 50]

        for size in sizes:
            city_map = dashboard._create_demo_city_map(grid_size=size)
            assert city_map.grid_size == size
            assert len(city_map.buildings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
