"""
Central Bank Agent for SimCity Simulation

中央銀行エージェント: 金融政策を決定
- Taylor ruleによる金利決定
- 金利平滑化
- 金融システム管理
"""

from pathlib import Path
from typing import Any

from loguru import logger

from src.agents.base_agent import BaseAgent, load_prompt_template
from src.llm.llm_interface import LLMInterface
from src.models.data_models import CentralBankState
from src.models.economic_models import TaylorRule


class CentralBankAgent(BaseAgent):
    """
    中央銀行エージェント

    LLMを使用して金融政策を決定:
    - 金利: Taylor ruleに基づく政策金利の設定
    - 金融安定: 預金・貸出の監視と調整
    """

    def __init__(
        self,
        state: CentralBankState,
        llm_interface: LLMInterface,
        prompt_template_path: str | Path | None = None,
    ):
        """
        Args:
            state: 中央銀行状態
            llm_interface: LLMインターフェース
            prompt_template_path: プロンプトテンプレートのパス
        """
        # システムプロンプトの読み込み
        if prompt_template_path is None:
            prompt_template_path = (
                Path(__file__).parent.parent
                / "llm"
                / "prompts"
                / "central_bank_system.txt"
            )

        system_prompt = load_prompt_template(prompt_template_path)

        super().__init__(
            agent_id="central_bank",
            agent_type="central_bank",
            llm_interface=llm_interface,
            system_prompt=system_prompt,
            memory_size=10,  # 長期記憶が重要
        )

        self.state = state

        # Taylor rule
        self.taylor_rule = TaylorRule(
            natural_rate=state.natural_rate,
            inflation_target=state.inflation_target,
            alpha=state.taylor_alpha,
            beta=state.taylor_beta,
            smoothing_factor=state.smoothing_factor,
        )

        logger.info("CentralBankAgent created")

    def get_profile_str(self) -> str:
        """
        現在の状態を文字列で返す

        Returns:
            状態文字列
        """
        # 金利情報
        deposit_rate = self.state.get_deposit_rate()
        loan_rate = self.state.get_loan_rate()

        # 金融システムの健全性
        if self.state.total_deposits > 0:
            loan_to_deposit_ratio = self.state.total_loans / self.state.total_deposits
        else:
            loan_to_deposit_ratio = 0.0

        profile = f"""
Central Bank Monetary Policy:
- Policy Rate: {self.state.policy_rate*100:.2f}%
- Natural Rate (r*): {self.state.natural_rate*100:.2f}%
- Inflation Target (π*): {self.state.inflation_target*100:.2f}%

Interest Rate Structure:
- Deposit Rate: {deposit_rate*100:.2f}% (Policy Rate - {abs(self.state.deposit_rate_spread)*100:.2f}%)
- Loan Rate: {loan_rate*100:.2f}% (Policy Rate + {self.state.loan_rate_spread*100:.2f}%)

Taylor Rule Parameters:
- Inflation Coefficient (α): {self.state.taylor_alpha}
- Output Gap Coefficient (β): {self.state.taylor_beta}
- Smoothing Factor (ρ): {self.state.smoothing_factor}

Financial System:
- Total Deposits: ${self.state.total_deposits:.2f}
- Total Loans: ${self.state.total_loans:.2f}
- Loan-to-Deposit Ratio: {loan_to_deposit_ratio:.2%}
"""
        return profile.strip()

    def get_available_actions(self) -> list[dict[str, Any]]:
        """
        利用可能な行動のリストを返す（OpenAI Function Calling形式）

        Returns:
            関数定義のリスト
        """
        return [
            # 金利決定
            {
                "name": "set_policy_rate",
                "description": "Set the policy interest rate based on economic conditions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_rate": {
                            "type": "number",
                            "description": "Target policy rate (as decimal, e.g., 0.02 for 2%)",
                        },
                        "use_taylor_rule": {
                            "type": "boolean",
                            "description": "Whether to apply Taylor rule or set rate manually",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for interest rate decision",
                        },
                    },
                    "required": ["target_rate", "use_taylor_rule", "reasoning"],
                },
            },
            # 金利スプレッド調整
            {
                "name": "adjust_spreads",
                "description": "Adjust deposit and loan rate spreads",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "deposit_spread_change": {
                            "type": "number",
                            "description": "Change to deposit rate spread (negative value)",
                        },
                        "loan_spread_change": {
                            "type": "number",
                            "description": "Change to loan rate spread (positive value)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for spread adjustment",
                        },
                    },
                    "required": [
                        "deposit_spread_change",
                        "loan_spread_change",
                        "reasoning",
                    ],
                },
            },
            # 現状維持
            {
                "name": "maintain_policy",
                "description": "Maintain current monetary policy",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for maintaining current policy",
                        }
                    },
                    "required": ["reasoning"],
                },
            },
        ]

    def _get_fallback_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        """
        LLM呼び出しが失敗した場合のフォールバック行動

        Args:
            observation: 環境からの観察情報

        Returns:
            デフォルトの行動（現状維持）
        """
        return {
            "function_name": "maintain_policy",
            "arguments": {"reasoning": "Fallback: Maintaining current monetary policy"},
        }

    def calculate_target_rate(
        self, inflation: float, gdp: float, potential_gdp: float
    ) -> float:
        """
        Taylor ruleに基づく目標金利を計算

        Args:
            inflation: 現在のインフレ率
            gdp: 現在のGDP
            potential_gdp: 潜在GDP

        Returns:
            目標政策金利
        """
        return self.taylor_rule.calculate_target_rate(inflation, gdp, potential_gdp)

    def update_policy_rate(
        self, target_rate: float, use_smoothing: bool = True
    ) -> float:
        """
        政策金利を更新

        Args:
            target_rate: 目標金利
            use_smoothing: 金利平滑化を適用するか

        Returns:
            新しい政策金利
        """
        if use_smoothing:
            new_rate = self.taylor_rule.smooth_rate(target_rate, self.state.policy_rate)
        else:
            new_rate = target_rate

        # 非負制約
        new_rate = max(0.0, new_rate)

        self.state.policy_rate = new_rate
        logger.info(f"Policy rate updated: {new_rate*100:.2f}%")

        return new_rate

    def update_state(self, updates: dict[str, Any]):
        """
        状態を更新

        Args:
            updates: 更新する属性の辞書
        """
        for key, value in updates.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

        # Taylor ruleパラメータが更新された場合、再構築
        if any(
            key
            in [
                "natural_rate",
                "inflation_target",
                "taylor_alpha",
                "taylor_beta",
                "smoothing_factor",
            ]
            for key in updates
        ):
            self.taylor_rule = TaylorRule(
                natural_rate=self.state.natural_rate,
                inflation_target=self.state.inflation_target,
                alpha=self.state.taylor_alpha,
                beta=self.state.taylor_beta,
                smoothing_factor=self.state.smoothing_factor,
            )

    def get_current_rates(self) -> dict[str, float]:
        """
        現在の金利構造を取得

        Returns:
            金利辞書
        """
        return {
            "policy_rate": self.state.policy_rate,
            "deposit_rate": self.state.get_deposit_rate(),
            "loan_rate": self.state.get_loan_rate(),
        }
