"""
Data models for SimCity simulation

エージェントや経済状態を表現するデータ構造
"""

from dataclasses import dataclass, field
from enum import Enum


class EmploymentStatus(Enum):
    """雇用状態"""

    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    SEEKING = "seeking"


class EducationLevel(Enum):
    """教育レベル"""

    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    GRADUATE = "graduate"


class GoodCategory(Enum):
    """財のカテゴリ"""

    FOOD = "food"
    CLOTHING = "clothing"
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    FURNITURE = "furniture"
    OTHER = "other"


@dataclass
class HouseholdProfile:
    """
    家計プロファイル

    論文のTable 1に基づく属性
    """

    id: int
    name: str
    age: int
    education_level: EducationLevel
    skills: dict[str, float] = field(default_factory=dict)  # スキル名: レベル(0-1)

    # 経済状態
    cash: float = 0.0
    savings: float = 0.0
    debt: float = 0.0
    monthly_income: float = 0.0

    # 雇用状態
    employment_status: EmploymentStatus = EmploymentStatus.UNEMPLOYED
    employer_id: int | None = None
    wage: float = 0.0

    # 消費嗜好（各財カテゴリへの選好度）
    consumption_preferences: dict[str, float] = field(default_factory=dict)

    # 住居
    location: tuple[int, int] = (0, 0)
    housing_cost: float = 0.0

    # 保有株式（firm_id: 株式数）
    stock_holdings: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "education_level": self.education_level.value,
            "skills": self.skills,
            "cash": self.cash,
            "savings": self.savings,
            "debt": self.debt,
            "monthly_income": self.monthly_income,
            "employment_status": self.employment_status.value,
            "employer_id": self.employer_id,
            "wage": self.wage,
            "consumption_preferences": self.consumption_preferences,
            "location": self.location,
            "housing_cost": self.housing_cost,
            "stock_holdings": self.stock_holdings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HouseholdProfile":
        """辞書形式から復元"""
        data = data.copy()
        data["education_level"] = EducationLevel(data["education_level"])
        data["employment_status"] = EmploymentStatus(data["employment_status"])
        return cls(**data)


@dataclass
class FirmProfile:
    """
    企業プロファイル

    Cobb-Douglas生産関数を使用
    """

    id: int
    name: str
    goods_type: str  # 生産する財の種類
    goods_category: GoodCategory

    # 財務状態
    cash: float = 0.0
    debt: float = 0.0

    # 生産要素
    capital: float = 100.0  # 資本ストック K
    total_factor_productivity: float = 1.0  # 全要素生産性 A
    employees: list[int] = field(default_factory=list)  # household IDs

    # 生産・販売
    inventory: float = 0.0  # 在庫
    price: float = 100.0  # 販売価格
    production_quantity: float = 0.0  # 生産量（前期）
    sales_quantity: float = 0.0  # 販売量（前期）

    # 雇用
    wage_offered: float = 1500.0  # 提示賃金
    job_openings: int = 0  # 求人数
    skill_requirements: dict[str, float] = field(default_factory=dict)  # 必要スキル

    # 所有構造
    shareholders: dict[int, int] = field(default_factory=dict)  # household_id: 株式数

    # 位置
    location: tuple[int, int] = (0, 0)

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "goods_type": self.goods_type,
            "goods_category": self.goods_category.value,
            "cash": self.cash,
            "debt": self.debt,
            "capital": self.capital,
            "total_factor_productivity": self.total_factor_productivity,
            "employees": self.employees,
            "inventory": self.inventory,
            "price": self.price,
            "production_quantity": self.production_quantity,
            "sales_quantity": self.sales_quantity,
            "wage_offered": self.wage_offered,
            "job_openings": self.job_openings,
            "skill_requirements": self.skill_requirements,
            "shareholders": self.shareholders,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FirmProfile":
        """辞書形式から復元"""
        data = data.copy()
        data["goods_category"] = GoodCategory(data["goods_category"])
        return cls(**data)


