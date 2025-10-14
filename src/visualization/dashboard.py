"""
Streamlit Dashboard for SimCity Simulation

Streamlitダッシュボード:
- シミュレーション結果の可視化
- 都市マップ表示
- 経済指標グラフ
- インタラクティブコントロール
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.environment.geography import BuildingType, CityMap
from src.visualization.map_generator import MapGenerator
from src.visualization.plots import EconomicPlots


class SimCityDashboard:
    """
    SimCityシミュレーションダッシュボード

    Streamlitを使用したインタラクティブな可視化
    """

    def __init__(self):
        """ダッシュボードの初期化"""
        self.map_generator = MapGenerator()
        self.plots = EconomicPlots()

    def run(self):
        """ダッシュボードを実行"""
        st.set_page_config(
            page_title="SimCity Economic Simulation",
            page_icon=":cityscape:",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("SimCity: Multi-Agent Urban Development Simulation")
        st.markdown(
            """
            LLMを活用したマクロ経済シミュレーションフレームワーク
            """
        )

        # サイドバー
        self._render_sidebar()

        # メインコンテンツ
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "City Map", "Economic Indicators", "Analysis"]
        )

        with tab1:
            self._render_overview()

        with tab2:
            self._render_city_map()

        with tab3:
            self._render_economic_indicators()

        with tab4:
            self._render_analysis()

    def _render_sidebar(self):
        """サイドバーを描画"""
        st.sidebar.header("Simulation Controls")

        # シミュレーション設定
        st.sidebar.subheader("Settings")
        grid_size = st.sidebar.slider("Grid Size", 20, 100, 50, 10)
        num_households = st.sidebar.slider("Households", 10, 200, 50, 10)
        num_firms = st.sidebar.slider("Firms", 5, 50, 20, 5)

        # データソース選択
        st.sidebar.subheader("Data Source")
        data_source = st.sidebar.radio(
            "Select data source:",
            ["Demo Data", "Upload Results", "Live Simulation"],
        )

        if data_source == "Upload Results":
            st.sidebar.file_uploader("Upload simulation results (CSV)", type=["csv"])

        # セッション状態に保存
        if "settings" not in st.session_state:
            st.session_state.settings = {}

        st.session_state.settings.update(
            {
                "grid_size": grid_size,
                "num_households": num_households,
                "num_firms": num_firms,
                "data_source": data_source,
            }
        )

    def _render_overview(self):
        """概要タブを描画"""
        st.header("Simulation Overview")

        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("GDP", "$125.5M", "+2.3%")

        with col2:
            st.metric("Unemployment", "5.2%", "-0.5%")

        with col3:
            st.metric("Inflation", "2.1%", "+0.3%")

        with col4:
            st.metric("Population", "10,250", "+150")

        st.divider()

        # 統計情報
        st.subheader("System Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Agent Statistics**")
            agent_stats = pd.DataFrame(
                {
                    "Agent Type": ["Households", "Firms", "Government", "Central Bank"],
                    "Count": [200, 44, 1, 1],
                    "Active": [198, 42, 1, 1],
                }
            )
            st.dataframe(agent_stats, use_container_width=True)

        with col2:
            st.markdown("**Market Statistics**")
            market_stats = pd.DataFrame(
                {
                    "Market": ["Labor", "Goods", "Financial"],
                    "Transactions": [1250, 3420, 580],
                    "Volume": ["$2.5M", "$15.3M", "$8.7M"],
                }
            )
            st.dataframe(market_stats, use_container_width=True)

        st.divider()

        # プロジェクト情報
        st.subheader("About This Simulation")
        st.markdown(
            """
            このプロジェクトは論文 "SimCity: Multi-Agent Urban Development Simulation with Rich Interactions" の実装です。

            **主な特徴:**
            - 4種類のLLM駆動エージェント（家計、企業、政府、中央銀行）
            - 3つの市場（労働市場、財市場、金融市場）
            - マクロ経済現象の再現（フィリップス曲線、オークンの法則、ベバリッジ曲線等）
            """
        )

    def _render_city_map(self):
        """都市マップタブを描画"""
        st.header("City Map Visualization")

        # マップタイプ選択
        map_type = st.selectbox(
            "Select map type:",
            ["Building Types", "Occupancy Heatmap", "Density Map", "Combined View"],
        )

        # デモ用のCityMapを作成
        grid_size = st.session_state.settings.get("grid_size", 50)
        city_map = self._create_demo_city_map(grid_size)

        # 統計情報表示
        stats = city_map.get_statistics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Buildings", stats["total_buildings"])
        with col2:
            st.metric("Residential", stats["buildings_by_type"].get("residential", 0))
        with col3:
            st.metric("Commercial", stats["buildings_by_type"].get("commercial", 0))
        with col4:
            st.metric("Occupancy Rate", f"{stats['occupancy_rate'] * 100:.1f}%")

        st.divider()

        # マップ表示
        if map_type == "Building Types":
            fig = self.map_generator.generate_building_type_map(
                city_map, figsize=(10, 8)
            )
            st.pyplot(fig)

        elif map_type == "Occupancy Heatmap":
            fig = self.map_generator.generate_occupancy_heatmap(
                city_map, figsize=(10, 8)
            )
            st.pyplot(fig)

        elif map_type == "Density Map":
            building_type = st.selectbox(
                "Filter by building type:",
                ["All", "Residential", "Commercial", "Public"],
            )

            if building_type == "All":
                fig = self.map_generator.generate_density_map(
                    city_map, radius=5, figsize=(10, 8)
                )
            else:
                bt = BuildingType[building_type.upper()]
                fig = self.map_generator.generate_density_map(
                    city_map, building_type=bt, radius=5, figsize=(10, 8)
                )
            st.pyplot(fig)

        elif map_type == "Combined View":
            fig = self.map_generator.generate_combined_view(city_map, figsize=(15, 5))
            st.pyplot(fig)

    def _render_economic_indicators(self):
        """経済指標タブを描画"""
        st.header("Economic Indicators")

        # 時系列データ生成（デモ用）
        steps = 50
        time_series = self._generate_demo_time_series(steps)

        # 指標選択
        indicators = st.multiselect(
            "Select indicators to display:",
            ["GDP", "Unemployment Rate", "Inflation Rate", "Interest Rate", "Wages"],
            default=["GDP", "Unemployment Rate", "Inflation Rate"],
        )

        if indicators:
            # 選択された指標のみ表示
            selected_data = {k: v for k, v in time_series.items() if k in indicators}

            fig = self.plots.plot_time_series(
                selected_data, title="Economic Indicators Over Time", figsize=(12, 6)
            )
            st.pyplot(fig)

        st.divider()

        # データテーブル
        st.subheader("Data Table")
        df = pd.DataFrame(time_series)
        df.insert(0, "Step", range(len(df)))
        st.dataframe(df, use_container_width=True)

        # ダウンロードボタン
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "economic_indicators.csv",
            "text/csv",
            key="download-csv",
        )

    def _render_analysis(self):
        """分析タブを描画"""
        st.header("Economic Phenomena Analysis")

        # 分析タイプ選択
        analysis_type = st.selectbox(
            "Select analysis:",
            [
                "Phillips Curve",
                "Okun's Law",
                "Beveridge Curve",
                "Engel's Law",
                "Price Elasticity",
                "Income Distribution",
            ],
        )

        st.divider()

        if analysis_type == "Phillips Curve":
            self._render_phillips_curve()

        elif analysis_type == "Okun's Law":
            self._render_okun_law()

        elif analysis_type == "Beveridge Curve":
            self._render_beveridge_curve()

        elif analysis_type == "Engel's Law":
            self._render_engel_law()

        elif analysis_type == "Price Elasticity":
            self._render_price_elasticity()

        elif analysis_type == "Income Distribution":
            self._render_income_distribution()

    def _render_phillips_curve(self):
        """フィリップス曲線を描画"""
        st.subheader("Phillips Curve Analysis")
        st.markdown(
            """
            失業率とインフレ率の関係を示す曲線。
            理論的には負の相関（失業率が低いとインフレ率が高い）を示すことが期待される。
            """
        )

        # デモデータ生成
        unemployment = np.linspace(0.03, 0.10, 30)
        inflation = 0.05 - 0.3 * unemployment + np.random.randn(30) * 0.005

        fig, stats = self.plots.plot_phillips_curve(
            unemployment.tolist(), inflation.tolist(), figsize=(8, 6)
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Correlation", f"{stats['correlation']:.3f}")
            st.metric("R-squared", f"{stats['r_squared']:.3f}")
            st.metric("Slope", f"{stats['slope']:.3f}")
            st.metric("P-value", f"{stats['p_value']:.4f}")

            if stats["correlation"] < 0:
                st.success("Negative correlation detected (expected)")
            else:
                st.warning("Positive correlation (unexpected)")

    def _render_okun_law(self):
        """オークンの法則を描画"""
        st.subheader("Okun's Law Analysis")
        st.markdown(
            """
            失業率の変化とGDP成長率の関係を示す法則。
            理論的には負の相関（失業率が上がるとGDPが下がる）を示すことが期待される。
            """
        )

        # デモデータ生成
        unemployment_change = np.linspace(-0.02, 0.03, 30)
        gdp_growth = 0.03 - 2.0 * unemployment_change + np.random.randn(30) * 0.01

        fig, stats = self.plots.plot_okun_law(
            unemployment_change.tolist(), gdp_growth.tolist(), figsize=(8, 6)
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Correlation", f"{stats['correlation']:.3f}")
            st.metric("R-squared", f"{stats['r_squared']:.3f}")
            st.metric("Slope (Okun Coef.)", f"{stats['slope']:.3f}")

            if stats["correlation"] < 0:
                st.success("Negative correlation detected (expected)")

    def _render_beveridge_curve(self):
        """ベバリッジ曲線を描画"""
        st.subheader("Beveridge Curve Analysis")
        st.markdown(
            """
            失業率と求人率の関係を示す曲線。
            理論的には負の相関（失業率が高いと求人率が低い）を示すことが期待される。
            """
        )

        # デモデータ生成
        unemployment = np.linspace(0.03, 0.10, 30)
        vacancy = 0.08 - 0.5 * unemployment + np.random.randn(30) * 0.005

        fig, stats = self.plots.plot_beveridge_curve(
            unemployment.tolist(), vacancy.tolist(), figsize=(8, 6)
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Correlation", f"{stats['correlation']:.3f}")

            if stats["correlation"] < -0.5:
                st.success("Strong negative correlation (expected)")
            elif stats["correlation"] < 0:
                st.info("Moderate negative correlation")
            else:
                st.warning("Unexpected correlation")

    def _render_engel_law(self):
        """エンゲルの法則を描画"""
        st.subheader("Engel's Law Analysis")
        st.markdown(
            """
            所得と食料支出割合の関係を示す法則。
            理論的には所得が増えると食料支出割合が減少することが期待される。
            """
        )

        # デモデータ生成
        income = np.linspace(20000, 100000, 50)
        food_share = 0.5 - 0.08 * np.log(income / 20000) + np.random.randn(50) * 0.02

        fig, stats = self.plots.plot_engel_curve(
            income.tolist(), food_share.tolist(), figsize=(8, 6)
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Slope", f"{stats['slope']:.4f}")
            st.metric("R-squared", f"{stats['r_squared']:.3f}")

            if stats["slope"] < 0:
                st.success("Negative slope (Engel's Law confirmed)")

    def _render_price_elasticity(self):
        """価格弾力性を描画"""
        st.subheader("Price Elasticity Analysis")
        st.markdown(
            """
            価格と需要量の関係から価格弾力性を計算。
            - 必需品: -1 < 弾力性 < 0（非弾力的）
            - 贅沢品: 弾力性 < -1（弾力的）
            """
        )

        # 財選択
        good_type = st.selectbox(
            "Select good type:", ["Necessity (Food)", "Luxury (Jewelry)"]
        )

        # デモデータ生成
        prices = np.linspace(1.0, 3.0, 30)

        if "Necessity" in good_type:
            quantities = 100 * prices**-0.5 + np.random.randn(30) * 2
            good_name = "Food (Necessity)"
        else:
            quantities = 100 * prices**-2.0 + np.random.randn(30) * 2
            good_name = "Jewelry (Luxury)"

        fig, stats = self.plots.plot_price_elasticity(
            prices.tolist(), quantities.tolist(), good_name=good_name, figsize=(8, 6)
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Elasticity", f"{stats['elasticity']:.3f}")
            st.metric("R-squared", f"{stats['r_squared']:.3f}")
            st.info(f"Type: {stats['elasticity_type']}")

    def _render_income_distribution(self):
        """所得分布を描画"""
        st.subheader("Income Distribution Analysis")
        st.markdown(
            """
            世帯の所得分布を表示。
            対数正規分布に従うことが期待される。
            """
        )

        # デモデータ生成
        income = np.random.lognormal(10.5, 0.5, 1000).tolist()

        fig, stats = self.plots.plot_distribution(
            income, title="Household Income Distribution", xlabel="Income ($)", bins=50
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.pyplot(fig)

        with col2:
            st.markdown("**Statistics**")
            st.metric("Mean", f"${stats['mean']:,.0f}")
            st.metric("Median", f"${stats['median']:,.0f}")
            st.metric("Std Dev", f"${stats['std']:,.0f}")
            st.metric("Min", f"${stats['min']:,.0f}")
            st.metric("Max", f"${stats['max']:,.0f}")

    def _create_demo_city_map(self, grid_size: int) -> CityMap:
        """デモ用のCityMapを作成"""
        city_map = CityMap(grid_size=grid_size)

        # ランダムに建物を配置
        num_residential = int(grid_size * 0.3)
        num_commercial = int(grid_size * 0.2)
        num_public = int(grid_size * 0.05)

        # 住宅
        for _ in range(num_residential):
            b = city_map.add_building(BuildingType.RESIDENTIAL, capacity=10)
            if b:
                # ランダムに居住者を追加
                num_occupants = np.random.randint(0, b.capacity + 1)
                for _j in range(num_occupants):
                    b.add_occupant(np.random.randint(1000, 9999))

        # 商業施設
        for _ in range(num_commercial):
            b = city_map.add_building(BuildingType.COMMERCIAL, capacity=20)
            if b:
                num_occupants = np.random.randint(0, b.capacity + 1)
                for _j in range(num_occupants):
                    b.add_occupant(np.random.randint(1000, 9999))

        # 公共施設
        for _ in range(num_public):
            city_map.add_building(BuildingType.PUBLIC, capacity=50)

        return city_map

    def _generate_demo_time_series(self, steps: int) -> dict:
        """デモ用の時系列データを生成"""
        gdp = 100 + np.cumsum(np.random.randn(steps) * 2)
        unemployment = 0.05 + np.random.randn(steps) * 0.01
        unemployment = np.clip(unemployment, 0.01, 0.15)
        inflation = 0.02 + np.random.randn(steps) * 0.005
        inflation = np.clip(inflation, -0.02, 0.10)
        interest = 0.025 + np.random.randn(steps) * 0.002
        interest = np.clip(interest, 0.0, 0.10)
        wages = 50 + np.cumsum(np.random.randn(steps) * 0.5)

        return {
            "GDP": gdp.tolist(),
            "Unemployment Rate": unemployment.tolist(),
            "Inflation Rate": inflation.tolist(),
            "Interest Rate": interest.tolist(),
            "Wages": wages.tolist(),
        }


def main():
    """メイン関数"""
    dashboard = SimCityDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
