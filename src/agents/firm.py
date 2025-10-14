"""
Firm Agent for SimCity Simulation

企業エージェント: 3つの意思決定を行う
1. 生産量・価格決定
2. 労働市場行動（雇用/解雇/賃金）
3. 投資決定（借入/資本購入）
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from src.agents.base_agent import BaseAgent, load_prompt_template
from src.llm.llm_interface import LLMInterface
from src.models.data_models import FirmProfile, GoodCategory
from src.models.economic_models import ProductionFunction


class FirmAgent(BaseAgent):
    """
    企業エージェント

    LLMを使用して3つの意思決定を行う:
    - 生産: 生産量と価格の決定
    - 労働: 雇用、解雇、賃金の決定
    - 投資: 借入と資本購入の決定
    """

    def __init__(
        self,
        profile: FirmProfile,
        llm_interface: LLMInterface,
        production_function: ProductionFunction | None = None,
        prompt_template_path: str | Path | None = None,
    ):
        """
        Args:
            profile: 企業プロファイル
            llm_interface: LLMインターフェース
            production_function: 生産関数（Noneの場合はデフォルト）
            prompt_template_path: プロンプトテンプレートのパス
        """
        # システムプロンプトの読み込み
        if prompt_template_path is None:
            prompt_template_path = (
                Path(__file__).parent.parent / "llm" / "prompts" / "firm_system.txt"
            )

        system_prompt = load_prompt_template(prompt_template_path)

        super().__init__(
            agent_id=f"firm_{profile.id}",
            agent_type="firm",
            llm_interface=llm_interface,
            system_prompt=system_prompt,
            memory_size=5,
        )

        self.profile = profile

        # 生産関数
        if production_function is None:
            self.production_function = ProductionFunction(
                alpha=0.33, tfp=profile.total_factor_productivity
            )
        else:
            self.production_function = production_function

        # 破産フラグ
        self.is_bankrupt = False
        self.negative_cash_months = 0  # 現金がマイナスの月数

        # 属性として保存
        self.attributes = {
            "profile_id": profile.id,
            "goods_type": profile.goods_type,
            "goods_category": profile.goods_category.value,
        }

        logger.info(
            f"FirmAgent created: id={profile.id}, "
            f"goods={profile.goods_type}, "
            f"capital={profile.capital:.2f}"
        )

    def get_profile_str(self) -> str:
        """
        プロフィール文字列を生成

        Returns:
            プロフィール文字列
        """
        # 雇用情報
        num_employees = len(self.profile.employees)
        employee_ids = (
            ", ".join(map(str, self.profile.employees[:5]))
            if self.profile.employees
            else "None"
        )
        if num_employees > 5:
            employee_ids += f" ... ({num_employees - 5} more)"

        # スキル要件
        skills_str = ", ".join(
            [f"{skill}: {level:.2f}" for skill, level in self.profile.skill_requirements.items()]
        )

        # 財務健全性
        cash_status = "Healthy" if self.profile.cash > 0 else "⚠️ NEGATIVE"
        debt_str = f"${self.profile.debt:.2f}" if self.profile.debt > 0 else "None"

        profile = f"""
Company: {self.profile.name}
ID: {self.profile.id}
Product: {self.profile.goods_type} (Category: {self.profile.goods_category.value})

Financial Status:
- Cash: ${self.profile.cash:.2f} ({cash_status})
- Debt: {debt_str}
- Capital: ${self.profile.capital:.2f}

Production:
- TFP (Productivity): {self.profile.total_factor_productivity:.2f}
- Inventory: {self.profile.inventory:.2f} units
- Current Price: ${self.profile.price:.2f}/unit
- Last Period Production: {self.profile.production_quantity:.2f} units
- Last Period Sales: {self.profile.sales_quantity:.2f} units

Employment:
- Employees: {num_employees} people
- Employee IDs: {employee_ids}
- Wage Offered: ${self.profile.wage_offered:.2f}/month
- Job Openings: {self.profile.job_openings}
- Skill Requirements: {skills_str}

