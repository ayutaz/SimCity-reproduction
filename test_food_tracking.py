"""
食料支出比率追跡のテスト
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.environment.simulation import Simulation
from src.utils.config import load_config

# .envファイルを読み込み
load_dotenv()

# OpenAI API Keyがない場合はダミーを設定（テスト用）
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"

# 設定を読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーション初期化
sim = Simulation(config)

# 12ステップ実行
print("Running simulation for 12 steps...")
for i in range(12):
    indicators = sim.step()
    print(f"Step {i}: GDP=${indicators['gdp']:.2f}, Unemployment={indicators['unemployment_rate']:.2%}")

# 結果を確認
print("\n=== Results ===")
print(f"Steps: {sim.state.step}")

# 食料支出比率の確認
food_ratios = sim.state.history.get("food_expenditure_ratios", [])
print(f"\nFood Expenditure Ratios (per step):")
for i, ratio in enumerate(food_ratios):
    print(f"  Step {i}: {ratio:.4f} ({ratio*100:.2f}%)")

if food_ratios:
    avg_ratio = sum(food_ratios) / len(food_ratios)
    print(f"\nAverage Food Expenditure Ratio: {avg_ratio:.4f} ({avg_ratio*100:.2f}%)")

# 価格データも確認
prices = sim.state.history.get("prices", {})
print(f"\nPrice tracking enabled for {len(prices)} goods")

# 結果を保存
output_dir = Path("experiments/food_tracking_test")
sim.save_results(output_dir)

print(f"\n✓ Results saved to {output_dir}")
