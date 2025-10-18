"""
Phase 8.1-8.2 修正検証テスト（10ステップ）

検証項目：
1. LLM消費決定が購入注文に反映されているか
2. 需要データが記録されているか（非ゼロ）
3. 失業率が変動しているか
4. 食料支出比率が連続値になっているか
"""

import json
from pathlib import Path

from loguru import logger

from src.environment.simulation import Simulation
from src.utils.config import load_config


def main():
    """Phase 8.1-8.2の検証テスト実行"""
    # 出力ディレクトリ
    output_dir = Path("experiments/test_phase8_1_2_verification")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 設定読み込み
    config = load_config("config/simulation_config.yaml")

    # シミュレーション初期化
    sim = Simulation(config)

    logger.info("=" * 60)
    logger.info("Phase 8.1-8.2 修正検証テスト開始（10ステップ）")
    logger.info("=" * 60)

    # 10ステップ実行
    num_steps = 10
    for step in range(num_steps):
        logger.info(f"\n{'='*60}")
        logger.info(f"Step {step + 1}/{num_steps}")
        logger.info(f"{'='*60}")

        indicators = sim.step()

        # ステップごとの診断ログ
        logger.info(f"Step {step} 完了:")
        logger.info(f"  失業率: {indicators['unemployment_rate']:.2%}")
        logger.info(f"  GDP: ${indicators['gdp']:.2f}")
        logger.info(f"  消費: ${indicators['consumption']:.2f}")
        logger.info(f"  投資: ${indicators['investment']:.2f}")

    # 結果を保存
    sim.save_results(output_dir)

    # 検証レポート作成
    with open(output_dir / "results.json", encoding="utf-8") as f:
        results = json.load(f)

    report = {
        "test_name": "Phase 8.1-8.2 Verification Test",
        "steps": num_steps,
        "verification_results": {},
    }

    # 1. 需要データの検証
    demands = results["history"]["demands"]
    non_zero_demands = {}
    for good_id, demand_history in demands.items():
        non_zero_count = sum(1 for d in demand_history if d > 0)
        if non_zero_count > 0:
            non_zero_demands[good_id] = {
                "total_steps": len(demand_history),
                "non_zero_steps": non_zero_count,
                "max_demand": max(demand_history),
                "avg_demand": sum(demand_history) / len(demand_history),
            }

    report["verification_results"]["demand_data"] = {
        "total_goods": len(demands),
        "goods_with_demand": len(non_zero_demands),
        "status": "✅ PASS" if len(non_zero_demands) > 0 else "❌ FAIL",
        "details": non_zero_demands,
    }

    # 2. 失業率の変動性検証
    unemployment_rates = results["history"]["unemployment_rate"]
    unique_rates = len(set(unemployment_rates))
    unemployment_variation = max(unemployment_rates) - min(unemployment_rates)

    report["verification_results"]["unemployment_variability"] = {
        "unique_values": unique_rates,
        "min_rate": min(unemployment_rates),
        "max_rate": max(unemployment_rates),
        "variation": unemployment_variation,
        "status": "✅ PASS" if unique_rates > 1 else "❌ FAIL",
        "all_rates": unemployment_rates,
    }

    # 3. 食料支出比率の検証
    food_ratios = results["history"]["food_expenditure_ratios"]
    # 全ステップ、全世帯の比率を収集
    all_ratios = [ratio for step_ratios in food_ratios for ratio in step_ratios]
    unique_ratios = len(set(all_ratios))
    # 0.0と1.0以外の値があるか
    continuous_ratios = [r for r in all_ratios if 0 < r < 1]

    report["verification_results"]["food_expenditure_ratios"] = {
        "total_samples": len(all_ratios),
        "unique_values": unique_ratios,
        "continuous_values_count": len(continuous_ratios),
        "binary_only": len(continuous_ratios) == 0,
        "status": "✅ PASS" if len(continuous_ratios) > 0 else "❌ FAIL",
        "sample_values": all_ratios[:20],  # 最初の20個をサンプル表示
    }

    # 4. GDP構成の検証
    consumption = results["history"]["consumption"]
    investment = results["history"]["investment"]
    gdp = results["history"]["gdp"]

    report["verification_results"]["gdp_composition"] = {
        "avg_consumption": sum(consumption) / len(consumption),
        "avg_investment": sum(investment) / len(investment),
        "avg_gdp": sum(gdp) / len(gdp),
        "consumption_ratio": sum(consumption) / sum(gdp) if sum(gdp) > 0 else 0,
        "investment_ratio": sum(investment) / sum(gdp) if sum(gdp) > 0 else 0,
    }

    # サマリー
    passed_tests = sum(
        1
        for result in report["verification_results"].values()
        if isinstance(result, dict) and result.get("status") == "✅ PASS"
    )
    total_tests = sum(
        1
        for result in report["verification_results"].values()
        if isinstance(result, dict) and "status" in result
    )

    report["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": total_tests - passed_tests,
        "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
    }

    # レポート保存
    with open(output_dir / "verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 結果表示
    logger.info("\n" + "=" * 60)
    logger.info("Phase 8.1-8.2 検証結果")
    logger.info("=" * 60)

    for test_name, result in report["verification_results"].items():
        if isinstance(result, dict) and "status" in result:
            logger.info(f"{test_name}: {result['status']}")

    logger.info(f"\n総合結果: {passed_tests}/{total_tests} テスト成功")
    logger.info(f"結果保存先: {output_dir}")

    return report


if __name__ == "__main__":
    main()
