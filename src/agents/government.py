"""
Government Agent for SimCity Simulation

政府エージェント: 経済政策を決定
- 税制（所得税、付加価値税）
- 福祉（UBI、失業給付）
- 公共サービス
"""

from pathlib import Path
from typing import Any

from loguru import logger

from src.agents.base_agent import BaseAgent, load_prompt_template
from src.llm.llm_interface import LLMInterface
from src.models.data_models import GovernmentState
from src.models.economic_models import TaxationSystem


class GovernmentAgent(BaseAgent):
    """
    政府エージェント

    LLMを使用して経済政策を決定:
    - 税制: 所得税率や税制構造の調整
    - 福祉: UBI金額や失業給付率の調整
    - 公共サービス: インフラ投資や公共サービスの拡充
    """

    def __init__(
        self,
        state: GovernmentState,
        llm_interface: LLMInterface,
        prompt_template_path: str | Path | None = None,
    ):
        """
        Args:
            state: 政府状態
            llm_interface: LLMインターフェース
            prompt_template_path: プロンプトテンプレートのパス
        """
        # システムプロンプトの読み込み
        if prompt_template_path is None:
            prompt_template_path = (
                Path(__file__).parent.parent / "llm" / "prompts" / "government_system.txt"
            )

        system_prompt = load_prompt_template(prompt_template_path)

        super().__init__(
            agent_id="government",
            agent_type="government",
            llm_interface=llm_interface,
            system_prompt=system_prompt,
            memory_size=10,  # 政府は長期記憶が重要
        )

        self.state = state

        # 税制システム（所得税のみ）
        self.taxation = TaxationSystem(brackets=state.income_tax_brackets)

        logger.info("GovernmentAgent created")

    def get_profile_str(self) -> str:
        """
        現在の状態を文字列で返す

        Returns:
            状態文字列
        """
        # 税制情報
        tax_brackets_str = "\n".join(
            [
                f"    Income > ${bracket[0]:.0f}: {bracket[1]*100:.1f}%"
                for bracket in self.state.income_tax_brackets
            ]
        )

        # 予算情報
        budget_balance = self.state.tax_revenue - self.state.expenditure
        budget_status = "Surplus" if budget_balance >= 0 else "Deficit"

        profile = f"""
Government Financial Status:
- Reserves: ${self.state.reserves:.2f}
- Tax Revenue (current period): ${self.state.tax_revenue:.2f}
- Expenditure (current period): ${self.state.expenditure:.2f}
- Budget Balance: ${budget_balance:.2f} ({budget_status})

Tax Policy:
- Income Tax Brackets:
{tax_brackets_str}
- VAT Rate: {self.state.vat_rate*100:.1f}%

Welfare Policy:
- UBI Enabled: {self.state.ubi_enabled}
- UBI Amount: ${self.state.ubi_amount:.2f}/month
- Unemployment Benefit Rate: {self.state.unemployment_benefit_rate*100:.1f}%

Macroeconomic Indicators:
- GDP: ${self.state.gdp:.2f}
- Real GDP: ${self.state.real_gdp:.2f}
- Inflation Rate: {self.state.inflation_rate*100:.2f}%
- Unemployment Rate: {self.state.unemployment_rate*100:.2f}%
- Gini Coefficient: {self.state.gini_coefficient:.3f}
"""
        return profile.strip()

    def get_available_actions(self) -> list[dict[str, Any]]:
        """
        利用可能な行動のリストを返す（OpenAI Function Calling形式）

        Returns:
            関数定義のリスト
        """
        return [
            # 税制調整
            {
                "name": "adjust_tax_policy",
                "description": "Adjust tax rates and tax policy",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "income_tax_adjustment": {
                            "type": "number",
                            "description": "Percentage adjustment to income tax rates (-0.1 to +0.1)",
                        },
                        "vat_adjustment": {
                            "type": "number",
                            "description": "Adjustment to VAT rate (-0.05 to +0.05)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for tax policy adjustment",
                        },
                    },
                    "required": ["income_tax_adjustment", "vat_adjustment", "reasoning"],
                },
            },
            # 福祉政策調整
            {
                "name": "adjust_welfare_policy",
                "description": "Adjust welfare benefits (UBI, unemployment benefits)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ubi_enabled": {
                            "type": "boolean",
                            "description": "Enable or disable UBI",
                        },
                        "ubi_amount": {
                            "type": "number",
                            "description": "Monthly UBI amount per person",
                        },
                        "unemployment_benefit_rate": {
                            "type": "number",
                            "description": "Unemployment benefit rate (0.0 to 1.0)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for welfare policy adjustment",
                        },
                    },
                    "required": ["ubi_enabled", "ubi_amount", "unemployment_benefit_rate", "reasoning"],
                },
            },
            # 公共サービス投資
            {
                "name": "public_investment",
                "description": "Invest in public infrastructure and services",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "investment_type": {
                            "type": "string",
                            "enum": [
                                "infrastructure",
                                "education",
                                "healthcare",
                                "none",
                            ],
                            "description": "Type of public investment",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount to invest",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for public investment",
                        },
                    },
                    "required": ["investment_type", "amount", "reasoning"],
                },
            },
            # 現状維持
            {
                "name": "maintain_policy",
                "description": "Maintain current policies without changes",
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
            "arguments": {"reasoning": "Fallback: Maintaining current policy"},
        }

    def collect_income_tax(self, income: float) -> float:
        """
        所得税を徴収

        Args:
            income: 所得

        Returns:
            税額
        """
        return self.taxation.calculate_income_tax(income)

    def collect_vat(self, transaction_value: float) -> float:
        """
        付加価値税を徴収

        Args:
            transaction_value: 取引額

        Returns:
            税額
        """
        return transaction_value * self.state.vat_rate

    def distribute_ubi(self, num_households: int) -> float:
        """
        UBIを配布

        Args:
            num_households: 世帯数

        Returns:
            総支出額
        """
        if not self.state.ubi_enabled:
            return 0.0

        return self.state.ubi_amount * num_households

    def calculate_unemployment_benefit(
        self, previous_wage: float, months_unemployed: int
    ) -> float:
        """
        失業給付を計算

        Args:
            previous_wage: 前職の賃金
            months_unemployed: 失業月数

        Returns:
            給付額
        """
        # 6ヶ月まで給付
        if months_unemployed > 6:
            return 0.0

        return previous_wage * self.state.unemployment_benefit_rate

    def update_state(self, updates: dict[str, Any]):
        """
        状態を更新

        Args:
            updates: 更新する属性の辞書
        """
        for key, value in updates.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

        # 税制システムも更新
        if "income_tax_brackets" in updates:
            self.taxation = TaxationSystem(brackets=self.state.income_tax_brackets)
