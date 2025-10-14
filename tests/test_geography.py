"""Tests for Geography System"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.geography import Building, BuildingType, CityMap


class TestBuilding:
    def test_building_creation(self):
        building = Building(
            building_id=1,
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
            capacity=5,
        )

        assert building.building_id == 1
        assert building.building_type == BuildingType.RESIDENTIAL
        assert building.location == (10, 20)
        assert building.capacity == 5
        assert building.occupants == []

    def test_is_vacant(self):
        building = Building(
            building_id=1,
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
            capacity=3,
        )

        assert building.is_vacant() is True

        building.occupants = [101, 102]
        assert building.is_vacant() is True

        building.occupants = [101, 102, 103]
        assert building.is_vacant() is False

    def test_add_occupant(self):
        building = Building(
            building_id=1,
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
            capacity=2,
        )

        # Add first occupant
        result = building.add_occupant(101)
        assert result is True
        assert 101 in building.occupants

        # Add second occupant
        result = building.add_occupant(102)
        assert result is True
        assert 102 in building.occupants

        # Try to add third occupant (should fail - at capacity)
        result = building.add_occupant(103)
        assert result is False
        assert len(building.occupants) == 2

        # Try to add duplicate occupant
        result = building.add_occupant(101)
        assert result is False
        assert len(building.occupants) == 2

    def test_remove_occupant(self):
        building = Building(
            building_id=1,
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
            capacity=5,
        )

        building.occupants = [101, 102, 103]

        # Remove existing occupant
        result = building.remove_occupant(102)
        assert result is True
        assert 102 not in building.occupants
        assert len(building.occupants) == 2

        # Try to remove non-existent occupant
        result = building.remove_occupant(999)
        assert result is False
        assert len(building.occupants) == 2


class TestCityMap:
    @pytest.fixture
    def city_map(self):
        return CityMap(grid_size=50)

    def test_initialization(self, city_map):
        assert city_map.grid_size == 50
        assert city_map.grid.shape == (50, 50)
        assert len(city_map.buildings) == 0
        assert city_map.next_building_id == 1

    def test_add_building_with_location(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
            capacity=5,
        )

        assert building is not None
        assert building.building_id == 1
        assert building.building_type == BuildingType.RESIDENTIAL
        assert building.location == (10, 20)
        assert building.capacity == 5
        assert city_map.grid[20, 10] == 1

    def test_add_building_auto_location(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.COMMERCIAL,
            capacity=10,
        )

        assert building is not None
        assert building.building_id == 1
        assert building.building_type == BuildingType.COMMERCIAL
        x, y = building.location
        assert 0 <= x < 50
        assert 0 <= y < 50

    def test_add_building_out_of_bounds(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(100, 100),
        )

        assert building is None

    def test_add_building_occupied_location(self, city_map):
        # Add first building
        building1 = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
        )
        assert building1 is not None

        # Try to add second building at same location
        building2 = city_map.add_building(
            building_type=BuildingType.COMMERCIAL,
            location=(10, 20),
        )
        assert building2 is None

    def test_remove_building(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
        )

        assert building.building_id in city_map.buildings
        assert city_map.grid[20, 10] == building.building_id

        result = city_map.remove_building(building.building_id)

        assert result is True
        assert building.building_id not in city_map.buildings
        assert city_map.grid[20, 10] == 0

    def test_remove_nonexistent_building(self, city_map):
        result = city_map.remove_building(999)
        assert result is False

    def test_get_building(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
        )

        retrieved = city_map.get_building(building.building_id)
        assert retrieved is building

        retrieved = city_map.get_building(999)
        assert retrieved is None

    def test_get_building_at(self, city_map):
        building = city_map.add_building(
            building_type=BuildingType.RESIDENTIAL,
            location=(10, 20),
        )

        retrieved = city_map.get_building_at((10, 20))
        assert retrieved is building

        retrieved = city_map.get_building_at((15, 25))
        assert retrieved is None

        # Test out of bounds
        retrieved = city_map.get_building_at((100, 100))
        assert retrieved is None

    def test_get_buildings_by_type(self, city_map):
        city_map.add_building(BuildingType.RESIDENTIAL, location=(10, 10))
        city_map.add_building(BuildingType.RESIDENTIAL, location=(20, 20))
        city_map.add_building(BuildingType.COMMERCIAL, location=(30, 30))
        city_map.add_building(BuildingType.PUBLIC, location=(40, 40))

        residential = city_map.get_buildings_by_type(BuildingType.RESIDENTIAL)
        assert len(residential) == 2

        commercial = city_map.get_buildings_by_type(BuildingType.COMMERCIAL)
        assert len(commercial) == 1

        public = city_map.get_buildings_by_type(BuildingType.PUBLIC)
        assert len(public) == 1

        empty = city_map.get_buildings_by_type(BuildingType.EMPTY)
        assert len(empty) == 0

    def test_calculate_distance(self):
        # Test Euclidean distance
        dist = CityMap.calculate_distance((0, 0), (3, 4))
        assert dist == 5.0

        dist = CityMap.calculate_distance((10, 10), (10, 10))
        assert dist == 0.0

    def test_calculate_manhattan_distance(self):
        # Test Manhattan distance
        dist = CityMap.calculate_manhattan_distance((0, 0), (3, 4))
        assert dist == 7

        dist = CityMap.calculate_manhattan_distance((10, 10), (10, 10))
        assert dist == 0

        dist = CityMap.calculate_manhattan_distance((5, 8), (2, 3))
        assert dist == 8  # |5-2| + |8-3| = 3 + 5 = 8

    def test_get_statistics(self, city_map):
        # Add buildings with occupants
        b1 = city_map.add_building(
            BuildingType.RESIDENTIAL, location=(10, 10), capacity=5
        )
        b1.add_occupant(101)
        b1.add_occupant(102)

        b2 = city_map.add_building(
            BuildingType.RESIDENTIAL, location=(20, 20), capacity=5
        )
        b2.add_occupant(201)

        b3 = city_map.add_building(
            BuildingType.COMMERCIAL, location=(30, 30), capacity=10
        )
        b3.add_occupant(1)

        stats = city_map.get_statistics()

        assert stats["grid_size"] == 50
        assert stats["total_buildings"] == 3
        assert stats["buildings_by_type"]["residential"] == 2
        assert stats["buildings_by_type"]["commercial"] == 1
        assert stats["buildings_by_type"]["public"] == 0
        assert stats["total_capacity"] == 20  # 5 + 5 + 10
        assert stats["total_occupants"] == 4  # 2 + 1 + 1
        assert stats["occupancy_rate"] == 0.2  # 4 / 20
        assert stats["empty_cells"] == 50 * 50 - 3

    def test_get_nearby_buildings(self, city_map):
        # Add buildings at various distances
        b1 = city_map.add_building(BuildingType.RESIDENTIAL, location=(10, 10))
        b2 = city_map.add_building(BuildingType.RESIDENTIAL, location=(12, 12))
        city_map.add_building(BuildingType.COMMERCIAL, location=(20, 20))
        city_map.add_building(BuildingType.RESIDENTIAL, location=(30, 30))

        # Find all buildings within distance 5.0 from (10, 10)
        nearby = city_map.get_nearby_buildings((10, 10), max_distance=5.0)

        # b1 is at (10, 10) - distance 0
        # b2 is at (12, 12) - distance sqrt(8) ≈ 2.83
        # b3 is at (20, 20) - distance sqrt(200) ≈ 14.14
        # b4 is at (30, 30) - distance sqrt(800) ≈ 28.28

        assert len(nearby) == 2
        assert nearby[0][0] == b1  # Distance 0
        assert nearby[1][0] == b2  # Distance ~2.83

    def test_get_nearby_buildings_with_type_filter(self, city_map):
        # Add buildings
        city_map.add_building(BuildingType.RESIDENTIAL, location=(10, 10))
        b2 = city_map.add_building(BuildingType.COMMERCIAL, location=(12, 12))
        city_map.add_building(BuildingType.RESIDENTIAL, location=(14, 14))

        # Find only residential buildings nearby
        nearby = city_map.get_nearby_buildings(
            (10, 10), building_type=BuildingType.RESIDENTIAL, max_distance=10.0
        )

        assert len(nearby) == 2
        assert all(b[0].building_type == BuildingType.RESIDENTIAL for b in nearby)

        # Find only commercial buildings nearby
        nearby = city_map.get_nearby_buildings(
            (10, 10), building_type=BuildingType.COMMERCIAL, max_distance=10.0
        )

        assert len(nearby) == 1
        assert nearby[0][0] == b2

    def test_nearby_buildings_sorted_by_distance(self, city_map):
        # Add buildings at known distances
        city_map.add_building(BuildingType.RESIDENTIAL, location=(15, 10))  # Distance 5
        city_map.add_building(BuildingType.RESIDENTIAL, location=(13, 10))  # Distance 3
        city_map.add_building(BuildingType.RESIDENTIAL, location=(10, 10))  # Distance 0

        nearby = city_map.get_nearby_buildings((10, 10), max_distance=10.0)

        # Should be sorted by distance
        assert len(nearby) == 3
        assert nearby[0][1] == 0.0  # b3
        assert nearby[1][1] == 3.0  # b2
        assert nearby[2][1] == 5.0  # b1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
