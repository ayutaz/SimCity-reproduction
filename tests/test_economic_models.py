"""
Tests for economic models

経済モデルの単体テスト
"""

import pytest

from src.models.economic_models import (
    MacroeconomicIndicators,
    ProductionFunction,
    TaxationSystem,
    TaylorRule,
    calculate_effective_labor,
)


class TestProductionFunction:
    """Cobb-Douglas生産関数のテスト"""

    def test_basic_output(self):
        """基本的な産出計算"""
        prod = ProductionFunction(alpha=0.33, tfp=1.0)

        # Y = 1.0 * 10^0.67 * 100^0.33 ≈ 21.5
        output = prod.calculate_output(labor=10, capital=100)

        assert output > 0
        assert 20 < output < 25

    def test_zero_inputs(self):
        """ゼロ投入のケース"""
        prod = ProductionFunction()

        assert prod.calculate_output(0, 0) == 0.0
        assert prod.calculate_output(0, 100) == 0.0
        assert prod.calculate_output(10, 0) == 0.0

    def test_marginal_products(self):
        """限界生産物の計算"""
        prod = ProductionFunction(alpha=0.33, tfp=1.0)

        mpl = prod.calculate_marginal_product_labor(10, 100)
        mpk = prod.calculate_marginal_product_capital(10, 100)

        assert mpl > 0
        assert mpk > 0


class TestTaxationSystem:
    """累進課税システムのテスト"""

    def test_no_tax_below_threshold(self):
        """閾値以下は非課税"""
        tax_system = TaxationSystem(
            [(0, 0.0), (20000, 0.1), (50000, 0.2), (100000, 0.3)]
        )

        assert tax_system.calculate_income_tax(10000) == 0.0

    def test_progressive_taxation(self):
        """累進課税の動作"""
        tax_system = TaxationSystem(
            [(0, 0.0), (20000, 0.1), (50000, 0.2), (100000, 0.3)]
        )

        # 所得30000の場合
        # 0-20000: 0円
        # 20000-30000: (30000-20000) * 0.1 = 1000円
        tax = tax_system.calculate_income_tax(30000)
        assert tax == pytest.approx(1000)

    def test_effective_rate(self):
        """実効税率の計算"""
        tax_system = TaxationSystem(
            [(0, 0.0), (20000, 0.1), (50000, 0.2)]
        )

        effective_rate = tax_system.calculate_effective_rate(30000)
        assert 0 < effective_rate < 0.1


class TestTaylorRule:
    """Taylor ruleのテスト"""

    def test_basic_rate(self):
        """基本的な金利計算"""
        taylor = TaylorRule(
            natural_rate=0.02,
            inflation_target=0.02,
            alpha=1.5,
            beta=0.5,
        )

        # インフレ目標達成、GDPギャップなしの場合
        target_rate = taylor.calculate_target_rate(
            inflation=0.02, gdp=100, potential_gdp=100
        )

        # r̂ = 0.02 + 0.02 + 1.5*(0.02-0.02) + 0.5*0 = 0.04
        assert target_rate == pytest.approx(0.04)

    def test_high_inflation_response(self):
        """高インフレへの反応"""
        taylor = TaylorRule(alpha=1.5)

        # インフレが目標を超えた場合
        target_rate = taylor.calculate_target_rate(
            inflation=0.05, gdp=100, potential_gdp=100
        )

        # 金利は上昇するべき
        assert target_rate > 0.04

    def test_interest_rate_smoothing(self):
        """金利平滑化のテスト"""
        taylor = TaylorRule(smoothing_factor=0.8)

        target = 0.05
        previous = 0.02

        smoothed = taylor.smooth_rate(target, previous)

        # 0.8*0.02 + 0.2*0.05 = 0.026
        assert smoothed == pytest.approx(0.026)

    def test_non_negative_constraint(self):
        """非負制約のテスト"""
        taylor = TaylorRule()

        # マイナスになりうる条件でも0以上
        target_rate = taylor.calculate_target_rate(
            inflation=-0.05, gdp=50, potential_gdp=100
        )

        assert target_rate >= 0.0


