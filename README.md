# SimCity: マルチエージェント都市経済シミュレーション

LLMを活用したマクロ経済シミュレーションフレームワーク。異質なエージェント間の豊かな相互作用と、都市拡大のダイナミクスを統合した環境でのマクロ経済現象の再現を目指します。

## 概要

このプロジェクトは、論文 ["SimCity: Multi-Agent Urban Development Simulation with Rich Interactions"](2510.01297v1.md) の実装です。

### 主な特徴

- **4種類のLLM駆動エージェント**: 家計（200世帯）、企業（動的）、政府、中央銀行
- **3つの市場**: 労働市場、財市場（10カテゴリ、44種類の商品）、金融市場
- **マクロ経済現象の再現**:
  - フィリップス曲線（Phillips Curve）
  - オークンの法則（Okun's Law）
  - ベバリッジ曲線（Beveridge Curve）
  - 需要の価格弾力性（Price Elasticity）
  - エンゲルの法則（Engel's Law）
  - 投資のボラティリティ
  - 価格の粘着性
- **データ駆動設計**: 58種類のスキル、44種類の財、44企業テンプレート
- **コスト最適化**: gpt-4o-mini使用で180ステップあたり$15-18

## 技術スタック

- **Python**: 3.12
- **パッケージ管理**: uv
- **LLM**: OpenAI gpt-4o-mini
- **可視化**: Streamlit + Matplotlib
- **データ処理**: NumPy, Pandas, SciPy
- **設定管理**: YAML, Pydantic, python-dotenv
- **コード品質**: ruff (linter + formatter)
- **テスト**: pytest

## インストール

### 前提条件

- Python 3.12以上
- uv (Pythonパッケージマネージャー)
- OpenAI APIキー

### uvのインストール

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### セットアップ手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/ayutaz/SimCity-reproduction.git
cd SimCity
```

2. **Python環境のセットアップ（uvで自動管理）**
```bash
# Pythonバージョンとパッケージのインストール
uv sync
```

3. **環境変数の設定**
```bash
cp .env.example .env
# .envファイルを編集してOpenAI APIキーを設定
```

.envファイル内:
```
OPENAI_API_KEY=your_actual_api_key_here
```

## クイックスタート

### ダッシュボードの起動

```bash
# Streamlitダッシュボードを起動
uv run streamlit run app.py

# ブラウザが自動で開き、http://localhost:8501 でアクセス可能
```

ダッシュボードには以下の機能があります：
- **Overview**: シミュレーション概要とシステム統計
- **City Map**: 都市マップの可視化（建物タイプ、占有率、密度）
- **Economic Indicators**: 経済指標の時系列グラフ
- **Analysis**: 経済現象の分析（フィリップス曲線、オークンの法則等）

### テストの実行

```bash
# 全テストの実行（189テスト）
uv run pytest

# カバレッジ付き（カバレッジ: 86%）
uv run pytest --cov=src --cov-report=html

# 特定のテストファイル
uv run pytest tests/test_labor_market.py -v
```

### 設定のカスタマイズ

`config/simulation_config.yaml` でシミュレーションパラメータを調整:
```yaml
simulation:
  max_steps: 180  # ステップ数を変更
agents:
  households:
    max: 200  # 最大世帯数を変更
```

`config/llm_config.yaml` でLLM設定を調整:
```yaml
openai:
  model: "gpt-4o-mini"  # モデルを変更
  temperature: 0.7  # 生成のランダム性を調整
