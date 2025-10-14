# SimCity: マルチエージェント都市経済シミュレーション

[![Tests](https://github.com/ayutaz/SimCity-reproduction/actions/workflows/test.yml/badge.svg)](https://github.com/ayutaz/SimCity-reproduction/actions/workflows/test.yml)
[![Lint](https://github.com/ayutaz/SimCity-reproduction/actions/workflows/lint.yml/badge.svg)](https://github.com/ayutaz/SimCity-reproduction/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/ayutaz/SimCity-reproduction/branch/main/graph/badge.svg)](https://codecov.io/gh/ayutaz/SimCity-reproduction)

**AIエージェントによる都市経済シミュレーション**

LLMで制御される200世帯のエージェントが、労働・消費・投資を行い、現実の経済現象（フィリップス曲線、オークンの法則など）を再現します。

## 主な機能

- **AIエージェント**: LLMで意思決定する200世帯、企業、政府、中央銀行
- **経済現象の再現**: フィリップス曲線、オークンの法則、ベバリッジ曲線など7つの経済法則
- **インタラクティブダッシュボード**: リアルタイム経済指標と都市マップの可視化
- **実験機能**: 価格ショック、政策変更、人口変動などのシナリオ実行

## クイックスタート

### 1. インストール

```bash
# リポジトリのクローン
git clone https://github.com/ayutaz/SimCity-reproduction.git
cd SimCity

# 依存パッケージのインストール（uvが自動でPython環境を管理）
curl -LsSf https://astral.sh/uv/install.sh | sh  # uvのインストール（初回のみ）
uv sync
```

### 2. API キーの設定

```bash
# .envファイルを作成
cp .env.example .env

# .envを編集してOpenAI APIキーを設定
# OPENAI_API_KEY=your_api_key_here
```

### 3. ダッシュボードの起動

```bash
uv run streamlit run app.py
```

ブラウザで http://localhost:8501 が開き、以下を確認できます：
- **経済指標の時系列**: GDP、失業率、インフレ率、Gini係数
- **都市マップ**: 建物配置と占有率の可視化
- **経済現象の分析**: フィリップス曲線などの統計的検証

## 使い方

### シミュレーションの実行

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

# 設定ファイルの読み込み
config = load_config("config/simulation_config.yaml")

# シミュレーションの実行（180ステップ = 15年）
sim = Simulation(config)
sim.run(steps=180)

# 結果の保存
sim.save_results("results/run_001")
```

### 経済現象の検証

```python
from experiments.validation import EconomicPhenomenaValidator

# シミュレーション結果の検証
validator = EconomicPhenomenaValidator(sim.state.history)
results = validator.validate_all()

print(f"検証成功: {results['summary']['success_rate']:.0%}")
```

### 外生ショック実験

```bash
# 価格ショック: 食料価格が2倍に
uv run python scripts/run_shock_experiments.py --experiment price_shock --shock-magnitude 2.0

# 政策ショック: UBIを月額500ドルに変更
uv run python scripts/run_shock_experiments.py --experiment policy_shock --shock-magnitude 500
```

## 設定のカスタマイズ

### シミュレーション設定（`config/simulation_config.yaml`）

```yaml
simulation:
  max_steps: 180        # シミュレーションステップ数（1ステップ=1ヶ月）
  random_seed: 42       # 再現性のための乱数シード

agents:
  households:
    initial_count: 200  # 初期世帯数
    max: 500            # 最大世帯数
```

### LLM設定（`config/llm_config.yaml`）

```yaml
openai:
  model: "gpt-4o-mini"  # 使用するモデル
  temperature: 0.7      # 生成のランダム性（0-1）
  max_tokens: 1000      # 最大トークン数
```

## 再現される経済現象

| 経済現象 | 説明 |
|---------|------|
| **フィリップス曲線** | 失業率↓ → インフレ↑ の関係 |
| **オークンの法則** | GDP成長↑ → 失業率↓ の関係 |
| **ベバリッジ曲線** | 求人↑ → 失業率↓ の関係 |
| **エンゲルの法則** | 所得↑ → 食料支出割合↓ |
| **価格弾力性** | 価格↑ → 需要↓（必需品は弾力性小） |
| **投資のボラティリティ** | 投資の変動 > 消費の変動 |
| **価格の粘着性** | 価格調整が需要変化に遅れる |

## コスト

**gpt-4o-miniの場合**（2024年12月時点）:
- 180ステップ実行: 約 **$15-18**
- 開発・テスト（月間）: 約 $50-70

> 論文のgpt-4版（$180/回）と比較して **90%以上のコスト削減**

## ドキュメント

- **[docs/USAGE.md](docs/USAGE.md)** - 詳しい使い方ガイド
- **[docs/API.md](docs/API.md)** - APIリファレンス
- **[docs/OPTIMIZATION.md](docs/OPTIMIZATION.md)** - コスト削減のヒント

## 技術スタック

- **Python 3.12** + **uv**（パッケージ管理）
- **OpenAI API**（gpt-4o-mini）
- **Streamlit**（ダッシュボード）
- **NumPy / Pandas / SciPy**（データ処理）
- **Pytest**（テスト: 207件、カバレッジ88%）
- **Ruff**（コード品質: 100%準拠）

## 貢献

バグ報告や機能提案は [Issues](https://github.com/ayutaz/SimCity-reproduction/issues) までお願いします。

## ライセンス

Apache License 2.0 - 詳細は [LICENSE](LICENSE) を参照

Copyright 2025 ayutaz

## 参考論文

このプロジェクトは以下の論文の実装です:

> **SimCity: Multi-Agent Urban Development Simulation with Rich Interactions**
> Yeqi Feng, Yucheng Lu, Hongyu Su, Tianxing He
> arXiv:2510.01297v1 [cs.MA] 1 Oct 2025

---

**注意**: このプロジェクトは研究・教育目的です。実世界の経済予測には使用しないでください。
