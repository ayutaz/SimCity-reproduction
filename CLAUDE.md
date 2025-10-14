# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは、論文「SIMCITY: MULTI-AGENT URBAN DEVELOPMENT SIMULATION WITH RICH INTERACTIONS」の実装を目指すプロジェクトです。LLMを活用したマルチエージェント経済シミュレーションフレームワークで、世帯、企業、中央銀行、政府の4つの主要エージェントが相互作用し、マクロ経済現象を再現します。

## 現在の実装状況（2025-10-14）

### 完了済みフェーズ

**Phase 0: プロジェクトセットアップ（完了）**
- uv + ruff環境構築完了
- 設定ファイル整備（simulation_config.yaml, llm_config.yaml）
- Apache 2.0ライセンス設定
- ドキュメント作成（README.md, CLAUDE.md, TASKS.md）

**Phase 1: コア基盤実装（完了）**
- LLM統合（`src/llm/llm_interface.py` 263行）
  - OpenAI API統合
  - Function Calling実装
  - コスト追跡
  - リトライ機構
- プロンプトテンプレート（`src/llm/prompts/` 4ファイル）
- データモデル（`src/models/data_models.py` 361行）
- 経済モデル（`src/models/economic_models.py` 471行）
  - Cobb-Douglas生産関数
  - TaxationSystem
  - TaylorRule
  - MacroeconomicIndicators
- シミュレーションエンジン骨格（`src/environment/simulation.py` 355行）
- BaseAgent（`src/agents/base_agent.py` 283行）
- ユーティリティ（`src/utils/` 399行）

**Phase 2: エージェント実装（完了）**
- HouseholdAgent（`src/agents/household.py` 501行）
  - Lognormal分布プロファイル生成
  - 5つの意思決定関数
  - 58スキル対応
- FirmAgent（`src/agents/firm.py` 395行）
  - 44企業テンプレート対応
  - Cobb-Douglas生産関数統合
  - 破産判定ロジック
- GovernmentAgent（`src/agents/government.py` 301行）
  - 累進課税システム
  - UBI配布
  - 失業給付
- CentralBankAgent（`src/agents/central_bank.py` 287行）
  - Taylor rule実装
  - 金利平滑化（ρ=0.8）
- テスト: 41/41成功

**Phase 3: 市場メカニズム実装（完了）**
- LaborMarket（`src/environment/markets/labor_market.py` 297行）
  - 確率的マッチングアルゴリズム
  - スキルベース効率計算
  - 距離考慮オプション
- GoodsMarket（`src/environment/markets/goods_market.py` 261行）
  - 44財の取引メカニズム
  - 価格ベースマッチング
  - 需給ミスマッチ追跡
- FinancialMarket（`src/environment/markets/financial_market.py` 179行）
  - 預金・貸出システム
  - 政策金利+スプレッド方式
  - 預貸率追跡
- テスト: 17/17成功

**Phase 4: 地理・可視化実装（完了）**
- 地理システム（`src/environment/geography.py` 332行）
  - 100×100グリッドベース都市マップ
  - 建物管理（追加、削除、検索）
  - 距離計算（ユークリッド、マンハッタン）
- マップ可視化（`src/visualization/map_generator.py` 348行）
  - 建物タイプマップ
  - 占有率ヒートマップ
  - 密度マップ
  - 複合ビュー
- 経済グラフ（`src/visualization/plots.py` 561行）
  - フィリップス曲線
  - オークンの法則
  - ベバリッジ曲線
  - エンゲルの法則
  - 価格弾力性分析
  - 分布ヒストグラム
- Streamlitダッシュボード（`src/visualization/dashboard.py` 573行）
  - インタラクティブWeb UI
  - 4つのタブ（Overview, City Map, Economic Indicators, Analysis）
  - リアルタイム可視化
- テスト: 58/58成功

**Phase 5: データ準備（部分完了 6/8）**
- スキルデータ（`src/data/skill_types.py` 525行）
  - 58種類のスキル定義
  - 10カテゴリ
  - 賃金乗数計算
- 財データ（`src/data/goods_types.py` 528行）
  - 44種類の財定義
  - 10カテゴリ
  - 必需品22、奢侈品22
- 企業テンプレート（`src/data/firm_templates.json` 598行）
  - 44企業テンプレート
