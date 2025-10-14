"""Tests for Phase 5: Data Preparation and Initialization"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.household import HouseholdProfileGenerator
from src.models.data_models import EducationLevel, EmploymentStatus, HouseholdProfile


class TestHouseholdProfileGenerator:
    """Test HouseholdProfileGenerator"""

    @pytest.fixture
    def generator(self):
        """Create generator with fixed seed"""
        return HouseholdProfileGenerator(random_seed=42)

    def test_generate_single_profile(self, generator):
        """Test generating a single profile"""
        profiles = generator.generate(count=1)

        assert len(profiles) == 1
        profile = profiles[0]

        assert profile.id == 1
        assert profile.name == "Household_1"
        assert 20 <= profile.age <= 70
        assert isinstance(profile.education_level, EducationLevel)
        assert isinstance(profile.employment_status, EmploymentStatus)
        assert profile.cash > 0
        assert len(profile.skills) >= 2

    def test_generate_multiple_profiles(self, generator):
        """Test generating multiple profiles"""
        profiles = generator.generate(count=50)

        assert len(profiles) == 50

        # Check IDs are unique
        ids = [p.id for p in profiles]
        assert len(ids) == len(set(ids))

        # Check ages are within range
        ages = [p.age for p in profiles]
        assert all(20 <= age <= 70 for age in ages)
        # Mean age should be close to 40
        assert 35 <= sum(ages) / len(ages) <= 45

    def test_age_distribution(self, generator):
        """Test age distribution follows normal distribution"""
        profiles = generator.generate(count=200)
        ages = [p.age for p in profiles]

        mean_age = sum(ages) / len(ages)
        std_age = (sum((a - mean_age) ** 2 for a in ages) / len(ages)) ** 0.5

        # Should be close to target (40 ± 12)
        assert 38 <= mean_age <= 42
        assert 10 <= std_age <= 14

    def test_income_distribution(self, generator):
        """Test income distribution is lognormal"""
        profiles = generator.generate(count=200)
        incomes = [p.cash for p in profiles]

        # All incomes should be positive
        assert all(income > 0 for income in incomes)

        # Should have wide range (characteristic of lognormal)
        min_income = min(incomes)
        max_income = max(incomes)
        assert max_income / min_income > 10  # At least 10x range

    def test_skill_assignment(self, generator):
        """Test skill assignment"""
        profiles = generator.generate(count=50)

        for profile in profiles:
            # Should have 2-5 skills
            assert 2 <= len(profile.skills) <= 5

            # Skill levels should be between 0.2 and 1.0
            for skill_id, level in profile.skills.items():
                assert 0.2 <= level <= 1.0
                assert isinstance(skill_id, str)

    def test_education_skill_correlation(self, generator):
        """Test that higher education leads to more skills"""
        profiles = generator.generate(count=100)

        high_school = [
            p for p in profiles if p.education_level == EducationLevel.HIGH_SCHOOL
        ]
        graduate = [p for p in profiles if p.education_level == EducationLevel.GRADUATE]

        if high_school and graduate:
            avg_skills_hs = sum(len(p.skills) for p in high_school) / len(high_school)
            avg_skills_grad = sum(len(p.skills) for p in graduate) / len(graduate)

            # Graduates should have more skills on average
            assert avg_skills_grad > avg_skills_hs

    def test_employment_rate(self, generator):
        """Test employment rate (Phase 9.9.4: 全員失業状態で開始)"""
        profiles = generator.generate(count=200)

        employed = sum(
            1 for p in profiles if p.employment_status == EmploymentStatus.EMPLOYED
        )
        employment_rate = employed / len(profiles)

        # Phase 9.9.4以降: 全世帯は失業状態で開始し、労働市場でマッチングされる
        assert employment_rate == 0.0  # 全員失業状態で開始

        # 全員が UNEMPLOYED であることを確認
        assert all(p.employment_status == EmploymentStatus.UNEMPLOYED for p in profiles)

    def test_consumption_preferences(self, generator):
        """Test consumption preferences are normalized"""
        profiles = generator.generate(count=10)

        for profile in profiles:
            # Should have preferences
            assert len(profile.consumption_preferences) > 0

            # Sum should be approximately 1.0
            total = sum(profile.consumption_preferences.values())
            assert 0.99 <= total <= 1.01

    def test_profile_serialization(self, generator):
        """Test profile can be serialized and deserialized"""
        profiles = generator.generate(count=1)
        profile = profiles[0]

        # Convert to dict
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["id"] == profile.id
        assert profile_dict["age"] == profile.age

        # Convert back from dict
        restored_profile = HouseholdProfile.from_dict(profile_dict)
        assert restored_profile.id == profile.id
        assert restored_profile.age == profile.age
        assert restored_profile.education_level == profile.education_level
        assert restored_profile.employment_status == profile.employment_status
        assert restored_profile.cash == profile.cash

    def test_reproducibility(self):
        """Test that same seed produces consistent results in fresh instances"""
        # Create two fresh generators with same seed (not reusing instances)
        import random as py_random

        import numpy as np

        # First run
        py_random.seed(123)
        np.random.seed(123)
        gen1 = HouseholdProfileGenerator(random_seed=123)
        profiles1 = gen1.generate(count=3)

        # Second run - reset seeds
        py_random.seed(123)
        np.random.seed(123)
        gen2 = HouseholdProfileGenerator(random_seed=123)
        profiles2 = gen2.generate(count=3)

        # Compare first profiles (IDs will match, values should match)
        p1, p2 = profiles1[0], profiles2[0]
        assert p1.age == p2.age
        assert p1.education_level == p2.education_level
        assert abs(p1.cash - p2.cash) < 0.01  # Float comparison with tolerance


class TestInitialDataset:
    """Test initial household dataset"""

    @pytest.fixture
    def dataset_path(self):
        """Path to the generated dataset"""
        return Path("data/initial_households.json")

    def test_dataset_exists(self, dataset_path):
        """Test that dataset file exists"""
        assert dataset_path.exists(), (
            "Initial dataset not found. Run generate_initial_households.py first"
        )

    def test_dataset_structure(self, dataset_path):
        """Test dataset has correct structure"""
        if not dataset_path.exists():
            pytest.skip("Dataset not generated yet")

        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check top-level structure
        assert "metadata" in data
        assert "statistics" in data
        assert "households" in data

        # Check metadata
        assert data["metadata"]["count"] == 200
        assert data["metadata"]["random_seed"] == 42

        # Check statistics
        stats = data["statistics"]
        assert "age_mean" in stats
        assert "employment_rate" in stats

        # Check households
        households = data["households"]
        assert len(households) == 200

    def test_dataset_household_validity(self, dataset_path):
        """Test that all households in dataset are valid"""
        if not dataset_path.exists():
            pytest.skip("Dataset not generated yet")

        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)

        households = data["households"]

        for i, h_dict in enumerate(households):
            # Can be restored to HouseholdProfile
            profile = HouseholdProfile.from_dict(h_dict)

            assert profile.id == i + 1
            assert 20 <= profile.age <= 70
            assert profile.cash > 0
            assert len(profile.skills) >= 2

    def test_dataset_statistics_match(self, dataset_path):
        """Test that statistics match actual data"""
        if not dataset_path.exists():
            pytest.skip("Dataset not generated yet")

        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)

        stats = data["statistics"]
        households = data["households"]

        # Calculate statistics from households
        ages = [h["age"] for h in households]
        actual_age_mean = sum(ages) / len(ages)

        # Should match within 0.1
        assert abs(stats["age_mean"] - actual_age_mean) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