@dataclass
class GovernmentState:
    """
    政府の状態

    税収と支出を管理
    """

    # 財務状態
    reserves: float = 100000.0  # 準備金
    tax_revenue: float = 0.0  # 税収（当期）
    expenditure: float = 0.0  # 支出（当期）

    # 税制
    income_tax_brackets: list[tuple[float, float]] = field(
        default_factory=lambda: [
            (0, 0.0),
            (20000, 0.1),
            (50000, 0.2),
            (100000, 0.3),
        ]
    )
    vat_rate: float = 0.1  # 付加価値税率

    # 福祉政策
    ubi_enabled: bool = True
    ubi_amount: float = 500.0
    unemployment_benefit_rate: float = 0.5  # 失業給付率

    # マクロ経済指標（モニタリング用）
    gdp: float = 0.0
    real_gdp: float = 0.0
    inflation_rate: float = 0.0
    unemployment_rate: float = 0.0
    gini_coefficient: float = 0.0

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "reserves": self.reserves,
            "tax_revenue": self.tax_revenue,
            "expenditure": self.expenditure,
            "income_tax_brackets": self.income_tax_brackets,
            "vat_rate": self.vat_rate,
            "ubi_enabled": self.ubi_enabled,
            "ubi_amount": self.ubi_amount,
            "unemployment_benefit_rate": self.unemployment_benefit_rate,
            "gdp": self.gdp,
            "real_gdp": self.real_gdp,
            "inflation_rate": self.inflation_rate,
            "unemployment_rate": self.unemployment_rate,
            "gini_coefficient": self.gini_coefficient,
        }


@dataclass
class CentralBankState:
    """
    中央銀行の状態

    金融政策と金融システムを管理
    """

    # 金融政策
    policy_rate: float = 0.02  # 政策金利（2%）
    natural_rate: float = 0.02  # 自然利子率
    inflation_target: float = 0.02  # インフレ目標

    # Taylor rule パラメータ
    taylor_alpha: float = 1.5  # インフレ反応係数
    taylor_beta: float = 0.5  # 産出ギャップ反応係数
    smoothing_factor: float = 0.8  # 金利平滑化係数 ρ

    # 金融システム
    total_deposits: float = 0.0  # 総預金
    total_loans: float = 0.0  # 総貸出
    deposit_rate_spread: float = -0.01  # 預金金利スプレッド
    loan_rate_spread: float = 0.02  # 貸出金利スプレッド

    def get_deposit_rate(self) -> float:
        """預金金利を計算"""
        return max(0, self.policy_rate + self.deposit_rate_spread)

    def get_loan_rate(self) -> float:
        """貸出金利を計算"""
        return self.policy_rate + self.loan_rate_spread

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "policy_rate": self.policy_rate,
            "natural_rate": self.natural_rate,
            "inflation_target": self.inflation_target,
            "taylor_alpha": self.taylor_alpha,
            "taylor_beta": self.taylor_beta,
            "smoothing_factor": self.smoothing_factor,
            "total_deposits": self.total_deposits,
            "total_loans": self.total_loans,
            "deposit_rate_spread": self.deposit_rate_spread,
            "loan_rate_spread": self.loan_rate_spread,
        }


@dataclass
class MarketState:
    """
    市場の状態
    """

    # 労働市場
    total_jobs: int = 0  # 総求人数
    total_unemployed: int = 0  # 総失業者数
    job_vacancy_rate: float = 0.0  # 求人率

    # 財市場
    goods_prices: dict[str, float] = field(default_factory=dict)  # 商品名: 価格
    goods_demand: dict[str, float] = field(default_factory=dict)  # 商品名: 需要量
    goods_supply: dict[str, float] = field(default_factory=dict)  # 商品名: 供給量

    # 金融市場
    interest_rate: float = 0.02

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "total_jobs": self.total_jobs,
            "total_unemployed": self.total_unemployed,
            "job_vacancy_rate": self.job_vacancy_rate,
            "goods_prices": self.goods_prices,
            "goods_demand": self.goods_demand,
            "goods_supply": self.goods_supply,
            "interest_rate": self.interest_rate,
        }


@dataclass
class SimulationState:
    """
    シミュレーション全体の状態

    すべてのエージェントと市場の状態を保持
    """

    step: int = 0
    phase: str = "move_in"  # "move_in" or "development"

    households: list[HouseholdProfile] = field(default_factory=list)
    firms: list[FirmProfile] = field(default_factory=list)
    government: GovernmentState | None = None
    central_bank: CentralBankState | None = None
    market: MarketState = field(default_factory=MarketState)

    # 履歴データ（時系列記録用）
    history: dict[str, list[float]] = field(default_factory=dict)

    def get_household(self, household_id: int) -> HouseholdProfile | None:
        """IDから家計を取得"""
        for h in self.households:
            if h.id == household_id:
                return h
        return None

    def get_firm(self, firm_id: int) -> FirmProfile | None:
        """IDから企業を取得"""
        for f in self.firms:
            if f.id == firm_id:
                return f
        return None

    def to_dict(self) -> dict:
        """辞書形式に変換（保存用）"""
        return {
            "step": self.step,
            "phase": self.phase,
            "households": [h.to_dict() for h in self.households],
            "firms": [f.to_dict() for f in self.firms],
            "government": self.government.to_dict() if self.government else None,
            "central_bank": self.central_bank.to_dict() if self.central_bank else None,
            "market": self.market.to_dict(),
            "history": self.history,
        }
