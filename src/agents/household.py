"""
Household Agent for SimCity Simulation

世帯エージェント: 4つの意思決定を行う
1. 消費バンドル決定
2. 労働市場行動（求職/受諾/辞職）
3. 住居選択
4. 金融意思決定（貯蓄/借入/投資）
"""

import random
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from src.agents.base_agent import BaseAgent, load_prompt_template
from src.data.skill_types import calculate_wage_multiplier, get_all_skill_ids
from src.llm.llm_interface import LLMInterface
from src.models.data_models import (
    EducationLevel,
    EmploymentStatus,
    GoodCategory,
    HouseholdProfile,
)


class HouseholdAgent(BaseAgent):
    """
    世帯エージェント

    LLMを使用して4つの意思決定を行う:
    - 消費: どの財をどれだけ購入するか
    - 労働: 求職、就職、辞職の判断
    - 住居: 住居の選択
    - 金融: 貯蓄、借入、投資の判断
    """

    def __init__(
        self,
        household_id: str | None = None,
        profile: HouseholdProfile | None = None,
        llm_interface: LLMInterface | None = None,
        prompt_template_path: str | Path | None = None,
    ):
        """
        Args:
            household_id: 世帯ID（後方互換性のため）
            profile: 世帯プロファイル
            llm_interface: LLMインターフェース
            prompt_template_path: プロンプトテンプレートのパス
        """
        # 後方互換性: household_idが渡された場合、profileから取得
        if profile is None:
            raise ValueError("profile is required")

        # システムプロンプトの読み込み
        if prompt_template_path is None:
            prompt_template_path = (
                Path(__file__).parent.parent
                / "llm"
                / "prompts"
                / "household_system.txt"
            )

        system_prompt = load_prompt_template(prompt_template_path)

        # Phase 10.1: 決定頻度の最適化（OPTIMIZATION.md Phase 1）
        decision_frequencies = {
            "housing": 12,  # 12ステップごと（1年）
            "skill_investment": 6,  # 6ステップごと（半年）
            # savings: ヒューリスティック（heuristic_savings_decision使用）
        }

        super().__init__(
            agent_id=f"household_{profile.id}",
            agent_type="household",
            llm_interface=llm_interface,
            system_prompt=system_prompt,
            memory_size=5,
            decision_frequencies=decision_frequencies,
        )

        self.profile = profile

        # Phase 7.3.1: ヒューリスティック貯蓄率（最適化）
        self.heuristic_savings_rate = 0.15  # デフォルト15%

        # 初期化時にデータから属性を設定
        self.income = getattr(profile, "monthly_income", 50000.0)
        self.consumption = getattr(profile, "cash", 50000.0) * 0.1  # 10%を消費
        self.food_expenditure = self.consumption * 0.3  # 消費の30%を食料

        # Phase 8.1: 月間支出追跡（経済現象検証用）
        self.total_spending = 0.0  # 月間総支出
        self.food_spending = 0.0  # 月間食料支出
        self.purchased_goods = {}  # 購入した財 {good_id: quantity}

        # Phase 8.1: LLM消費決定の保存（財市場で使用）
        self.pending_consumption_decision = None  # {good_id: quantity} の辞書

        # Phase 10.3: 静的プロファイル部分をキャッシュ
        self._static_profile_cached = False
        self._cache_static_profile_info()

        # 属性として保存（enum or string対応）
        education_value = (
            profile.education_level.value
            if hasattr(profile.education_level, "value")
            else profile.education_level
        )
        employment_value = (
            profile.employment_status.value
            if hasattr(profile.employment_status, "value")
            else profile.employment_status
        )

        self.attributes = {
            "profile_id": profile.id,
            "age": profile.age,
            "education": education_value,
            "employment_status": employment_value,
        }

        logger.info(
            f"HouseholdAgent created: id={profile.id}, "
            f"age={profile.age}, education={education_value}"
        )

    def _get_enum_value(self, field):
        """Helper to safely get enum value (handles both enum and string)"""
        if isinstance(field, str):
            return field
        return field.value if hasattr(field, "value") else str(field)

    def _cache_static_profile_info(self):
        """
        静的プロファイル情報をキャッシュ（Phase 10.3）

        名前、年齢、教育レベル、スキルなど変わらない情報を事前にフォーマット
        """
        if not hasattr(self.llm, "cache_static_content"):
            return

        # スキル情報
        skills_str = ", ".join(
            [f"{skill}: {level:.2f}" for skill, level in self.profile.skills.items()]
        )
        if not skills_str:
            skills_str = "None"

        static_info = f"""Name: {self.profile.name}
Age: {self.profile.age}
Education: {self._get_enum_value(self.profile.education_level)}
Skills: {skills_str}"""

        cache_key = f"profile_household_{self.profile.id}"
        self.llm.cache_static_content(cache_key, static_info)
        self._static_profile_cached = True

    def get_profile_str(self) -> str:
        """
        プロフィール文字列を生成

        Returns:
            プロフィール文字列
        """
        # スキル情報
        skills_str = ", ".join(
            [f"{skill}: {level:.2f}" for skill, level in self.profile.skills.items()]
        )
        if not skills_str:
            skills_str = "None"

        # 雇用状態
        employment_str = self._get_enum_value(self.profile.employment_status)
        employment_status_enum = (
            EmploymentStatus(self.profile.employment_status)
            if isinstance(self.profile.employment_status, str)
            else self.profile.employment_status
        )
        if employment_status_enum == EmploymentStatus.EMPLOYED:
            employment_str += f" (wage: ${self.profile.wage:.2f}/month)"

        # 予算計算
        available_budget = self.profile.cash + self.profile.monthly_income
        debt_str = f"${self.profile.debt:.2f}" if self.profile.debt > 0 else "None"

        profile = f"""
Name: {self.profile.name}
Age: {self.profile.age}
Education: {self._get_enum_value(self.profile.education_level)}
Skills: {skills_str}

Financial Status:
- Cash: ${self.profile.cash:.2f}
- Savings: ${self.profile.savings:.2f}
- Monthly Income: ${self.profile.monthly_income:.2f}
- Debt: {debt_str}
- Available Budget: ${available_budget:.2f}

Employment:
- Status: {employment_str}
- Employer ID: {self.profile.employer_id if self.profile.employer_id else "None"}

Housing:
- Location: {self.profile.location}
- Housing Cost: ${self.profile.housing_cost:.2f}/month

Consumption Preferences:
{self._format_preferences()}
"""
        return profile.strip()

    def _format_preferences(self) -> str:
        """消費嗜好をフォーマット"""
        if not self.profile.consumption_preferences:
            return "- Not yet determined"

        lines = []
        for category, pref in self.profile.consumption_preferences.items():
            lines.append(f"- {category}: {pref:.2f}")
        return "\n".join(lines)

    def get_integrated_action_function(self) -> dict[str, Any]:
        """
        統合意思決定用のFunction Calling定義（Phase 10.2: 最適化）

        1回の呼び出しで複数の決定を取得

        Returns:
            統合関数定義
        """
        return {
            "name": "decide_all_integrated",
            "description": "Make all household decisions in a single call (consumption, labor, housing, finance)",
            "parameters": {
                "type": "object",
                "properties": {
                    # 消費決定
                    "consumption": {
                        "type": "object",
                        "properties": {
                            "goods": {
                                "type": "object",
                                "description": "Goods to purchase with quantities",
                                "additionalProperties": {"type": "number"},
                            },
                            "reasoning": {"type": "string"},
                        },
                        "required": ["goods", "reasoning"],
                    },
                    # 労働決定
                    "labor": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["find_job", "accept_offer", "resign", "stay"],
                            },
                            "target_wage": {"type": "number"},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["action", "reasoning"],
                    },
                    # 住居決定（頻度制御により12ステップごと）
                    "housing": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "minItems": 2,
                                "maxItems": 2,
                            },
                            "max_rent": {"type": "number"},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["location", "max_rent", "reasoning"],
                    },
                    # 金融決定（貯蓄はヒューリスティック）
                    "finance": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "save",
                                    "withdraw",
                                    "borrow",
                                    "repay_debt",
                                    "invest",
                                    "do_nothing",
                                ],
                            },
                            "amount": {"type": "number"},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["action", "amount", "reasoning"],
                    },
                    # スキル投資決定（頻度制御により6ステップごと）
                    "skill_investment": {
                        "type": "object",
                        "properties": {
                            "skill_to_improve": {"type": "string"},
                            "investment_amount": {"type": "number"},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["reasoning"],
                    },
                },
                "required": ["consumption", "labor"],  # 必須は毎ステップの決定のみ
            },
        }

    def get_available_actions(self) -> list[dict[str, Any]]:
        """
        利用可能な行動のリストを返す（OpenAI Function Calling形式）

        Phase 10.2: 統合関数も利用可能にする

        Returns:
            関数定義のリスト
        """
        return [
            # Phase 10.2: 統合意思決定関数
            self.get_integrated_action_function(),
            # 以下は後方互換性のため残す
            # 消費バンドル決定
            {
                "name": "decide_consumption",
                "description": "Decide which goods to purchase and in what quantities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goods": {
                            "type": "object",
                            "description": "Goods to purchase with quantities",
                            "additionalProperties": {"type": "number"},
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this consumption decision",
                        },
                    },
                    "required": ["goods", "reasoning"],
                },
            },
            # 労働市場行動
            {
                "name": "labor_action",
                "description": "Take action in the labor market (find job, accept offer, resign)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["find_job", "accept_offer", "resign", "stay"],
                            "description": "Labor market action to take",
                        },
                        "target_wage": {
                            "type": "number",
                            "description": "Target wage if finding job (optional)",
                        },
                        "job_offer_id": {
                            "type": "integer",
                            "description": "Job offer ID if accepting (optional)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this decision",
                        },
                    },
                    "required": ["action", "reasoning"],
                },
            },
            # 住居選択
            {
                "name": "choose_housing",
                "description": "Choose housing location and type",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                            "description": "Desired location [x, y] coordinates",
                        },
                        "max_rent": {
                            "type": "number",
                            "description": "Maximum acceptable monthly rent",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this housing choice",
                        },
                    },
                    "required": ["location", "max_rent", "reasoning"],
                },
            },
            # 金融意思決定
            {
                "name": "financial_decision",
                "description": "Make financial decisions (save, borrow, invest)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "save",
                                "withdraw",
                                "borrow",
                                "repay_debt",
                                "invest",
                                "do_nothing",
                            ],
                            "description": "Financial action to take",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount of money for this action",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for this financial decision",
                        },
                    },
                    "required": ["action", "amount", "reasoning"],
                },
            },
            # 需要修正（消費嗜好の更新）
            {
                "name": "modify_needs",
                "description": "Modify consumption preferences based on experience",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preferences": {
                            "type": "object",
                            "description": "Updated consumption preferences by category",
                            "additionalProperties": {"type": "number"},
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for modifying preferences",
                        },
                    },
                    "required": ["preferences", "reasoning"],
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
        # 雇用状態に応じてフォールバック
        employment_status = (
            EmploymentStatus(self.profile.employment_status)
            if isinstance(self.profile.employment_status, str)
            else self.profile.employment_status
        )
        if employment_status == EmploymentStatus.UNEMPLOYED:
            return {
                "function_name": "labor_action",
                "arguments": {
                    "action": "find_job",
                    "target_wage": 1500.0,
                    "reasoning": "Fallback: Looking for employment",
                },
            }
        else:
            # 最小限の消費
            return {
                "function_name": "decide_consumption",
                "arguments": {
                    "goods": {"food": 10.0},  # 最低限の食料
                    "reasoning": "Fallback: Minimal consumption",
                },
            }

    def process_integrated_decision(
        self, decision: dict[str, Any], step: int
    ) -> list[dict[str, Any]]:
        """
        統合意思決定の結果を処理（Phase 10.2: 最適化）

        decide_all_integrated関数の出力を個別の行動に分解して返す

        Args:
            decision: 統合意思決定の結果（decide_all_integratedの出力）
            step: 現在のステップ数

        Returns:
            個別行動のリスト
        """
        actions = []

        # 消費決定（必須）
        if "consumption" in decision:
            actions.append(
                {
                    "function_name": "decide_consumption",
                    "arguments": decision["consumption"],
                }
            )

        # 労働決定（必須）
        if "labor" in decision:
            actions.append(
                {
                    "function_name": "labor_action",
                    "arguments": decision["labor"],
                }
            )

        # 住居決定（頻度制御により12ステップごと）
        if "housing" in decision and self.should_make_decision("housing", step):
            actions.append(
                {
                    "function_name": "choose_housing",
                    "arguments": decision["housing"],
                }
            )

        # 金融決定（貯蓄はヒューリスティック）
        if "finance" in decision:
            actions.append(
                {
                    "function_name": "financial_decision",
                    "arguments": decision["finance"],
                }
            )

        # スキル投資決定（頻度制御により6ステップごと）
        if "skill_investment" in decision and self.should_make_decision(
            "skill_investment", step
        ):
            # skill_to_improveとinvestment_amountが指定されている場合のみ
            if decision["skill_investment"].get("skill_to_improve"):
                actions.append(
                    {
                        "function_name": "modify_needs",  # スキル投資用の代替関数
                        "arguments": {
                            "preferences": {},  # 空の嗜好更新
                            "reasoning": decision["skill_investment"]["reasoning"],
                        },
                    }
                )

        return actions

    def decide_primary_action(
        self, observation: dict[str, Any], step: int
    ) -> dict[str, Any]:
        """
        主要な意思決定を実行

        Phase 10.2対応: 統合意思決定の結果を処理できるように拡張

        Args:
            observation: 環境からの観察情報
            step: 現在のステップ数

        Returns:
            決定した行動（または統合決定の最初の行動）
        """
        decision = self.decide_action(observation, step)

        # Phase 10.2: 統合意思決定の場合は処理して最初の行動を返す
        if decision.get("function_name") == "decide_all_integrated":
            actions = self.process_integrated_decision(
                decision["arguments"], step
            )
            # 最初の行動を返す（後続の行動はメモリに保存）
            if actions:
                # 残りの行動をメモリに記録
                for action in actions[1:]:
                    self.memory.append(
                        {
                            "step": step,
                            "action": action["function_name"],
                            "arguments": action["arguments"],
                            "observation": observation,
                        }
                    )
                return actions[0]

        return decision

    def update_profile(self, updates: dict[str, Any]):
        """
        プロフィールを更新

        Args:
            updates: 更新する属性の辞書
        """
        for key, value in updates.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)

        # 属性も更新
        if "age" in updates:
            self.attributes["age"] = updates["age"]
        if "employment_status" in updates:
            self.attributes["employment_status"] = self._get_enum_value(
                updates["employment_status"]
            )

    def heuristic_savings_decision(self, current_step: int) -> dict[str, Any]:
        """
        ヒューリスティック貯蓄決定（Phase 7.3.1: 最適化）

        LLMを使わずに、単純なルールベースで貯蓄額を計算します。

        Args:
            current_step: 現在のステップ

        Returns:
            貯蓄決定の辞書
        """
        # 所得の15%を貯蓄
        savings_amount = self.income * self.heuristic_savings_rate

        # 現金が不足している場合は貯蓄しない
        if self.profile.cash < savings_amount:
            savings_amount = 0.0

        return {
            "function_name": "financial_decision",
            "arguments": {
                "action": "save" if savings_amount > 0 else "do_nothing",
                "amount": savings_amount,
                "reasoning": f"Heuristic: Save {self.heuristic_savings_rate:.0%} of monthly income",
            },
        }

    def reset_monthly_spending(self):
        """
        月間支出をリセット（Phase 8.1: 経済現象検証用）

        毎月のステップ開始時に呼び出される
        """
        self.total_spending = 0.0
        self.food_spending = 0.0
        self.purchased_goods = {}

    def record_purchase(self, good_id: str, quantity: float, price: float):
        """
        購入を記録（Phase 8.1: 経済現象検証用）

        Args:
            good_id: 財のID
            quantity: 購入数量
            price: 単価
        """
        cost = quantity * price
        self.total_spending += cost

        # 食料財の判定（good_idに"food"が含まれる場合）
        if "food" in good_id.lower():
            self.food_spending += cost

        # 購入数量を記録
        if good_id in self.purchased_goods:
            self.purchased_goods[good_id] += quantity
        else:
            self.purchased_goods[good_id] = quantity


