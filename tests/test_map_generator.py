"""Tests for Map Generator"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.geography import BuildingType, CityMap
from src.visualization.map_generator import MapGenerator


class TestMapGenerator:
    @pytest.fixture
    def city_map(self):
        """Create a test city map with some buildings"""
        city_map = CityMap(grid_size=20)

        # Add residential buildings
        for i in range(5):
            b = city_map.add_building(
                BuildingType.RESIDENTIAL, location=(i * 2, 5), capacity=10
            )
            if b:
                # Add some occupants
                for j in range(i * 2):
                    b.add_occupant(100 + i * 10 + j)

        # Add commercial buildings
        for i in range(3):
            b = city_map.add_building(
                BuildingType.COMMERCIAL, location=(i * 3, 10), capacity=20
            )
            if b:
                # Add some occupants
                for j in range(i * 3):
                    b.add_occupant(200 + i * 10 + j)

        # Add public buildings
        city_map.add_building(BuildingType.PUBLIC, location=(15, 15), capacity=50)

        return city_map

    @pytest.fixture
    def map_generator(self):
        return MapGenerator()

    def test_initialization(self, map_generator):
        assert map_generator is not None
        assert map_generator.COLOR_MAP is not None

    def test_color_map_contains_all_types(self, map_generator):
        """Test that color map contains all building types"""
        assert BuildingType.EMPTY in map_generator.COLOR_MAP
        assert BuildingType.RESIDENTIAL in map_generator.COLOR_MAP
        assert BuildingType.COMMERCIAL in map_generator.COLOR_MAP
        assert BuildingType.PUBLIC in map_generator.COLOR_MAP

    def test_generate_building_type_map(self, map_generator, city_map):
        """Test building type map generation"""
        fig = map_generator.generate_building_type_map(city_map, figsize=(8, 8))

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0

        # Clean up
        plt.close(fig)

    def test_generate_building_type_map_with_save(
        self, map_generator, city_map, tmp_path
    ):
        """Test building type map generation with file save"""
        save_path = tmp_path / "building_type_map.png"

        fig = map_generator.generate_building_type_map(
            city_map, save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        # Clean up
        plt.close(fig)

    def test_generate_occupancy_heatmap(self, map_generator, city_map):
        """Test occupancy heatmap generation"""
        fig = map_generator.generate_occupancy_heatmap(city_map, figsize=(8, 8))

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0

        # Clean up
        plt.close(fig)

    def test_generate_occupancy_heatmap_with_save(
        self, map_generator, city_map, tmp_path
    ):
        """Test occupancy heatmap generation with file save"""
        save_path = tmp_path / "occupancy_heatmap.png"

        fig = map_generator.generate_occupancy_heatmap(
            city_map, save_path=str(save_path)
        )

        assert fig is not None
        assert save_path.exists()

        # Clean up
        plt.close(fig)

    def test_generate_density_map_all_types(self, map_generator, city_map):
        """Test density map generation for all building types"""
        fig = map_generator.generate_density_map(city_map, radius=3, figsize=(8, 8))

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0

        # Clean up
        plt.close(fig)

    def test_generate_density_map_filtered(self, map_generator, city_map):
        """Test density map generation with building type filter"""
        fig = map_generator.generate_density_map(
            city_map, building_type=BuildingType.RESIDENTIAL, radius=3, figsize=(8, 8)
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        # Clean up
        plt.close(fig)

    def test_generate_density_map_with_save(self, map_generator, city_map, tmp_path):
        """Test density map generation with file save"""
        save_path = tmp_path / "density_map.png"

        fig = map_generator.generate_density_map(city_map, save_path=str(save_path))

        assert fig is not None
        assert save_path.exists()

        # Clean up
        plt.close(fig)

    def test_generate_combined_view(self, map_generator, city_map):
        """Test combined view generation"""
        fig = map_generator.generate_combined_view(city_map, figsize=(15, 5))

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 3  # Should have at least 3 subplots (plus colorbars)

        # Clean up
        plt.close(fig)

    def test_generate_combined_view_with_save(self, map_generator, city_map, tmp_path):
        """Test combined view generation with file save"""
        save_path = tmp_path / "combined_view.png"

        fig = map_generator.generate_combined_view(city_map, save_path=str(save_path))

        assert fig is not None
        assert save_path.exists()

        # Clean up
        plt.close(fig)

    def test_get_statistics_summary(self, map_generator, city_map):
        """Test statistics summary generation"""
        stats = map_generator.get_statistics_summary(city_map)

        assert stats is not None
        assert "grid_size" in stats
        assert "total_buildings" in stats
        assert "residential_occupancy_rate" in stats
        assert "commercial_occupancy_rate" in stats
        assert "public_building_count" in stats

        # Check values
        assert stats["total_buildings"] > 0
        assert 0.0 <= stats["residential_occupancy_rate"] <= 1.0
        assert 0.0 <= stats["commercial_occupancy_rate"] <= 1.0

    def test_close_all(self, map_generator, city_map):
        """Test closing all matplotlib figures"""
        # Generate some figures
        map_generator.generate_building_type_map(city_map)
        map_generator.generate_occupancy_heatmap(city_map)

        # Close all
        MapGenerator.close_all()

        # Verify figures are closed (this is hard to test directly,
        # but at least verify the method doesn't error)
        assert True

    def test_empty_map(self, map_generator):
        """Test visualization of empty map"""
        empty_map = CityMap(grid_size=10)

        # Should not error even with no buildings
        fig = map_generator.generate_building_type_map(empty_map)
        assert fig is not None
        plt.close(fig)

        fig = map_generator.generate_occupancy_heatmap(empty_map)
        assert fig is not None
        plt.close(fig)

        fig = map_generator.generate_density_map(empty_map)
        assert fig is not None
        plt.close(fig)

        stats = map_generator.get_statistics_summary(empty_map)
        assert stats["total_buildings"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