- 世帯プロファイルジェネレータ（`src/agents/household.py`）
  - Lognormal所得分布
  - スキル・年齢・教育レベル生成
- 初期データ生成スクリプト（`scripts/generate_initial_households.py`）
  - 200世帯データセット生成
- テスト: 14/14成功

**Phase 6: 統合テスト・検証（部分完了 4/15）**
- **Phase 6.2 統合テスト**: ✅ 完了（`tests/test_integration.py` 585行）
  - 市場メカニズム統合テスト（5テスト）
  - シミュレーション実行テスト（5テスト）
  - 状態保存/復元テスト（4テスト）
  - 地理システム統合テスト（2テスト）
  - テスト結果: 15/15成功 ✅

### テスト結果

```
全165テスト実行: 165/165成功 (100%)
- test_economic_models.py: 18テスト
- test_financial_market.py: 5テスト
- test_geography.py: 20テスト
- test_goods_market.py: 4テスト
- test_household_agent.py: 14テスト
- test_labor_market.py: 8テスト
- test_llm_integration.py: 2テスト
- test_map_generator.py: 14テスト
- test_phase2_agents.py: 27テスト
- test_plots.py: 20テスト
- test_dashboard.py: 4テスト
- test_phase5_data.py: 14テスト (Phase 5データ生成)
- test_integration.py: 15テスト (Phase 6.2統合テスト)

コード品質: ruff All checks passed
```

### 未実装フェーズ

**Phase 6: 統合テスト・検証（部分完了: Phase 6.2完了、残り11タスク）**
- ✅ Phase 6.2: 統合テスト（完了）
- Phase 6.1: Unit Test補完（3タスク）
- Phase 6.3: 経済現象検証（7つの曲線、7タスク）
- Phase 6.4: ロバストネステスト（3タスク）
- Phase 6.5: 外生ショック実験（1タスク）

**Phase 7: 実験・最適化**
- パフォーマンス最適化
- コスト削減

**Phase 8: 配布準備**
- ドキュメント整備
- CI/CD設定

## アーキテクチャの理解

### 1. 三層構造

システムは以下の3つのコアレイヤーで構成されます：

1. **Environment（環境層）**
   - シミュレーションステップ：1ステップ = 1ヶ月
   - 2つのフェーズ：Move-in phase（人口増加）、Development phase（定常状態）
   - 3つの市場：財市場、労働市場、金融市場

2. **Interaction Protocol（相互作用プロトコル層）**
   - Function Calling方式でLLMとやり取り
   - エージェントはJSON形式でアクションとパラメータを返す
   - フレームワークが検証後に実行

3. **Agents（エージェント層）**
   - 4つのエージェントタイプ（詳細は後述）

### 2. エージェントの設計

#### 2.1 Household（世帯エージェント）
- **数量**: 200世帯（異質なプロファイル）
- **実装ファイル**: `src/agents/household.py`
- **属性**:
  - 年齢、教育レベル、消費嗜好、スキル保有
  - 現金保有量、労働参加状況、住居
- **意思決定**:
  1. 消費バンドル（必需品への最低支出）
  2. 労働市場行動（求職、辞職、応募）
  3. 住居選択
  4. 金融意思決定（貯蓄、借入、投資）

#### 2.2 Firm（企業エージェント）
- **数量**: 複数（44種類の財テンプレートから動的生成）
- **実装ファイル**: `src/agents/firm.py`
- **生産関数**: Cobb-Douglas型
  - `Y_i = A * L_i^(1-α) * K_i^α`
  - 実装: `src/models/economic_models.py:15-84`
- **意思決定**:
  1. 生産量と価格設定
  2. 労働市場行動（採用、解雇、賃金調整）
  3. 投資判断（借入、資本購入）

#### 2.3 Government（政府エージェント）
- **実装ファイル**: `src/agents/government.py`
- **役割**:
  - マクロ経済指標のモニタリング（GDP、インフレ率、失業率、ジニ係数）
  - 税収管理（累進課税、VAT）
  - 福祉政策（UBI配布、公共サービス建設）
- **税制**:
  - 所得税（世帯）：累進課税
  - 実装: `src/models/economic_models.py:87-145`

