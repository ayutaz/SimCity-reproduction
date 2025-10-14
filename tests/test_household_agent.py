"""
Tests for HouseholdAgent and HouseholdProfileGenerator
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.household import HouseholdAgent, HouseholdProfileGenerator
from src.llm.llm_interface import LLMInterface
from src.models.data_models import EducationLevel, EmploymentStatus


class TestHouseholdProfileGenerator:
    """HouseholdProfileGeneratorのテスト"""

    def test_generate_single_profile(self):
        """単一プロファイル生成のテスト"""
        generator = HouseholdProfileGenerator(random_seed=42)
        profiles = generator.generate(count=1)

        assert len(profiles) == 1
        profile = profiles[0]

        # 基本属性のチェック
        assert profile.id == 1
        assert profile.name == "Household_1"
        assert 20 <= profile.age <= 70
        assert isinstance(profile.education_level, EducationLevel)

        # スキルのチェック
        assert len(profile.skills) >= 2
        assert len(profile.skills) <= 5
        for _, level in profile.skills.items():
            assert 0.0 <= level <= 1.0

        # 財務状態のチェック
        assert profile.cash > 0
        assert profile.savings >= 0
        assert profile.debt >= 0
        assert profile.monthly_income >= 0

        # 雇用状態のチェック
        assert isinstance(profile.employment_status, EmploymentStatus)
        if profile.employment_status == EmploymentStatus.EMPLOYED:
            assert profile.employer_id is not None
            assert profile.wage > 0
        else:
            assert profile.employer_id is None
            assert profile.wage == 0

        # 消費嗜好のチェック
        assert len(profile.consumption_preferences) > 0
        total_pref = sum(profile.consumption_preferences.values())
        assert abs(total_pref - 1.0) < 0.01  # 合計が約1

        # 住居のチェック
        assert len(profile.location) == 2
        assert 0 <= profile.location[0] < 100
        assert 0 <= profile.location[1] < 100
        assert profile.housing_cost >= 0

    def test_generate_multiple_profiles(self):
        """複数プロファイル生成のテスト"""
        generator = HouseholdProfileGenerator(random_seed=42)
        profiles = generator.generate(count=10)

        assert len(profiles) == 10

        # IDがユニークかチェック
        ids = [p.id for p in profiles]
        assert len(ids) == len(set(ids))

        # 次のIDが正しく更新されているか
        assert generator.next_id == 11

    def test_lognormal_distribution(self):
        """Lognormal分布に従っているかテスト"""
        generator = HouseholdProfileGenerator(
            income_mean=10.0, income_std=0.5, random_seed=42
        )
        profiles = generator.generate(count=100)

        # 所得（cash）の分布をチェック
        incomes = [p.cash for p in profiles]

        # 対数をとって正規分布に近いか確認
        log_incomes = np.log(incomes)
        mean = np.mean(log_incomes)
        std = np.std(log_incomes)

        # 平均が設定値に近いか（誤差10%以内）
        assert abs(mean - 10.0) < 1.0

        # 標準偏差が設定値に近いか（誤差50%以内）
        assert abs(std - 0.5) < 0.25

    def test_age_distribution(self):
        """年齢分布のテスト"""
        generator = HouseholdProfileGenerator(age_mean=40.0, age_std=12.0, random_seed=42)
        profiles = generator.generate(count=100)

        ages = [p.age for p in profiles]

        # 全ての年齢が範囲内
        assert all(20 <= age <= 70 for age in ages)

        # 平均が設定値に近いか
        mean_age = np.mean(ages)
        assert abs(mean_age - 40.0) < 5.0

    def test_education_distribution(self):
        """教育レベル分布のテスト"""
        generator = HouseholdProfileGenerator(random_seed=42)
        profiles = generator.generate(count=100)

        education_counts = dict.fromkeys(EducationLevel, 0)
        for profile in profiles:
            education_counts[profile.education_level] += 1

        # 全ての教育レベルが存在する
        assert all(count > 0 for count in education_counts.values())

    def test_skills_match_education(self):
        """スキル数が教育レベルに応じているかテスト"""
        generator = HouseholdProfileGenerator(random_seed=42)
        profiles = generator.generate(count=50)

        for profile in profiles:
            skill_count = len(profile.skills)

            if profile.education_level == EducationLevel.HIGH_SCHOOL:
                assert 2 <= skill_count <= 3
            elif profile.education_level == EducationLevel.COLLEGE:
                assert 3 <= skill_count <= 4
            elif profile.education_level == EducationLevel.GRADUATE:
                assert 4 <= skill_count <= 5


class TestHouseholdAgent:
    """HouseholdAgentのテスト"""

    @pytest.fixture
    def mock_llm(self):
        """モックLLMインターフェース"""
        llm = MagicMock(spec=LLMInterface)
        llm.function_call.return_value = {
            "function_name": "decide_consumption",
            "arguments": {"goods": {"food": 10.0}, "reasoning": "Test reasoning"},
            "raw_response": {},
        }
        llm.validate_response.return_value = (True, None)
        return llm

    @pytest.fixture
    def sample_profile(self):
        """サンプルプロファイル"""
        generator = HouseholdProfileGenerator(random_seed=42)
        return generator.generate(count=1)[0]

    def test_agent_initialization(self, sample_profile, mock_llm):
        """エージェント初期化のテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        assert agent.agent_id == f"household_{sample_profile.id}"
        assert agent.agent_type == "household"
        assert agent.profile == sample_profile
        assert agent.attributes["profile_id"] == sample_profile.id
        assert agent.attributes["age"] == sample_profile.age

    def test_get_profile_str(self, sample_profile, mock_llm):
        """プロフィール文字列生成のテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)
        profile_str = agent.get_profile_str()

        # 必須情報が含まれているか
        assert sample_profile.name in profile_str
        assert str(sample_profile.age) in profile_str
        assert sample_profile.education_level.value in profile_str
        assert "Cash:" in profile_str
        assert "Employment:" in profile_str

    def test_get_available_actions(self, sample_profile, mock_llm):
        """利用可能な行動リストのテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)
        actions = agent.get_available_actions()

        # 5つの行動が定義されているか
        assert len(actions) == 5

        action_names = [a["name"] for a in actions]
        expected_names = [
            "decide_consumption",
            "labor_action",
            "choose_housing",
            "financial_decision",
            "modify_needs",
        ]

        for name in expected_names:
            assert name in action_names

        # 各行動にparametersが定義されているか
        for action in actions:
            assert "parameters" in action
            assert "type" in action["parameters"]
            assert "properties" in action["parameters"]

    def test_fallback_action_unemployed(self, sample_profile, mock_llm):
        """失業中のフォールバック行動テスト"""
        sample_profile.employment_status = EmploymentStatus.UNEMPLOYED
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        observation = {"market_state": {}}
        fallback = agent._get_fallback_action(observation)

        assert fallback["function_name"] == "labor_action"
        assert fallback["arguments"]["action"] == "find_job"

    def test_fallback_action_employed(self, sample_profile, mock_llm):
        """雇用中のフォールバック行動テスト"""
        sample_profile.employment_status = EmploymentStatus.EMPLOYED
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        observation = {"market_state": {}}
        fallback = agent._get_fallback_action(observation)

        assert fallback["function_name"] == "decide_consumption"
        assert "food" in fallback["arguments"]["goods"]

    def test_decide_primary_action(self, sample_profile, mock_llm):
        """意思決定のテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        observation = {
            "step": 1,
            "available_goods": ["food", "clothing"],
            "market_prices": {"food": 10.0, "clothing": 50.0},
        }

        action = agent.decide_primary_action(observation, step=1)

        # LLMが呼び出されたか
        assert mock_llm.function_call.called

        # 正しい形式で返されるか
        assert "function_name" in action
        assert "arguments" in action

    def test_update_profile(self, sample_profile, mock_llm):
        """プロフィール更新のテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        original_cash = sample_profile.cash
        original_age = sample_profile.age

        updates = {"cash": 5000.0, "age": 41, "savings": 1000.0}

        agent.update_profile(updates)

        assert agent.profile.cash == 5000.0
        assert agent.profile.cash != original_cash
        assert agent.profile.age == 41
        assert agent.profile.age != original_age
        assert agent.profile.savings == 1000.0

        # 属性も更新されているか
        assert agent.attributes["age"] == 41

    def test_memory_management(self, sample_profile, mock_llm):
        """メモリ管理のテスト"""
        agent = HouseholdAgent(profile=sample_profile, llm_interface=mock_llm)

        observation = {"step": 1}

        # 複数回行動を決定
        for i in range(3):
            agent.decide_primary_action(observation, step=i)

        # メモリに記録されているか
        assert len(agent.memory) == 3

        # メモリに正しい情報が含まれているか
        for i, memory in enumerate(agent.memory):
            assert memory["step"] == i
            assert "action" in memory
            assert "arguments" in memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
