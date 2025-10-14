# SimCity 使い方ガイド

SimCityは、LLM駆動のマクロ経済シミュレーションフレームワークです。このガイドでは、基本的な使い方から実践的な活用方法まで説明します。

## 目次

1. [クイックスタート](#クイックスタート)
2. [シミュレーション実行](#シミュレーション実行)
3. [経済現象の検証](#経済現象の検証)
4. [結果の可視化](#結果の可視化)
5. [トラブルシューティング](#トラブルシューティング)

---

## クイックスタート

### 前提条件

- Python 3.12以上
- OpenAI APIキー
- 推奨: 8GB以上のメモリ

### 環境セットアップ

```bash
# 1. .envファイルの作成
cp .env.example .env

# 2. APIキーを設定
# .envファイルを編集してOPENAI_API_KEYを追加
OPENAI_API_KEY=sk-your-api-key-here

# 3. 依存関係のインストール（uvが自動的に処理）
uv run pytest  # テスト実行で確認
```

### 最も簡単な実行方法: Streamlitダッシュボード

```bash
# Web UIを起動
streamlit run app.py

# または
uv run streamlit run app.py
```

ブラウザが自動的に開き、インタラクティブなダッシュボードが表示されます：

- **Live Simulation**: リアルタイムでシミュレーション実行
- **Upload Results**: 既存の結果ファイルを表示
- **Demo Data**: デモデータで機能を試用

### コマンドラインからの実行

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

# 設定の読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーションの初期化
sim = Simulation(config)

# 12ステップ実行
for step in range(12):
    sim.step()
    metrics = sim.get_metrics()
    print(f"Step {step}: GDP=${metrics['gdp']:.2f}, "
          f"Unemployment={metrics['unemployment_rate']:.2%}")

# 結果の保存
sim.save_results("outputs/my_run")
```

---

## シミュレーション実行

### ベースライン実行スクリプト

180ステップの完全なシミュレーションを実行：

```bash
# 基本的な実行
uv run python scripts/run_baseline.py --steps 180

# 検証と可視化を含む実行
uv run python scripts/run_baseline.py \
    --steps 180 \
    --validate \
    --visualize \
    --output experiments/my_baseline
```

**オプション:**
- `--steps N`: ステップ数（デフォルト: 180）
- `--seed N`: 乱数シード（デフォルト: 42）
- `--validate`: 経済現象を自動検証
- `--visualize`: グラフを自動生成
- `--checkpoint-interval N`: チェックポイント保存間隔

### 設定のカスタマイズ

`config/simulation_config.yaml` を編集：

```yaml
simulation:
  max_steps: 180
  random_seed: 42

agents:
  households:
    max: 200        # 世帯数
  firms:
    max: 44         # 企業数

markets:
  labor:
    matching_rate: 0.7    # 労働マッチング率
```

コードから設定を上書き:

```python
config = load_config("config/simulation_config.yaml")
config.agents.households.max = 100  # 世帯数を100に削減
sim = Simulation(config)
```

### 複数シード実行（ロバストネステスト）

```python
from pathlib import Path

seeds = [42, 123, 456]
output_dir = Path("experiments/robustness")

for seed in seeds:
    config = load_config("config/simulation_config.yaml")
    config.simulation.random_seed = seed

    sim = Simulation(config)
    for step in range(180):
        sim.step()

    sim.save_results(str(output_dir / f"seed_{seed}"))
```

---

## 経済現象の検証

SimCityは7つのマクロ経済現象を再現します。検証システムで統計的に確認できます。

### 基本的な検証

```python
from experiments.validation import EconomicPhenomenaValidator
import json

# 結果の読み込み
with open("experiments/my_run/results.json") as f:
    sim_data = json.load(f)

# 検証システムの初期化
validator = EconomicPhenomenaValidator(sim_data)

# 全現象を検証
results = validator.validate_all()

# サマリー表示
print(f"Success Rate: {results['summary']['success_rate']:.1%}")
print(f"Passed: {results['summary']['valid']}/{results['summary']['total']}")

# レポート生成
validator.generate_report("validation_report.json")
```

### 検証される7つの経済現象

| 現象 | 説明 | 検証基準 |
|-----|------|---------|
| **Phillips Curve** | 失業率とインフレ率の負の相関 | r < 0, p < 0.05 |
| **Okun's Law** | 失業率変化とGDP成長率の負の相関 | r < 0, p < 0.05 |
| **Beveridge Curve** | 求人率と失業率の強い負の相関 | r < -0.5, p < 0.05 |
| **Price Elasticity** | 必需品は非弾力的、贅沢品は弾力的 | -1 < E < 0 (必需品), E < -1 (贅沢品) |
| **Engel's Law** | 所得上昇で食料支出割合が減少 | r < 0, p < 0.05 |
| **Investment Volatility** | 投資のボラティリティ > 消費 | std(I) > std(C) |
| **Price Stickiness** | 価格は需要変化に遅れて調整 | 価格変化頻度 < 需要変化頻度 |

### 個別検証

```python
# Phillips Curveのみ
phillips = validator.validate_phillips_curve()
print(f"Valid: {phillips['valid']}")
print(f"Correlation: {phillips['correlation']:.3f}")
print(f"P-value: {phillips['p_value']:.4f}")

# Okun's Lawのみ
okun = validator.validate_okuns_law()
```

### ロバストネステスト

複数シード実行の結果から安定性を検証：

```python
from experiments.robustness_test import run_robustness_test

# 複数実行の結果ファイル
simulation_files = [
    "experiments/robustness/seed_42/results.json",
    "experiments/robustness/seed_123/results.json",
    "experiments/robustness/seed_456/results.json",
]

# ロバストネステスト
report = run_robustness_test(
    simulation_data_paths=simulation_files,
    output_path="experiments/robustness_report.json"
)

# 結果確認
assessment = report["overall_assessment"]
print(f"Qualitative Consistency: {'✅' if assessment['qualitative_consistency'] else '❌'}")
print(f"Statistical Stability: {'✅' if assessment['statistical_stability'] else '❌'}")
print(f"Trend Consistency: {'✅' if assessment['trend_consistency'] else '❌'}")
print(f"Overall: {'✅ ROBUST' if assessment['robust'] else '❌ NOT ROBUST'}")
```

---

## 結果の可視化

### Streamlitダッシュボード（推奨）

```bash
streamlit run app.py
```

**4つのタブ:**
1. **Overview**: シミュレーション概要、リアルタイムメトリクス
2. **City Map**: 都市マップ（建物配置、占有率、密度）
3. **Economic Indicators**: 経済指標の時系列グラフ
4. **Analysis**: 経済現象の分析（散布図、相関）

### Pythonコードからの可視化

```python
from src.visualization.plots import EconomicPlots
import matplotlib.pyplot as plt
import json

# 結果読み込み
with open("experiments/my_run/results.json") as f:
    data = json.load(f)

plotter = EconomicPlots()

# 時系列グラフ
fig = plotter.plot_time_series({
    "GDP": data['history']['gdp'],
    "Unemployment": data['history']['unemployment_rate'],
    "Inflation": data['history']['inflation'],
})
plt.savefig("economic_indicators.png", dpi=300)

# Phillips Curve
fig, stats = plotter.plot_phillips_curve(
    data['history']['unemployment_rate'],
    data['history']['inflation']
)
plt.savefig("phillips_curve.png", dpi=300)
print(f"Correlation: {stats['correlation']:.3f}")
```

---

## トラブルシューティング

### よくある問題

#### 1. OpenAI APIエラー

**エラー**: `AuthenticationError` or `RateLimitError`

**解決方法:**
```bash
# .envファイルを確認
cat .env

# APIキーが正しく設定されているか確認
# 余分なスペースや改行がないことを確認
```

#### 2. メモリ不足

**エラー**: `MemoryError` または極端な遅延

**解決方法:**
```yaml
# config/simulation_config.yaml
agents:
  households:
    max: 50  # 200 → 50 に削減（テスト用）
```

#### 3. コストが高すぎる

**解決方法:**
- `gpt-4o-mini` を使用（`gpt-4` より約10倍安い）
- ステップ数を減らす（テスト時は12-30ステップ）
- 世帯数を減らす

```yaml
# config/llm_config.yaml
openai:
  model: "gpt-4o-mini"  # gpt-4ではなくgpt-4o-miniを使用
```

#### 4. 検証テストの失敗

**解決方法:**
- シミュレーションステップ数を増やす（最低30ステップ推奨、180ステップ理想）
- 複数シードで実行して一貫性を確認
- 市場パラメータを調整

### デバッグのヒント

#### ログレベルの調整

```python
from src.utils.logger import setup_logger

# 詳細なログ
setup_logger(log_level="DEBUG", log_file="debug.log")
```

#### LLMコスト監視

```python
from src.llm.llm_interface import LLMInterface

llm = LLMInterface(config)
# ... シミュレーション実行 ...
print(f"Total cost: ${llm.get_total_cost():.2f}")
print(f"Total tokens: {llm.get_total_tokens()}")
```

---

## さらなるリソース

- **[API.md](API.md)**: 完全なAPIリファレンス
- **[OPTIMIZATION.md](OPTIMIZATION.md)**: パフォーマンス最適化ガイド
- **[README.md](../README.md)**: プロジェクト概要
- **[CLAUDE.md](../CLAUDE.md)**: アーキテクチャと設計ガイド
- **[論文](../2510.01297v1.md)**: 元論文（マークダウン版）

## コスト見積もり

**180ステップシミュレーション:**
- **gpt-4o-mini**: 約 $20-25（推奨）
- **gpt-4**: 約 $180-200

**テスト実行（12-30ステップ）:**
- **gpt-4o-mini**: $2-5
- **gpt-4**: $15-30

---

**Note**: このプロジェクトは研究・教育目的です。実世界の経済予測には使用しないでください。