#### 2.4 Central Bank（中央銀行エージェント）
- **実装ファイル**: `src/agents/central_bank.py`
- **役割**: 金融政策の実行
- **金利設定**: 修正Taylor rule
  - `r̂ = max{r^n + π^t + α(π - π^t) + β(Y - Y^n), 0}`
  - 実装: `src/models/economic_models.py:149-218`
- **金利平滑化**:
  - `r_t = ρ * r_{t-1} + (1-ρ) * r̂_t`（ρ = 0.8）

### 3. 市場メカニズム

#### 3.1 労働市場（LaborMarket）
- **実装ファイル**: `src/environment/markets/labor_market.py`
- **マッチングアルゴリズム**: 確率的スキルベースマッチング
- **スコアリング**: 70% スキル適合度 + 30% 賃金適合度
- **確率**: 0.7（設定可能）
- **テスト**: `tests/test_labor_market.py` 8テスト

#### 3.2 財市場（GoodsMarket）
- **実装ファイル**: `src/environment/markets/goods_market.py`
- **財の種類**: 44種類（10カテゴリ）
- **マッチングアルゴリズム**: 価格ベース
- **機能**: 需給ミスマッチ追跡、在庫管理
- **テスト**: `tests/test_goods_market.py` 4テスト

#### 3.3 金融市場（FinancialMarket）
- **実装ファイル**: `src/environment/markets/financial_market.py`
- **金利構造**:
  - 預金金利 = 政策金利 + deposit_spread (-0.01)
  - 貸出金利 = 政策金利 + loan_spread (+0.02)
- **機能**: 預金・貸出処理、預貸率追跡
- **テスト**: `tests/test_financial_market.py` 5テスト

### 4. 実装済みディレクトリ構造

```
SimCity/
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # 基底エージェントクラス (283行)
│   │   ├── household.py           # 世帯エージェント (501行)
│   │   ├── firm.py                # 企業エージェント (395行)
│   │   ├── government.py          # 政府エージェント (301行)
│   │   └── central_bank.py        # 中央銀行エージェント (287行)
│   ├── environment/
│   │   ├── simulation.py          # シミュレーション実行エンジン (355行)
│   │   └── markets/
│   │       ├── labor_market.py    # 労働市場 (297行)
│   │       ├── goods_market.py    # 財市場 (261行)
│   │       └── financial_market.py # 金融市場 (179行)
│   ├── llm/
│   │   ├── llm_interface.py       # LLM API インターフェース (263行)
│   │   └── prompts/
│   │       ├── household_system.txt
│   │       ├── firm_system.txt
│   │       ├── government_system.txt
│   │       └── central_bank_system.txt
│   ├── models/
│   │   ├── data_models.py         # データモデル (361行)
│   │   └── economic_models.py     # 経済モデル (471行)
│   ├── data/
│   │   ├── skill_types.py         # 58スキル定義 (525行)
│   │   ├── goods_types.py         # 44財定義 (528行)
│   │   └── firm_templates.json    # 44企業テンプレート (598行)
│   ├── utils/
│   │   ├── config.py              # 設定管理 (285行)
│   │   └── logger.py              # ログ管理 (114行)
│   └── visualization/             # Phase 4完了
│       ├── geography.py           # 地理システム (332行)
│       ├── map_generator.py       # マップ可視化 (348行)
│       ├── plots.py               # 経済グラフ (561行)
│       └── dashboard.py           # Streamlitダッシュボード (573行)
├── scripts/                       # Phase 5スクリプト
│   └── generate_initial_households.py  # 初期世帯データ生成 (154行)
├── tests/                         # 165テスト、100%成功
│   ├── test_dashboard.py          # 4テスト
│   ├── test_economic_models.py    # 18テスト
│   ├── test_financial_market.py   # 5テスト
│   ├── test_geography.py          # 20テスト
│   ├── test_goods_market.py       # 4テスト
│   ├── test_household_agent.py    # 14テスト
│   ├── test_labor_market.py       # 8テスト
│   ├── test_llm_integration.py    # 2テスト
│   ├── test_map_generator.py      # 14テスト
│   ├── test_phase2_agents.py      # 27テスト
│   ├── test_plots.py              # 20テスト
│   ├── test_phase5_data.py        # 14テスト (Phase 5)
│   └── test_integration.py        # 15テスト (Phase 6.2)
├── config/
│   ├── simulation_config.yaml     # シミュレーション設定
│   └── llm_config.yaml            # LLM設定
├── experiments/                   # 未実装
├── pyproject.toml                 # uv管理
├── .env.example
├── .gitignore
├── LICENSE                        # Apache 2.0
├── README.md
├── CLAUDE.md                      # 本ファイル
└── TASKS.md                       # 進捗管理（108/134完了、81%）
```