Location: {self.profile.location}
"""
        return profile.strip()

    def get_available_actions(self) -> list[dict[str, Any]]:
        """
        利用可能な行動のリストを返す（OpenAI Function Calling形式）

        Returns:
            関数定義のリスト
        """
        return [
            # 生産・価格決定
            {
                "name": "decide_production",
                "description": "Decide production quantity and pricing for next period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_production": {
                            "type": "number",
                            "description": "Target production quantity for next period",
                        },
                        "price": {
                            "type": "number",
                            "description": "Product price per unit",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this production decision",
                        },
                    },
                    "required": ["target_production", "price", "reasoning"],
                },
            },
            # 労働市場行動
            {
                "name": "labor_decision",
                "description": "Make hiring, firing, or wage adjustment decisions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["hire", "fire", "adjust_wage", "maintain"],
                            "description": "Labor market action",
                        },
                        "target_employees": {
                            "type": "integer",
                            "description": "Target number of employees (for hire/fire)",
                        },
                        "job_openings": {
                            "type": "integer",
                            "description": "Number of job openings to post",
                        },
                        "wage_offered": {
                            "type": "number",
                            "description": "Wage to offer (for hire/adjust_wage)",
                        },
                        "fire_employee_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Employee IDs to fire (for fire action)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this labor decision",
                        },
                    },
                    "required": ["action", "reasoning"],
                },
            },
            # 投資決定
            {
                "name": "investment_decision",
                "description": "Decide on borrowing and capital investment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "borrow",
                                "repay_debt",
                                "invest_capital",
                                "do_nothing",
                            ],
                            "description": "Investment action",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount to borrow, repay, or invest",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this investment decision",
                        },
                    },
                    "required": ["action", "amount", "reasoning"],
                },
            },
        ]

    def _get_fallback_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        """
        LLM呼び出しが失敗した場合のフォールバック行動

        Args:
            observation: 環境からの観察情報

        Returns:
            デフォルトの行動（最も安全な選択）
        """
        # 現状維持の生産決定
        return {
            "function_name": "decide_production",
            "arguments": {
                "target_production": self.profile.production_quantity,
                "price": self.profile.price,
                "reasoning": "Fallback: Maintain current production level",
            },
        }

    def calculate_production_capacity(self) -> float:
        """
        現在の生産能力を計算（Cobb-Douglas）

        Returns:
            生産能力（最大生産量）
        """
        labor = len(self.profile.employees)
        if labor == 0:
            return 0.0

        # 効率的労働力（スキルマッチング考慮）
        # 簡略版: 実際のスキルマッチングはPhase 3で実装
        effective_labor = labor * 0.8  # 仮定: 平均80%の効率

        return self.production_function.calculate_output(
            labor=effective_labor,
            capital=self.profile.capital,
            tfp=self.profile.total_factor_productivity,
        )

    def check_bankruptcy(self) -> bool:
        """
        破産判定

        Returns:
            True: 破産, False: 正常
        """
        # 現金がマイナスかチェック
        if self.profile.cash < 0:
            self.negative_cash_months += 1
        else:
            self.negative_cash_months = 0

        # 3ヶ月連続でマイナスの場合、破産
        if self.negative_cash_months >= 3:
            self.is_bankrupt = True
            logger.warning(f"Firm {self.profile.id} ({self.profile.name}) is bankrupt!")
            return True

        return False

    def update_profile(self, updates: dict[str, Any]):
        """
        プロフィールを更新

        Args:
            updates: 更新する属性の辞書
        """
        for key, value in updates.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)


class FirmTemplateLoader:
    """企業テンプレートローダー"""

    @staticmethod
    def load_templates(
        template_path: str | Path | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        企業テンプレートをJSONから読み込む

        Args:
            template_path: テンプレートファイルのパス

        Returns:
            firm_id: テンプレート辞書のマッピング
        """
        if template_path is None:
            template_path = (
                Path(__file__).parent.parent / "data" / "firm_templates.json"
            )

        template_path = Path(template_path)

        if not template_path.exists():
            raise FileNotFoundError(f"Firm templates not found: {template_path}")

        with open(template_path, encoding="utf-8") as f:
            data = json.load(f)

        templates = {}
        for firm_data in data.get("firms", []):
            firm_id = firm_data["firm_id"]
            templates[firm_id] = firm_data

        logger.info(f"Loaded {len(templates)} firm templates")
        return templates

    @staticmethod
    def create_firm_profile(
        firm_id: str,
        template: dict[str, Any],
        location: tuple[int, int] = (50, 50),
    ) -> FirmProfile:
        """
        テンプレートから企業プロファイルを生成

        Args:
            firm_id: 企業ID（数値）
            template: 企業テンプレート
            location: 企業の位置

        Returns:
            企業プロファイル
        """
        # カテゴリの変換
        category_str = template["goods_category"]
        goods_category = GoodCategory(category_str)

        profile = FirmProfile(
            id=int(firm_id) if isinstance(firm_id, str) and firm_id.isdigit() else hash(firm_id) % 1000000,
            name=template["name"],
            goods_type=template["goods_type"],
            goods_category=goods_category,
            cash=template["initial_capital"],
            debt=0.0,
            capital=template["initial_capital"] * 0.5,  # 初期資本の半分を設備投資
            total_factor_productivity=template["tfp"],
            employees=[],
            inventory=0.0,
            price=100.0,  # デフォルト価格
            production_quantity=0.0,
            sales_quantity=0.0,
            wage_offered=template["initial_wage"],
            job_openings=5,  # 初期求人数
            skill_requirements=template["skill_requirements"],
            shareholders={},
            location=location,
        )

        return profile