```

## プロジェクト構造

```
SimCity/
├── src/
│   ├── agents/              # エージェント実装（Phase 2完了）
│   │   ├── base_agent.py           # 基底エージェントクラス (283行)
│   │   ├── household.py            # 世帯エージェント (501行)
│   │   ├── firm.py                 # 企業エージェント (395行)
│   │   ├── government.py           # 政府エージェント (301行)
│   │   └── central_bank.py         # 中央銀行エージェント (287行)
│   ├── environment/         # シミュレーション環境
│   │   ├── simulation.py           # シミュレーションエンジン (355行)
│   │   └── markets/                # 市場メカニズム（Phase 3完了）
│   │       ├── labor_market.py     # 労働市場 (297行)
│   │       ├── goods_market.py     # 財市場 (261行)
│   │       └── financial_market.py # 金融市場 (179行)
│   ├── llm/                 # LLM統合（Phase 1完了）
│   │   ├── llm_interface.py        # LLM APIインターフェース (263行)
│   │   └── prompts/                # プロンプトテンプレート (4ファイル)
│   ├── models/              # 経済モデル（Phase 1完了）
│   │   ├── data_models.py          # データモデル (361行)
│   │   └── economic_models.py      # 経済モデル (471行)
│   ├── data/                # データ定義（Phase 5完了）
│   │   ├── skill_types.py          # 58種類のスキル定義 (410行)
│   │   ├── goods_types.py          # 44種類の財定義 (342行)
│   │   └── firm_templates/         # 44企業テンプレート (44ファイル)
│   ├── utils/               # ユーティリティ
│   │   ├── config.py               # 設定管理 (285行)
│   │   └── logger.py               # ロガー (114行)
│   └── visualization/       # 可視化（Phase 4完了）
│       ├── geography.py             # 地理システム (332行)
│       ├── map_generator.py         # マップ可視化 (348行)
│       ├── plots.py                 # 経済グラフ生成 (561行)
│       └── dashboard.py             # Streamlitダッシュボード (573行)
├── tests/                   # テスト（189テスト、100%成功、カバレッジ86%）
│   ├── test_dashboard.py            # 4テスト
│   ├── test_economic_models.py      # 18テスト
│   ├── test_financial_market.py     # 5テスト
│   ├── test_geography.py            # 20テスト
│   ├── test_goods_market.py         # 4テスト
│   ├── test_household_agent.py      # 14テスト
│   ├── test_integration.py          # 15テスト（Phase 6.2）
│   ├── test_labor_market.py         # 8テスト
│   ├── test_llm_integration.py      # 2テスト
│   ├── test_map_generator.py        # 14テスト
│   ├── test_performance.py          # 6テスト（Phase 6.1）
│   ├── test_phase2_agents.py        # 27テスト
│   ├── test_phase5_data.py          # 14テスト
│   ├── test_plots.py                # 20テスト
│   ├── test_robustness.py           # 6テスト（Phase 6.4）
│   └── test_validation.py           # 12テスト（Phase 6.3）
├── config/                 # 設定ファイル
│   ├── simulation_config.yaml      # シミュレーション設定
│   └── llm_config.yaml             # LLM設定
├── experiments/            # 実験・検証スクリプト（Phase 6完了）
│   ├── validation.py               # 経済現象検証システム (560行)
│   └── robustness_test.py          # ロバストネステストシステム (440行)
├── pyproject.toml          # プロジェクト設定（uv管理）
├── LICENSE                 # Apache License 2.0
├── README.md               # 本ファイル
├── CLAUDE.md               # 実装ガイド
└── TASKS.md                # タスク管理・進捗追跡
```

## 実装状況

### Phase 0: プロジェクトセットアップ（完了）
- uv + ruff環境構築
- 設定ファイル整備
- ドキュメント作成
- Apache 2.0ライセンス設定

### Phase 1: コア基盤実装（完了）
- **LLM統合**: OpenAI API統合、Function Calling、コスト追跡
- **データモデル**: HouseholdProfile, FirmProfile, GovernmentState等の全モデル
- **経済モデル**: Cobb-Douglas生産関数、TaxationSystem、TaylorRule、MacroeconomicIndicators
- **シミュレーションエンジン骨格**: 4段階ループ、状態管理
- **BaseAgent**: エージェント基底クラス、メモリ管理
- **ユーティリティ**: Pydantic設定管理、Loguru統合

### Phase 2: エージェント実装（完了）
- **HouseholdAgent**: 5つの意思決定関数、Lognormal分布プロファイル生成
- **FirmAgent**: 44企業テンプレート対応、Cobb-Douglas生産関数統合
- **GovernmentAgent**: 累進課税、UBI配布、失業給付
- **CentralBankAgent**: Taylor rule、金利平滑化（ρ=0.8）
- **テスト**: 41/41テスト成功

### Phase 3: 市場メカニズム実装（完了）
- **LaborMarket**: 確率的マッチング、スキルベース効率計算、距離考慮オプション
- **GoodsMarket**: 44財の取引、価格ベースマッチング、需給ミスマッチ追跡
- **FinancialMarket**: 預金・貸出システム、政策金利+スプレッド方式
- **テスト**: 17/17テスト成功

### Phase 4: 地理・可視化実装（完了）
- **地理システム (geography.py)**: 100×100グリッドベース都市マップ、建物管理、距離計算
- **マップ可視化 (map_generator.py)**: 建物タイプマップ、占有率ヒートマップ、密度マップ、複合ビュー
- **経済グラフ (plots.py)**: フィリップス曲線、オークンの法則、ベバリッジ曲線、エンゲルの法則、価格弾力性、分布分析
- **Streamlitダッシュボード (dashboard.py)**: インタラクティブWeb UI、リアルタイム可視化
- **テスト**: 58/58テスト成功（geography 20 + map_generator 14 + plots 20 + dashboard 4）

### Phase 5: データ準備（完了）
- **スキルデータ**: 58種類定義完了（10カテゴリ）
- **財データ**: 44種類定義完了（10カテゴリ、必需品22+奢侈品22）
- **企業テンプレート**: 44種類のJSONテンプレート完了
- **世帯プロファイル生成**: HouseholdProfileGenerator完全実装（Lognormal分布、正規分布年齢、教育レベル別スキル割り当て）
- **初期データセット**: 200世帯データ生成スクリプト + JSONデータ（224.8 KB）
- **テスト**: 14/14テスト成功

### Phase 6: 統合テスト・検証（完了: 15/15タスク）✅
- **Phase 6.1 単体テスト補完**: ✅ 完了（6テスト、カバレッジ86%）
  - パフォーマンステスト（世帯生成、Gini係数計算、生産関数）
  - スケーラビリティテスト（100/200/500世帯）
  - カバレッジ目標80%達成（実績86%）
- **Phase 6.2 統合テスト**: ✅ 完了（15テスト、100%成功）
  - 市場メカニズム統合テスト
  - シミュレーション実行テスト（12ステップ）
  - 状態保存/復元テスト
  - 地理システム統合テスト
- **Phase 6.3 経済現象検証**: ✅ 完了（12テスト、7つの経済法則）
  - Phillips Curve、Okun's Law、Beveridge Curve
  - Price Elasticity、Engel's Law
  - Investment Volatility、Price Stickiness
  - 統計的検証システム（experiments/validation.py）
- **Phase 6.4 ロバストネステスト**: ✅ 完了（6テスト）
  - 定性的一致検証（7つの経済現象）
  - 統計的有意性検証（変動係数による安定性評価）
  - トレンド一致性検証（時系列相関分析）
  - ロバストネステストシステム（experiments/robustness_test.py）

### Phase 7: 実験・最適化（進行中）
- **Phase 7.1 ベースライン実行**: 180ステップのベースライン実行、全経済指標の記録
- **Phase 7.2 外生ショック実験**: 価格ショック、政策変更、人口変動の影響分析
- **Phase 7.3 パフォーマンス最適化**: LLM呼び出し削減、キャッシング、バッチ処理、メモリ削減
- **Phase 7.4 ドキュメント整備**: 使い方ガイド、API文書、実験結果の文書化（進行中）

### Phase 8: 配布準備（未実装）
- Docker化
- CI/CD整備
- PyPI公開準備

## テスト結果

```bash
全189テスト実行: 189/189成功 (100%)
- Phase 1: 20テスト (経済モデル18 + LLM統合2)
- Phase 2: 41テスト (世帯14 + 全エージェント27)
- Phase 3: 17テスト (労働市場8 + 財市場4 + 金融市場5)
- Phase 4: 58テスト (地理20 + マップ14 + グラフ20 + ダッシュボード4)
- Phase 5: 14テスト (データ生成・検証)
- Phase 6: 39テスト (統合15 + 検証12 + ロバストネス6 + パフォーマンス6)