## 主要技術スタック

### 必須ライブラリ（実装済み）
- **LLM統合**: `openai` (1.59.7)
- **数値計算**: `numpy` (2.2.1), `scipy` (1.15.1)
- **データ処理**: `pandas` (2.2.3)
- **設定管理**: `pyyaml` (6.0.2), `python-dotenv` (1.0.1), `pydantic` (2.10.5)
- **ロギング**: `loguru` (0.7.3)
- **コード品質**: `ruff` (0.9.1)
- **テスト**: `pytest` (8.4.2), `pytest-cov` (7.0.0)
- **可視化**: `streamlit`, `matplotlib`

### 未実装ライブラリ
- **分析**: `statsmodels`（経済指標の相関分析）

## 重要な実装の詳細

### LLM統合（src/llm/llm_interface.py）

```python
class LLMInterface:
    """
    OpenAI APIとのインターフェース

    機能:
    - Function Calling実装
    - コスト追跡
    - リトライ機構（max_retries=3）
    - タイムアウト設定（30秒）
    """

    def call_with_functions(
        self,
        messages: list[dict],
        functions: list[dict],
        function_call: str | dict = "auto"
    ) -> dict:
        """Function Callingを使用したLLM呼び出し"""
```

### プロンプト構造

各エージェントは以下の情報を受け取る：

```
System Prompt:
- エージェントの役割と目標
- 応答フォーマット（JSON）

User Prompt:
### Profile
- 個別属性情報

### Report
- 過去の行動履歴

### Observation
- 環境の状態（市場価格、失業率等）

### Actions
- 実行可能なアクション一覧
```

### データ初期化

#### 世帯プロファイル生成（src/agents/household.py:343-398）
- **所得分布**: Lognormal分布
  - `ln(m_i,0) ~ N(μ=10.5, σ=0.5)`（デフォルト設定）
  - 論文版: μ=11.1496, σ²=1.1455（2023 ACS IPUMS microdataからMLE推定）
- **年齢分布**: 正規分布（μ=40, σ=12）
- **スキル**: 58種類からランダム割り当て

#### 企業テンプレート（src/data/firm_templates.json）
- **データソース**: OECD Input-Output Tables（論文記載）
- **テンプレート数**: 44種類
- **内容**: 初期資本、TFP、賃金、スキル要件

## 開発ガイドライン

### テストの実行

```bash
# 全テストの実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=src --cov-report=html

# 特定のテストファイル
uv run pytest tests/test_labor_market.py -v
```

### コード品質チェック

```bash
# ruff チェック
uv run ruff check src/ tests/

# 自動修正
uv run ruff check --fix src/ tests/

# フォーマット適用
uv run ruff format src/ tests/
```

### 新しいエージェントの追加

```python
from src.agents.base_agent import BaseAgent
from src.llm.llm_interface import LLMInterface

class CustomAgent(BaseAgent):
    """カスタムエージェント"""

    def __init__(self, llm_interface: LLMInterface, ...):
        super().__init__(
            agent_id="custom_agent",
            agent_type="custom",
            llm_interface=llm_interface,
        )

    def decide_action(self, observation: dict) -> dict:
        """意思決定メソッド"""
        # プロンプト生成
        messages = self._build_prompt(observation)

        # Function定義
        functions = [...]

        # LLM呼び出し
        response = self.llm_interface.call_with_functions(
            messages=messages,
            functions=functions
        )

        return response
```

### 新しい市場の追加

```python
from dataclasses import dataclass
from loguru import logger

@dataclass
class MarketRequest:
    """市場への要求"""
    agent_id: int
    ...

class CustomMarket:
    """カスタム市場"""

    def __init__(self):
        self.total_transactions = 0
        logger.info("CustomMarket initialized")

    def match(self, requests: list[MarketRequest]) -> list:
        """マッチング処理"""
        transactions = []
        # マッチングロジック
        return transactions

    def get_statistics(self) -> dict:
        """統計情報取得"""
        return {
            "total_transactions": self.total_transactions,
            ...
        }
```

