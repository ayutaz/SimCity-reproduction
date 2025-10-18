"""
30ステップの検証テストスクリプト

Phase 10最適化の効果を検証するため、30ステップ実行してログを確認
"""

import os
import time
from pathlib import Path

from loguru import logger

from src.environment.simulation import Simulation
from src.utils.config import load_config


def main():
    """30ステップ検証テストを実行"""
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)

    # ログ設定
    logger.remove()  # デフォルトハンドラを削除
    logger.add(
        "logs/test_30steps_{time}.log",
        rotation="10 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    )

    logger.info("=== 30ステップ検証テスト開始 ===")

    # 設定の読み込み
    config = load_config("config/simulation_config.yaml")

    # 環境変数チェック
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set, using dummy key for testing")
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"

    # シミュレーション初期化
    logger.info("Initializing simulation...")
    sim = Simulation(config)

    logger.info(
        f"Initial state: {len(sim.households)} households, {len(sim.firms)} firms"
    )

    # 30ステップ実行
    steps = 30
    start_time = time.time()

    results = []
    for step in range(steps):
        step_start = time.time()

        # 1ステップ実行
        indicators = sim.step()
        results.append(indicators)

        step_time = time.time() - step_start

        # 5ステップごとに詳細ログ
        if (step + 1) % 5 == 0:
            logger.info(f"--- Step {step + 1}/{steps} Summary ---")
            logger.info(f"  Time: {step_time:.2f}s")
            logger.info(f"  GDP: ${indicators['gdp']:,.2f}")
            logger.info(f"  Real GDP: ${indicators['real_gdp']:,.2f}")
            logger.info(f"  Unemployment: {indicators['unemployment_rate']:.2%}")
            logger.info(f"  Inflation: {indicators['inflation']:.4%}")
            logger.info(f"  Gini: {indicators['gini']:.3f}")
            logger.info(f"  Households: {indicators['num_households']}")
            logger.info(f"  Firms: {indicators['num_firms']}")
            logger.info("")

    total_time = time.time() - start_time

    # 結果サマリー
    logger.info("=== 30ステップ検証テスト完了 ===")
    logger.info(f"Total time: {total_time:.2f}s ({total_time / steps:.2f}s/step)")
    logger.info(f"Final GDP: ${results[-1]['gdp']:,.2f}")
    logger.info(f"Final Unemployment: {results[-1]['unemployment_rate']:.2%}")
    logger.info(f"Final Inflation: {results[-1]['inflation']:.4%}")

    # 結果保存
    output_dir = Path("experiments/test_30steps_baseline")
    sim.save_results(output_dir)
    logger.info(f"Results saved to {output_dir}")

    # LLMコスト確認（将来の実装用）
    if hasattr(sim.llm_interface, "get_total_cost"):
        total_cost = sim.llm_interface.get_total_cost()
        total_calls = sim.llm_interface.get_total_calls()
        if total_calls > 0:
            logger.info(f"LLM Cost: ${total_cost:.4f} ({total_calls} calls)")
        else:
            logger.info("LLM Cost: $0.00 (no LLM calls - using simplified simulation)")

    logger.info("=== Test completed successfully ===")


if __name__ == "__main__":
    main()
