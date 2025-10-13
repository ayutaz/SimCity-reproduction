# SimCity: マルチエージェント都市経済シミュレーション

LLMを活用したマクロ経済シミュレーションフレームワーク。異質なエージェント間の豊かな相互作用と、都市拡大のダイナミクスを統合した環境でのマクロ経済現象の再現を目指します。

## 📖 概要

このプロジェクトは、論文 ["SimCity: Multi-Agent Urban Development Simulation with Rich Interactions"](2510.01297v1.md) の実装です。

### 主な特徴

- **4種類のLLM駆動エージェント**: 家計（200世帯）、企業（動的）、政府、中央銀行
- **3つの市場**: 労働市場、財市場（10+カテゴリ、44種類の商品）、金融市場
- **マクロ経済現象の再現**:
  - フィリップス曲線（Phillips Curve）
  - オークンの法則（Okun's Law）
  - ベバリッジ曲線（Beveridge Curve）
  - 需要の価格弾力性（Price Elasticity）
  - エンゲルの法則（Engel's Law）
  - 投資のボラティリティ
  - 価格の粘着性
- **可視化**: Streamlitベースのリアルタイムダッシュボード
- **コスト最適化**: gpt-4o-mini使用で180ステップあたり$15-18

## 🛠️ 技術スタック

- **Python**: 3.12
- **LLM**: OpenAI gpt-4o-mini
- **可視化**: Streamlit + Plotly
- **データ処理**: NumPy, Pandas, SciPy
- **設定管理**: YAML, python-dotenv

## 📦 インストール

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
git clone <repository-url>
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

## 🚀 クイックスタート

### 基本的な実行

```bash
# シミュレーションの実行（CLIモード）
uv run python -m src.main

# Streamlit UIの起動
uv run streamlit run src/visualization/app.py
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

## 📁 プロジェクト構造

```
SimCity/
├── src/
│   ├── agents/              # エージェント実装
│   │   ├── base_agent.py
│   │   ├── household.py
│   │   ├── firm.py
│   │   ├── government.py
│   │   └── central_bank.py
│   ├── environment/         # シミュレーション環境
│   │   ├── simulation.py
│   │   ├── markets/
│   │   │   ├── labor_market.py
│   │   │   ├── goods_market.py
│   │   │   └── financial_market.py
│   │   └── geography.py
│   ├── llm/                 # LLM統合
│   │   ├── llm_interface.py
│   │   └── prompts/
│   ├── models/              # 経済モデル
│   │   ├── production.py
│   │   ├── taxation.py
│   │   └── monetary_policy.py
│   ├── data/                # データファイル
│   │   ├── skills.json
│   │   ├── goods.json
│   │   └── household_profiles.json
│   ├── visualization/       # Streamlit UI
│   │   └── app.py
│   ├── utils/               # ユーティリティ
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py             # エントリーポイント
├── tests/                   # テスト
├── experiments/            # 実験結果
│   ├── logs/
│   ├── plots/
│   └── outputs/
├── config/                 # 設定ファイル
│   ├── simulation_config.yaml
│   └── llm_config.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md               # 実装ガイド
└── IMPLEMENTATION_PLAN.md  # 実装計画
```

## 🎯 使用例

### Python APIでの実行

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

### カスタムエージェントの作成

```python
from src.agents.base_agent import BaseAgent

class CustomHousehold(BaseAgent):
    def decide_actions(self, observation: dict) -> dict:
        # カスタム意思決定ロジック
        pass
```

## 📊 評価とバリデーション

シミュレーションは以下のマクロ経済現象を再現します:

| 現象 | 説明 | 検証方法 |
|------|------|----------|
| フィリップス曲線 | 失業率とインフレの負の相関 | 相関係数 r < 0 |
| オークンの法則 | 失業率変化とGDP成長率の負の相関 | 相関係数 r < 0 |
| ベバリッジ曲線 | 求人率と失業率の負の相関 | 相関係数 r < -0.5 |
| 価格弾力性 | 必需品は非弾力的、贅沢品は弾力的 | -1 < E < 0 (必需品), E < -1 (贅沢品) |
| エンゲルの法則 | 所得増加に伴う食料支出割合の減少 | 回帰分析 |

実験の実行:
```bash
uv run python -m src.experiments.validate_phenomena
```

## 💰 コスト見積もり

**gpt-4o-mini使用時**（2024年12月時点）:
- 入力: $0.15 / 100万トークン
- 出力: $0.60 / 100万トークン

**180ステップシミュレーション**:
- 推定コスト: $15-18
- 開発時（月間）: $50-70

コスト削減のヒント:
- プロンプトキャッシングを有効化（`llm_config.yaml`）
- 履歴圧縮を使用
- 不要なログを無効化

## 🔧 開発

### テストの実行

```bash
# 全テストの実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=src --cov-report=html

# 特定のテスト
uv run pytest tests/test_agents.py
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

# mypy（型チェック）
uv run mypy src/
```

### デバッグモード

`config/llm_config.yaml`で:
```yaml
debug:
  log_all_prompts: true
  log_all_responses: true
  save_failed_calls: true
```

## 📚 ドキュメント

- [CLAUDE.md](CLAUDE.md) - アーキテクチャと実装ガイド
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 8フェーズの実装計画
- [2510.01297v1.md](2510.01297v1.md) - 元論文（マークダウン版）

## 🛣️ ロードマップ

- [x] **Phase 0**: プロジェクトセットアップ（完了）
- [ ] **Phase 1**: LLM統合とコア基盤（進行中）
- [ ] **Phase 2**: エージェント実装
- [ ] **Phase 3**: 市場メカニズム
- [ ] **Phase 4**: 地理と可視化
- [ ] **Phase 5**: データ準備
- [ ] **Phase 6**: 統合テストとバリデーション
- [ ] **Phase 7**: 実験と最適化
- [ ] **Phase 8**: 配布準備

詳細は [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) を参照してください。

## ⚠️ 制限事項

1. **LLMの異常行動**: ヒューリスティックチェックで検証
2. **複雑な金融活動の欠如**: 債券、株式、デリバティブは未実装
3. **計算コスト**: 大規模シミュレーション（世帯数 > 500）は高コスト
4. **実世界との乖離**: キャリブレーションされていない学術的シミュレーション

## 📄 ライセンス

[ライセンスを指定してください]

## 🙏 謝辞

このプロジェクトは以下の論文に基づいています:

**SimCity: Multi-Agent Urban Development Simulation with Rich Interactions**
Yeqi Feng, Yucheng Lu, Hongyu Su, Tianxing He
arXiv:2510.01297v1 [cs.MA] 1 Oct 2025

## 📞 連絡先

問題や質問がある場合は、[Issueを作成](../../issues)してください。

---

**Note**: このプロジェクトは研究・教育目的です。実世界の経済予測には使用しないでください。
