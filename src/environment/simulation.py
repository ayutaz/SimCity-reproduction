"""
Simulation engine for SimCity

シミュレーションのメインループと状態管理を提供
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

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

        # 政府と中央銀行の初期化
        self.state.government = GovernmentState(
            income_tax_brackets=self.config.economy.taxation.income_tax_brackets,
            vat_rate=self.config.economy.taxation.vat_rate,
            ubi_enabled=self.config.economy.welfare.ubi_enabled,
            ubi_amount=self.config.economy.welfare.ubi_amount,
            unemployment_benefit_rate=self.config.economy.welfare.unemployment_benefit_rate,
        )

        self.state.central_bank = CentralBankState(
            policy_rate=self.config.economy.financial.initial_interest_rate,
            smoothing_factor=self.config.economy.financial.interest_rate_smoothing,
            natural_rate=self.config.economy.financial.taylor_rule.natural_rate,
            inflation_target=self.config.economy.financial.taylor_rule.inflation_target,
            taylor_alpha=self.config.economy.financial.taylor_rule.inflation_coefficient,
            taylor_beta=self.config.economy.financial.taylor_rule.output_coefficient,
        )

        self.state.market = MarketState()

        # 履歴の初期化
        self.state.history = {
            "gdp": [],
            "real_gdp": [],
            "inflation": [],
            "unemployment": [],
            "gini": [],
            "policy_rate": [],
            "num_households": [],
            "num_firms": [],
        }

        logger.info("State initialized")

    def step(self) -> Dict[str, float]:
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

    def _calculate_indicators(self) -> Dict[str, float]:
        """
        マクロ経済指標を計算

        Returns:
            指標の辞書
        """
        # 家計所得の集計
        household_incomes = [h.monthly_income for h in self.state.households]

        # 企業産出の集計
        firm_outputs = [f.production_quantity * f.price for f in self.state.firms]

        # GDP計算
        gdp = MacroeconomicIndicators.calculate_gdp(
            household_incomes,
            firm_outputs,
            self.state.government.expenditure if self.state.government else 0.0,
        )

        # インフレ率計算（前期との比較）
        if len(self.state.history.get("gdp", [])) > 0:
            # 簡略化: GDP deflatorを使用
            prev_gdp = self.state.history["gdp"][-1]
            if prev_gdp > 0:
                inflation = (gdp - prev_gdp) / prev_gdp
            else:
                inflation = 0.0
        else:
            inflation = 0.0

        # 失業率計算
        total_labor_force = len(self.state.households)
        employed = sum(
            1
            for h in self.state.households
            if h.employment_status.value == "employed"
        )
        unemployment_rate = MacroeconomicIndicators.calculate_unemployment_rate(
            total_labor_force, employed
        )

        # Gini係数
        incomes = [h.monthly_income for h in self.state.households]
        gini = MacroeconomicIndicators.calculate_gini_coefficient(incomes)

        # 政府の状態更新
        if self.state.government:
            self.state.government.gdp = gdp
            self.state.government.inflation_rate = inflation
            self.state.government.unemployment_rate = unemployment_rate
            self.state.government.gini_coefficient = gini

        return {
            "gdp": gdp,
            "real_gdp": gdp,  # TODO: 実質GDPは別途計算
            "inflation": inflation,
            "unemployment_rate": unemployment_rate,
            "gini": gini,
            "policy_rate": (
                self.state.central_bank.policy_rate if self.state.central_bank else 0.0
            ),
            "num_households": len(self.state.households),
            "num_firms": len(self.state.firms),
        }

    def _record_history(self, indicators: Dict[str, float]):
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

    def get_indicators(self) -> Dict[str, float]:
        """
        現在のマクロ経済指標を取得

        Returns:
            指標の辞書
        """
        return self._calculate_indicators()

    def run(self, steps: int) -> List[Dict[str, float]]:
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

    def get_summary(self) -> Dict[str, any]:
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
