"""
Geography System for SimCity Simulation

都市の地理情報管理:
- グリッドベースマップ（100×100）
- 建物配置ロジック
- 距離計算（通勤距離等）
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
from loguru import logger


class BuildingType(Enum):
    """建物タイプ"""

    RESIDENTIAL = "residential"  # 住宅
    COMMERCIAL = "commercial"  # 商業施設（企業）
    PUBLIC = "public"  # 公共施設
    EMPTY = "empty"  # 空き地


@dataclass
class Building:
    """
    建物情報

    Attributes:
        building_id: 建物ID
        building_type: 建物タイプ
        location: 座標 (x, y)
        capacity: 収容人数または従業員数
        occupants: 現在の居住者/従業員のIDリスト
        owner_id: 所有者ID（世帯IDまたは企業ID）
        metadata: 追加情報
    """

    building_id: int
    building_type: BuildingType
    location: tuple[int, int]
    capacity: int = 10
    occupants: list[int] | None = None
    owner_id: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.occupants is None:
            self.occupants = []
        if self.metadata is None:
            self.metadata = {}

    def is_vacant(self) -> bool:
        """空きがあるか"""
        return len(self.occupants) < self.capacity

    def add_occupant(self, occupant_id: int) -> bool:
        """居住者/従業員を追加"""
        if self.is_vacant() and occupant_id not in self.occupants:
            self.occupants.append(occupant_id)
            return True
        return False

    def remove_occupant(self, occupant_id: int) -> bool:
        """居住者/従業員を削除"""
        if occupant_id in self.occupants:
            self.occupants.remove(occupant_id)
            return True
        return False


class CityMap:
    """
    都市マップ

    グリッドベースの都市地理情報を管理
    - 100×100グリッド
    - 建物配置
    - 距離計算
    """

    def __init__(self, grid_size: int = 100):
        """
        Args:
            grid_size: グリッドサイズ（デフォルト100×100）
        """
        self.grid_size = grid_size
        self.grid: np.ndarray = np.zeros((grid_size, grid_size), dtype=int)
        self.buildings: dict[int, Building] = {}
        self.next_building_id = 1

        logger.info(f"CityMap initialized: grid_size={grid_size}×{grid_size}")

    def add_building(
        self,
        building_type: BuildingType,
        location: tuple[int, int] | None = None,
        capacity: int = 10,
        owner_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Building | None:
        """
        建物を追加

        Args:
            building_type: 建物タイプ
            location: 座標 (x, y)。Noneの場合は空き地に自動配置
            capacity: 収容人数
            owner_id: 所有者ID
            metadata: 追加情報

        Returns:
            追加された建物、または失敗時はNone
        """
        # 位置が指定されていない場合は空き地を探す
        if location is None:
            location = self._find_empty_location()
            if location is None:
                logger.warning("No empty location available")
                return None

        x, y = location

        # 範囲チェック
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            logger.warning(f"Location out of bounds: {location}")
            return None

        # 既に建物がある場合
        if self.grid[y, x] != 0:
            logger.warning(f"Location already occupied: {location}")
            return None

        # 建物を作成
        building = Building(
            building_id=self.next_building_id,
            building_type=building_type,
            location=location,
            capacity=capacity,
            owner_id=owner_id,
            metadata=metadata or {},
        )

        # グリッドと辞書に追加
        self.grid[y, x] = building.building_id
        self.buildings[building.building_id] = building
        self.next_building_id += 1

        logger.debug(
            f"Building added: id={building.building_id}, "
            f"type={building_type.value}, location={location}"
        )

        return building

    def remove_building(self, building_id: int) -> bool:
        """
        建物を削除

        Args:
            building_id: 建物ID

        Returns:
            削除成功時True
        """
        if building_id not in self.buildings:
            return False

        building = self.buildings[building_id]
        x, y = building.location

        # グリッドから削除
        self.grid[y, x] = 0

        # 辞書から削除
        del self.buildings[building_id]

        logger.debug(f"Building removed: id={building_id}")
        return True

    def get_building(self, building_id: int) -> Building | None:
        """建物情報を取得"""
        return self.buildings.get(building_id)

    def get_building_at(self, location: tuple[int, int]) -> Building | None:
        """指定座標の建物を取得"""
        x, y = location
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return None

        building_id = self.grid[y, x]
        if building_id == 0:
            return None

        return self.buildings.get(building_id)

    def get_buildings_by_type(self, building_type: BuildingType) -> list[Building]:
        """指定タイプの建物一覧を取得"""
        return [b for b in self.buildings.values() if b.building_type == building_type]

    def _find_empty_location(self) -> tuple[int, int] | None:
        """空き地を探す（ランダムサーチ）"""
        empty_locations = np.argwhere(self.grid == 0)
        if len(empty_locations) == 0:
            return None

        # ランダムに選択
        idx = np.random.randint(len(empty_locations))
        y, x = empty_locations[idx]
        return (int(x), int(y))

    @staticmethod
    def calculate_distance(loc1: tuple[int, int], loc2: tuple[int, int]) -> float:
        """
        2点間の距離を計算（ユークリッド距離）

        Args:
            loc1: 座標1 (x, y)
            loc2: 座標2 (x, y)

        Returns:
            距離
        """
        x1, y1 = loc1
        x2, y2 = loc2
        return float(np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

    @staticmethod
    def calculate_manhattan_distance(
        loc1: tuple[int, int], loc2: tuple[int, int]
    ) -> int:
        """
        2点間のマンハッタン距離を計算

        Args:
            loc1: 座標1 (x, y)
            loc2: 座標2 (x, y)

        Returns:
            マンハッタン距離
        """
        x1, y1 = loc1
        x2, y2 = loc2
        return abs(x2 - x1) + abs(y2 - y1)

    def get_statistics(self) -> dict[str, Any]:
        """都市統計を取得"""
        total_buildings = len(self.buildings)
        buildings_by_type = {
            building_type.value: len(self.get_buildings_by_type(building_type))
            for building_type in BuildingType
            if building_type != BuildingType.EMPTY
        }

        total_capacity = sum(b.capacity for b in self.buildings.values())
        total_occupants = sum(len(b.occupants) for b in self.buildings.values())

        return {
            "grid_size": self.grid_size,
            "total_buildings": total_buildings,
            "buildings_by_type": buildings_by_type,
            "total_capacity": total_capacity,
            "total_occupants": total_occupants,
            "occupancy_rate": (
                total_occupants / total_capacity if total_capacity > 0 else 0.0
            ),
            "empty_cells": int(np.sum(self.grid == 0)),
        }

    def get_nearby_buildings(
        self,
        location: tuple[int, int],
        building_type: BuildingType | None = None,
        max_distance: float = 10.0,
    ) -> list[tuple[Building, float]]:
        """
        指定座標の近くの建物を取得

        Args:
            location: 基準座標
            building_type: 建物タイプフィルタ（Noneの場合は全タイプ）
            max_distance: 最大距離

        Returns:
            (建物, 距離)のタプルのリスト（距離順）
        """
        nearby = []

        buildings = (
            self.get_buildings_by_type(building_type)
            if building_type
            else self.buildings.values()
        )

        for building in buildings:
            distance = self.calculate_distance(location, building.location)
            if distance <= max_distance:
                nearby.append((building, distance))

        # 距離順にソート
        nearby.sort(key=lambda x: x[1])
        return nearby
