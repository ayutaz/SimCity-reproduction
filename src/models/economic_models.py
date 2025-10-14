"""
Economic models for SimCity simulation

経済理論に基づくモデル実装:
- Cobb-Douglas生産関数
- 累進課税
- Taylor rule
- マクロ経済指標計算
"""


import numpy as np


class ProductionFunction:
    """
    Cobb-Douglas生産関数

    Y = A * L^(1-α) * K^α

    where:
        Y = 産出量
        A = 全要素生産性 (Total Factor Productivity)
        L = 労働投入 (effective labor)
        K = 資本ストック
        α = 資本分配率 (capital share)
    """

    def __init__(self, alpha: float = 0.33, tfp: float = 1.0):
        """
        Args:
            alpha: 資本分配率（0 < α < 1）、通常0.3-0.4
            tfp: 全要素生産性
        """
        if not 0 < alpha < 1:
            raise ValueError("Alpha must be between 0 and 1")

        self.alpha = alpha
        self.tfp = tfp

    def calculate_output(
        self, labor: float, capital: float, tfp: float = None
    ) -> float:
        """
        産出量を計算

        Args:
            labor: 労働投入（実効労働量）
            capital: 資本ストック
            tfp: 全要素生産性（Noneの場合はデフォルト値を使用）

        Returns:
            産出量
        """
        if labor < 0 or capital < 0:
            return 0.0

        a = tfp if tfp is not None else self.tfp
        output = a * (labor ** (1 - self.alpha)) * (capital**self.alpha)

        return output

    def calculate_marginal_product_labor(
        self, labor: float, capital: float, tfp: float = None
    ) -> float:
        """
        労働の限界生産物を計算

        MPL = ∂Y/∂L = (1-α) * A * L^(-α) * K^α

        Args:
            labor: 労働投入
            capital: 資本ストック
            tfp: 全要素生産性

        Returns:
            労働の限界生産物
        """
        if labor <= 0:
            return 0.0

        a = tfp if tfp is not None else self.tfp
        mpl = (1 - self.alpha) * a * (labor ** (-self.alpha)) * (capital**self.alpha)

        return mpl

    def calculate_marginal_product_capital(
        self, labor: float, capital: float, tfp: float = None
    ) -> float:
        """
        資本の限界生産物を計算

        MPK = ∂Y/∂K = α * A * L^(1-α) * K^(α-1)

        Args:
            labor: 労働投入
            capital: 資本ストック
            tfp: 全要素生産性

        Returns:
            資本の限界生産物
        """
        if capital <= 0:
            return 0.0

        a = tfp if tfp is not None else self.tfp
        mpk = (
            self.alpha * a * (labor ** (1 - self.alpha)) * (capital ** (self.alpha - 1))
        )

        return mpk


class TaxationSystem:
    """
    累進課税システム

    税率区分に基づいて所得税を計算
    """

    def __init__(self, brackets: list[tuple[float, float]]):
        """
        Args:
            brackets: 税率区分のリスト [(所得閾値, 税率), ...]
                     例: [(0, 0.0), (20000, 0.1), (50000, 0.2), (100000, 0.3)]
        """
        # 閾値でソート
        self.brackets = sorted(brackets, key=lambda x: x[0])

    def calculate_income_tax(self, income: float) -> float:
        """
        所得税を計算

        累進課税: t_i = Σ r_k [min{z_i, b_{k+1}} - b_k]_+

        Args:
            income: 課税対象所得

        Returns:
            所得税額
        """
        if income <= 0:
            return 0.0

        tax = 0.0

        for i in range(len(self.brackets)):
            threshold, rate = self.brackets[i]

            if income <= threshold:
                break

            # 次の区分の閾値
            if i + 1 < len(self.brackets):
                next_threshold = self.brackets[i + 1][0]
            else:
                next_threshold = float("inf")

            # この区分での課税所得
            taxable = min(income, next_threshold) - threshold
            tax += taxable * rate

        return tax

    def calculate_effective_rate(self, income: float) -> float:
        """
        実効税率を計算

        Args:
            income: 所得

        Returns:
            実効税率（税額 / 所得）
        """
        if income <= 0:
            return 0.0

        tax = self.calculate_income_tax(income)
        return tax / income


class TaylorRule:
    """
    Taylor rule for monetary policy

    r̂ = max{r^n + π^t + α(π - π^t) + β(Y - Y^n), 0}

    金利平滑化:
    r_t = ρ * r_{t-1} + (1-ρ) * r̂_t

    where:
        r̂ = 目標政策金利
        r^n = 自然利子率
        π = 現在のインフレ率
        π^t = インフレ目標
        Y = 現在のGDP
        Y^n = 潜在GDP
        α = インフレへの反応係数（通常1.5）
        β = 産出ギャップへの反応係数（通常0.5）
        ρ = 金利平滑化係数（通常0.8）
    """

    def __init__(
        self,
        natural_rate: float = 0.02,
        inflation_target: float = 0.02,
        alpha: float = 1.5,
        beta: float = 0.5,
        smoothing_factor: float = 0.8,
    ):
        """
        Args:
            natural_rate: 自然利子率
            inflation_target: インフレ目標
            alpha: インフレ反応係数
            beta: 産出ギャップ反応係数
            smoothing_factor: 金利平滑化係数 ρ
        """
        self.natural_rate = natural_rate
        self.inflation_target = inflation_target
        self.alpha = alpha
        self.beta = beta
        self.smoothing_factor = smoothing_factor

    def calculate_target_rate(
        self, inflation: float, gdp: float, potential_gdp: float
    ) -> float:
        """
        目標政策金利を計算（平滑化前）

        Args:
            inflation: 現在のインフレ率
            gdp: 現在のGDP
            potential_gdp: 潜在GDP

        Returns:
            目標政策金利
        """
        # 産出ギャップ
        if potential_gdp > 0:
            output_gap = (gdp - potential_gdp) / potential_gdp
        else:
            output_gap = 0.0

        # Taylor rule
        target_rate = (
            self.natural_rate
            + self.inflation_target
            + self.alpha * (inflation - self.inflation_target)
            + self.beta * output_gap
        )

        # 非負制約
        return max(0.0, target_rate)

    def smooth_rate(self, target_rate: float, previous_rate: float) -> float:
        """
        金利平滑化を適用

        r_t = ρ * r_{t-1} + (1-ρ) * r̂_t

        Args:
            target_rate: 目標金利
            previous_rate: 前期の金利

        Returns:
            平滑化された金利
        """
        smoothed = (
            self.smoothing_factor * previous_rate
            + (1 - self.smoothing_factor) * target_rate
        )

        return max(0.0, smoothed)


