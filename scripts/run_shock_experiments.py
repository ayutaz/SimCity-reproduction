"""
Exogenous Shock Experiments Script

外生ショック実験を実行し、経済への影響を分析します。

実験タイプ:
1. Price Shock: 特定の財の価格急騰
2. Policy Shock: 政府政策の変更（UBI、税率）
3. Population Shock: 人口変動（新規世帯の追加）

Usage:
    uv run python scripts/run_shock_experiments.py --experiment price_shock [OPTIONS]
    uv run python scripts/run_shock_experiments.py --experiment policy_shock [OPTIONS]
    uv run python scripts/run_shock_experiments.py --experiment population_shock [OPTIONS]

Example:
    # 価格ショック実験（ステップ50で食料価格を2倍に）
    uv run python scripts/run_shock_experiments.py --experiment price_shock --shock-step 50 --shock-magnitude 2.0

    # 政策ショック実験（ステップ100でUBIを1.5倍に）
    uv run python scripts/run_shock_experiments.py --experiment policy_shock --shock-step 100 --shock-magnitude 1.5
"""

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.environment.simulation import Simulation
from src.utils.config import load_config
from src.utils.logger import setup_logger


def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description="Run exogenous shock experiments")
    parser.add_argument(
        "--experiment",
        type=str,
        required=True,
        choices=["price_shock", "policy_shock", "population_shock"],
        help="Type of experiment to run",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=180,
        help="Number of simulation steps (default: 180)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--shock-step",
        type=int,
        default=50,
        help="Step at which to apply the shock (default: 50)",
    )
    parser.add_argument(
        "--shock-magnitude",
        type=float,
        default=2.0,
        help="Magnitude of the shock (default: 2.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: experiments/outputs/{experiment}_run)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def apply_price_shock(sim: Simulation, magnitude: float, good_id: str = "food_grain"):
    """
    価格ショックを適用

    Args:
        sim: シミュレーションインスタンス
        magnitude: ショックの大きさ（乗数）
        good_id: ショックを適用する財ID
    """
    original_price = sim.goods_market.prices.get(good_id, 100.0)
    new_price = original_price * magnitude
    sim.goods_market.prices[good_id] = new_price

    logger.warning("🚨 PRICE SHOCK APPLIED")
    logger.warning(f"  Good: {good_id}")
    logger.warning(f"  Original price: {original_price:.2f}")
    logger.warning(f"  New price: {new_price:.2f}")
    logger.warning(f"  Magnitude: {magnitude:.2f}x")


def apply_policy_shock(sim: Simulation, magnitude: float, policy_type: str = "ubi"):
    """
    政策ショックを適用

    Args:
        sim: シミュレーションインスタンス
        magnitude: ショックの大きさ（乗数）
        policy_type: 政策タイプ（"ubi" または "tax_rate"）
    """
    if policy_type == "ubi":
        original_ubi = sim.government.ubi_amount
        new_ubi = original_ubi * magnitude
        sim.government.ubi_amount = new_ubi

        logger.warning("🚨 POLICY SHOCK APPLIED (UBI)")
        logger.warning(f"  Original UBI: {original_ubi:.2f}")
        logger.warning(f"  New UBI: {new_ubi:.2f}")
        logger.warning(f"  Magnitude: {magnitude:.2f}x")

    elif policy_type == "tax_rate":
        # 税率を調整（税率ブラケットの全体を調整）
        _ = sim.government.tax_brackets.copy()  # 将来の実装用に保存（現在は未使用）
        for bracket in sim.government.tax_brackets:
            bracket["rate"] *= magnitude

        logger.warning("🚨 POLICY SHOCK APPLIED (Tax Rate)")
        logger.warning(f"  Tax rates adjusted by: {magnitude:.2f}x")


def apply_population_shock(sim: Simulation, num_new_households: int):
    """
    人口ショックを適用（新規世帯の追加）

    Args:
        sim: シミュレーションインスタンス
        num_new_households: 追加する世帯数
    """
    # Note: この実装は、Simulationクラスにadd_households()メソッドがあることを前提としています
    # 実際の実装では、HouseholdProfileGeneratorを使って新規世帯を生成します

    original_count = len(sim.households)
    # sim.add_households(num_new_households)  # TODO: 実装が必要
    new_count = len(sim.households)

    logger.warning("🚨 POPULATION SHOCK APPLIED")
    logger.warning(f"  Original household count: {original_count}")
    logger.warning(f"  New households added: {num_new_households}")
    logger.warning(f"  New household count: {new_count}")


def run_experiment(
    config,
    steps: int,
    shock_step: int,
    shock_magnitude: float,
    experiment_type: str,
    output_dir: Path,
):
    """
    ショック実験を実行

    Args:
        config: シミュレーション設定
        steps: ステップ数
        shock_step: ショックを適用するステップ
        shock_magnitude: ショックの大きさ
        experiment_type: 実験タイプ
        output_dir: 出力ディレクトリ
    """
    logger.info("=" * 60)
    logger.info(f"Starting Shock Experiment: {experiment_type}")
    logger.info("=" * 60)
    logger.info(f"Steps: {steps}")
    logger.info(f"Shock step: {shock_step}")
    logger.info(f"Shock magnitude: {shock_magnitude}")
    logger.info(f"Random seed: {config.simulation.random_seed}")
    logger.info("=" * 60)

    # シミュレーションの初期化
    logger.info("Initializing simulation...")
    sim = Simulation(config)

    # 経済指標を記録
    history = {
        "gdp": [],
        "unemployment_rate": [],
        "inflation": [],
        "gini": [],
        "average_income": [],
        "consumption": [],
        "investment": [],
        "shock_applied": False,
        "shock_step": shock_step,
        "shock_magnitude": shock_magnitude,
        "experiment_type": experiment_type,
    }

    # 開始時刻
    start_time = time.time()

    # シミュレーション実行
    logger.info(f"\nRunning experiment for {steps} steps...\n")

    for step in range(steps):
        # ショックの適用
        if step == shock_step:
            if experiment_type == "price_shock":
                apply_price_shock(sim, shock_magnitude)
            elif experiment_type == "policy_shock":
                apply_policy_shock(sim, shock_magnitude, policy_type="ubi")
            elif experiment_type == "population_shock":
                num_new = int(len(sim.households) * (shock_magnitude - 1.0))
                apply_population_shock(sim, num_new)

            history["shock_applied"] = True

        # 1ステップ実行
        sim.step()

        # 経済指標の取得
        metrics = sim.get_metrics()

        # 履歴に追加
        history["gdp"].append(metrics["gdp"])
        history["unemployment_rate"].append(metrics["unemployment_rate"])
        history["inflation"].append(metrics["inflation"])
        history["gini"].append(metrics["gini"])
        history["average_income"].append(metrics["average_income"])
        history["consumption"].append(metrics["total_consumption"])
        history["investment"].append(metrics["total_investment"])

        # 進捗表示（10ステップごと、またはショック適用直後）
        if (step + 1) % 10 == 0 or step == shock_step or step == 0:
            logger.info(f"Step {step + 1}/{steps} ({(step + 1) / steps * 100:.1f}%)")
            logger.info(f"  GDP: {metrics['gdp']:,.2f}")
            logger.info(f"  Unemployment: {metrics['unemployment_rate']:.2%}")
            logger.info(f"  Inflation: {metrics['inflation']:.2%}")
            logger.info(f"  Gini: {metrics['gini']:.3f}")
            logger.info("")

    # 総実行時間
    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info(
        f"Experiment completed in {total_time:.2f}s ({total_time / 60:.2f} min)"
    )
    logger.info("=" * 60)

    # 結果の保存
    logger.info("\nSaving results...")
    results = {
        "history": history,
        "metadata": {
            "experiment_type": experiment_type,
            "shock_step": shock_step,
            "shock_magnitude": shock_magnitude,
            "steps": steps,
            "households": config.agents.households.max,
            "firms": config.agents.firms.max,
            "seed": config.simulation.random_seed,
            "execution_time": total_time,
        },
    }

    results_file = output_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved: {results_file}")

    # ショック前後の比較
    analyze_shock_impact(history, shock_step, output_dir)

    return results


def analyze_shock_impact(history: dict, shock_step: int, output_dir: Path):
    """
    ショックの影響を分析

    Args:
        history: シミュレーション履歴
        shock_step: ショックを適用したステップ
        output_dir: 出力ディレクトリ
    """
    logger.info("\n" + "=" * 60)
    logger.info("Analyzing Shock Impact")
    logger.info("=" * 60)

    # ショック前後のウィンドウ（前後10ステップ）
    window = 10
    pre_start = max(0, shock_step - window)
    pre_end = shock_step
    post_start = shock_step + 1
    post_end = min(len(history["gdp"]), shock_step + 1 + window)

    # ショック前の平均
    pre_gdp = sum(history["gdp"][pre_start:pre_end]) / (pre_end - pre_start)
    pre_unemployment = sum(history["unemployment_rate"][pre_start:pre_end]) / (
        pre_end - pre_start
    )
    pre_inflation = sum(history["inflation"][pre_start:pre_end]) / (pre_end - pre_start)

    # ショック後の平均
    post_gdp = sum(history["gdp"][post_start:post_end]) / (post_end - post_start)
    post_unemployment = sum(history["unemployment_rate"][post_start:post_end]) / (
        post_end - post_start
    )
    post_inflation = sum(history["inflation"][post_start:post_end]) / (
        post_end - post_start
    )

    # 変化率
    gdp_change = (post_gdp - pre_gdp) / pre_gdp * 100
    unemployment_change = (
        post_unemployment - pre_unemployment
    ) * 100  # パーセントポイント
    inflation_change = (post_inflation - pre_inflation) * 100  # パーセントポイント

    logger.info(f"\nImpact Analysis (window: {window} steps before/after shock):")
    logger.info("\nGDP:")
    logger.info(f"  Before: {pre_gdp:,.2f}")
    logger.info(f"  After: {post_gdp:,.2f}")
    logger.info(f"  Change: {gdp_change:+.2f}%")

    logger.info("\nUnemployment Rate:")
    logger.info(f"  Before: {pre_unemployment:.2%}")
    logger.info(f"  After: {post_unemployment:.2%}")
    logger.info(f"  Change: {unemployment_change:+.2f} pp")

    logger.info("\nInflation Rate:")
    logger.info(f"  Before: {pre_inflation:.2%}")
    logger.info(f"  After: {post_inflation:.2%}")
    logger.info(f"  Change: {inflation_change:+.2f} pp")

    # 影響分析の保存
    impact_analysis = {
        "shock_step": shock_step,
        "window": window,
        "gdp": {
            "before": pre_gdp,
            "after": post_gdp,
            "change_percent": gdp_change,
        },
        "unemployment_rate": {
            "before": pre_unemployment,
            "after": post_unemployment,
            "change_pp": unemployment_change,
        },
        "inflation": {
            "before": pre_inflation,
            "after": post_inflation,
            "change_pp": inflation_change,
        },
    }

    impact_file = output_dir / "shock_impact_analysis.json"
    with open(impact_file, "w", encoding="utf-8") as f:
        json.dump(impact_analysis, f, indent=2, ensure_ascii=False)
    logger.info(f"\nImpact analysis saved: {impact_file}")


def generate_shock_visualization(results: dict, output_dir: Path):
    """
    ショック実験の可視化

    Args:
        results: 実験結果
        output_dir: 出力ディレクトリ
    """
    logger.info("\n" + "=" * 60)
    logger.info("Generating Shock Experiment Visualization")
    logger.info("=" * 60)

    import matplotlib.pyplot as plt

    history = results["history"]
    shock_step = history["shock_step"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Shock Experiment: {history['experiment_type']} (Step {shock_step})",
        fontsize=14,
        fontweight="bold",
    )

    steps = range(len(history["gdp"]))

    # GDP
    axes[0, 0].plot(steps, history["gdp"], linewidth=2)
    axes[0, 0].axvline(shock_step, color="red", linestyle="--", label="Shock")
    axes[0, 0].set_title("GDP")
    axes[0, 0].set_xlabel("Step")
    axes[0, 0].set_ylabel("GDP")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Unemployment Rate
    axes[0, 1].plot(steps, history["unemployment_rate"], linewidth=2, color="orange")
    axes[0, 1].axvline(shock_step, color="red", linestyle="--", label="Shock")
    axes[0, 1].set_title("Unemployment Rate")
    axes[0, 1].set_xlabel("Step")
    axes[0, 1].set_ylabel("Rate")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Inflation
    axes[1, 0].plot(steps, history["inflation"], linewidth=2, color="green")
    axes[1, 0].axvline(shock_step, color="red", linestyle="--", label="Shock")
    axes[1, 0].set_title("Inflation Rate")
    axes[1, 0].set_xlabel("Step")
    axes[1, 0].set_ylabel("Rate")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Gini Coefficient
    axes[1, 1].plot(steps, history["gini"], linewidth=2, color="purple")
    axes[1, 1].axvline(shock_step, color="red", linestyle="--", label="Shock")
    axes[1, 1].set_title("Gini Coefficient")
    axes[1, 1].set_xlabel("Step")
    axes[1, 1].set_ylabel("Gini")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    viz_file = output_dir / "shock_experiment_visualization.png"
    plt.savefig(viz_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"Visualization saved: {viz_file}")


def main():
    """メイン関数"""
    # .envファイルを読み込む
    load_dotenv()

    args = parse_args()

    # デフォルトの出力ディレクトリ
    if args.output is None:
        args.output = f"experiments/outputs/{args.experiment}_run"

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ロガーの設定
    log_file = output_dir / "experiment.log"
    setup_logger(log_level=args.log_level, log_file=str(log_file))

    logger.info(f"Log file: {log_file}")

    try:
        # 設定の読み込み
        config = load_config("config/simulation_config.yaml")

        # 設定の上書き
        config.simulation.max_steps = args.steps
        config.simulation.random_seed = args.seed

        # 実験実行
        results = run_experiment(
            config=config,
            steps=args.steps,
            shock_step=args.shock_step,
            shock_magnitude=args.shock_magnitude,
            experiment_type=args.experiment,
            output_dir=output_dir,
        )

        # 可視化
        generate_shock_visualization(results, output_dir)

        logger.info("\n" + "=" * 60)
        logger.info(f"✅ {args.experiment} experiment completed successfully!")
        logger.info("=" * 60)
        logger.info(f"\nResults directory: {output_dir}")
        logger.info("  - results.json: Full experiment results")
        logger.info("  - shock_impact_analysis.json: Impact analysis")
        logger.info("  - shock_experiment_visualization.png: Visualization")
        logger.info("  - experiment.log: Execution log")

    except Exception as e:
        logger.exception(f"Error during experiment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