カバレッジ: 86%（目標80%達成）
コード品質: ruff All checks passed
```

## 使い方ガイド

### 1. 基本的なシミュレーション実行

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

# 設定の読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーションの初期化
sim = Simulation(config)

# シミュレーションの実行
for step in range(config.simulation.max_steps):
    sim.step()

    # マクロ経済指標の取得
    metrics = sim.get_metrics()
    print(f"Step {step}: GDP={metrics['gdp']:.2f}, "
          f"Unemployment={metrics['unemployment_rate']:.2%}")

# 結果の保存
sim.save_results("experiments/outputs/run_001")
```

### 2. 経済現象の検証

シミュレーション結果から7つの経済現象を統計的に検証できます：

```python
from experiments.validation import EconomicPhenomenaValidator
import json

# シミュレーション結果の読み込み
with open("experiments/outputs/run_001/results.json") as f:
    sim_data = json.load(f)

# 検証システムの初期化
validator = EconomicPhenomenaValidator(sim_data)

# 全ての経済現象を検証
results = validator.validate_all()

# 結果の確認
print(f"検証成功率: {results['summary']['success_rate']:.1%}")
print(f"Phillips Curve: {results['phillips_curve']['valid']}")
print(f"Okun's Law: {results['okuns_law']['valid']}")

# レポートの生成
validator.generate_report("experiments/outputs/validation_report.json")
```

**検証される経済現象:**

