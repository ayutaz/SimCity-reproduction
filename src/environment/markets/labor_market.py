"""
Labor Market for SimCity Simulation

労働市場:
- 求人と求職者のマッチング
- スキルベースの適合度計算
- 確率的マッチングアルゴリズム
"""

import random
from dataclasses import dataclass
from typing import Any

import numpy as np
from loguru import logger


@dataclass
class JobPosting:
    """
    求人情報

    Attributes:
        firm_id: 企業ID
        num_openings: 募集人数
        wage_offered: 提示賃金
        skill_requirements: スキル要件 {skill_id: required_level}
        location: 企業の位置 (x, y)
    """

    firm_id: int
    num_openings: int
    wage_offered: float
    skill_requirements: dict[str, float]
    location: tuple[int, int]


@dataclass
class JobSeeker:
    """
    求職者情報

    Attributes:
        household_id: 世帯ID
        skills: スキル {skill_id: level}
        reservation_wage: 希望最低賃金（留保賃金）
        location: 世帯の位置 (x, y)
        currently_employed: 現在雇用されているか
    """

    household_id: int
    skills: dict[str, float]
    reservation_wage: float
    location: tuple[int, int]
    currently_employed: bool = False


@dataclass
class JobMatch:
    """
    マッチング結果

    Attributes:
        firm_id: 企業ID
        household_id: 世帯ID
        wage: 合意賃金
        skill_match_score: スキル適合度 (0.0-1.0)
    """

    firm_id: int
    household_id: int
    wage: float
    skill_match_score: float


class LaborMarket:
    """
    労働市場

    求人と求職者をマッチングする市場メカニズム
    - 確率的マッチングアルゴリズム
    - スキル適合度の計算
    - 距離を考慮したマッチング（オプション）
    """

    def __init__(
        self,
        matching_probability: float = 0.7,
        consider_distance: bool = False,
        max_commute_distance: float = 50.0,
    ):
        """
        Args:
            matching_probability: マッチング成功確率（0.0-1.0）
            consider_distance: 距離を考慮するか
            max_commute_distance: 最大通勤距離
        """
        self.matching_probability = matching_probability
        self.consider_distance = consider_distance
        self.max_commute_distance = max_commute_distance

        # 統計情報
        self.total_postings = 0
        self.total_seekers = 0
        self.total_matches = 0
        self.rejected_by_wage = 0
        self.rejected_by_distance = 0
        self.rejected_by_probability = 0

        logger.info(
            f"LaborMarket initialized: matching_prob={matching_probability}, "
            f"consider_distance={consider_distance}"
        )

    def match(
        self,
        job_postings: list[JobPosting],
        job_seekers: list[JobSeeker],
    ) -> list[JobMatch]:
        """
        求人と求職者をマッチング

        Args:
            job_postings: 求人リスト
            job_seekers: 求職者リスト

        Returns:
            マッチング結果のリスト
        """
        # 求人枠の総数をカウント
        self.total_postings += sum(p.num_openings for p in job_postings)
        self.total_seekers += len(job_seekers)

        matches: list[JobMatch] = []

        # 求職者ごとに最適な求人を探す
        matched_seekers = set()

        for seeker in job_seekers:
            if seeker.household_id in matched_seekers:
                continue

            # 候補求人をスコアリング
            candidates = self._score_job_postings(seeker, job_postings)

            # スコアが高い順にマッチングを試行
            for score, posting in sorted(candidates, key=lambda x: -x[0]):
                # 求人枠が残っているか
                if posting.num_openings <= 0:
                    continue

                # 賃金条件チェック
                if posting.wage_offered < seeker.reservation_wage:
                    self.rejected_by_wage += 1
                    continue

                # 距離チェック（オプション）
                if self.consider_distance:
                    distance = self._calculate_distance(
                        seeker.location, posting.location
                    )
                    if distance > self.max_commute_distance:
                        self.rejected_by_distance += 1
                        continue

                # 確率的マッチング
                if random.random() > self.matching_probability:
                    self.rejected_by_probability += 1
                    continue

                # マッチング成功
                match = JobMatch(
                    firm_id=posting.firm_id,
                    household_id=seeker.household_id,
                    wage=posting.wage_offered,
                    skill_match_score=score,
                )
                matches.append(match)
                matched_seekers.add(seeker.household_id)
                posting.num_openings -= 1  # 求人枠を減らす
                self.total_matches += 1
                break

        logger.info(
            f"Labor market matching: {len(matches)} matches "
            f"from {len(job_postings)} postings and {len(job_seekers)} seekers"
        )

        return matches

    def _score_job_postings(
        self, seeker: JobSeeker, postings: list[JobPosting]
    ) -> list[tuple[float, JobPosting]]:
        """
        求職者に対する求人のスコアリング

        Args:
            seeker: 求職者
            postings: 求人リスト

        Returns:
            (スコア, 求人)のリスト
        """
        scored = []

        for posting in postings:
            # スキル適合度を計算
            skill_score = self._calculate_skill_match(
                seeker.skills, posting.skill_requirements
            )

            # 賃金スコア（高いほど良い、正規化）
            wage_score = min(1.0, posting.wage_offered / max(1.0, seeker.reservation_wage * 1.5))

            # 総合スコア（スキル70%、賃金30%）
            total_score = 0.7 * skill_score + 0.3 * wage_score

            scored.append((total_score, posting))

        return scored

    def _calculate_skill_match(
        self, seeker_skills: dict[str, float], required_skills: dict[str, float]
    ) -> float:
        """
        スキル適合度を計算

        Args:
            seeker_skills: 求職者のスキル
            required_skills: 必要スキル

        Returns:
            適合度（0.0-1.0）
        """
        if not required_skills:
            # スキル要件がない場合は1.0
            return 1.0

        match_scores = []

        for skill_id, required_level in required_skills.items():
            actual_level = seeker_skills.get(skill_id, 0.0)
            # スキルレベルの比率（上限1.0）
            match = min(1.0, actual_level / max(0.01, required_level))
            match_scores.append(match)

        # 平均適合度
        return float(np.mean(match_scores)) if match_scores else 0.5

    def _calculate_distance(
        self, loc1: tuple[int, int], loc2: tuple[int, int]
    ) -> float:
        """
        2点間の距離を計算（ユークリッド距離）

        Args:
            loc1: 位置1
            loc2: 位置2

        Returns:
            距離
        """
        return float(np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2))

    def get_statistics(self) -> dict[str, Any]:
        """
        労働市場の統計情報を取得

        Returns:
            統計情報辞書
        """
        match_rate = (
            self.total_matches / self.total_seekers if self.total_seekers > 0 else 0.0
        )
        fill_rate = (
            self.total_matches / self.total_postings if self.total_postings > 0 else 0.0
        )

        return {
            "total_postings": self.total_postings,
            "total_seekers": self.total_seekers,
            "total_matches": self.total_matches,
            "match_rate": match_rate,
            "fill_rate": fill_rate,
            "rejected_by_wage": self.rejected_by_wage,
            "rejected_by_distance": self.rejected_by_distance,
            "rejected_by_probability": self.rejected_by_probability,
        }

    def reset_statistics(self):
        """統計情報をリセット"""
        self.total_postings = 0
        self.total_seekers = 0
        self.total_matches = 0
        self.rejected_by_wage = 0
        self.rejected_by_distance = 0
        self.rejected_by_probability = 0
