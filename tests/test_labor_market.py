"""
Tests for Labor Market
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.markets.labor_market import (
    JobMatch,
    JobPosting,
    JobSeeker,
    LaborMarket,
)


class TestLaborMarket:
    """労働市場のテスト"""

    @pytest.fixture
    def labor_market(self):
        """労働市場インスタンス（確率1.0で確定的マッチング）"""
        return LaborMarket(matching_probability=1.0, consider_distance=False)

    @pytest.fixture
    def sample_postings(self):
        """サンプル求人"""
        return [
            JobPosting(
                firm_id=1,
                num_openings=2,
                wage_offered=3000.0,
                skill_requirements={"tech_programming": 0.8},
                location=(50, 50),
            ),
            JobPosting(
                firm_id=2,
                num_openings=1,
                wage_offered=2500.0,
                skill_requirements={"biz_marketing": 0.6},
                location=(60, 60),
            ),
        ]

    @pytest.fixture
    def sample_seekers(self):
        """サンプル求職者"""
        return [
            JobSeeker(
                household_id=101,
                skills={"tech_programming": 0.9},
                reservation_wage=2800.0,
                location=(55, 55),
            ),
            JobSeeker(
                household_id=102,
                skills={"biz_marketing": 0.7},
                reservation_wage=2400.0,
                location=(65, 65),
            ),
            JobSeeker(
                household_id=103,
                skills={"tech_programming": 0.5},
                reservation_wage=2900.0,
                location=(55, 55),
            ),
        ]

    def test_basic_matching(self, labor_market, sample_postings, sample_seekers):
        """基本的なマッチングテスト"""
        matches = labor_market.match(sample_postings, sample_seekers)

        # マッチングが発生すること
        assert len(matches) > 0
        assert all(isinstance(m, JobMatch) for m in matches)

        # マッチした世帯IDが求職者リストに含まれること
        matched_ids = {m.household_id for m in matches}
        seeker_ids = {s.household_id for s in sample_seekers}
        assert matched_ids.issubset(seeker_ids)

    def test_wage_filter(self, labor_market):
        """賃金条件によるフィルタリング"""
        # 高い希望賃金
        postings = [
            JobPosting(
                firm_id=1,
                num_openings=1,
                wage_offered=2000.0,  # 低い賃金
                skill_requirements={},
                location=(50, 50),
            )
        ]

        seekers = [
            JobSeeker(
                household_id=101,
                skills={},
                reservation_wage=2500.0,  # 高い希望賃金
                location=(50, 50),
            )
        ]

        matches = labor_market.match(postings, seekers)

        # 賃金が合わないのでマッチングしない
        assert len(matches) == 0
        assert labor_market.rejected_by_wage > 0

    def test_skill_match_calculation(self, labor_market):
        """スキル適合度計算のテスト"""
        # 完全一致
        seeker_skills = {"tech_programming": 1.0}
        required_skills = {"tech_programming": 1.0}
        score = labor_market._calculate_skill_match(seeker_skills, required_skills)
        assert score == 1.0

        # 部分一致（50%）
        seeker_skills = {"tech_programming": 0.5}
        required_skills = {"tech_programming": 1.0}
        score = labor_market._calculate_skill_match(seeker_skills, required_skills)
        assert score == 0.5

        # スキル不足なし（求職者が上回る）
        seeker_skills = {"tech_programming": 1.5}
        required_skills = {"tech_programming": 1.0}
        score = labor_market._calculate_skill_match(seeker_skills, required_skills)
        assert score == 1.0  # 上限1.0

    def test_no_skill_requirements(self, labor_market):
        """スキル要件なしの求人"""
        postings = [
            JobPosting(
                firm_id=1,
                num_openings=1,
                wage_offered=2000.0,
                skill_requirements={},  # スキル要件なし
                location=(50, 50),
            )
        ]

        seekers = [
            JobSeeker(
                household_id=101,
                skills={"tech_programming": 0.5},
                reservation_wage=1500.0,
                location=(50, 50),
            )
        ]

        matches = labor_market.match(postings, seekers)

        # スキル要件がないのでマッチングする
        assert len(matches) == 1
        assert matches[0].skill_match_score >= 0.9  # スキル要件なしなので高スコア

    def test_multiple_openings(self, labor_market):
        """複数の求人枠"""
        postings = [
            JobPosting(
                firm_id=1,
                num_openings=3,  # 3人募集
                wage_offered=2500.0,
                skill_requirements={},
                location=(50, 50),
            )
        ]

        seekers = [
            JobSeeker(
                household_id=101,
                skills={},
                reservation_wage=2000.0,
                location=(50, 50),
            ),
            JobSeeker(
                household_id=102,
                skills={},
                reservation_wage=2000.0,
                location=(50, 50),
            ),
        ]

        matches = labor_market.match(postings, seekers)

        # 2人の求職者に対して2人マッチング
        assert len(matches) == 2
        assert postings[0].num_openings == 1  # 3 - 2 = 1

    def test_matching_probability(self):
        """確率的マッチングのテスト"""
        # 低い確率でマッチング
        market = LaborMarket(matching_probability=0.1)

        postings = [
            JobPosting(
                firm_id=1,
                num_openings=10,
                wage_offered=3000.0,
                skill_requirements={},
                location=(50, 50),
            )
        ]

        seekers = [
            JobSeeker(
                household_id=i,
                skills={},
                reservation_wage=2000.0,
                location=(50, 50),
            )
            for i in range(100)
        ]

        matches = market.match(postings, seekers)

        # 確率0.1なので、100人のうち約10人がマッチング（±誤差）
        assert 5 <= len(matches) <= 15  # 統計的ばらつきを許容
        assert market.rejected_by_probability > 0

    def test_statistics(self, labor_market, sample_postings, sample_seekers):
        """統計情報のテスト"""
        labor_market.reset_statistics()

        # 求人枠の総数を計算（前のテストで変更されていない新しいfixtureを使用）
        total_openings = sum(p.num_openings for p in sample_postings)

        matches = labor_market.match(sample_postings, sample_seekers)

        stats = labor_market.get_statistics()

        assert stats["total_postings"] == total_openings  # 求人枠の総数
        assert stats["total_seekers"] == len(sample_seekers)
        assert stats["total_matches"] == len(matches)
        assert 0 <= stats["match_rate"] <= 1.0
        assert 0 <= stats["fill_rate"] <= 1.0

    def test_distance_consideration(self):
        """距離を考慮したマッチング"""
        market = LaborMarket(
            matching_probability=1.0,
            consider_distance=True,
            max_commute_distance=10.0,  # 最大10の距離
        )

        postings = [
            JobPosting(
                firm_id=1,
                num_openings=1,
                wage_offered=3000.0,
                skill_requirements={},
                location=(0, 0),  # 原点
            )
        ]

        seekers = [
            JobSeeker(
                household_id=101,
                skills={},
                reservation_wage=2000.0,
                location=(50, 50),  # 遠い位置
            )
        ]

        matches = market.match(postings, seekers)

        # 距離が遠すぎるのでマッチングしない
        assert len(matches) == 0
        assert market.rejected_by_distance > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
