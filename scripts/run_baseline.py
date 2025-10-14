"""
Baseline Simulation Run Script

180ステップのベースラインシミュレーションを実行し、
全経済指標を記録・可視化します。

Usage:
    uv run python scripts/run_baseline.py [--steps STEPS] [--seed SEED] [--output OUTPUT_DIR]

Example:
    uv run python scripts/run_baseline.py --steps 180 --seed 42 --output experiments/baseline_run_001
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

from experiments.validation import EconomicPhenomenaValidator
from src.environment.simulation import Simulation
from src.utils.config import load_config
from src.utils.logger import setup_logger


def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description="Run baseline simulation")
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
        "--output",
        type=str,
        default="experiments/outputs/baseline_run",
        help="Output directory (default: experiments/outputs/baseline_run)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=30,
        help="Save checkpoint every N steps (default: 30)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run economic phenomena validation after simulation",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization plots after simulation",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def run_simulation(config, steps: int, output_dir: Path, checkpoint_interval: int):
    """
    シミュレーションを実行

    Args:
        config: シミュレーション設定
        steps: ステップ数
        output_dir: 出力ディレクトリ
        checkpoint_interval: チェックポイント保存間隔
    """
    logger.info("=" * 60)
    logger.info("Starting Baseline Simulation")
    logger.info("=" * 60)
    logger.info(f"Steps: {steps}")
    logger.info(f"Random seed: {config.simulation.random_seed}")
    logger.info(f"Households: {config.agents.households.max}")
    logger.info(f"Firms: {config.agents.firms.max}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)

    # シミュレーションの初期化
    logger.info("Initializing simulation...")
    sim = Simulation(config)

    # 経済指標を記録するリスト
    history = {
        "gdp": [],
        "unemployment_rate": [],
        "inflation": [],
        "gini": [],
        "average_income": [],
        "consumption": [],
        "investment": [],
        "vacancy_rate": [],
        "policy_rate": [],
        "government_spending": [],
        "tax_revenue": [],
        "household_incomes": [],
        "food_expenditure_ratios": [],
        "prices": {},
        "demands": {},
    }

    # 開始時刻
    start_time = time.time()

    # シミュレーション実行
    logger.info(f"\nRunning simulation for {steps} steps...\n")

    for step in range(steps):
        step_start_time = time.time()

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
        history["vacancy_rate"].append(metrics.get("vacancy_rate", 0.0))
        history["policy_rate"].append(metrics.get("policy_rate", 0.02))
        history["government_spending"].append(metrics.get("government_spending", 0.0))
        history["tax_revenue"].append(metrics.get("tax_revenue", 0.0))

        # 世帯所得
        household_incomes = [
            getattr(h.profile, "monthly_income", 50000.0) for h in sim.households
        ]
        history["household_incomes"].append(household_incomes)

        # 食料支出比率はsimulation内で計算・記録されるためスキップ
        # （simulation.pyの_record_history()で自動的に記録される）

        # 価格と需要の追跡もsimulation内で自動記録されるためスキップ
        # （simulation.pyの_record_history()で自動的に記録される）

        step_time = time.time() - step_start_time

        # 進捗表示（10ステップごと）
        if (step + 1) % 10 == 0 or step == 0:
            elapsed = time.time() - start_time
            remaining_steps = steps - (step + 1)
            estimated_remaining = (elapsed / (step + 1)) * remaining_steps

            logger.info(f"Step {step + 1}/{steps} ({(step + 1) / steps * 100:.1f}%)")
            logger.info(f"  GDP: {metrics['gdp']:,.2f}")
            logger.info(f"  Unemployment: {metrics['unemployment_rate']:.2%}")
            logger.info(f"  Inflation: {metrics['inflation']:.2%}")
            logger.info(f"  Gini: {metrics['gini']:.3f}")
            logger.info(f"  Step time: {step_time:.2f}s")
            logger.info(
                f"  Elapsed: {elapsed:.0f}s, "
                f"Estimated remaining: {estimated_remaining:.0f}s"
            )
            logger.info("")

        # チェックポイント保存
        if checkpoint_interval > 0 and (step + 1) % checkpoint_interval == 0:
            checkpoint_dir = output_dir / "checkpoints" / f"step_{step + 1}"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            sim.save_state(str(checkpoint_dir / "state.json"))
            logger.info(f"  Checkpoint saved: {checkpoint_dir}")

    # 総実行時間
    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info(
        f"Simulation completed in {total_time:.2f}s ({total_time / 60:.2f} min)"
    )
    logger.info(f"Average time per step: {total_time / steps:.2f}s")
    logger.info("=" * 60)

    # 最終結果の保存
    logger.info("\nSaving results...")

    # simulation.state.historyから食料支出比率と価格・需要データをマージ
    history["food_expenditure_ratios"] = sim.state.history.get("food_expenditure_ratios", [])
    history["prices"] = sim.state.history.get("prices", {})
    history["demands"] = sim.state.history.get("demands", {})

    results = {
        "history": history,
        "metadata": {
            "steps": steps,
            "households": config.agents.households.max,
            "firms": config.agents.firms.max,
            "seed": config.simulation.random_seed,
            "execution_time": total_time,
        },
    }

    # 結果をJSONで保存
    results_file = output_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved: {results_file}")

    # サマリーの保存
    summary = {
        "final_gdp": history["gdp"][-1],
        "final_unemployment": history["unemployment_rate"][-1],
        "final_inflation": history["inflation"][-1],
        "final_gini": history["gini"][-1],
        "avg_gdp": sum(history["gdp"]) / len(history["gdp"]),
        "avg_unemployment": sum(history["unemployment_rate"])
        / len(history["unemployment_rate"]),
        "avg_inflation": sum(history["inflation"]) / len(history["inflation"]),
        "avg_gini": sum(history["gini"]) / len(history["gini"]),
        "execution_time": total_time,
        "steps": steps,
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"Summary saved: {summary_file}")

    return results


def validate_results(results: dict, output_dir: Path):
    """
    経済現象を検証

    Args:
        results: シミュレーション結果
        output_dir: 出力ディレクトリ
    """
    logger.info("\n" + "=" * 60)
    logger.info("Validating Economic Phenomena")
    logger.info("=" * 60)

    validator = EconomicPhenomenaValidator(results)
    validation_results = validator.validate_all()

    # 検証結果の表示
    summary = validation_results["summary"]
    logger.info("\nValidation Summary:")
    logger.info(f"  Success rate: {summary['success_rate']:.1%}")
    logger.info(f"  Passed: {summary['passed']}/{summary['total']}")
    logger.info("")

    # 各現象の結果
    phenomena = [
        "phillips_curve",
        "okuns_law",
        "beveridge_curve",
        "price_elasticity",
        "engels_law",
        "investment_volatility",
        "price_stickiness",
    ]

    for phenomenon in phenomena:
        result = validation_results[phenomenon]
        valid = result.get("valid", False)
        status = "✅" if valid else "❌"
        logger.info(f"{status} {phenomenon}")

        if "correlation" in result:
            logger.info(f"    Correlation: {result['correlation']:.3f}")
        if "p_value" in result:
            logger.info(f"    P-value: {result['p_value']:.4f}")

    # レポートの保存
    report_file = output_dir / "validation_report.json"
    validator.generate_report(str(report_file))
    logger.info(f"\nValidation report saved: {report_file}")

    return validation_results


def generate_visualizations(results: dict, output_dir: Path):
    """
    可視化を生成

    Args:
        results: シミュレーション結果
        output_dir: 出力ディレクトリ
    """
    logger.info("\n" + "=" * 60)
    logger.info("Generating Visualizations")
    logger.info("=" * 60)

    import matplotlib.pyplot as plt

    from src.visualization.plots import (
        plot_beveridge_curve,
        plot_economic_indicators,
        plot_income_distribution,
        plot_okuns_law,
        plot_phillips_curve,
    )

    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    history = results["history"]

    # 1. 経済指標の時系列
    logger.info("Generating economic indicators plot...")
    fig = plot_economic_indicators(history)
    plt.savefig(viz_dir / "economic_indicators.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved: {viz_dir / 'economic_indicators.png'}")

    # 2. Phillips Curve
    logger.info("Generating Phillips Curve plot...")
    fig = plot_phillips_curve(history)
    plt.savefig(viz_dir / "phillips_curve.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved: {viz_dir / 'phillips_curve.png'}")

    # 3. Okun's Law
    logger.info("Generating Okun's Law plot...")
    fig = plot_okuns_law(history)
    plt.savefig(viz_dir / "okuns_law.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved: {viz_dir / 'okuns_law.png'}")

    # 4. Beveridge Curve
    logger.info("Generating Beveridge Curve plot...")
    fig = plot_beveridge_curve(history)
    plt.savefig(viz_dir / "beveridge_curve.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved: {viz_dir / 'beveridge_curve.png'}")

    # 5. 最終所得分布
    logger.info("Generating income distribution plot...")
    final_incomes = history["household_incomes"][-1]
    fig = plot_income_distribution(final_incomes)
    plt.savefig(viz_dir / "income_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved: {viz_dir / 'income_distribution.png'}")

    logger.info(f"\nAll visualizations saved to: {viz_dir}")


def main():
    """メイン関数"""
    # .envファイルを読み込む
    load_dotenv()

    args = parse_args()

    # ロガーの設定
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "simulation.log"
    setup_logger(log_level=args.log_level, log_file=str(log_file))

    logger.info(f"Log file: {log_file}")

    try:
        # 設定の読み込み
        config = load_config("config/simulation_config.yaml")

        # 設定の上書き
        config.simulation.max_steps = args.steps
        config.simulation.random_seed = args.seed

        # シミュレーション実行
        results = run_simulation(
            config=config,
            steps=args.steps,
            output_dir=output_dir,
            checkpoint_interval=args.checkpoint_interval,
        )

        # 検証（オプション）
        if args.validate:
            validate_results(results, output_dir)

        # 可視化（オプション）
        if args.visualize:
            generate_visualizations(results, output_dir)

        logger.info("\n" + "=" * 60)
        logger.info("✅ Baseline simulation completed successfully!")
        logger.info("=" * 60)
        logger.info(f"\nResults directory: {output_dir}")
        logger.info("  - results.json: Full simulation results")
        logger.info("  - summary.json: Summary statistics")
        logger.info("  - simulation.log: Execution log")
        if args.validate:
            logger.info("  - validation_report.json: Economic phenomena validation")
        if args.visualize:
            logger.info("  - visualizations/: All plots")

    except Exception as e:
        logger.exception(f"Error during simulation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
