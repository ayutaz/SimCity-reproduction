"""Performance Tests for SimCity

主要な処理のパフォーマンスを測定し、
許容可能な実行時間内に収まることを確認する。

Note: このテストは実際のAPIを使用してパフォーマンスを計測します。
"""

import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.household import HouseholdProfileGenerator
from src.models.economic_models import MacroeconomicIndicators, ProductionFunction


class TestPerformance:
    """Performance tests for key operations

    Note: パフォーマンステストは、主要な処理が許容範囲内で完了することを確認します。
    """

    def test_household_generation_performance(self):
        """Test household profile generation performance"""
        generator = HouseholdProfileGenerator(random_seed=42)

        start = time.time()
        profiles = generator.generate(count=200)
        elapsed = time.time() - start

        assert len(profiles) == 200
        # Should complete in under 1 second
        assert elapsed < 1.0, (
            f"Household generation took {elapsed:.2f}s (expected <1.0s)"
        )

        print(f"\nHousehold generation (200): {elapsed:.3f}s")

    def test_gini_coefficient_performance(self):
        """Test Gini coefficient calculation performance"""
        indicators = MacroeconomicIndicators()

        # Generate sample data
        np.random.seed(42)
        household_incomes = np.random.lognormal(10.5, 0.5, 200).tolist()

        start = time.time()

        # Calculate Gini coefficient 1000 times
        for _ in range(1000):
            _ = indicators.calculate_gini_coefficient(household_incomes)

        elapsed = time.time() - start

        # Should complete in under 1.0 seconds
        assert elapsed < 1.0, (
            f"Gini coefficient calculation took {elapsed:.2f}s (expected <1.0s)"
        )

        print(f"\nGini coefficient (1000 calculations): {elapsed:.3f}s")

    def test_production_function_performance(self):
        """Test production function calculation performance"""
        prod_func = ProductionFunction(alpha=0.33)

        start = time.time()

        # Calculate production 10000 times
        for _ in range(10000):
            _ = prod_func.calculate_output(labor=10.0, capital=20.0)

        elapsed = time.time() - start

        # Should complete in under 0.1 seconds
        assert elapsed < 0.1, (
            f"Production function calculation took {elapsed:.2f}s (expected <0.1s)"
        )

        print(f"\nProduction function (10000 calculations): {elapsed:.3f}s")


@pytest.mark.parametrize("count", [100, 200, 500])
def test_scalability_household_generation(count):
    """Test scalability of household generation"""
    generator = HouseholdProfileGenerator(random_seed=42)

    start = time.time()
    profiles = generator.generate(count=count)
    elapsed = time.time() - start

    assert len(profiles) == count

    # Should scale roughly linearly (allow 2x for overhead)
    expected_time = count / 200.0  # 200 households in ~1s
    max_time = expected_time * 2

    assert elapsed < max_time, (
        f"Generation of {count} households took {elapsed:.2f}s (expected <{max_time:.2f}s)"
    )

    print(f"\nHousehold generation ({count}): {elapsed:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
