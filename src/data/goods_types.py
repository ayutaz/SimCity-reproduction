"""
Goods Types Definition for SimCity Simulation

44種類の財定義と価格設定
論文で言及される10カテゴリ、44種類の異質財
"""

from dataclasses import dataclass

from src.models.data_models import GoodCategory


@dataclass
class GoodDefinition:
    """財の定義"""

    good_id: str
    name: str
    category: GoodCategory
    is_necessity: bool  # True: 必需品, False: 奢侈品
    base_price: float
    price_elasticity: float  # 価格弾力性（負の値）
    description: str


# 44種類の財定義
GOODS = [
    # FOOD (6 goods) - 必需品
    GoodDefinition(
        "food_basic",
        "Basic Food",
        GoodCategory.FOOD,
        True,
        20.0,
        -0.3,
        "Essential food items",
    ),
    GoodDefinition(
        "food_fresh",
        "Fresh Produce",
        GoodCategory.FOOD,
        True,
        30.0,
        -0.5,
        "Fresh fruits and vegetables",
    ),
    GoodDefinition(
        "food_meat",
        "Meat & Fish",
        GoodCategory.FOOD,
        True,
        50.0,
        -0.6,
        "Meat and seafood",
    ),
    GoodDefinition(
        "food_prepared",
        "Prepared Meals",
        GoodCategory.FOOD,
        False,
        40.0,
        -1.2,
        "Ready-to-eat meals",
    ),
    GoodDefinition(
        "food_restaurant",
        "Restaurant Dining",
        GoodCategory.FOOD,
        False,
        80.0,
        -1.5,
        "Restaurant services",
    ),
    GoodDefinition(
        "food_gourmet",
        "Gourmet Food",
        GoodCategory.FOOD,
        False,
        120.0,
        -2.0,
        "High-end gourmet items",
    ),
    # CLOTHING (5 goods)
    GoodDefinition(
        "clothing_basic",
        "Basic Clothing",
        GoodCategory.CLOTHING,
        True,
        30.0,
        -0.4,
        "Essential clothing",
    ),
    GoodDefinition(
        "clothing_casual",
        "Casual Wear",
        GoodCategory.CLOTHING,
        False,
        60.0,
        -1.0,
        "Everyday casual clothing",
    ),
    GoodDefinition(
        "clothing_formal",
        "Formal Wear",
        GoodCategory.CLOTHING,
        False,
        150.0,
        -1.3,
        "Business and formal attire",
    ),
    GoodDefinition(
        "clothing_luxury",
        "Luxury Fashion",
        GoodCategory.CLOTHING,
        False,
        500.0,
        -2.5,
        "Designer and luxury brands",
    ),
    GoodDefinition(
        "clothing_footwear",
        "Footwear",
        GoodCategory.CLOTHING,
        True,
        50.0,
        -0.7,
        "Shoes and footwear",
    ),
    # HOUSING (4 goods) - 必需品
    GoodDefinition(
        "housing_basic",
        "Basic Housing",
        GoodCategory.HOUSING,
        True,
        800.0,
        -0.2,
        "Basic apartment rental",
    ),
    GoodDefinition(
        "housing_standard",
        "Standard Housing",
        GoodCategory.HOUSING,
        True,
        1200.0,
        -0.4,
        "Standard apartment",
    ),
    GoodDefinition(
        "housing_premium",
        "Premium Housing",
        GoodCategory.HOUSING,
        False,
        2000.0,
        -1.0,
        "High-quality housing",
    ),
    GoodDefinition(
        "housing_luxury",
        "Luxury Housing",
        GoodCategory.HOUSING,
        False,
        4000.0,
        -1.8,
        "Luxury residences",
    ),
    # TRANSPORTATION (5 goods)
    GoodDefinition(
        "trans_public",
        "Public Transport",
        GoodCategory.TRANSPORTATION,
        True,
        50.0,
        -0.3,
        "Bus and subway passes",
    ),
    GoodDefinition(
        "trans_taxi",
        "Taxi Services",
        GoodCategory.TRANSPORTATION,
        False,
        100.0,
        -1.2,
        "Taxi and ride-sharing",
    ),
    GoodDefinition(
        "trans_vehicle_economy",
        "Economy Vehicle",
        GoodCategory.TRANSPORTATION,
        False,
        15000.0,
        -1.5,
        "Basic car purchase",
    ),
    GoodDefinition(
        "trans_vehicle_standard",
        "Standard Vehicle",
        GoodCategory.TRANSPORTATION,
        False,
        30000.0,
        -1.8,
        "Standard car",
    ),
    GoodDefinition(
        "trans_vehicle_luxury",
        "Luxury Vehicle",
        GoodCategory.TRANSPORTATION,
        False,
        80000.0,
        -2.5,
        "Luxury car",
    ),
    # HEALTHCARE (4 goods) - 必需品
    GoodDefinition(
        "health_basic",
        "Basic Healthcare",
        GoodCategory.HEALTHCARE,
        True,
        100.0,
        -0.2,
        "Basic medical services",
    ),
    GoodDefinition(
        "health_dental",
        "Dental Care",
        GoodCategory.HEALTHCARE,
        True,
        150.0,
        -0.4,
        "Dental services",
    ),
    GoodDefinition(
        "health_specialized",
        "Specialized Care",
        GoodCategory.HEALTHCARE,
        True,
        300.0,
        -0.5,
        "Specialist medical care",
    ),
    GoodDefinition(
        "health_wellness",
        "Wellness Services",
        GoodCategory.HEALTHCARE,
        False,
        200.0,
        -1.5,
        "Preventive and wellness",
    ),
    # EDUCATION (4 goods)
    GoodDefinition(
        "edu_basic",
        "Basic Education",
        GoodCategory.EDUCATION,
        True,
        200.0,
        -0.3,
        "Primary and secondary education",
    ),
    GoodDefinition(
        "edu_higher",
        "Higher Education",
        GoodCategory.EDUCATION,
        False,
        5000.0,
        -0.8,
        "College and university",
    ),
    GoodDefinition(
        "edu_vocational",
        "Vocational Training",
        GoodCategory.EDUCATION,
        False,
        1000.0,
        -1.0,
        "Skills training",
    ),
    GoodDefinition(
        "edu_tutoring",
        "Private Tutoring",
        GoodCategory.EDUCATION,
        False,
        500.0,
        -1.3,
        "Private lessons",
    ),
    # ENTERTAINMENT (5 goods) - 奢侈品
    GoodDefinition(
        "ent_media",
        "Media & Streaming",
        GoodCategory.ENTERTAINMENT,
        False,
        50.0,
        -1.0,
        "TV, streaming services",
    ),
    GoodDefinition(
        "ent_events",
        "Events & Shows",
        GoodCategory.ENTERTAINMENT,
        False,
        100.0,
        -1.5,
        "Concerts, theater, sports",
    ),
    GoodDefinition(
        "ent_hobbies",
        "Hobbies & Crafts",
        GoodCategory.ENTERTAINMENT,
        False,
        80.0,
        -1.3,
        "Hobby supplies and activities",
    ),
    GoodDefinition(
        "ent_gaming",
        "Gaming",
        GoodCategory.ENTERTAINMENT,
        False,
        60.0,
        -1.4,
        "Video games and consoles",
    ),
    GoodDefinition(
        "ent_travel",
        "Travel & Vacation",
        GoodCategory.ENTERTAINMENT,
        False,
        2000.0,
        -2.0,
        "Tourism and vacations",
    ),
    # UTILITIES (3 goods) - 必需品
    GoodDefinition(
        "util_electricity",
        "Electricity",
        GoodCategory.UTILITIES,
        True,
        80.0,
        -0.1,
        "Electrical power",
    ),
    GoodDefinition(
        "util_water",
        "Water & Sewage",
        GoodCategory.UTILITIES,
        True,
        40.0,
        -0.1,
        "Water and sewage services",
    ),
    GoodDefinition(
        "util_internet",
        "Internet & Phone",
        GoodCategory.UTILITIES,
        True,
        60.0,
        -0.3,
        "Communication services",
    ),
    # FURNITURE (4 goods)
    GoodDefinition(
        "furn_basic",
        "Basic Furniture",
        GoodCategory.FURNITURE,
        True,
        500.0,
        -0.5,
        "Essential furniture",
    ),
    GoodDefinition(
        "furn_appliances",
        "Home Appliances",
        GoodCategory.FURNITURE,
        True,
        800.0,
        -0.7,
        "Refrigerator, washer, etc.",
    ),
    GoodDefinition(
        "furn_decor",
        "Home Decor",
        GoodCategory.FURNITURE,
        False,
        300.0,
        -1.2,
        "Decorative items",
    ),
    GoodDefinition(
        "furn_premium",
        "Premium Furniture",
        GoodCategory.FURNITURE,
        False,
        2000.0,
        -1.8,
        "High-end furniture",
    ),
    # OTHER (4 goods)
    GoodDefinition(
        "other_personal_care",
        "Personal Care",
        GoodCategory.OTHER,
        True,
        40.0,
        -0.4,
        "Hygiene and grooming",
    ),
    GoodDefinition(
        "other_insurance",
        "Insurance",
        GoodCategory.OTHER,
        True,
        150.0,
        -0.2,
        "Various insurance policies",
    ),
    GoodDefinition(
        "other_financial",
        "Financial Services",
        GoodCategory.OTHER,
        False,
        100.0,
        -0.6,
        "Banking and financial services",
    ),
    GoodDefinition(
        "other_luxury",
        "Luxury Goods",
        GoodCategory.OTHER,
        False,
        1000.0,
        -2.0,
        "Jewelry, watches, etc.",
    ),
]

