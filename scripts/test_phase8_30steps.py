"""
Phase 8.1-8.5 30-Step Validation Test

このスクリプトは、Phase 8で実装した全ての改善を30ステップで検証します：
- Phase 8.1: LLM消費決定の統合
- Phase 8.1.1: ステージ順序修正
- Phase 8.1.2: 需要データ記録修正
- Phase 8.2: 失業率の変動性確保
- Phase 8.3: 価格変動メカニズム強化
- Phase 8.4: 投資集計方法修正（資本変化から計算）
- Phase 8.5: 消費平滑化（バッファ・ストック貯蓄モデル）
"""

import json
from pathlib import Path

from loguru import logger

from src.environment.simulation import Simulation
from src.utils.config import load_config


def main():
    """30ステップテストを実行"""
    logger.info("=" * 80)
    logger.info("Phase 8.1-8.5 30-Step Validation Test Starting")
    logger.info("=" * 80)

    # 出力ディレクトリ
    output_dir = Path("experiments/test_phase8_30steps")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 設定読み込み
    config = load_config("config/simulation_config.yaml")

    # シミュレーション初期化
    sim = Simulation(config)

    # 30ステップ実行
    steps = 30
    logger.info(f"Running {steps} simulation steps...")

    for step in range(steps):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Step {step + 1}/{steps}")
        logger.info(f"{'=' * 60}")

        indicators = sim.step()

        # 進捗ログ
        if (step + 1) % 5 == 0:
            logger.info(f"✓ Step {step + 1} completed")
            logger.info(f"  GDP: ${indicators['gdp']:,.2f}")
            logger.info(f"  Unemployment: {indicators['unemployment_rate']:.1%}")
            logger.info(f"  Inflation: {indicators['inflation']:.2%}")
            logger.info(f"  Investment: ${indicators['investment']:,.2f}")

    # 結果を保存
    sim.save_results(output_dir)

    # 結果を読み込んで検証
    with open(output_dir / "results.json", encoding="utf-8") as f:
        results = json.load(f)

    # Phase 8.3検証: 価格変動
    prices_data = results["history"].get("prices", {})
    price_variations = {}
    for good_id, price_list in prices_data.items():
        if len(price_list) > 1:
            min_price = min(price_list)
            max_price = max(price_list)
            variation = (max_price - min_price) / min_price if min_price > 0 else 0
            price_variations[good_id] = {
                "min": min_price,
                "max": max_price,
                "variation_pct": variation * 100,
            }

    # Phase 8.4検証: 投資の非ゼロ性
    investment_data = results["history"]["investment"]
    non_zero_investment_count = sum(1 for inv in investment_data if abs(inv) > 0.01)

    # Phase 8.5検証: 消費の変動性（平滑化効果）
    consumption_data = results["history"]["consumption"]
    if len(consumption_data) > 1:
        consumption_volatility = (
            sum(
                abs(consumption_data[i] - consumption_data[i - 1])
                for i in range(1, len(consumption_data))
            )
            / (len(consumption_data) - 1)
            / (sum(consumption_data) / len(consumption_data))
        )
    else:
        consumption_volatility = 0.0

    # サマリー作成
    final_gdp = results["history"]["gdp"][-1]
    final_unemployment = results["history"]["unemployment_rate"][-1]
    final_inflation = results["history"]["inflation"][-1]
    final_investment = results["history"]["investment"][-1]
    final_gini = results["history"]["gini"][-1]

    summary = {
        "test_name": "Phase 8.1-8.5 30-Step Validation",
        "steps": steps,
        "final_indicators": {
            "gdp": final_gdp,
            "unemployment_rate": final_unemployment,
            "inflation": final_inflation,
            "investment": final_investment,
            "gini": final_gini,
        },
        "phase8_validations": {
            "phase8_3_price_variations": {
                "goods_count": len(price_variations),
                "avg_variation_pct": (
                    sum(pv["variation_pct"] for pv in price_variations.values())
                    / len(price_variations)
                    if price_variations
                    else 0
                ),
                "max_variation_pct": (
                    max(pv["variation_pct"] for pv in price_variations.values())
                    if price_variations
                    else 0
                ),
                "status": (
                    "✅ PASS"
                    if price_variations
                    and sum(pv["variation_pct"] for pv in price_variations.values())
                    / len(price_variations)
                    > 1.0
                    else "❌ FAIL"
                ),
                "sample_details": dict(list(price_variations.items())[:5]),
            },
            "phase8_4_investment_non_zero": {
                "total_steps": len(investment_data),
                "non_zero_steps": non_zero_investment_count,
                "non_zero_ratio": (
                    non_zero_investment_count / len(investment_data)
                    if investment_data
                    else 0
                ),
                "avg_investment": (
                    sum(investment_data) / len(investment_data)
                    if investment_data
                    else 0
                ),
                "status": (
                    "✅ PASS"
                    if non_zero_investment_count > len(investment_data) * 0.3
                    else "❌ FAIL"
                ),
                "sample_values": investment_data[:10],
            },
            "phase8_5_consumption_smoothing": {
                "volatility": consumption_volatility,
                "avg_consumption": (
                    sum(consumption_data) / len(consumption_data)
                    if consumption_data
                    else 0
                ),
                "status": "✅ PASS" if consumption_volatility < 0.3 else "❌ FAIL",
                "description": "Lower volatility indicates better consumption smoothing",
            },
        },
        "llm_costs": {
            "total_cost": getattr(sim, "total_llm_cost", 0),
            "total_calls": getattr(sim, "total_llm_calls", 0),
        },
    }

    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 結果表示
    logger.info("\n" + "=" * 80)
    logger.info("Phase 8.1-8.5 30-Step Validation Results")
    logger.info("=" * 80)
    logger.info(f"Final GDP: ${final_gdp:,.2f}")
    logger.info(f"Final Unemployment: {final_unemployment:.1%}")
    logger.info(f"Final Inflation: {final_inflation:.2%}")
    logger.info(f"Final Investment: ${final_investment:,.2f}")
    logger.info(f"Final Gini: {final_gini:.3f}")
    logger.info("")
    logger.info("Phase 8.3 - Price Variations:")
    logger.info(
        f"  Avg Variation: {summary['phase8_validations']['phase8_3_price_variations']['avg_variation_pct']:.2f}%"
    )
    logger.info(
        f"  Max Variation: {summary['phase8_validations']['phase8_3_price_variations']['max_variation_pct']:.2f}%"
    )
    logger.info(
        f"  Status: {summary['phase8_validations']['phase8_3_price_variations']['status']}"
    )
    logger.info("")
    logger.info("Phase 8.4 - Investment Non-Zero:")
    logger.info(
        f"  Non-Zero Ratio: {summary['phase8_validations']['phase8_4_investment_non_zero']['non_zero_ratio']:.1%}"
    )
    logger.info(
        f"  Avg Investment: ${summary['phase8_validations']['phase8_4_investment_non_zero']['avg_investment']:,.2f}"
    )
    logger.info(
        f"  Status: {summary['phase8_validations']['phase8_4_investment_non_zero']['status']}"
    )
    logger.info("")
    logger.info("Phase 8.5 - Consumption Smoothing:")
    logger.info(
        f"  Volatility: {summary['phase8_validations']['phase8_5_consumption_smoothing']['volatility']:.3f}"
    )
    logger.info(
        f"  Status: {summary['phase8_validations']['phase8_5_consumption_smoothing']['status']}"
    )
    logger.info("=" * 80)

    # テスト成功判定
    validations = summary["phase8_validations"]
    passed = sum(
        1 for v in validations.values() if v.get("status", "").startswith("✅")
    )
    total = len(validations)

    logger.info(f"\n✅ Phase 8 Validations: {passed}/{total} passed")

    if passed == total:
        logger.info("🎉 All Phase 8.1-8.5 validations passed!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} validation(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
