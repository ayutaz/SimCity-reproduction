"""
Streamlit Dashboard for SimCity Simulation

Streamlitダッシュボード:
- シミュレーション結果の可視化
- 都市マップ表示
- 経済指標グラフ
- インタラクティブコントロール
- リアルタイムシミュレーション実行
"""

# .envファイルから環境変数を読み込み（importの前に実行）
from dotenv import load_dotenv

load_dotenv()

import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from loguru import logger  # noqa: E402

from src.environment.geography import BuildingType, CityMap  # noqa: E402
from src.environment.simulation import Simulation  # noqa: E402
from src.utils.config import load_config  # noqa: E402
from src.visualization.map_generator import MapGenerator  # noqa: E402
from src.visualization.plots import EconomicPlots  # noqa: E402


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

        # セッション状態の初期化
        self._initialize_session_state()

        # データソース選択
        st.sidebar.subheader("Data Source")
        data_source = st.sidebar.radio(
            "Select data source:",
            ["Demo Data", "Upload Results", "Live Simulation"],
        )

        st.session_state.data_source = data_source

        if data_source == "Upload Results":
            uploaded_file = st.sidebar.file_uploader(
                "Upload simulation results (JSON)", type=["json"]
            )
            if uploaded_file is not None:
                self._load_results_file(uploaded_file)

        elif data_source == "Live Simulation":
            self._render_simulation_controls()

        # デモデータ用の設定（Demo Data選択時のみ）
        if data_source == "Demo Data":
            st.sidebar.subheader("Demo Settings")
            grid_size = st.sidebar.slider("Grid Size", 20, 100, 50, 10)
            st.session_state.settings = {"grid_size": grid_size}

    def _initialize_session_state(self):
        """セッション状態を初期化"""
        if "simulation" not in st.session_state:
            st.session_state.simulation = None

        if "sim_state" not in st.session_state:
            st.session_state.sim_state = "idle"  # idle/running/paused/stopped

        if "sim_history" not in st.session_state:
            st.session_state.sim_history = None

        if "settings" not in st.session_state:
            st.session_state.settings = {}

        if "data_source" not in st.session_state:
            st.session_state.data_source = "Demo Data"

    def _render_simulation_controls(self):
        """シミュレーション実行コントロールを描画"""
        st.sidebar.subheader("Simulation Settings")

        # シミュレーション設定
        num_households = st.sidebar.number_input(
            "Number of Households", min_value=5, max_value=200, value=20, step=5
        )
        num_firms = st.sidebar.number_input(
            "Number of Firms", min_value=1, max_value=50, value=3, step=1
        )
        num_steps = st.sidebar.number_input(
            "Number of Steps", min_value=1, max_value=180, value=12, step=1
        )
        random_seed = st.sidebar.number_input(
            "Random Seed", min_value=0, max_value=9999, value=42, step=1
        )

        st.sidebar.divider()

        # 実行ボタン
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("▶️ Start", use_container_width=True):
                self._start_simulation(
                    num_households, num_firms, num_steps, random_seed
                )

        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                self._stop_simulation()

        # 一時停止/再開ボタン
        col3, col4 = st.sidebar.columns(2)

        with col3:
            if st.button("⏸️ Pause", use_container_width=True):
                self._pause_simulation()

        with col4:
            if st.button("⏯️ Resume", use_container_width=True):
                self._resume_simulation()

        # ステータス表示
        st.sidebar.divider()
        st.sidebar.subheader("Status")

        status_color = {
            "idle": "🔵",
            "running": "🟢",
            "paused": "🟡",
            "stopped": "🔴",
        }
        st.sidebar.markdown(
            f"**State**: {status_color.get(st.session_state.sim_state, '⚪')} {st.session_state.sim_state.upper()}"
        )

        if st.session_state.simulation is not None:
            current_step = st.session_state.simulation.state.step
            st.sidebar.markdown(f"**Current Step**: {current_step}")

    def _start_simulation(
        self, num_households: int, num_firms: int, num_steps: int, random_seed: int
    ):
        """シミュレーションを開始"""
        try:
            st.session_state.sim_state = "running"

            # 設定読み込み（デフォルトパスを指定）
            config = load_config("config/simulation_config.yaml")

            # 設定を上書き
            config.agents.households.initial = num_households
            config.agents.households.max = num_households
            config.agents.firms.initial = num_firms
            config.simulation.random_seed = random_seed

            # シミュレーション初期化（LLMInterfaceは内部で自動初期化される）
            simulation = Simulation(config)

            st.session_state.simulation = simulation
            st.session_state.num_steps = num_steps
            st.session_state.target_step = num_steps

            logger.info(f"Simulation started: {num_steps} steps")

        except Exception as e:
            st.error(f"Failed to start simulation: {e}")
            logger.error(f"Simulation start error: {e}")
            st.session_state.sim_state = "idle"

    def _stop_simulation(self):
        """シミュレーションを停止"""
        st.session_state.sim_state = "stopped"
        logger.info("Simulation stopped")

    def _pause_simulation(self):
        """シミュレーションを一時停止"""
        if st.session_state.sim_state == "running":
            st.session_state.sim_state = "paused"
            logger.info("Simulation paused")

    def _resume_simulation(self):
        """シミュレーションを再開"""
        if st.session_state.sim_state == "paused":
            st.session_state.sim_state = "running"
            logger.info("Simulation resumed")

    def _load_results_file(self, uploaded_file):
        """結果ファイルを読み込み"""
        try:
            content = uploaded_file.read()
            data = json.loads(content)

            st.session_state.sim_history = data.get("history", {})
            st.success("Results loaded successfully!")
            logger.info("Results file loaded")

        except Exception as e:
            st.error(f"Failed to load results: {e}")
            logger.error(f"Results loading error: {e}")

    def _run_simulation_step(self):
        """シミュレーションステップを実行"""
        sim = st.session_state.simulation

        if st.session_state.sim_state == "running":
            current_step = sim.state.step
            target_step = st.session_state.get("target_step", 12)

            # 進捗バー
            progress_placeholder = st.empty()
            log_placeholder = st.empty()

            if current_step < target_step:
                # 進捗表示
                progress = current_step / target_step
                progress_placeholder.progress(
                    progress, text=f"Step {current_step}/{target_step}"
                )

                try:
                    # 1ステップ実行
                    log_placeholder.info(f"Executing step {current_step + 1}...")
                    sim.step()

                    # 画面を更新
                    time.sleep(0.1)  # 視覚的なフィードバックのための短い遅延
                    st.rerun()

                except Exception as e:
                    log_placeholder.error(f"Error in step {current_step}: {e}")
                    logger.error(f"Simulation step error: {e}")
                    st.session_state.sim_state = "stopped"

            else:
                # シミュレーション完了
                progress_placeholder.success("✅ Simulation completed!")
                st.session_state.sim_state = "stopped"
                st.session_state.sim_history = sim.state.history

    def _display_metrics(self):
        """メトリクスを表示"""
        sim = st.session_state.simulation

        col1, col2, col3, col4 = st.columns(4)

        # ライブシミュレーションまたはアップロードされた結果からメトリクスを表示
        if sim is not None and st.session_state.data_source == "Live Simulation":
            history = sim.state.history

            if len(history["gdp"]) > 0:
                # 最新の値を表示
                latest_gdp = history["gdp"][-1]
                latest_unemployment = history["unemployment_rate"][-1]
                latest_inflation = history["inflation"][-1]

                # 世帯数
                num_households = len(sim.households)

                # 変化量計算（前ステップとの差分）
                gdp_delta = (
                    latest_gdp - history["gdp"][-2] if len(history["gdp"]) > 1 else 0
                )
                unemployment_delta = (
                    latest_unemployment - history["unemployment_rate"][-2]
                    if len(history["unemployment_rate"]) > 1
                    else 0
                )
                inflation_delta = (
                    latest_inflation - history["inflation"][-2]
                    if len(history["inflation"]) > 1
                    else 0
                )

                with col1:
                    st.metric(
                        "GDP",
                        f"${latest_gdp:,.0f}",
                        f"{gdp_delta:+,.0f}",
                        delta_color="normal",
                    )

                with col2:
                    st.metric(
                        "Unemployment",
                        f"{latest_unemployment * 100:.1f}%",
                        f"{unemployment_delta * 100:+.1f}%",
                        delta_color="inverse",
                    )

                with col3:
                    st.metric(
                        "Inflation",
                        f"{latest_inflation * 100:.1f}%",
                        f"{inflation_delta * 100:+.1f}%",
                        delta_color="normal",
                    )

                with col4:
                    st.metric("Households", f"{num_households:,}")
            else:
                # データがまだない場合
                with col1:
                    st.metric("GDP", "N/A")
                with col2:
                    st.metric("Unemployment", "N/A")
                with col3:
                    st.metric("Inflation", "N/A")
                with col4:
                    st.metric("Households", len(sim.households) if sim else 0)

        elif st.session_state.sim_history is not None:
            # アップロードされた結果を表示
            history = st.session_state.sim_history

            if len(history.get("gdp", [])) > 0:
                latest_gdp = history["gdp"][-1]
                latest_unemployment = history["unemployment_rate"][-1]
                # 新旧両方のキー名に対応
                latest_inflation = (
                    history.get("inflation", history.get("inflation_rate", [0]))[-1]
                    if history.get("inflation") or history.get("inflation_rate")
                    else 0
                )

                with col1:
                    st.metric("GDP", f"${latest_gdp:,.0f}")
                with col2:
                    st.metric("Unemployment", f"{latest_unemployment * 100:.1f}%")
                with col3:
                    st.metric("Inflation", f"{latest_inflation * 100:.1f}%")
                with col4:
                    st.metric("Population", "N/A")
            else:
                with col1:
                    st.metric("GDP", "N/A")
                with col2:
                    st.metric("Unemployment", "N/A")
                with col3:
                    st.metric("Inflation", "N/A")
                with col4:
                    st.metric("Population", "N/A")

        else:
            # デモデータ
            with col1:
                st.metric("GDP", "$125.5M", "+2.3%")
            with col2:
                st.metric("Unemployment", "5.2%", "-0.5%")
            with col3:
                st.metric("Inflation", "2.1%", "+0.3%")
            with col4:
                st.metric("Population", "10,250", "+150")

    def _render_overview(self):
        """概要タブを描画"""
        st.header("Simulation Overview")

        # ライブシミュレーション実行中の場合
        if (
            st.session_state.data_source == "Live Simulation"
            and st.session_state.simulation is not None
        ):
            self._run_simulation_step()

        # メトリクス表示
        self._display_metrics()

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

        # データソースに応じて時系列データを取得
        time_series = self._get_time_series_data()

        if time_series is None or len(list(time_series.values())[0]) == 0:
            st.info("No data available. Please run a simulation or upload results.")
            return

        # 指標選択
        available_indicators = list(time_series.keys())
        indicators = st.multiselect(
            "Select indicators to display:",
            available_indicators,
            default=available_indicators[:3]
            if len(available_indicators) >= 3
            else available_indicators,
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

    def _get_time_series_data(self) -> dict | None:
        """データソースから時系列データを取得"""
        # ライブシミュレーション
        if (
            st.session_state.data_source == "Live Simulation"
            and st.session_state.simulation is not None
        ):
            history = st.session_state.simulation.state.history

            if len(history["gdp"]) > 0:
                return {
                    "GDP": history["gdp"],
                    "Unemployment Rate": history["unemployment_rate"],
                    "Inflation Rate": history["inflation"],
                    "Gini Coefficient": history["gini"],
                }
            else:
                return None

        # アップロードされた結果
        elif st.session_state.sim_history is not None:
            history = st.session_state.sim_history

            if len(history.get("gdp", [])) > 0:
                result = {}
                if "gdp" in history:
                    result["GDP"] = history["gdp"]
                if "unemployment_rate" in history:
                    result["Unemployment Rate"] = history["unemployment_rate"]
                # 新旧両方のキー名に対応
                if "inflation" in history:
                    result["Inflation Rate"] = history["inflation"]
                elif "inflation_rate" in history:
                    result["Inflation Rate"] = history["inflation_rate"]
                # 新旧両方のキー名に対応
                if "gini" in history:
                    result["Gini Coefficient"] = history["gini"]
                elif "gini_coefficient" in history:
                    result["Gini Coefficient"] = history["gini_coefficient"]
                return result
            else:
                return None

        # デモデータ
        else:
            steps = 50
            return self._generate_demo_time_series(steps)

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