# 財IDから定義へのマッピング
GOODS_MAP = {good.good_id: good for good in GOODS}

# カテゴリごとの財リスト
GOODS_BY_CATEGORY = {
    category: [good for good in GOODS if good.category == category]
    for category in GoodCategory
}

# 必需品リスト
NECESSITY_GOODS = [good for good in GOODS if good.is_necessity]

# 奢侈品リスト
LUXURY_GOODS = [good for good in GOODS if not good.is_necessity]


def get_good(good_id: str) -> GoodDefinition | None:
    """
    財IDから財定義を取得

    Args:
        good_id: 財ID

    Returns:
        財定義（存在しない場合はNone）
    """
    return GOODS_MAP.get(good_id)


def get_goods_by_category(category: GoodCategory) -> list[GoodDefinition]:
    """
    カテゴリから財リストを取得

    Args:
        category: 財カテゴリ

    Returns:
        財定義のリスト
    """
    return GOODS_BY_CATEGORY.get(category, [])


def get_all_good_ids() -> list[str]:
    """
    全財IDを取得

    Returns:
        財IDのリスト
    """
    return list(GOODS_MAP.keys())


def calculate_demand_from_price(
    base_demand: float, base_price: float, current_price: float, elasticity: float
) -> float:
    """
    価格弾力性を用いて需要を計算

    Q = Q0 * (P/P0)^ε

    Args:
        base_demand: 基準需要量
        base_price: 基準価格
        current_price: 現在価格
        elasticity: 価格弾力性（負の値）

    Returns:
        需要量
    """
    if current_price <= 0 or base_price <= 0:
        return 0.0

    price_ratio = current_price / base_price
    demand = base_demand * (price_ratio**elasticity)

    return max(0.0, demand)


def calculate_engel_coefficient(food_expenditure: float, total_income: float) -> float:
    """
    エンゲル係数を計算

    Args:
        food_expenditure: 食料支出
        total_income: 総所得

    Returns:
        エンゲル係数（0-1）
    """
    if total_income <= 0:
        return 0.0

    return min(1.0, food_expenditure / total_income)
