"""
Initial Household Dataset Generator

200世帯の初期データセットを生成し、JSONファイルに保存
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.agents.household import HouseholdProfileGenerator
from src.utils.logger import setup_logger

# Setup logger
setup_logger(log_level="INFO")


def generate_initial_households(
    count: int = 200,
    output_path: str = "data/initial_households.json",
    random_seed: int = 42,
):
    """
    初期世帯データセットを生成

    Args:
        count: 生成する世帯数（デフォルト: 200）
        output_path: 出力ファイルパス
        random_seed: 乱数シード（再現性のため）
    """
    logger.info(f"Generating {count} initial households with seed={random_seed}")

    # Generator作成
    generator = HouseholdProfileGenerator(
        income_mean=10.5,  # log(income)の平均 -> exp(10.5) ≈ $36,315
        income_std=0.5,  # 標準偏差
        age_mean=40.0,  # 平均年齢40歳
        age_std=12.0,  # 標準偏差12歳
        random_seed=random_seed,
    )

    # 世帯プロファイル生成
    profiles = generator.generate(count=count)

    # 統計情報の計算
    ages = [p.age for p in profiles]
    incomes = [p.cash for p in profiles]
    monthly_incomes = [p.monthly_income for p in profiles]
    employed = sum(1 for p in profiles if p.employment_status.value == "employed")

    logger.info(f"Generated {len(profiles)} households")
    logger.info(f"Age: mean={sum(ages) / len(ages):.1f}, min={min(ages)}, max={max(ages)}")
    logger.info(
        f"Initial Cash: mean=${sum(incomes) / len(incomes):.2f}, "
        f"min=${min(incomes):.2f}, max=${max(incomes):.2f}"
    )
    logger.info(
        f"Monthly Income: mean=${sum(monthly_incomes) / len(monthly_incomes):.2f}"
    )
    logger.info(f"Employment Rate: {employed / len(profiles) * 100:.1f}%")

    # JSON形式に変換
    households_data = {
        "metadata": {
            "count": count,
            "random_seed": random_seed,
            "income_mean": 10.5,
            "income_std": 0.5,
            "age_mean": 40.0,
            "age_std": 12.0,
        },
        "statistics": {
            "age_mean": sum(ages) / len(ages),
            "age_min": min(ages),
            "age_max": max(ages),
            "cash_mean": sum(incomes) / len(incomes),
            "cash_min": min(incomes),
            "cash_max": max(incomes),
            "monthly_income_mean": sum(monthly_incomes) / len(monthly_incomes),
            "employment_rate": employed / len(profiles),
        },
        "households": [p.to_dict() for p in profiles],
    }

    # ファイルに保存
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(households_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved to {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")

    return households_data


def load_initial_households(file_path: str = "data/initial_households.json") -> dict:
    """
    初期世帯データを読み込む

    Args:
        file_path: 読み込むファイルパス

    Returns:
        世帯データの辞書
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {data['metadata']['count']} households from {file_path}")
    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate initial household dataset"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="Number of households to generate (default: 200)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/initial_households.json",
        help="Output file path (default: data/initial_households.json)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    # 生成実行
    generate_initial_households(
        count=args.count,
        output_path=args.output,
        random_seed=args.seed,
    )

    logger.info("Done!")