class MacroeconomicIndicators:
    """
    マクロ経済指標の計算

    - GDP
    - インフレ率
    - 失業率
    - Gini係数
    """

    @staticmethod
    def calculate_gdp(
        household_incomes: list[float],
        firm_outputs: list[float],
        government_spending: float = 0.0,
    ) -> float:
        """
        名目GDPを計算（支出アプローチ）

        GDP = C + I + G
        簡略化版: 総所得 + 政府支出

        Args:
            household_incomes: 家計所得のリスト
            firm_outputs: 企業産出のリスト
            government_spending: 政府支出

        Returns:
            名目GDP
        """
        consumption = sum(household_incomes)
        investment = sum(firm_outputs)
        gdp = consumption + investment + government_spending

        return max(0.0, gdp)

    @staticmethod
    def calculate_inflation(
        current_prices: dict[str, float], previous_prices: dict[str, float]
    ) -> float:
        """
        インフレ率を計算

        π = (P_t - P_{t-1}) / P_{t-1}

        Args:
            current_prices: 現在の価格辞書 {商品名: 価格}
            previous_prices: 前期の価格辞書

        Returns:
            インフレ率
        """
        if not previous_prices or not current_prices:
            return 0.0

        # 共通の商品のみを対象
        common_goods = set(current_prices.keys()) & set(previous_prices.keys())

        if not common_goods:
            return 0.0

        # 平均価格変化率
        inflation_rates = []
        for good in common_goods:
            prev_price = previous_prices[good]
            curr_price = current_prices[good]

            if prev_price > 0:
                rate = (curr_price - prev_price) / prev_price
                inflation_rates.append(rate)

        if inflation_rates:
            return np.mean(inflation_rates)
        else:
            return 0.0

    @staticmethod
    def calculate_unemployment_rate(
        total_labor_force: int, employed: int
    ) -> float:
        """
        失業率を計算

        u = (労働力人口 - 就業者数) / 労働力人口

        Args:
            total_labor_force: 労働力人口
            employed: 就業者数

        Returns:
            失業率
        """
        if total_labor_force <= 0:
            return 0.0

        unemployed = max(0, total_labor_force - employed)
        return unemployed / total_labor_force

    @staticmethod
    def calculate_gini_coefficient(incomes: list[float]) -> float:
        """
        Gini係数を計算（所得不平等度）

        Args:
            incomes: 所得のリスト

        Returns:
            Gini係数（0-1、0が完全平等、1が完全不平等）
        """
        if not incomes or len(incomes) == 0:
            return 0.0

        # ゼロや負の所得を除外
        incomes = [max(0, inc) for inc in incomes]

        if sum(incomes) == 0:
            return 0.0

        # ソート
        sorted_incomes = sorted(incomes)
        n = len(sorted_incomes)

        # Gini係数の計算
        cumulative_income = np.cumsum(sorted_incomes)
        sum_income = cumulative_income[-1]

        if sum_income == 0:
            return 0.0

        # G = (2 * Σ(i * y_i)) / (n * Σy_i) - (n+1)/n
        gini = (2 * sum((i + 1) * y for i, y in enumerate(sorted_incomes))) / (
            n * sum_income
        ) - (n + 1) / n

        return max(0.0, min(1.0, gini))

    @staticmethod
    def calculate_job_vacancy_rate(total_jobs: int, filled_jobs: int) -> float:
        """
        求人率を計算

        Args:
            total_jobs: 総求人数
            filled_jobs: 充足された求人数

        Returns:
            求人率（空きポジション / 総求人数）
        """
        if total_jobs <= 0:
            return 0.0

        vacancies = max(0, total_jobs - filled_jobs)
        return vacancies / total_jobs


def calculate_effective_labor(
    workers: list[dict[str, float]], skill_requirements: dict[str, float]
) -> float:
    """
    実効労働量を計算

    各労働者のスキルと求められるスキルのマッチング度を考慮

    Args:
        workers: 労働者のリスト [{skill_name: level, ...}, ...]
        skill_requirements: 必要スキル {skill_name: required_level, ...}

    Returns:
        実効労働量
    """
    if not workers:
        return 0.0

    effective_labor = 0.0

    for worker_skills in workers:
        # 各労働者のスキルマッチング度を計算
        if not skill_requirements:
            # スキル要件がない場合は1人として計算
            efficiency = 1.0
        else:
            # スキルマッチング効率
            efficiencies = []
            for skill, required_level in skill_requirements.items():
                actual_level = worker_skills.get(skill, 0.0)
                # スキルレベルの比率（上限1.0）
                efficiency = min(1.0, actual_level / max(0.01, required_level))
                efficiencies.append(efficiency)

            # 平均効率
            efficiency = np.mean(efficiencies) if efficiencies else 0.5

        effective_labor += efficiency

    return effective_labor