class HouseholdProfileGenerator:
    """
    世帯プロファイル生成器

    Lognormal分布を使用して所得・年齢分布を生成
    """

    def __init__(
        self,
        income_mean: float = 10.5,  # log(income)の平均
        income_std: float = 0.5,  # log(income)の標準偏差
        age_mean: float = 40.0,
        age_std: float = 12.0,
        random_seed: int | None = None,
    ):
        """
        Args:
            income_mean: 所得の対数の平均値
            income_std: 所得の対数の標準偏差
            age_mean: 年齢の平均
            age_std: 年齢の標準偏差
            random_seed: 乱数シード
        """
        self.income_mean = income_mean
        self.income_std = income_std
        self.age_mean = age_mean
        self.age_std = age_std

        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)

        self.next_id = 1

    def generate(self, count: int = 1) -> list[HouseholdProfile]:
        """
        世帯プロファイルを生成

        Args:
            count: 生成する世帯数

        Returns:
            世帯プロファイルのリスト
        """
        profiles = []

        for _ in range(count):
            profile = self._generate_single()
            profiles.append(profile)
            self.next_id += 1

        logger.info(f"Generated {count} household profiles")
        return profiles

    def _generate_single(self) -> HouseholdProfile:
        """単一の世帯プロファイルを生成"""
        # ID
        household_id = self.next_id

        # 名前
        name = f"Household_{household_id}"

        # 年齢（正規分布、20-70歳に制限）
        age = int(np.clip(np.random.normal(self.age_mean, self.age_std), 20, 70))

        # 教育レベル（年齢に応じて決定）
        if age < 25:
            # 若い世代は大卒が多い
            education_weights = [0.2, 0.5, 0.3]  # high_school, college, graduate
        elif age < 40:
            education_weights = [0.3, 0.5, 0.2]
        else:
            education_weights = [0.4, 0.4, 0.2]

        education_level = random.choices(
            [
                EducationLevel.HIGH_SCHOOL,
                EducationLevel.COLLEGE,
                EducationLevel.GRADUATE,
            ],
            weights=education_weights,
        )[0]

        # スキル（教育レベルに応じて2-5個）
        skill_count = {
            EducationLevel.HIGH_SCHOOL: random.randint(2, 3),
            EducationLevel.COLLEGE: random.randint(3, 4),
            EducationLevel.GRADUATE: random.randint(4, 5),
        }[education_level]

        all_skill_ids = get_all_skill_ids()
        selected_skills = random.sample(all_skill_ids, skill_count)

        skills = {}
        for skill_id in selected_skills:
            # スキルレベル（教育レベルに応じて調整）
            base_level = {
                EducationLevel.HIGH_SCHOOL: 0.4,
                EducationLevel.COLLEGE: 0.6,
                EducationLevel.GRADUATE: 0.7,
            }[education_level]

            level = np.clip(np.random.normal(base_level, 0.15), 0.2, 1.0)
            skills[skill_id] = level

        # 初期所得（Lognormal分布）
        log_income = np.random.normal(self.income_mean, self.income_std)
        initial_cash = np.exp(log_income)

        # 貯蓄（所得の0-20%）
        savings = initial_cash * random.uniform(0, 0.2)

        # 月収（スキルベースで計算）
        base_monthly_income = 2000.0
        wage_multiplier = calculate_wage_multiplier(skills)
        monthly_income = base_monthly_income * wage_multiplier

        # 雇用状態（Phase 9.9.4修正: Enum使用に統一）
        # 全員失業状態で開始し、労働市場でマッチング
        employment_status = EmploymentStatus.UNEMPLOYED
        employer_id = None
        wage = 0.0
        monthly_income = (
            0.0  # 失業中は収入なし（reservation_wage計算で最低希望賃金1000になる）
        )

        # 消費嗜好（ランダム、合計が1になるように正規化）
        preferences = {}
        for category in GoodCategory:
            preferences[category.value] = random.uniform(0.5, 1.5)

        total = sum(preferences.values())
        preferences = {k: v / total for k, v in preferences.items()}

        # 住居（ランダムな位置）
        location = (random.randint(0, 99), random.randint(0, 99))
        housing_cost = monthly_income * random.uniform(0.2, 0.3)  # 収入の20-30%

        # 負債（30%の確率で負債あり）
        debt = initial_cash * random.uniform(0, 0.5) if random.random() < 0.3 else 0.0

        profile = HouseholdProfile(
            id=household_id,
            name=name,
            age=age,
            education_level=education_level,
            skills=skills,
            cash=initial_cash,
            savings=savings,
            debt=debt,
            monthly_income=monthly_income,
            employment_status=employment_status,
            employer_id=employer_id,
            wage=wage,
            consumption_preferences=preferences,
            location=location,
            housing_cost=housing_cost,
            stock_holdings={},
        )

        return profile
