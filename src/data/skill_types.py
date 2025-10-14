"""
Skill Types Definition for SimCity Simulation

58種類のスキル定義とカテゴリ分類
論文で言及されているスキルベースのマッチングに使用
"""

from dataclasses import dataclass
from enum import Enum


class SkillCategory(Enum):
    """スキルカテゴリ"""

    TECHNOLOGY = "technology"  # 技術系
    BUSINESS = "business"  # ビジネス系
    CREATIVE = "creative"  # クリエイティブ系
    HEALTHCARE = "healthcare"  # 医療・健康系
    EDUCATION = "education"  # 教育系
    MANUFACTURING = "manufacturing"  # 製造系
    SERVICE = "service"  # サービス系
    CONSTRUCTION = "construction"  # 建設系
    TRANSPORT = "transport"  # 運輸系
    AGRICULTURE = "agriculture"  # 農業系


@dataclass
class SkillDefinition:
    """スキル定義"""

    skill_id: str
    name: str
    category: SkillCategory
    description: str
    base_wage_multiplier: float = 1.0  # 基本賃金倍率


# 58種類のスキル定義
SKILLS = [
    # Technology (10 skills)
    SkillDefinition(
        "tech_programming",
        "Programming",
        SkillCategory.TECHNOLOGY,
        "Software development and coding",
        1.5,
    ),
    SkillDefinition(
        "tech_data_analysis",
        "Data Analysis",
        SkillCategory.TECHNOLOGY,
        "Data science and analytics",
        1.4,
    ),
    SkillDefinition(
        "tech_ai_ml",
        "AI/ML",
        SkillCategory.TECHNOLOGY,
        "Artificial intelligence and machine learning",
        1.6,
    ),
    SkillDefinition(
        "tech_cybersecurity",
        "Cybersecurity",
        SkillCategory.TECHNOLOGY,
        "Information security",
        1.5,
    ),
    SkillDefinition(
        "tech_cloud_computing",
        "Cloud Computing",
        SkillCategory.TECHNOLOGY,
        "Cloud infrastructure and services",
        1.4,
    ),
    SkillDefinition(
        "tech_networking",
        "Networking",
        SkillCategory.TECHNOLOGY,
        "Network administration and engineering",
        1.3,
    ),
    SkillDefinition(
        "tech_database",
        "Database Management",
        SkillCategory.TECHNOLOGY,
        "Database design and administration",
        1.3,
    ),
    SkillDefinition(
        "tech_web_dev",
        "Web Development",
        SkillCategory.TECHNOLOGY,
        "Website and web application development",
        1.3,
    ),
    SkillDefinition(
        "tech_mobile_dev",
        "Mobile Development",
        SkillCategory.TECHNOLOGY,
        "Mobile app development",
        1.4,
    ),
    SkillDefinition(
        "tech_devops", "DevOps", SkillCategory.TECHNOLOGY, "DevOps and CI/CD", 1.4
    ),
    # Business (10 skills)
    SkillDefinition(
        "biz_accounting",
        "Accounting",
        SkillCategory.BUSINESS,
        "Financial accounting and bookkeeping",
        1.2,
    ),
    SkillDefinition(
        "biz_finance",
        "Finance",
        SkillCategory.BUSINESS,
        "Financial analysis and management",
        1.4,
    ),
    SkillDefinition(
        "biz_marketing",
        "Marketing",
        SkillCategory.BUSINESS,
        "Marketing strategy and execution",
        1.2,
    ),
    SkillDefinition(
        "biz_sales", "Sales", SkillCategory.BUSINESS, "Sales and customer relations", 1.1
    ),
    SkillDefinition(
        "biz_hr",
        "Human Resources",
        SkillCategory.BUSINESS,
        "HR management and recruitment",
        1.1,
    ),
    SkillDefinition(
        "biz_project_mgmt",
        "Project Management",
        SkillCategory.BUSINESS,
        "Project planning and execution",
        1.3,
    ),
    SkillDefinition(
        "biz_business_analysis",
        "Business Analysis",
        SkillCategory.BUSINESS,
        "Business process analysis",
        1.2,
    ),
    SkillDefinition(
        "biz_consulting",
        "Consulting",
        SkillCategory.BUSINESS,
        "Business consulting",
        1.4,
    ),
    SkillDefinition(
        "biz_operations",
        "Operations Management",
        SkillCategory.BUSINESS,
        "Operations and logistics",
        1.2,
    ),
    SkillDefinition(
        "biz_entrepreneurship",
        "Entrepreneurship",
        SkillCategory.BUSINESS,
        "Business creation and management",
        1.3,
    ),
    # Creative (8 skills)
    SkillDefinition(
        "creative_graphic_design",
        "Graphic Design",
        SkillCategory.CREATIVE,
        "Visual design and graphics",
        1.1,
    ),
    SkillDefinition(
        "creative_video_production",
        "Video Production",
        SkillCategory.CREATIVE,
        "Video creation and editing",
        1.2,
    ),
    SkillDefinition(
        "creative_writing",
        "Writing",
        SkillCategory.CREATIVE,
        "Content writing and copywriting",
        1.0,
    ),
    SkillDefinition(
        "creative_photography",
        "Photography",
        SkillCategory.CREATIVE,
        "Photography and image capture",
        1.0,
    ),
    SkillDefinition(
        "creative_music",
        "Music Production",
        SkillCategory.CREATIVE,
        "Music creation and production",
        1.1,
    ),
    SkillDefinition(
        "creative_animation",
        "Animation",
        SkillCategory.CREATIVE,
        "2D/3D animation",
        1.2,
    ),
    SkillDefinition(
        "creative_ui_ux",
        "UI/UX Design",
        SkillCategory.CREATIVE,
        "User interface and experience design",
        1.3,
    ),
    SkillDefinition(
        "creative_illustration",
        "Illustration",
        SkillCategory.CREATIVE,
        "Artistic illustration",
        1.0,
    ),
    # Healthcare (6 skills)
    SkillDefinition(
        "health_nursing",
        "Nursing",
        SkillCategory.HEALTHCARE,
        "Patient care and nursing",
        1.3,
    ),
    SkillDefinition(
        "health_pharmacy",
        "Pharmacy",
        SkillCategory.HEALTHCARE,
        "Pharmaceutical services",
        1.4,
    ),
    SkillDefinition(
        "health_medical_tech",
        "Medical Technology",
        SkillCategory.HEALTHCARE,
        "Medical equipment and technology",
        1.3,
    ),
    SkillDefinition(
        "health_physical_therapy",
        "Physical Therapy",
        SkillCategory.HEALTHCARE,
        "Physical rehabilitation",
        1.2,
    ),
    SkillDefinition(
        "health_mental_health",
        "Mental Health",
        SkillCategory.HEALTHCARE,
        "Mental health counseling",
        1.2,
    ),
    SkillDefinition(
        "health_emergency_care",
        "Emergency Care",
        SkillCategory.HEALTHCARE,
        "Emergency medical services",
        1.4,
    ),
    # Education (4 skills)
    SkillDefinition(
        "edu_teaching",
        "Teaching",
        SkillCategory.EDUCATION,
        "General teaching skills",
        1.0,
    ),
    SkillDefinition(
        "edu_curriculum",
        "Curriculum Development",
        SkillCategory.EDUCATION,
        "Educational program design",
        1.1,
    ),
    SkillDefinition(
        "edu_tutoring",
        "Tutoring",
        SkillCategory.EDUCATION,
        "One-on-one instruction",
        0.9,
    ),
    SkillDefinition(
        "edu_training",
        "Training & Development",
        SkillCategory.EDUCATION,
        "Corporate training",
        1.1,
    ),
    # Manufacturing (6 skills)
    SkillDefinition(
        "mfg_assembly",
        "Assembly",
        SkillCategory.MANUFACTURING,
        "Product assembly",
        0.9,
    ),
    SkillDefinition(
        "mfg_quality_control",
        "Quality Control",
        SkillCategory.MANUFACTURING,
        "Quality assurance and testing",
        1.0,
    ),
    SkillDefinition(
        "mfg_machine_operation",
        "Machine Operation",
        SkillCategory.MANUFACTURING,
        "Industrial machinery operation",
        1.0,
    ),
    SkillDefinition(
        "mfg_maintenance",
        "Equipment Maintenance",
        SkillCategory.MANUFACTURING,
        "Equipment repair and maintenance",
        1.1,
    ),
    SkillDefinition(
        "mfg_production_planning",
        "Production Planning",
        SkillCategory.MANUFACTURING,
        "Manufacturing planning and scheduling",
        1.2,
    ),
    SkillDefinition(
        "mfg_supply_chain",
        "Supply Chain",
        SkillCategory.MANUFACTURING,
        "Supply chain management",
        1.2,
    ),
    # Service (6 skills)
    SkillDefinition(
        "svc_customer_service",
        "Customer Service",
        SkillCategory.SERVICE,
        "Customer support and service",
        0.8,
    ),
    SkillDefinition(
        "svc_hospitality",
        "Hospitality",
        SkillCategory.SERVICE,
        "Hotel and restaurant service",
        0.9,
    ),
    SkillDefinition(
        "svc_retail", "Retail", SkillCategory.SERVICE, "Retail sales and operations", 0.8
    ),
    SkillDefinition(
        "svc_food_service",
        "Food Service",
        SkillCategory.SERVICE,
        "Food preparation and service",
        0.8,
    ),
    SkillDefinition(
        "svc_cleaning",
        "Cleaning Services",
        SkillCategory.SERVICE,
        "Cleaning and maintenance",
        0.7,
    ),
    SkillDefinition(
        "svc_security",
        "Security",
        SkillCategory.SERVICE,
        "Security and protection services",
        0.9,
    ),
    # Construction (4 skills)
    SkillDefinition(
        "const_carpentry",
        "Carpentry",
        SkillCategory.CONSTRUCTION,
        "Woodworking and carpentry",
        1.1,
    ),
    SkillDefinition(
        "const_electrical",
        "Electrical Work",
        SkillCategory.CONSTRUCTION,
        "Electrical installation and repair",
        1.2,
    ),
    SkillDefinition(
        "const_plumbing",
        "Plumbing",
        SkillCategory.CONSTRUCTION,
        "Plumbing installation and repair",
        1.1,
    ),
    SkillDefinition(
        "const_hvac",
        "HVAC",
        SkillCategory.CONSTRUCTION,
        "Heating, ventilation, and air conditioning",
        1.1,
    ),
    # Transport (2 skills)
    SkillDefinition(
        "trans_driving",
        "Driving",
        SkillCategory.TRANSPORT,
        "Vehicle operation and delivery",
        0.9,
    ),
    SkillDefinition(
        "trans_logistics",
        "Logistics",
        SkillCategory.TRANSPORT,
        "Transportation planning and logistics",
        1.1,
    ),
    # Agriculture (2 skills)
    SkillDefinition(
        "agri_farming",
        "Farming",
        SkillCategory.AGRICULTURE,
        "Crop cultivation and farming",
        0.8,
    ),
    SkillDefinition(
        "agri_animal_husbandry",
        "Animal Husbandry",
        SkillCategory.AGRICULTURE,
        "Livestock care and management",
        0.9,
    ),
]

