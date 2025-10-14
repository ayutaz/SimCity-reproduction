"""
Map Visualization for SimCity Simulation

都市マップの可視化:
- グリッドベースマップの描画
- 建物タイプ別の色分け
- 占有率の可視化
- Plotly/Matplotlib対応
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from matplotlib.colors import ListedColormap

from src.environment.geography import BuildingType, CityMap


class MapGenerator:
    """
    都市マップ可視化クラス

    CityMapの状態を可視化し、画像として出力
    - 建物タイプ別の色分け
    - 占有率のヒートマップ
    - 統計情報の表示
    """

    # 建物タイプごとの色定義
    COLOR_MAP = {
        BuildingType.EMPTY: "#FFFFFF",  # 白（空き地）
        BuildingType.RESIDENTIAL: "#87CEEB",  # スカイブルー（住宅）
        BuildingType.COMMERCIAL: "#FFD700",  # ゴールド（商業）
        BuildingType.PUBLIC: "#90EE90",  # ライトグリーン（公共）
    }

    def __init__(self):
        """MapGeneratorの初期化"""
        logger.info("MapGenerator initialized")

    def generate_building_type_map(
        self, city_map: CityMap, figsize: tuple[int, int] = (10, 10), save_path: str | None = None
    ) -> plt.Figure:
        """
        建物タイプマップを生成

        Args:
            city_map: CityMapインスタンス
            figsize: 図のサイズ
            save_path: 保存先パス（Noneの場合は保存しない）

        Returns:
            matplotlib Figure
        """
        # グリッドを建物タイプに変換
        type_grid = np.zeros((city_map.grid_size, city_map.grid_size))

        for building in city_map.buildings.values():
            x, y = building.location
            # EMPTY=0, RESIDENTIAL=1, COMMERCIAL=2, PUBLIC=3
            if building.building_type == BuildingType.RESIDENTIAL:
                type_grid[y, x] = 1
            elif building.building_type == BuildingType.COMMERCIAL:
                type_grid[y, x] = 2
            elif building.building_type == BuildingType.PUBLIC:
                type_grid[y, x] = 3

        # カラーマップを作成
        colors = [
            self.COLOR_MAP[BuildingType.EMPTY],
            self.COLOR_MAP[BuildingType.RESIDENTIAL],
            self.COLOR_MAP[BuildingType.COMMERCIAL],
            self.COLOR_MAP[BuildingType.PUBLIC],
        ]
        cmap = ListedColormap(colors)

        # プロット
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(type_grid, cmap=cmap, vmin=0, vmax=3, origin="lower")

        # カラーバー
        cbar = plt.colorbar(im, ax=ax, ticks=[0, 1, 2, 3])
        cbar.set_ticklabels(["Empty", "Residential", "Commercial", "Public"])

        # タイトルと軸ラベル
        ax.set_title("City Map - Building Types", fontsize=14, fontweight="bold")
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")

        # グリッド線
        ax.grid(False)

        # 統計情報をテキストで追加
        stats = city_map.get_statistics()
        stats_text = (
            f"Total Buildings: {stats['total_buildings']}\n"
            f"Residential: {stats['buildings_by_type'].get('residential', 0)}\n"
            f"Commercial: {stats['buildings_by_type'].get('commercial', 0)}\n"
            f"Public: {stats['buildings_by_type'].get('public', 0)}\n"
            f"Occupancy: {stats['occupancy_rate']:.1%}"
        )
        ax.text(
            1.15,
            0.5,
            stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="center",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Building type map saved to {save_path}")

        return fig

    def generate_occupancy_heatmap(
        self, city_map: CityMap, figsize: tuple[int, int] = (10, 10), save_path: str | None = None
    ) -> plt.Figure:
        """
        占有率ヒートマップを生成

        Args:
            city_map: CityMapインスタンス
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figure
        """
        # 占有率グリッド（0.0〜1.0）
        occupancy_grid = np.zeros((city_map.grid_size, city_map.grid_size))

        for building in city_map.buildings.values():
            x, y = building.location
            if building.capacity > 0:
                occupancy_rate = len(building.occupants) / building.capacity
                occupancy_grid[y, x] = occupancy_rate

        # プロット
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(occupancy_grid, cmap="YlOrRd", vmin=0, vmax=1, origin="lower")

        # カラーバー
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Occupancy Rate", rotation=270, labelpad=20)

        # タイトルと軸ラベル
        ax.set_title("City Map - Occupancy Heatmap", fontsize=14, fontweight="bold")
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Occupancy heatmap saved to {save_path}")

        return fig

    def generate_density_map(
        self,
        city_map: CityMap,
        building_type: BuildingType | None = None,
        radius: int = 5,
        figsize: tuple[int, int] = (10, 10),
        save_path: str | None = None,
    ) -> plt.Figure:
        """
        建物密度マップを生成

        Args:
            city_map: CityMapインスタンス
            building_type: 特定の建物タイプでフィルタ（Noneの場合は全タイプ）
            radius: 密度計算の半径
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figure
        """
        # 密度グリッド
        density_grid = np.zeros((city_map.grid_size, city_map.grid_size))

        # 対象建物のリスト
        if building_type:
            buildings = city_map.get_buildings_by_type(building_type)
        else:
            buildings = list(city_map.buildings.values())

        # 各グリッドセルについて周囲の建物数を計算
        for y in range(city_map.grid_size):
            for x in range(city_map.grid_size):
                count = 0
                for building in buildings:
                    bx, by = building.location
                    if abs(bx - x) <= radius and abs(by - y) <= radius:
                        count += 1
                density_grid[y, x] = count

        # プロット
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(density_grid, cmap="viridis", origin="lower")

        # カラーバー
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Building Count", rotation=270, labelpad=20)

        # タイトル
        title = "City Map - Building Density"
        if building_type:
            title += f" ({building_type.value.capitalize()})"
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Density map saved to {save_path}")

        return fig

    def generate_combined_view(
        self, city_map: CityMap, figsize: tuple[int, int] = (15, 5), save_path: str | None = None
    ) -> plt.Figure:
        """
        複合ビューを生成（タイプ + 占有率 + 密度）

        Args:
            city_map: CityMapインスタンス
            figsize: 図のサイズ
            save_path: 保存先パス

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(1, 3, figsize=figsize)

        # 1. 建物タイプマップ
        type_grid = np.zeros((city_map.grid_size, city_map.grid_size))
        for building in city_map.buildings.values():
            x, y = building.location
            if building.building_type == BuildingType.RESIDENTIAL:
                type_grid[y, x] = 1
            elif building.building_type == BuildingType.COMMERCIAL:
                type_grid[y, x] = 2
            elif building.building_type == BuildingType.PUBLIC:
                type_grid[y, x] = 3

        colors = [
            self.COLOR_MAP[BuildingType.EMPTY],
            self.COLOR_MAP[BuildingType.RESIDENTIAL],
            self.COLOR_MAP[BuildingType.COMMERCIAL],
            self.COLOR_MAP[BuildingType.PUBLIC],
        ]
        cmap = ListedColormap(colors)
        axes[0].imshow(type_grid, cmap=cmap, vmin=0, vmax=3, origin="lower")
        axes[0].set_title("Building Types")
        axes[0].set_xlabel("X")
        axes[0].set_ylabel("Y")

        # 2. 占有率ヒートマップ
        occupancy_grid = np.zeros((city_map.grid_size, city_map.grid_size))
        for building in city_map.buildings.values():
            x, y = building.location
            if building.capacity > 0:
                occupancy_grid[y, x] = len(building.occupants) / building.capacity

        im2 = axes[1].imshow(occupancy_grid, cmap="YlOrRd", vmin=0, vmax=1, origin="lower")
        axes[1].set_title("Occupancy Rate")
        axes[1].set_xlabel("X")
        axes[1].set_ylabel("Y")
        plt.colorbar(im2, ax=axes[1])

        # 3. 密度マップ
        density_grid = np.zeros((city_map.grid_size, city_map.grid_size))
        buildings = list(city_map.buildings.values())
        radius = 5

        for y in range(city_map.grid_size):
            for x in range(city_map.grid_size):
                count = sum(
                    1
                    for b in buildings
                    if abs(b.location[0] - x) <= radius and abs(b.location[1] - y) <= radius
                )
                density_grid[y, x] = count

        im3 = axes[2].imshow(density_grid, cmap="viridis", origin="lower")
        axes[2].set_title("Building Density")
        axes[2].set_xlabel("X")
        axes[2].set_ylabel("Y")
        plt.colorbar(im3, ax=axes[2])

        fig.suptitle("City Map - Combined View", fontsize=16, fontweight="bold", y=1.02)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Combined view saved to {save_path}")

        return fig

    def get_statistics_summary(self, city_map: CityMap) -> dict[str, Any]:
        """
        統計サマリーを取得

        Args:
            city_map: CityMapインスタンス

        Returns:
            統計情報の辞書
        """
        stats = city_map.get_statistics()

        # 追加の統計計算
        residential_buildings = city_map.get_buildings_by_type(BuildingType.RESIDENTIAL)
        commercial_buildings = city_map.get_buildings_by_type(BuildingType.COMMERCIAL)
        public_buildings = city_map.get_buildings_by_type(BuildingType.PUBLIC)

        residential_occupancy = (
            sum(len(b.occupants) for b in residential_buildings)
            / sum(b.capacity for b in residential_buildings)
            if residential_buildings
            else 0.0
        )

        commercial_occupancy = (
            sum(len(b.occupants) for b in commercial_buildings)
            / sum(b.capacity for b in commercial_buildings)
            if commercial_buildings
            else 0.0
        )

        return {
            **stats,
            "residential_occupancy_rate": residential_occupancy,
            "commercial_occupancy_rate": commercial_occupancy,
            "public_building_count": len(public_buildings),
        }

    @staticmethod
    def close_all():
        """全てのMatplotlib図を閉じる"""
        plt.close("all")
        logger.debug("All matplotlib figures closed")