| 現象 | 説明 | 検証基準 |
|------|------|----------|
| Phillips Curve | 失業率とインフレの負の相関 | r < 0, p < 0.05 |
| Okun's Law | 失業率変化とGDP成長率の負の相関 | r < 0, p < 0.05 |
| Beveridge Curve | 求人率と失業率の強い負の相関 | r < -0.5, p < 0.05 |
| Price Elasticity | 需要の価格弾力性 | 必需品: -1 < E < 0<br>贅沢品: E < -1 |
| Engel's Law | 所得上昇→食料支出割合減少 | r < 0, p < 0.05 |
| Investment Volatility | 投資のボラティリティ > 消費 | std(I) > std(C) |
| Price Stickiness | 価格調整の遅延 | 価格変化頻度 < 需要変化頻度 |

### 3. ロバストネステスト

異なる乱数シードで複数回実行し、結果の安定性を検証：

```python
from experiments.robustness_test import run_robustness_test

# 複数のシミュレーション結果でロバストネステスト
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
if report["overall_assessment"]["robust"]:
    print("✅ シミュレーションは robust と判定されました")
else:
    print("⚠️ ロバストネステストに失敗しました")
```

### 4. 結果の可視化

Streamlitダッシュボードで結果を可視化：

```bash
# ダッシュボードの起動
uv run streamlit run app.py
```

ダッシュボードでは以下の分析が可能です：
- 経済指標の時系列推移（GDP、失業率、インフレ率、Gini係数）
- 経済現象の可視化（Phillips Curve、Okun's Law等）
- 都市マップの可視化（建物配置、占有率）
- 分布分析（所得分布、価格分布）

## コスト見積もり

**gpt-4o-mini使用時**（2024年12月時点）:
- 入力: $0.15 / 100万トークン
- 出力: $0.60 / 100万トークン

**180ステップシミュレーション**:
- 推定コスト: $15-18（最適化後）
- 論文版（gpt-4）: $180
- 開発時（月間）: $50-70

コスト削減のヒント:
- プロンプトキャッシングを有効化（`llm_config.yaml`）
- 履歴圧縮を使用
- 不要なログを無効化

## 開発

### テストの実行

```bash
# 全テストの実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=src --cov-report=html

# 特定のテスト
uv run pytest tests/test_labor_market.py -v
```

### コードフォーマット

```bash
# Ruff（リンターとフォーマッター）
# チェックのみ
uv run ruff check src/ tests/

# フォーマット適用
uv run ruff format src/ tests/

# 自動修正
uv run ruff check --fix src/ tests/
```

## ドキュメント

- [docs/USAGE.md](docs/USAGE.md) - 詳細な使い方ガイド（シミュレーション実行、検証、可視化）
- [docs/API.md](docs/API.md) - APIリファレンス（クラス・メソッドの詳細）
- [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md) - パフォーマンス最適化戦略（コスト削減、高速化）
- [CLAUDE.md](CLAUDE.md) - アーキテクチャと実装ガイド
- [TASKS.md](TASKS.md) - 詳細なタスク管理・進捗追跡（119/134タスク完了、89%）
- [2510.01297v1.md](2510.01297v1.md) - 元論文（マークダウン版）

## ロードマップ

- [x] **Phase 0**: プロジェクトセットアップ（完了）
- [x] **Phase 1**: LLM統合とコア基盤（完了）
- [x] **Phase 2**: エージェント実装（完了）
- [x] **Phase 3**: 市場メカニズム（完了）
- [x] **Phase 4**: 地理と可視化（完了）
- [x] **Phase 5**: データ準備（完了）
- [x] **Phase 6**: 統合テストとバリデーション（完了）✅
- [ ] **Phase 7**: 実験と最適化（進行中）🚧
- [ ] **Phase 8**: 配布準備（待機）

**現在の進捗**: Phase 0-6 完了、Phase 7 進行中（119/134タスク、89%）

詳細は [TASKS.md](TASKS.md) を参照してください。

## 制限事項

1. **LLMの異常行動**: ヒューリスティックチェックで検証（実装予定）
2. **複雑な金融活動の欠如**: 債券、株式、デリバティブは未実装
3. **計算コスト**: 大規模シミュレーション（世帯数 > 500）は高コスト
4. **実世界との乖離**: キャリブレーションされていない学術的シミュレーション

## ライセンス

このプロジェクトはApache License 2.0の下でライセンスされています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

Copyright 2025 ayutaz

## 謝辞

このプロジェクトは以下の論文に基づいています:

**SimCity: Multi-Agent Urban Development Simulation with Rich Interactions**
Yeqi Feng, Yucheng Lu, Hongyu Su, Tianxing He
arXiv:2510.01297v1 [cs.MA] 1 Oct 2025

## 連絡先

問題や質問がある場合は、[Issueを作成](https://github.com/ayutaz/SimCity-reproduction/issues)してください。

---

**Note**: このプロジェクトは研究・教育目的です。実世界の経済予測には使用しないでください。