# スキルIDから定義へのマッピング
SKILL_MAP = {skill.skill_id: skill for skill in SKILLS}

# カテゴリごとのスキルリスト
SKILLS_BY_CATEGORY = {
    category: [skill for skill in SKILLS if skill.category == category]
    for category in SkillCategory
}


def get_skill(skill_id: str) -> SkillDefinition | None:
    """
    スキルIDからスキル定義を取得

    Args:
        skill_id: スキルID

    Returns:
        スキル定義（存在しない場合はNone）
    """
    return SKILL_MAP.get(skill_id)


def get_skills_by_category(category: SkillCategory) -> list[SkillDefinition]:
    """
    カテゴリからスキルリストを取得

    Args:
        category: スキルカテゴリ

    Returns:
        スキル定義のリスト
    """
    return SKILLS_BY_CATEGORY.get(category, [])


def get_all_skill_ids() -> list[str]:
    """
    全スキルIDを取得

    Returns:
        スキルIDのリスト
    """
    return list(SKILL_MAP.keys())


def calculate_wage_multiplier(skills: dict[str, float]) -> float:
    """
    スキルセットから賃金倍率を計算

    Args:
        skills: スキルID: レベル(0-1)の辞書

    Returns:
        賃金倍率（1.0が基準）
    """
    if not skills:
        return 0.7  # スキルなしの場合は低賃金

    total_multiplier = 0.0
    count = 0

    for skill_id, level in skills.items():
        skill_def = get_skill(skill_id)
        if skill_def:
            # スキルレベルに応じて倍率を調整
            multiplier = skill_def.base_wage_multiplier * level
            total_multiplier += multiplier
            count += 1

    if count == 0:
        return 0.7

    # 平均倍率を計算
    avg_multiplier = total_multiplier / count

    # 複数スキル保有ボーナス（最大20%）
    skill_diversity_bonus = min(0.2, (count - 1) * 0.05)

    return avg_multiplier * (1 + skill_diversity_bonus)
