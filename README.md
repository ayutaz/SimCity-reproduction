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
- **可視化**: Streamlit + Plotly（予定）
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

### テストの実行

```bash
# 全テストの実行（78テスト）
uv run pytest

# カバレッジ付き
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
│   ├── data/                # データ定義（Phase 5部分完了）
│   │   ├── skill_types.py          # 58種類のスキル定義 (525行)
│   │   ├── goods_types.py          # 44種類の財定義 (528行)
│   │   └── firm_templates.json     # 44企業テンプレート (598行)
│   ├── utils/               # ユーティリティ
│   │   ├── config.py               # 設定管理 (285行)
│   │   └── logger.py               # ロガー (114行)
│   └── visualization/       # 可視化（Phase 4未実装）
│       └── (未実装)
├── tests/                   # テスト（78テスト、100%成功）
│   ├── test_economic_models.py     # 18テスト
│   ├── test_financial_market.py    # 5テスト
│   ├── test_goods_market.py        # 4テスト
│   ├── test_household_agent.py     # 14テスト
│   ├── test_labor_market.py        # 8テスト
│   ├── test_llm_integration.py     # 2テスト
│   └── test_phase2_agents.py       # 27テスト
├── config/                 # 設定ファイル
│   ├── simulation_config.yaml      # シミュレーション設定
│   └── llm_config.yaml             # LLM設定
├── experiments/            # 実験スクリプト（未実装）
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

### Phase 5: データ準備（部分完了 6/8）
- **スキルデータ**: 58種類定義完了（10カテゴリ）
- **財データ**: 44種類定義完了（10カテゴリ、必需品22+奢侈品22）
- **企業テンプレート**: 44種類のJSONテンプレート完了

### Phase 4: 地理・可視化実装（未実装）
- Streamlitダッシュボード
- 都市マップ可視化
- グラフ生成

### Phase 6-8: 統合テスト・検証・配布（未実装）
- 経済現象検証（7つの曲線）
- ロバストネステスト
- 外生ショック実験
- パフォーマンス最適化
- ドキュメント整備

## テスト結果

```bash
全78テスト実行: 78/78成功 (100%)
- Phase 1: 20テスト (経済モデル18 + LLM統合2)
- Phase 2: 41テスト (世帯14 + 全エージェント27)
- Phase 3: 17テスト (労働市場8 + 財市場4 + 金融市場5)

コード品質: ruff All checks passed
```

## 使用例（実装予定）

### Python APIでの実行（Phase 6以降）

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

## 評価とバリデーション（Phase 6実装予定）

シミュレーションは以下のマクロ経済現象を再現します:

| 現象 | 説明 | 検証方法 |
|------|------|----------|
| フィリップス曲線 | 失業率とインフレの負の相関 | 相関係数 r < 0 |
| オークンの法則 | 失業率変化とGDP成長率の負の相関 | 相関係数 r < 0 |
| ベバリッジ曲線 | 求人率と失業率の負の相関 | 相関係数 r < -0.5 |
| 価格弾力性 | 必需品は非弾力的、贅沢品は弾力的 | -1 < E < 0 (必需品), E < -1 (贅沢品) |
| エンゲルの法則 | 所得増加に伴う食料支出割合の減少 | 回帰分析 |

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

- [CLAUDE.md](CLAUDE.md) - アーキテクチャと実装ガイド
- [TASKS.md](TASKS.md) - 詳細なタスク管理・進捗追跡（81/134タスク完了）
- [2510.01297v1.md](2510.01297v1.md) - 元論文（マークダウン版）

## ロードマップ

- [x] **Phase 0**: プロジェクトセットアップ（完了）
- [x] **Phase 1**: LLM統合とコア基盤（完了）
- [x] **Phase 2**: エージェント実装（完了）
- [x] **Phase 3**: 市場メカニズム（完了）
- [ ] **Phase 4**: 地理と可視化（待機）
- [ ] **Phase 5**: データ準備（6/8完了）
- [ ] **Phase 6**: 統合テストとバリデーション（待機）
- [ ] **Phase 7**: 実験と最適化（待機）
- [ ] **Phase 8**: 配布準備（待機）

**現在の進捗**: 81/134タスク完了 (60%)

詳細は [TASKS.md](TASKS.md) を参照してください。

## 制限事項

1. **LLMの異常行動**: ヒューリスティックチェックで検証（実装予定）
2. **複雑な金融活動の欠如**: 債券、株式、デリバティブは未実装
3. **計算コスト**: 大規模シミュレーション（世帯数 > 500）は高コスト
4. **実世界との乖離**: キャリブレーションされていない学術的シミュレーション
5. **可視化未実装**: Phase 4待機中

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