## 検証方法

### マクロ経済現象のチェックリスト（Phase 6実装予定）
1. **Phillips Curve**: 失業率とインフレ率の負の相関
2. **Okun's Law**: 失業率変化とGDP成長率の負の相関
3. **Beveridge Curve**: 求人率と失業率の負の相関
4. **Price Elasticity**: 需要の価格弾力性（必需品: -1<E<0、奢侈品: E<-1）
5. **Engel's Law**: 所得上昇に伴う食費割合の減少
6. **Investment Volatility**: 投資 > 消費のボラティリティ
7. **Price Stickiness**: 価格調整の遅延

### ロバストネス検証
- 異なる乱数シードで3回実行
- 定性的パターンの再現性を確認

### 外生ショック実験
- 44財のうち7財をランダム選択
- ±50%の価格ショック
- 6年間（72ステップ）の追跡

## パラメータ設定（論文より）

### シミュレーション設定
- 世帯数: 200
- Phase 1: 36ステップ（3年）
- Phase 2: 144ステップ（12年、48四半期）
- LLM: `gpt-4o-mini`（通常推論）、`gpt-4`（VLM）
- サンプリング: デフォルトパラメータ

### 経済パラメータ
- 生産関数: α（資本シェア）は企業ごとに設定
- Taylor rule: α（インフレ応答）、β（産出ギャップ応答）
- 金利平滑化: ρ = 0.8
- 初期価格: 全財50（具体値は影響小）

## コスト見積もり

論文Appendix Bより：
- 約800,000トークン/ステップ
- gpt-4: 約$0.25/ステップ → 180ステップで約$180
- gpt-4o-mini: 約$0.12/ステップ → 180ステップで約$21.6
- 最適化後: $15-18/180ステップ

## 重要な設計上の注意点

1. **エージェント数の制約**
   - 世帯200は計算コストとのバランス
   - 並列処理は無効化可能（論文記載）

2. **情報アクセス制約**
   - エージェントは前ステップの情報のみアクセス可能
   - 同時意思決定を避ける

3. **VLMの役割**（Phase 4実装予定）
   - 企業配置決定
   - プロンプトなしで自然にクラスタ構造形成

4. **金融市場の簡略化**
   - 債券、株式、デリバティブは未実装
   - 数理最適化は使用せず

5. **メモリ管理**
   - 構造化メモリでコンテキスト保持
   - 長期記憶と短期記憶の分離

## 追加資料

- 論文全文: `2510.01297v1.pdf`
- 論文Markdown版: `2510.01297v1.md`
- プロンプト例: 論文Appendix E（Listing 3-17）
- タスク管理: `TASKS.md`（詳細な進捗追跡）

## 開発時の留意事項

1. **再現性**: 乱数シードの固定、LLMパラメータの記録
2. **ログ**: 各エージェントの意思決定理由をログ化（loguru使用）
3. **検証**: 各ステップでマクロ経済指標を計算・記録
4. **モジュール化**: エージェント、市場、環境を疎結合に
5. **設定ファイル**: ハードコード避け、YAMLで管理
6. **テスト駆動**: 新機能追加時は必ずテストを作成

## 次のステップ推奨

### オプション1: Phase 6 - 統合テスト・経済現象検証
- シミュレーション全体の統合テスト
- 7つの経済現象の検証
  - Phillips Curve（フィリップス曲線）
  - Okun's Law（オークンの法則）
  - Beveridge Curve（ベバリッジ曲線）
  - Price Elasticity（価格弾力性）
  - Engel's Law（エンゲルの法則）
  - Investment Volatility（投資のボラティリティ）
  - Price Stickiness（価格の粘着性）

### オプション2: Phase 5.4 - 世帯プロファイル生成完了
- 200世帯の初期データ生成
- 年齢・スキル分布の実装
- 初期資産配分

### オプション3: Phase 7 - 実験と最適化
- パフォーマンス最適化
- LLMコスト削減
- 並列処理の実装
