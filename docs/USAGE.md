# SimCity 使い方ガイド

このガイドでは、SimCityマルチエージェント都市経済シミュレーションの使い方を詳しく説明します。

## 目次

1. [はじめに](#はじめに)
2. [基本的な使い方](#基本的な使い方)
3. [設定のカスタマイズ](#設定のカスタマイズ)
4. [シミュレーション実行](#シミュレーション実行)
5. [経済現象の検証](#経済現象の検証)
6. [ロバストネステスト](#ロバストネステスト)
7. [結果の可視化](#結果の可視化)
8. [高度な使い方](#高度な使い方)
9. [トラブルシューティング](#トラブルシューティング)

## はじめに

SimCityは、LLMを活用したマクロ経済シミュレーションフレームワークです。200世帯の家計エージェント、動的な企業エージェント、政府、中央銀行が相互作用し、7つの主要なマクロ経済現象を再現します。

### 前提知識

- Pythonの基本的な知識
- マクロ経済学の基礎（フィリップス曲線、オークンの法則など）
- コマンドライン操作の基本

### 必要な環境

- Python 3.12以上
- uv (Pythonパッケージマネージャー)
- OpenAI APIキー
- 推奨: 8GB以上のメモリ

## 基本的な使い方

### クイックスタート

最も簡単な方法は、Streamlitダッシュボードを起動することです：

```bash
# ダッシュボードの起動
uv run streamlit run app.py
```

ブラウザで http://localhost:8501 が開き、インタラクティブなUIが表示されます。

### コマンドラインからの実行

Pythonスクリプトから直接シミュレーションを実行することもできます：

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

# 設定の読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーションの初期化
sim = Simulation(config)

# 10ステップ実行
for step in range(10):
    sim.step()
    metrics = sim.get_metrics()
    print(f"Step {step}: GDP={metrics['gdp']:.2f}")

# 結果の保存
sim.save_results("outputs/my_first_run")
```

## 設定のカスタマイズ

### シミュレーション設定 (config/simulation_config.yaml)

主要な設定項目：

```yaml
simulation:
  max_steps: 180              # シミュレーションステップ数（デフォルト: 180）
  random_seed: 42             # 再現性のための乱数シード
  enable_geography: true      # 地理システムの有効化

agents:
  households:
    max: 200                  # 最大世帯数
    initial_count: 200        # 初期世帯数
  firms:
    max: 100                  # 最大企業数
    initial_count: 44         # 初期企業数（44種類のテンプレート）

markets:
  labor:
    matching_rate: 0.5        # 労働市場マッチング率
  goods:
    price_adjustment_rate: 0.1  # 価格調整速度
  financial:
    base_interest_rate: 0.02  # 基準金利
```

### LLM設定 (config/llm_config.yaml)

LLMの動作をカスタマイズ：

```yaml
openai:
  model: "gpt-4o-mini"        # 使用するモデル
  temperature: 0.7            # 生成のランダム性（0.0-2.0）
  max_tokens: 2000            # 最大トークン数

cost_tracking:
  enabled: true               # コスト追跡の有効化
  log_interval: 10            # コストログの出力間隔

prompt_caching:
  enabled: true               # プロンプトキャッシングの有効化
  ttl: 3600                   # キャッシュの有効期限（秒）
```

### 設定の上書き

コードから設定を上書きすることも可能です：

```python
from src.utils.config import load_config

config = load_config("config/simulation_config.yaml")

# 設定の上書き
config.simulation.max_steps = 100
config.agents.households.max = 300
config.markets.labor.matching_rate = 0.7

sim = Simulation(config)
```

## シミュレーション実行

### 基本的な実行パターン

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config
from src.utils.logger import setup_logger

# ロガーの設定
setup_logger(log_level="INFO", log_file="simulation.log")

# 設定の読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーションの初期化
sim = Simulation(config)

# ステップごとに実行
for step in range(config.simulation.max_steps):
    sim.step()

    # マクロ経済指標の取得
    metrics = sim.get_metrics()

    # 進捗の表示
    if step % 10 == 0:
        print(f"Step {step}/{config.simulation.max_steps}")
        print(f"  GDP: {metrics['gdp']:.2f}")
        print(f"  Unemployment: {metrics['unemployment_rate']:.2%}")
        print(f"  Inflation: {metrics['inflation']:.2%}")
        print(f"  Gini: {metrics['gini']:.3f}")

# 結果の保存
sim.save_results("experiments/outputs/baseline_run")
```

### 複数シード実行（ロバストネステスト用）

異なる乱数シードで複数回実行する例：

```python
from pathlib import Path

seeds = [42, 123, 456]
output_dir = Path("experiments/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

for seed in seeds:
    print(f"\n=== Running simulation with seed {seed} ===")

    config = load_config("config/simulation_config.yaml")
    config.simulation.random_seed = seed

    sim = Simulation(config)

    for step in range(config.simulation.max_steps):
        sim.step()

    # シード別に結果を保存
    sim.save_results(str(output_dir / f"run_seed{seed}"))
```

### 中間チェックポイント

長時間実行する場合、中間結果を保存：

```python
checkpoint_interval = 30  # 30ステップごとに保存

for step in range(config.simulation.max_steps):
    sim.step()

    # チェックポイント保存
    if (step + 1) % checkpoint_interval == 0:
        sim.save_results(f"experiments/checkpoints/step_{step+1}")
```

## 経済現象の検証

SimCityは7つの主要なマクロ経済現象を再現します。`EconomicPhenomenaValidator`を使って統計的に検証できます。

### 基本的な検証

```python
from experiments.validation import EconomicPhenomenaValidator
import json

# シミュレーション結果の読み込み
with open("experiments/outputs/baseline_run/results.json") as f:
    sim_data = json.load(f)

# 検証システムの初期化
validator = EconomicPhenomenaValidator(sim_data)

# 全ての経済現象を検証
results = validator.validate_all()

# サマリーの表示
summary = results['summary']
print(f"検証成功率: {summary['success_rate']:.1%}")
print(f"成功: {summary['passed']}/{summary['total']}")

# 各現象の結果
for phenomenon, result in results.items():
    if phenomenon != 'summary':
        print(f"\n{phenomenon}:")
        print(f"  Valid: {result.get('valid', 'N/A')}")
        if 'correlation' in result:
            print(f"  Correlation: {result['correlation']:.3f}")
        if 'p_value' in result:
            print(f"  P-value: {result['p_value']:.4f}")

# レポートの生成（JSON形式）
validator.generate_report("experiments/outputs/validation_report.json")
```

### 検証される7つの経済現象

#### 1. Phillips Curve（フィリップス曲線）

失業率とインフレ率の負の相関。

**検証基準**: `r < 0, p < 0.05`

```python
phillips = results['phillips_curve']
print(f"Phillips Curve: {'✅' if phillips['valid'] else '❌'}")
print(f"  Correlation: {phillips['correlation']:.3f}")
print(f"  P-value: {phillips['p_value']:.4f}")
```

#### 2. Okun's Law（オークンの法則）

失業率の変化とGDP成長率の負の相関。

**検証基準**: `r < 0, p < 0.05`

```python
okun = results['okuns_law']
print(f"Okun's Law: {'✅' if okun['valid'] else '❌'}")
print(f"  Correlation: {okun['correlation']:.3f}")
```

#### 3. Beveridge Curve（ベバリッジ曲線）

求人率と失業率の強い負の相関。

**検証基準**: `r < -0.5, p < 0.05`

```python
beveridge = results['beveridge_curve']
print(f"Beveridge Curve: {'✅' if beveridge['valid'] else '❌'}")
print(f"  Correlation: {beveridge['correlation']:.3f}")
```

#### 4. Price Elasticity（需要の価格弾力性）

必需品は非弾力的（-1 < E < 0）、贅沢品は弾力的（E < -1）。

**検証基準**:
- 必需品: `-1 < E < 0`
- 贅沢品: `E < -1`

```python
elasticity = results['price_elasticity']
print(f"Price Elasticity:")
print(f"  Necessities: {elasticity['necessities']['mean_elasticity']:.3f}")
print(f"  Luxuries: {elasticity['luxuries']['mean_elasticity']:.3f}")
```

#### 5. Engel's Law（エンゲルの法則）

所得が増えると、食料支出の割合が減少。

**検証基準**: `r < 0, p < 0.05`

```python
engel = results['engels_law']
print(f"Engel's Law: {'✅' if engel['valid'] else '❌'}")
print(f"  Correlation: {engel['correlation']:.3f}")
```

#### 6. Investment Volatility（投資のボラティリティ）

投資のボラティリティは消費よりも高い。

**検証基準**: `std(Investment) > std(Consumption)`

```python
volatility = results['investment_volatility']
print(f"Investment Volatility: {'✅' if volatility['valid'] else '❌'}")
print(f"  Investment std: {volatility['investment_std']:.2f}")
print(f"  Consumption std: {volatility['consumption_std']:.2f}")
```

#### 7. Price Stickiness（価格の粘着性）

価格は需要の変化に対して遅れて調整される。

**検証基準**: 価格変化頻度 < 需要変化頻度

```python
stickiness = results['price_stickiness']
print(f"Price Stickiness: {'✅' if stickiness['valid'] else '❌'}")
print(f"  Price change frequency: {stickiness['price_change_frequency']:.2%}")
print(f"  Demand change frequency: {stickiness['demand_change_frequency']:.2%}")
```

### カスタム検証

特定の経済現象のみを検証することも可能：

```python
# Phillips Curveのみ検証
phillips_result = validator.validate_phillips_curve()

# Okun's Lawのみ検証
okun_result = validator.validate_okuns_law()

# Price Elasticityのみ検証
elasticity_result = validator.validate_price_elasticity()
```

## ロバストネステスト

異なる乱数シードで複数回実行し、結果の安定性と一貫性を検証します。

### 基本的なロバストネステスト

```python
from experiments.robustness_test import run_robustness_test

# 複数のシミュレーション結果ファイル
simulation_files = [
    "experiments/outputs/run_seed42/results.json",
    "experiments/outputs/run_seed123/results.json",
    "experiments/outputs/run_seed456/results.json",
]

# ロバストネステストの実行
report = run_robustness_test(
    simulation_data_paths=simulation_files,
    output_path="experiments/outputs/robustness_report.json"
)

# 結果の確認
assessment = report["overall_assessment"]
print(f"\n{'='*50}")
print(f"Robustness Test Results")
print(f"{'='*50}")
print(f"Qualitative Consistency: {'✅' if assessment['qualitative_consistency'] else '❌'}")
print(f"Statistical Stability: {'✅' if assessment['statistical_stability'] else '❌'}")
print(f"Trend Consistency: {'✅' if assessment['trend_consistency'] else '❌'}")
print(f"\nOverall: {'✅ ROBUST' if assessment['robust'] else '❌ NOT ROBUST'}")
```

### ロバストネステストの3つの検証項目

#### 1. 定性的一致 (Qualitative Consistency)

すべての実行で7つの経済現象が同じ方向性（正/負の相関）を示すか確認。

```python
consistency = report["qualitative_consistency"]
print(f"\nQualitative Consistency: {consistency['overall_consistent']}")

for phenomenon, info in consistency['phenomena'].items():
    if 'consistent' in info:
        success_rate = info['success_rate']
        print(f"  {phenomenon}: {success_rate:.0%} consistent")
```

#### 2. 統計的安定性 (Statistical Significance)

経済指標の変動係数（CV）を計算し、安定性を評価。

**安定性の基準**:
- CV < 0.3: 低変動（安定）
- 0.3 ≤ CV < 0.6: 中程度の変動
- CV ≥ 0.6: 高変動（不安定）

```python
significance = report["statistical_significance"]

for indicator, stats in significance.items():
    print(f"\n{indicator}:")
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Std: {stats['std']:.2f}")
    print(f"  CV: {stats['cv']:.3f}")
    print(f"  Stability: {stats['stability']}")
```

#### 3. トレンド一致性 (Trend Consistency)

GDPや失業率などの時系列トレンド（上昇/下降）が一致するか確認。

```python
trends = report["trend_consistency"]

for indicator, info in trends.items():
    print(f"\n{indicator}:")
    print(f"  Trend directions: {info['trend_directions']}")
    print(f"  Consistent: {info['consistent']}")
    print(f"  Mean correlation: {info['mean_correlation']:.3f}")
```

### プログラムによる複数シード実行＋ロバストネステスト

```python
from pathlib import Path
from src.environment.simulation import Simulation
from src.utils.config import load_config
from experiments.robustness_test import run_robustness_test

# 1. 複数のシードで実行
seeds = [42, 123, 456]
output_dir = Path("experiments/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

simulation_files = []

for seed in seeds:
    print(f"\n=== Running simulation with seed {seed} ===")

    config = load_config("config/simulation_config.yaml")
    config.simulation.random_seed = seed

    sim = Simulation(config)

    for step in range(config.simulation.max_steps):
        sim.step()
        if step % 30 == 0:
            print(f"  Step {step}/{config.simulation.max_steps}")

    output_path = str(output_dir / f"run_seed{seed}")
    sim.save_results(output_path)
    simulation_files.append(f"{output_path}/results.json")

# 2. ロバストネステストの実行
print("\n=== Running robustness test ===")
report = run_robustness_test(
    simulation_data_paths=simulation_files,
    output_path=str(output_dir / "robustness_report.json")
)

# 3. 結果の表示
if report["overall_assessment"]["robust"]:
    print("\n✅ シミュレーションはrobustと判定されました")
else:
    print("\n⚠️ ロバストネステストに失敗しました")
```

## 結果の可視化

### Streamlitダッシュボード

最も簡単な可視化方法：

```bash
uv run streamlit run app.py
```

ダッシュボードの機能：

1. **Overview**: シミュレーション概要とシステム統計
2. **City Map**: 都市マップの可視化（建物タイプ、占有率、密度）
3. **Economic Indicators**: 経済指標の時系列グラフ
4. **Analysis**: 経済現象の分析（散布図、相関分析）

### Pythonコードからの可視化

#### 時系列グラフ

```python
from src.visualization.plots import plot_economic_indicators
import matplotlib.pyplot as plt

# 結果の読み込み
with open("experiments/outputs/baseline_run/results.json") as f:
    sim_data = json.load(f)

# 経済指標の可視化
fig = plot_economic_indicators(sim_data['history'])
plt.savefig("economic_indicators.png", dpi=300, bbox_inches='tight')
plt.show()
```

#### 経済現象の散布図

```python
from src.visualization.plots import plot_phillips_curve, plot_okuns_law

# Phillips Curve
fig_phillips = plot_phillips_curve(sim_data['history'])
plt.savefig("phillips_curve.png", dpi=300, bbox_inches='tight')

# Okun's Law
fig_okun = plot_okuns_law(sim_data['history'])
plt.savefig("okuns_law.png", dpi=300, bbox_inches='tight')
```

#### 都市マップ

```python
from src.visualization.map_generator import MapGenerator

# CityMapオブジェクトが必要
city_map = sim.city_map  # シミュレーション実行後

map_gen = MapGenerator(city_map)

# 建物タイプマップ
fig_building = map_gen.generate_building_type_map()
plt.savefig("city_building_map.png", dpi=300, bbox_inches='tight')

# 占有率ヒートマップ
fig_occupancy = map_gen.generate_occupancy_heatmap()
plt.savefig("city_occupancy.png", dpi=300, bbox_inches='tight')

# 密度マップ
fig_density = map_gen.generate_density_map()
plt.savefig("city_density.png", dpi=300, bbox_inches='tight')
```

#### 分布分析

```python
from src.visualization.plots import plot_income_distribution

# 所得分布
fig_income = plot_income_distribution(sim_data['history']['household_incomes'][-1])
plt.savefig("income_distribution.png", dpi=300, bbox_inches='tight')
```

## 高度な使い方

### カスタムエージェントの追加

独自のエージェントを作成する場合：

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str, config: dict):
        super().__init__(agent_id=agent_id, agent_type="custom")
        self.config = config

    def decide(self, state: dict) -> dict:
        """意思決定ロジック"""
        # LLMを使った意思決定
        prompt = f"Current state: {state}. What should I do?"
        response = self.llm_interface.generate(
            agent_type="custom",
            prompt=prompt,
            state=state
        )
        return response

    def step(self, environment_state: dict):
        """1ステップの実行"""
        decision = self.decide(environment_state)
        # 決定に基づいてアクションを実行
        return decision
```

### カスタム経済指標の追加

```python
from src.models.economic_models import MacroeconomicIndicators

class CustomIndicators(MacroeconomicIndicators):
    def calculate_custom_metric(self, data: list[float]) -> float:
        """カスタム指標の計算"""
        # 独自の経済指標を実装
        return sum(data) / len(data)
```

### LLMコールバックのカスタマイズ

```python
from src.llm.llm_interface import LLMInterface

def custom_callback(response: dict):
    """LLM呼び出し後のカスタム処理"""
    print(f"LLM Response: {response}")
    # カスタムロギングや分析

llm_interface = LLMInterface(config)
llm_interface.add_callback(custom_callback)
```

### 外生ショック実験

#### 価格ショック

```python
# シミュレーション実行中に価格ショックを注入
for step in range(config.simulation.max_steps):
    sim.step()

    # ステップ50で価格ショック（特定の財の価格を2倍に）
    if step == 50:
        goods_market = sim.goods_market
        goods_market.prices['food_grain'] *= 2.0
        print("Price shock injected: food_grain price doubled")
```

#### 政策変更

```python
# ステップ100でUBI金額を増加
for step in range(config.simulation.max_steps):
    sim.step()

    if step == 100:
        government = sim.government
        government.ubi_amount *= 1.5
        print("Policy change: UBI increased by 50%")
```

#### 人口変動

```python
# ステップ75で新規世帯を追加
for step in range(config.simulation.max_steps):
    sim.step()

    if step == 75:
        # 新規世帯の追加（実装によって異なる）
        sim.add_new_households(count=20)
        print("Population shock: 20 new households added")
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. OpenAI API エラー

**問題**: `openai.error.AuthenticationError`

**解決方法**:
- `.env`ファイルに正しいAPIキーが設定されているか確認
- APIキーに余分なスペースや改行が含まれていないか確認

```bash
# .envファイルの確認
cat .env
# OPENAI_API_KEY=sk-... （余分なスペースなし）
```

#### 2. メモリ不足

**問題**: `MemoryError` または極端な遅延

**解決方法**:
- 世帯数を減らす（`config/simulation_config.yaml`）
- LLM履歴の圧縮を有効化（`config/llm_config.yaml`）
- ステップ数を減らす

```yaml
# simulation_config.yaml
agents:
  households:
    max: 100  # 200 → 100に削減
```

#### 3. LLM応答の異常

**問題**: エージェントが異常な決定をする

**解決方法**:
- プロンプトテンプレートを確認（`src/llm/prompts/`）
- `temperature`を下げる（`config/llm_config.yaml`）
- ヒューリスティックチェックを実装

```yaml
# llm_config.yaml
openai:
  temperature: 0.5  # 0.7 → 0.5に削減
```

#### 4. 検証テストの失敗

**問題**: 経済現象の検証が失敗する

**解決方法**:
- シミュレーションステップ数を増やす（最低50ステップ推奨）
- 乱数シードを変更してみる
- 市場パラメータを調整する

```python
# より長いシミュレーション
config.simulation.max_steps = 180  # 推奨
```

#### 5. コストが高すぎる

**問題**: API使用料が予想以上に高い

**解決方法**:
- プロンプトキャッシングを有効化
- `gpt-4o-mini`を使用（`gpt-4`より安価）
- 履歴の長さを制限

```yaml
# llm_config.yaml
prompt_caching:
  enabled: true  # キャッシング有効化

memory:
  max_history_length: 5  # 履歴を5ステップに制限
```

### デバッグのヒント

#### ログレベルの調整

```python
from src.utils.logger import setup_logger

# 詳細なログを出力
setup_logger(log_level="DEBUG", log_file="debug.log")
```

#### 特定のステップでブレークポイント

```python
for step in range(config.simulation.max_steps):
    sim.step()

    # ステップ30で詳細な状態を確認
    if step == 30:
        metrics = sim.get_metrics()
        print(f"Detailed state at step {step}:")
        print(f"  GDP: {metrics['gdp']}")
        print(f"  Active households: {len(sim.households)}")
        print(f"  Active firms: {len(sim.firms)}")
        import pdb; pdb.set_trace()  # デバッガ起動
```

#### LLMコストの監視

```python
from src.llm.llm_interface import LLMInterface

llm = LLMInterface(config)

# シミュレーション実行後
print(f"Total cost: ${llm.get_total_cost():.2f}")
print(f"Total tokens: {llm.get_total_tokens()}")
```

## さらなるリソース

- [README.md](../README.md): プロジェクト概要
- [CLAUDE.md](../CLAUDE.md): アーキテクチャと設計ガイド
- [TASKS.md](../TASKS.md): 詳細なタスク管理と進捗
- [論文](../2510.01297v1.md): 元論文（マークダウン版）

## サポート

問題や質問がある場合は、[GitHubのIssue](https://github.com/ayutaz/SimCity-reproduction/issues)を作成してください。

---

**Note**: このプロジェクトは研究・教育目的です。実世界の経済予測には使用しないでください。