class TestMacroeconomicIndicators:
    """マクロ経済指標計算のテスト"""

    def test_gdp_calculation(self):
        """GDP計算"""
        household_incomes = [1000, 2000, 3000]
        firm_outputs = [5000, 3000]
        government_spending = 2000

        gdp = MacroeconomicIndicators.calculate_gdp(
            household_incomes, firm_outputs, government_spending
        )

        # 1000+2000+3000 + 5000+3000 + 2000 = 16000
        assert gdp == 16000

    def test_inflation_calculation(self):
        """インフレ率計算"""
        prev_prices = {"food": 100, "clothing": 200}
        curr_prices = {"food": 105, "clothing": 210}

        inflation = MacroeconomicIndicators.calculate_inflation(
            curr_prices, prev_prices
        )

        # (105-100)/100 = 5%, (210-200)/200 = 5%
        # 平均 5%
        assert inflation == pytest.approx(0.05)

    def test_unemployment_rate(self):
        """失業率計算"""
        unemployment_rate = MacroeconomicIndicators.calculate_unemployment_rate(
            total_labor_force=100, employed=92
        )

        assert unemployment_rate == pytest.approx(0.08)  # 8%

    def test_gini_coefficient(self):
        """Gini係数計算"""
        # 完全平等
        equal_incomes = [1000, 1000, 1000, 1000]
        gini_equal = MacroeconomicIndicators.calculate_gini_coefficient(equal_incomes)
        assert gini_equal == pytest.approx(0.0, abs=0.01)

        # 不平等
        unequal_incomes = [1000, 2000, 5000, 10000]
        gini_unequal = MacroeconomicIndicators.calculate_gini_coefficient(
            unequal_incomes
        )
        assert 0 < gini_unequal < 1


class TestEffectiveLabor:
    """実効労働量計算のテスト"""

    def test_no_skill_requirements(self):
        """スキル要件なしの場合"""
        workers = [{"skill_a": 0.5}, {"skill_b": 0.8}]
        skill_requirements = {}

        effective_labor = calculate_effective_labor(workers, skill_requirements)

        # スキル要件なし => 効率1.0 × 2人 = 2.0
        assert effective_labor == 2.0

    def test_perfect_match(self):
        """完全マッチの場合"""
        workers = [{"programming": 0.9}, {"programming": 0.8}]
        skill_requirements = {"programming": 0.5}

        effective_labor = calculate_effective_labor(workers, skill_requirements)

        # 両者とも要件を満たす => 約2.0
        assert 1.8 < effective_labor <= 2.0

    def test_partial_match(self):
        """部分マッチの場合"""
        workers = [{"programming": 0.3}, {"programming": 0.5}]
        skill_requirements = {"programming": 0.8}

        effective_labor = calculate_effective_labor(workers, skill_requirements)

        # スキルレベルが要件より低い => 2.0より小さい
        assert 0 < effective_labor < 2.0


def test_data_models_serialization():
    """データモデルのシリアライズテスト"""
    from src.models.data_models import (
        EducationLevel,
        EmploymentStatus,
        HouseholdProfile,
    )

    # 家計プロファイル作成
    household = HouseholdProfile(
        id=1,
        name="Test Family",
        age=35,
        education_level=EducationLevel.COLLEGE,
        skills={"programming": 0.8},
        cash=10000,
        employment_status=EmploymentStatus.EMPLOYED,
    )

    # 辞書に変換
    data_dict = household.to_dict()
    assert data_dict["id"] == 1
    assert data_dict["name"] == "Test Family"

    # 辞書から復元
    restored = HouseholdProfile.from_dict(data_dict)
    assert restored.id == household.id
    assert restored.name == household.name
    assert restored.education_level == household.education_level


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
