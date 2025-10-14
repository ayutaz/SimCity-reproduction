"""
Simulation engine for SimCity

シミュレーションのメインループと状態管理を提供
"""

import json
from pathlib import Path

from loguru import logger

from src.agents.central_bank import CentralBankAgent
from src.agents.government import GovernmentAgent
from src.agents.household import HouseholdAgent, HouseholdProfileGenerator
from src.environment.markets.financial_market import FinancialMarket
from src.environment.markets.goods_market import GoodsMarket
from src.environment.markets.labor_market import LaborMarket
from src.llm.llm_interface import LLMInterface
from src.models.data_models import (
    CentralBankState,
    FirmProfile,
    GovernmentState,
    HouseholdProfile,
    MarketState,
    SimulationState,
)
from src.models.economic_models import MacroeconomicIndicators
from src.utils.config import SimCityConfig


class Simulation:
    """
    SimCityシミュレーションエンジン

    論文のAlgorithm 1に基づくシミュレーションループ:
    1. Production and Trading Stage
    2. Taxation and Dividend Stage
    3. Metabolic Stage (人口流入・流出)
    4. Revision Stage (LLMによる意思決定)
    """

    def __init__(self, config: SimCityConfig):
        """
        Args:
            config: シミュレーション設定
        """
        self.config = config
        self.state = SimulationState()

        # 初期化
        self._initialize_state()

        logger.info(
            f"Simulation initialized: phase={self.state.phase}, "
            f"max_steps={config.simulation.max_steps}"
        )

    def _initialize_state(self):
        """シミュレーション状態の初期化"""
        self.state.step = 0
        self.state.phase = "move_in"

        # LLMインターフェースの初期化
        llm_config = {
            "api_key": self.config.llm.openai.api_key,
            "model": self.config.llm.openai.model,
            "temperature": self.config.llm.openai.temperature,
            "max_tokens": self.config.llm.openai.max_tokens,
        }
        self.llm_interface = LLMInterface(llm_config)

        # エージェントの初期化
        self._initialize_agents()

        # 市場の初期化
        self._initialize_markets()

        # 履歴の初期化
        self.state.history = {
            "gdp": [],
            "real_gdp": [],
            "inflation": [],
            "unemployment_rate": [],
            "gini": [],
            "policy_rate": [],
            "num_households": [],
            "num_firms": [],
            "vacancy_rate": [],
            "consumption": [],
            "investment": [],
            "household_incomes": [],
            "food_expenditure_ratios": [],
            "prices": {},
            "demands": {},
        }

        logger.info("State initialized")

    def _initialize_agents(self):
        """エージェントの初期化"""
        logger.info("Initializing agents...")

        # 世帯エージェントの初期化
        household_data_file = Path("data/initial_households.json")
        if household_data_file.exists():
            # データファイルから読み込み
            with open(household_data_file, encoding="utf-8") as f:
                household_profiles = json.load(f)

            self.households = [
                HouseholdAgent(
                    household_id=profile["household_id"],
                    profile=HouseholdProfile(**profile),
                    llm_interface=self.llm_interface,
                )
                for profile in household_profiles[:self.config.agents.households.initial_count]
            ]
        else:
            # プロファイルを生成
            generator = HouseholdProfileGenerator(random_seed=self.config.simulation.random_seed)
            profiles = generator.generate(count=self.config.agents.households.initial_count)

            self.households = [
                HouseholdAgent(
                    household_id=profile.household_id,
                    profile=profile,
                    llm_interface=self.llm_interface,
                )
                for profile in profiles
            ]

        # 企業エージェントの初期化（簡略版）
        self.firms = []
        # TODO: 企業テンプレートから企業を生成

        # 政府エージェントの初期化
        gov_state = GovernmentState(
            income_tax_brackets=self.config.economy.taxation.income_tax_brackets,
            vat_rate=self.config.economy.taxation.vat_rate,
            ubi_enabled=self.config.economy.welfare.ubi_enabled,
            ubi_amount=self.config.economy.welfare.ubi_amount,
            unemployment_benefit_rate=self.config.economy.welfare.unemployment_benefit_rate,
        )
        self.government = GovernmentAgent(
            agent_id="government",
            initial_state=gov_state,
            llm_interface=self.llm_interface,
        )

        # 中央銀行エージェントの初期化
        cb_state = CentralBankState(
            policy_rate=self.config.economy.financial.initial_interest_rate,
            smoothing_factor=self.config.economy.financial.interest_rate_smoothing,
            natural_rate=self.config.economy.financial.taylor_rule.natural_rate,
            inflation_target=self.config.economy.financial.taylor_rule.inflation_target,
            taylor_alpha=self.config.economy.financial.taylor_rule.inflation_coefficient,
            taylor_beta=self.config.economy.financial.taylor_rule.output_coefficient,
        )
        self.central_bank = CentralBankAgent(
            agent_id="central_bank",
            initial_state=cb_state,
            llm_interface=self.llm_interface,
        )

        # SimulationStateに設定
        self.state.households = [h.profile for h in self.households]
        self.state.firms = []
        self.state.government = gov_state
        self.state.central_bank = cb_state

        logger.info(f"Agents initialized: {len(self.households)} households, {len(self.firms)} firms")

    def _initialize_markets(self):
        """市場の初期化"""
        logger.info("Initializing markets...")

        # 労働市場
        self.labor_market = LaborMarket(config=self.config.markets.labor.model_dump())

        # 財市場
        self.goods_market = GoodsMarket(config=self.config.markets.goods.model_dump())

        # 金融市場
        self.financial_market = FinancialMarket(config=self.config.markets.financial.model_dump())

        self.state.market = MarketState()

        logger.info("Markets initialized")

    def step(self) -> dict[str, float]:
        """
        1ステップ（1ヶ月）を実行

        Returns:
            現在のマクロ経済指標
        """
        logger.info(f"=== Step {self.state.step} ===")

        # フェーズ管理
        if self.state.step >= self.config.simulation.phase1_steps:
            if self.state.phase == "move_in":
                self.state.phase = "development"
                logger.info("Phase transition: move_in -> development")

        # シミュレーションループ（簡略版）
        # 実際のエージェント実装はPhase 2で行う

        # Stage 1: Production and Trading
        self._production_and_trading_stage()

        # Stage 2: Taxation and Dividend
        self._taxation_and_dividend_stage()

        # Stage 3: Metabolic Stage
        if self.state.phase == "move_in":
            self._metabolic_stage()

        # Stage 4: Revision Stage (エージェント意思決定)
        # TODO: Phase 2でエージェント実装後に追加

        # マクロ経済指標の計算
        indicators = self._calculate_indicators()

        # 履歴に記録
        self._record_history(indicators)

        # ステップカウンタ更新
        self.state.step += 1

        logger.info(f"Step {self.state.step - 1} completed")
        logger.info(
            f"Indicators: GDP={indicators['gdp']:.2f}, "
            f"Unemployment={indicators['unemployment_rate']:.2%}"
        )

        return indicators

    def _production_and_trading_stage(self):
        """
        Stage 1: 生産と取引

        企業が財を生産し、家計が購入
        """
        # TODO: Phase 2でエージェント実装後に実装
        logger.debug("Production and Trading Stage (placeholder)")

    def _taxation_and_dividend_stage(self):
        """
        Stage 2: 課税と配当

        政府が税金を徴収し、UBI等を配分
        企業が配当を支払う
        """
        # TODO: Phase 2でエージェント実装後に実装
        logger.debug("Taxation and Dividend Stage (placeholder)")

    def _metabolic_stage(self):
        """
        Stage 3: 代謝ステージ

        新しい家計が流入
        """
        # TODO: Phase 2で家計エージェント実装後に追加
        max_households = self.config.agents.households.max
        current_households = len(self.state.households)
        monthly_inflow = self.config.agents.households.monthly_inflow

        if current_households < max_households:
            new_households = min(monthly_inflow, max_households - current_households)
            logger.debug(f"Adding {new_households} new households")
            # 実際の家計追加はPhase 2で実装

    def _calculate_indicators(self) -> dict[str, float]:
        """
        マクロ経済指標を計算

        Returns:
            指標の辞書
        """
        # 家計所得の集計
        if self.households:
            household_incomes = [
                getattr(h.profile, "monthly_income", 50000.0) for h in self.households
            ]
        else:
            household_incomes = []

        # GDP計算（簡略版）
        total_consumption = sum(getattr(h, "consumption", 5000.0) for h in self.households)
        total_investment = sum(getattr(f, "investment", 10000.0) for f in self.firms)
        government_spending = getattr(self.government.state, "expenditure", 0.0) if self.government else 0.0

        gdp = total_consumption + total_investment + government_spending

        # インフレ率計算（前期との比較）
        if len(self.state.history.get("gdp", [])) > 0:
            prev_gdp = self.state.history["gdp"][-1]
            if prev_gdp > 0:
                inflation = (gdp - prev_gdp) / prev_gdp
            else:
                inflation = 0.0
        else:
            inflation = 0.0

        # 失業率計算
        total_labor_force = len(self.households)
        if total_labor_force > 0:
            employed = sum(
                1 for h in self.households
                if getattr(h.profile, "employment_status", "unemployed") == "employed"
            )
            unemployment_rate = (total_labor_force - employed) / total_labor_force
        else:
            unemployment_rate = 0.0

        # Gini係数
        if household_incomes:
            gini = MacroeconomicIndicators.calculate_gini_coefficient(household_incomes)
        else:
            gini = 0.0

        # 政府の状態更新
        if self.government and self.government.state:
            self.government.state.gdp = gdp
            self.government.state.inflation_rate = inflation
            self.government.state.unemployment_rate = unemployment_rate
            self.government.state.gini_coefficient = gini

        # 中央銀行の状態更新
        policy_rate = self.central_bank.state.policy_rate if self.central_bank and self.central_bank.state else 0.02

        return {
            "gdp": gdp,
            "real_gdp": gdp,  # TODO: 実質GDPは別途計算
            "inflation": inflation,
            "unemployment_rate": unemployment_rate,
            "gini": gini,
            "policy_rate": policy_rate,
            "num_households": len(self.households),
            "num_firms": len(self.firms),
        }

    def _record_history(self, indicators: dict[str, float]):
        """
        指標を履歴に記録

        Args:
            indicators: 指標の辞書
        """
        for key, value in indicators.items():
            if key in self.state.history:
                self.state.history[key].append(value)

    def save_state(self, filepath: str | Path):
        """
        シミュレーション状態を保存

        Args:
            filepath: 保存先ファイルパス
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        state_dict = self.state.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"State saved to {filepath}")

    def load_state(self, filepath: str | Path):
        """
        シミュレーション状態を読み込み

        Args:
            filepath: 読み込むファイルパス
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")

        with open(filepath, encoding="utf-8") as f:
            state_dict = json.load(f)

        # 状態の復元
        self.state.step = state_dict["step"]
        self.state.phase = state_dict["phase"]

        # 家計の復元
        self.state.households = [
            HouseholdProfile.from_dict(h) for h in state_dict["households"]
        ]

        # 企業の復元
        self.state.firms = [FirmProfile.from_dict(f) for f in state_dict["firms"]]

        # 政府・中央銀行の復元
        if state_dict["government"]:
            self.state.government = GovernmentState(**state_dict["government"])

        if state_dict["central_bank"]:
            self.state.central_bank = CentralBankState(**state_dict["central_bank"])

        # 市場の復元
        self.state.market = MarketState(**state_dict["market"])

        # 履歴の復元
        self.state.history = state_dict["history"]

        logger.info(f"State loaded from {filepath}")

    def get_indicators(self) -> dict[str, float]:
        """
        現在のマクロ経済指標を取得

        Returns:
            指標の辞書
        """
        return self._calculate_indicators()

    def get_metrics(self) -> dict[str, float]:
        """
        現在のマクロ経済指標を取得（get_indicators()のエイリアス）

        Returns:
            指標の辞書
        """
        indicators = self._calculate_indicators()

        # スクリプトが期待する追加のメトリクス
        if self.households:
            household_incomes = [
                getattr(h.profile, "monthly_income", 50000.0) for h in self.households
            ]
            indicators["average_income"] = sum(household_incomes) / len(household_incomes)
        else:
            indicators["average_income"] = 0.0

        indicators["total_consumption"] = sum(
            getattr(h, "consumption", 5000.0) for h in self.households
        )
        indicators["total_investment"] = sum(
            getattr(f, "investment", 10000.0) for f in self.firms
        )
        indicators["vacancy_rate"] = getattr(self.state.market, "vacancy_rate", 0.03) if self.state.market else 0.03
        indicators["government_spending"] = (
            getattr(self.government.state, "expenditure", 0.0) if self.government and self.government.state else 0.0
        )
        indicators["tax_revenue"] = (
            getattr(self.government.state, "tax_revenue", 0.0) if self.government and self.government.state else 0.0
        )

        return indicators

    def save_results(self, output_dir: str | Path):
        """
        シミュレーション結果を保存

        Args:
            output_dir: 出力ディレクトリパス
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 結果の構築
        results = {
            "history": self.state.history,
            "metadata": {
                "steps": self.state.step,
                "households": len(self.state.households),
                "firms": len(self.state.firms),
                "seed": self.config.simulation.random_seed,
                "phase": self.state.phase,
            }
        }

        # results.jsonの保存
        results_file = output_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {results_file}")

        # サマリーの保存
        if self.state.history.get("gdp"):
            summary = {
                "final_gdp": self.state.history["gdp"][-1],
                "final_unemployment": self.state.history.get("unemployment", [0])[-1],
                "final_inflation": self.state.history.get("inflation", [0])[-1],
                "final_gini": self.state.history.get("gini", [0])[-1],
                "avg_gdp": sum(self.state.history["gdp"]) / len(self.state.history["gdp"]),
                "steps": self.state.step,
            }

            summary_file = output_dir / "summary.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"Summary saved to {summary_file}")

    def run(self, steps: int) -> list[dict[str, float]]:
        """
        複数ステップを実行

        Args:
            steps: 実行するステップ数

        Returns:
            各ステップの指標のリスト
        """
        results = []

        for _ in range(steps):
            indicators = self.step()
            results.append(indicators)

        return results

    def reset(self):
        """シミュレーションをリセット"""
        self._initialize_state()
        logger.info("Simulation reset")

    def get_summary(self) -> dict[str, any]:
        """
        シミュレーションサマリーを取得

        Returns:
            サマリー情報
        """
        return {
            "step": self.state.step,
            "phase": self.state.phase,
            "num_households": len(self.state.households),
            "num_firms": len(self.state.firms),
            "current_indicators": self.get_indicators(),
            "history_length": len(self.state.history.get("gdp", [])),
        }
