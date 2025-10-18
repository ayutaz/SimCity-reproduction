"""
LLM統合テストスクリプト

シミュレーションでLLMベースの意思決定が正しく動作するかを確認
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.environment.simulation import Simulation  # noqa: E402
from src.utils.config import load_config  # noqa: E402


def main():
    """LLM統合テストを実行"""
    # .envファイルを読み込み
    load_dotenv()

    logger.info("=== LLM Integration Test ===")

    # 環境変数チェック
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        logger.error("OPENAI_API_KEY not found or not set in .env file")
        logger.error("Please set a valid OPENAI_API_KEY in .env file")
        return 1

    logger.info("OPENAI_API_KEY found, proceeding with test...")

    # 設定を読み込み
    try:
        config = load_config("config/simulation_config.yaml")
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # シミュレーション初期化
    try:
        sim = Simulation(config)
        logger.info(
            f"Simulation initialized with {len(sim.households)} households and {len(sim.firms)} firms"
        )
    except Exception as e:
        logger.error(f"Failed to initialize simulation: {e}")
        return 1

    # 5ステップを実行
    test_steps = 5
    logger.info(f"Running {test_steps} steps with LLM-based decision making...")

    try:
        for step in range(test_steps):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Step {step + 1}/{test_steps}")
            logger.info(f"{'=' * 60}")

            indicators = sim.step()

            logger.info(f"Step {step + 1} completed:")
            logger.info(f"  GDP: ${indicators['gdp']:,.2f}")
            logger.info(f"  Real GDP: ${indicators['real_gdp']:,.2f}")
            logger.info(f"  Inflation: {indicators['inflation']:.4%}")
            logger.info(f"  Unemployment: {indicators['unemployment_rate']:.2%}")
            logger.info(f"  Gini: {indicators['gini']:.4f}")
            logger.info(f"  Policy Rate: {indicators['policy_rate']:.2%}")

        logger.info("\n" + "=" * 60)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        # LLMコスト確認
        if hasattr(sim.llm_interface, "total_cost"):
            logger.info(f"Total LLM cost: ${sim.llm_interface.total_cost:.4f}")
            logger.info(f"Total tokens: {sim.llm_interface.total_tokens:,}")

        # 最終結果を保存
        output_dir = Path("experiments/llm_integration_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        sim.save_results(output_dir)

        logger.info(f"\nResults saved to: {output_dir}")
        logger.info("\nLLM integration test completed successfully!")

        return 0

    except Exception as e:
        logger.error(f"Error during simulation: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
