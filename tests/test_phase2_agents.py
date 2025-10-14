"""
Tests for Phase 2 Agents: Firm, Government, and Central Bank
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.central_bank import CentralBankAgent
from src.agents.firm import FirmAgent, FirmTemplateLoader
from src.agents.government import GovernmentAgent
from src.data.goods_types import GOODS, GOODS_MAP, get_all_good_ids, get_good
from src.data.skill_types import get_all_skill_ids
from src.llm.llm_interface import LLMInterface
from src.models.data_models import (
    CentralBankState,
    GoodCategory,
    GovernmentState,
)


class TestGoodsData:
    """財データのテスト"""

    def test_goods_count(self):
        """44種類の財が定義されているか"""
        assert len(GOODS) == 44

    def test_goods_categories(self):
        """全カテゴリが網羅されているか"""
        categories = {good.category for good in GOODS}
        assert len(categories) == 10  # 10カテゴリ

    def test_goods_map(self):
        """財マッピングが正しいか"""
        assert len(GOODS_MAP) == 44
        for good in GOODS:
            assert good.good_id in GOODS_MAP
            assert GOODS_MAP[good.good_id] == good

    def test_get_good(self):
        """個別財取得が正しいか"""
        food_basic = get_good("food_basic")
        assert food_basic is not None
        assert food_basic.name == "Basic Food"
        assert food_basic.category == GoodCategory.FOOD
        assert food_basic.is_necessity is True

    def test_necessity_vs_luxury(self):
        """必需品と奢侈品の分類"""
        necessities = [g for g in GOODS if g.is_necessity]
        luxuries = [g for g in GOODS if not g.is_necessity]

        assert len(necessities) > 0
        assert len(luxuries) > 0
        assert len(necessities) + len(luxuries) == 44

    def test_price_elasticity(self):
        """価格弾力性が負の値か"""
        for good in GOODS:
            assert good.price_elasticity < 0, f"{good.good_id} has positive elasticity"


class TestFirmTemplates:
    """企業テンプレートのテスト"""

    def test_load_templates(self):
        """テンプレート読み込み"""
        templates = FirmTemplateLoader.load_templates()

        # 44種類の企業テンプレート
        assert len(templates) == 44

        # 各テンプレートが必要な情報を持っているか
        for _firm_id, template in templates.items():
            assert "firm_id" in template
            assert "name" in template
            assert "goods_type" in template
            assert "goods_category" in template
            assert "initial_capital" in template
            assert "tfp" in template
            assert "initial_wage" in template
            assert "skill_requirements" in template

    def test_create_firm_profile(self):
        """企業プロファイル生成"""
        templates = FirmTemplateLoader.load_templates()
        template = templates["firm_food_basic"]

        profile = FirmTemplateLoader.create_firm_profile(
            firm_id="1", template=template, location=(10, 20)
        )

        assert profile.name == template["name"]
        assert profile.goods_type == template["goods_type"]
        assert profile.goods_category == GoodCategory.FOOD
        assert profile.cash == template["initial_capital"]
        assert profile.total_factor_productivity == template["tfp"]
        assert profile.wage_offered == template["initial_wage"]
        assert profile.location == (10, 20)

    def test_firm_goods_match(self):
        """企業が生産する財が存在するか"""
        templates = FirmTemplateLoader.load_templates()
        all_good_ids = get_all_good_ids()

        for firm_id, template in templates.items():
            goods_type = template["goods_type"]
            assert goods_type in all_good_ids, (
                f"Firm {firm_id} produces non-existent good: {goods_type}"
            )

    def test_firm_skills_exist(self):
        """企業のスキル要件が存在するスキルか"""
        templates = FirmTemplateLoader.load_templates()
        all_skill_ids = get_all_skill_ids()

        for firm_id, template in templates.items():
            for skill_id in template["skill_requirements"].keys():
                assert skill_id in all_skill_ids, (
                    f"Firm {firm_id} requires non-existent skill: {skill_id}"
                )


class TestFirmAgent:
    """FirmAgentのテスト"""

    @pytest.fixture
    def mock_llm(self):
        """モックLLMインターフェース"""
        llm = MagicMock(spec=LLMInterface)
        llm.function_call.return_value = {
            "function_name": "decide_production",
            "arguments": {
                "target_production": 100.0,
                "price": 120.0,
                "reasoning": "Test reasoning",
            },
            "raw_response": {},
        }
        llm.validate_response.return_value = (True, None)
        return llm

    @pytest.fixture
    def sample_firm_profile(self):
        """サンプル企業プロファイル"""
        templates = FirmTemplateLoader.load_templates()
        template = templates["firm_food_basic"]
        return FirmTemplateLoader.create_firm_profile("1", template)

    def test_firm_agent_initialization(self, sample_firm_profile, mock_llm):
        """FirmAgent初期化"""
        agent = FirmAgent(sample_firm_profile, mock_llm)

        assert agent.agent_id == f"firm_{sample_firm_profile.id}"
        assert agent.agent_type == "firm"
        assert agent.profile == sample_firm_profile
        assert agent.is_bankrupt is False

    def test_get_profile_str(self, sample_firm_profile, mock_llm):
        """プロフィール文字列生成"""
        agent = FirmAgent(sample_firm_profile, mock_llm)
        profile_str = agent.get_profile_str()

        assert sample_firm_profile.name in profile_str
        assert sample_firm_profile.goods_type in profile_str
        assert "Capital:" in profile_str
        assert "Employees:" in profile_str

    def test_get_available_actions(self, sample_firm_profile, mock_llm):
        """利用可能な行動リスト"""
        agent = FirmAgent(sample_firm_profile, mock_llm)
        actions = agent.get_available_actions()

        # 3つの行動が定義されているか
        assert len(actions) == 3

        action_names = [a["name"] for a in actions]
        expected_names = [
            "decide_production",
            "labor_decision",
            "investment_decision",
        ]

        for name in expected_names:
            assert name in action_names

    def test_production_capacity(self, sample_firm_profile, mock_llm):
        """生産能力計算"""
        sample_firm_profile.employees = [1, 2, 3]  # 3人の従業員
        sample_firm_profile.capital = 50000.0

        agent = FirmAgent(sample_firm_profile, mock_llm)
        capacity = agent.calculate_production_capacity()

        # Cobb-Douglas: Y = A * L^(1-α) * K^α
        # 生産能力が0より大きいことを確認
        assert capacity > 0

    def test_bankruptcy_check(self, sample_firm_profile, mock_llm):
        """破産判定"""
        agent = FirmAgent(sample_firm_profile, mock_llm)

        # 正常状態
        sample_firm_profile.cash = 10000.0
        assert agent.check_bankruptcy() is False

        # 現金がマイナス（1ヶ月目）
        sample_firm_profile.cash = -1000.0
        assert agent.check_bankruptcy() is False  # まだ破産ではない
        assert agent.negative_cash_months == 1

        # 2ヶ月連続マイナス
        assert agent.check_bankruptcy() is False
        assert agent.negative_cash_months == 2

        # 3ヶ月連続マイナス → 破産
        assert agent.check_bankruptcy() is True
        assert agent.is_bankrupt is True


class TestGovernmentAgent:
    """GovernmentAgentのテスト"""

    @pytest.fixture
    def mock_llm(self):
        """モックLLMインターフェース"""
        llm = MagicMock(spec=LLMInterface)
        llm.function_call.return_value = {
            "function_name": "maintain_policy",
            "arguments": {"reasoning": "Test reasoning"},
            "raw_response": {},
        }
        llm.validate_response.return_value = (True, None)
        return llm

    @pytest.fixture
    def government_state(self):
        """政府状態"""
        return GovernmentState(
            reserves=100000.0,
            tax_revenue=0.0,
            expenditure=0.0,
            income_tax_brackets=[
                (0, 0.0),
                (20000, 0.1),
                (50000, 0.2),
                (100000, 0.3),
            ],
            vat_rate=0.1,
            ubi_enabled=True,
            ubi_amount=500.0,
            unemployment_benefit_rate=0.5,
        )

    def test_government_agent_initialization(self, government_state, mock_llm):
        """GovernmentAgent初期化"""
        agent = GovernmentAgent(government_state, mock_llm)

        assert agent.agent_id == "government"
        assert agent.agent_type == "government"
        assert agent.state == government_state

    def test_get_available_actions(self, government_state, mock_llm):
        """利用可能な行動リスト"""
        agent = GovernmentAgent(government_state, mock_llm)
        actions = agent.get_available_actions()

        # 4つの行動が定義されているか
        assert len(actions) == 4

        action_names = [a["name"] for a in actions]
        expected_names = [
            "adjust_tax_policy",
            "adjust_welfare_policy",
            "public_investment",
            "maintain_policy",
        ]

        for name in expected_names:
            assert name in action_names

    def test_collect_income_tax(self, government_state, mock_llm):
        """所得税徴収"""
        agent = GovernmentAgent(government_state, mock_llm)

        # 低所得（税率0%）
        tax = agent.collect_income_tax(15000.0)
        assert tax == 0.0

        # 中所得（税率10%）
        tax = agent.collect_income_tax(30000.0)
        assert tax > 0
        assert tax < 30000.0 * 0.2  # 累進課税なので平均税率は低い

    def test_collect_vat(self, government_state, mock_llm):
        """VAT徴収"""
        agent = GovernmentAgent(government_state, mock_llm)

        transaction_value = 1000.0
        vat = agent.collect_vat(transaction_value)

        assert vat == transaction_value * 0.1  # 10% VAT

    def test_distribute_ubi(self, government_state, mock_llm):
        """UBI配布"""
        agent = GovernmentAgent(government_state, mock_llm)

        # UBI有効
        total_expenditure = agent.distribute_ubi(num_households=100)
        assert total_expenditure == 500.0 * 100  # $500 × 100世帯

        # UBI無効
        government_state.ubi_enabled = False
        total_expenditure = agent.distribute_ubi(num_households=100)
        assert total_expenditure == 0.0

    def test_unemployment_benefit(self, government_state, mock_llm):
        """失業給付計算"""
        agent = GovernmentAgent(government_state, mock_llm)

        previous_wage = 2000.0

        # 失業1ヶ月目
        benefit = agent.calculate_unemployment_benefit(
            previous_wage, months_unemployed=1
        )
        assert benefit == previous_wage * 0.5  # 50%

        # 失業6ヶ月目
        benefit = agent.calculate_unemployment_benefit(
            previous_wage, months_unemployed=6
        )
        assert benefit == previous_wage * 0.5

        # 失業7ヶ月目（給付終了）
        benefit = agent.calculate_unemployment_benefit(
            previous_wage, months_unemployed=7
        )
        assert benefit == 0.0


class TestCentralBankAgent:
    """CentralBankAgentのテスト"""

    @pytest.fixture
    def mock_llm(self):
        """モックLLMインターフェース"""
        llm = MagicMock(spec=LLMInterface)
        llm.function_call.return_value = {
            "function_name": "maintain_policy",
            "arguments": {"reasoning": "Test reasoning"},
            "raw_response": {},
        }
        llm.validate_response.return_value = (True, None)
        return llm

    @pytest.fixture
    def central_bank_state(self):
        """中央銀行状態"""
        return CentralBankState(
            policy_rate=0.02,
            natural_rate=0.02,
            inflation_target=0.02,
            taylor_alpha=1.5,
            taylor_beta=0.5,
            smoothing_factor=0.8,
            total_deposits=1000000.0,
            total_loans=800000.0,
            deposit_rate_spread=-0.01,
            loan_rate_spread=0.02,
        )

    def test_central_bank_agent_initialization(self, central_bank_state, mock_llm):
        """CentralBankAgent初期化"""
        agent = CentralBankAgent(central_bank_state, mock_llm)

        assert agent.agent_id == "central_bank"
        assert agent.agent_type == "central_bank"
        assert agent.state == central_bank_state

    def test_get_available_actions(self, central_bank_state, mock_llm):
        """利用可能な行動リスト"""
        agent = CentralBankAgent(central_bank_state, mock_llm)
        actions = agent.get_available_actions()

        # 3つの行動が定義されているか
        assert len(actions) == 3

        action_names = [a["name"] for a in actions]
        expected_names = ["set_policy_rate", "adjust_spreads", "maintain_policy"]

        for name in expected_names:
            assert name in action_names

    def test_calculate_target_rate(self, central_bank_state, mock_llm):
        """Taylor rule目標金利計算"""
        agent = CentralBankAgent(central_bank_state, mock_llm)

        # 正常な経済状態（インフレ=目標、産出ギャップ=0）
        target_rate = agent.calculate_target_rate(
            inflation=0.02, gdp=1000000.0, potential_gdp=1000000.0
        )

        # Taylor rule: r = r^n + π^t + α(π - π^t) + β * output_gap
        # = 0.02 + 0.02 + 0 + 0 = 0.04
        assert abs(target_rate - 0.04) < 0.01

        # インフレが高い場合
        target_rate_high_inflation = agent.calculate_target_rate(
            inflation=0.05, gdp=1000000.0, potential_gdp=1000000.0
        )

        # 金利が上昇するはず
        assert target_rate_high_inflation > target_rate

    def test_update_policy_rate_with_smoothing(self, central_bank_state, mock_llm):
        """金利平滑化付き更新"""
        agent = CentralBankAgent(central_bank_state, mock_llm)

        current_rate = central_bank_state.policy_rate  # 0.02
        target_rate = 0.05  # 大きく異なる目標

        # 平滑化あり
        new_rate = agent.update_policy_rate(target_rate, use_smoothing=True)

        # 平滑化により、目標との中間値になる
        assert new_rate > current_rate
        assert new_rate < target_rate

    def test_update_policy_rate_without_smoothing(self, central_bank_state, mock_llm):
        """金利平滑化なし更新"""
        agent = CentralBankAgent(central_bank_state, mock_llm)

        target_rate = 0.05

        # 平滑化なし
        new_rate = agent.update_policy_rate(target_rate, use_smoothing=False)

        # 目標値そのままになる
        assert new_rate == target_rate

    def test_get_current_rates(self, central_bank_state, mock_llm):
        """金利構造取得"""
        agent = CentralBankAgent(central_bank_state, mock_llm)

        rates = agent.get_current_rates()

        assert "policy_rate" in rates
        assert "deposit_rate" in rates
        assert "loan_rate" in rates

        # 預金金利 < 政策金利 < 貸出金利
        assert rates["deposit_rate"] < rates["policy_rate"]
        assert rates["policy_rate"] < rates["loan_rate"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
