# SimCity 実装計画

## 📋 プロジェクト概要

**目標**: 論文「SIMCITY: MULTI-AGENT URBAN DEVELOPMENT SIMULATION WITH RICH INTERACTIONS」のLLMベース経済シミュレーションを実装

**技術選択**:
- **LLM**: OpenAI `gpt-4o-mini`（最安価: $0.15/1M input tokens, $0.60/1M output tokens）
- **UI**: Streamlit
- **言語**: Python 3.10+

**コスト見積もり**（gpt-4o-miniベース）:
- 論文の約1/10のコスト
- 約$18-20/180ステップ（論文は$180）
- 開発・テスト段階: 月$50-100程度

---

## 🎯 Phase 0: プロジェクトセットアップ（1-2日）

### 0.1 環境構築
- [ ] Gitリポジトリ初期化
- [ ] Python仮想環境作成
- [ ] 依存ライブラリインストール
- [ ] `.env`ファイル作成（OpenAI API Key）
- [ ] 基本ディレクトリ構造作成

### 0.2 設定ファイル整備
- [ ] `requirements.txt`作成
- [ ] `config/simulation_config.yaml`作成
- [ ] `config/llm_config.yaml`作成
- [ ] `.gitignore`設定

### 0.3 開発環境整備
- [ ] ロギング設定
- [ ] テストフレームワーク設定（pytest）
- [ ] コードフォーマッター設定（black, isort）

**成果物**:
```
SimCity/
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── CLAUDE.md
├── IMPLEMENTATION_PLAN.md
├── config/
│   ├── simulation_config.yaml
│   └── llm_config.yaml
├── src/
│   └── __init__.py
└── tests/
    └── __init__.py
```

---

## 🏗️ Phase 1: コア基盤実装（3-5日）

### 1.1 LLM統合モジュール
**優先度: 最高**

**ファイル**: `src/llm/llm_interface.py`
```python
class LLMInterface:
    def __init__(self, model="gpt-4o-mini", temperature=0.7):
        """OpenAI API クライアント初期化"""

    def function_call(self, system_prompt: str, user_prompt: str,
                     functions: list[dict]) -> dict:
        """Function Calling実行"""

    def validate_response(self, response: dict, expected_actions: list[str]) -> bool:
        """レスポンス検証（異常動作チェック）"""
```

**タスク**:
- [ ] OpenAI API統合
- [ ] Function Calling実装
- [ ] レスポンス検証機構
- [ ] エラーハンドリング
- [ ] リトライロジック
- [ ] コスト追跡機能

**テスト**:
- [ ] API接続テスト
- [ ] Function Calling正常系テスト
- [ ] 異常動作検出テスト

### 1.2 プロンプトテンプレート
**ファイル**: `src/llm/prompts.py`

**タスク**:
- [ ] 世帯エージェント用プロンプト
- [ ] 企業エージェント用プロンプト
- [ ] 政府エージェント用プロンプト
- [ ] 中央銀行エージェント用プロンプト
- [ ] プロンプトテンプレートエンジン

### 1.3 基本データモデル
**ファイル**: `src/models/data_models.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class HouseholdProfile:
    id: int
    age: int
    education_level: str
    skills: Dict[str, float]  # スキル名: レベル
    cash: float
    consumption_preferences: Dict[str, float]

@dataclass
class FirmProfile:
    id: int
    name: str
    goods_type: str
    cash: float
    capital: float
    employees: List[int]  # household IDs
    production_recipe: Dict[str, float]
```

**タスク**:
- [ ] 全データモデル定義
- [ ] シリアライズ/デシリアライズ
- [ ] バリデーション

### 1.4 経済モデル実装
**ファイル**: `src/models/economic_models.py`

**タスク**:
- [ ] Cobb-Douglas生産関数
- [ ] 累進課税計算
- [ ] Taylor rule（金利決定）
- [ ] マクロ経済指標計算（GDP, インフレ, Gini係数）

**テスト**:
- [ ] 各モデルの単体テスト
- [ ] 数値精度検証

### 1.5 シミュレーションエンジン骨格
**ファイル**: `src/environment/simulation.py`

```python
class Simulation:
    def __init__(self, config: dict):
        """シミュレーション初期化"""
        self.step_count = 0
        self.phase = "move_in"  # or "development"

    def step(self):
        """1ステップ実行（1ヶ月）"""
        # 1. Production and Trading Stage
        # 2. Taxation and Dividend Stage
        # 3. Metabolic Stage
        # 4. Revision Stage (LLM呼び出し)

    def save_state(self, filepath: str):
        """状態保存"""

    def load_state(self, filepath: str):
        """状態読み込み"""
```

**タスク**:
- [ ] ステップ実行ループ
- [ ] フェーズ管理
- [ ] 状態保存/読み込み
- [ ] イベントログ記録

**成果物**: LLMを使った簡単なエージェント行動のプロトタイプ

---

## 👥 Phase 2: エージェント実装（5-7日）

### 2.1 世帯エージェント
**ファイル**: `src/agents/household.py`

**優先度: 最高**（最も複雑）

```python
class HouseholdAgent(BaseAgent):
    def __init__(self, profile: HouseholdProfile):
        """初期化"""

    def decide_actions(self, observation: dict) -> dict:
        """4つの意思決定を実行"""
        # 1. 消費バンドル
        # 2. 労働市場行動
        # 3. 住居選択
        # 4. 金融意思決定

    def update_memory(self, report: dict):
        """記憶更新"""
```

**タスク**:
- [ ] プロファイル生成（Lognormal分布）
- [ ] スキルシステム（58種類）
- [ ] 4つの意思決定モジュール
- [ ] メモリ管理
- [ ] Function定義（find_job, modify_needs等）

**テスト**:
- [ ] プロファイル生成分布検証
- [ ] 意思決定の妥当性テスト
- [ ] メモリ管理テスト

### 2.2 企業エージェント
**ファイル**: `src/agents/firm.py`

**タスク**:
- [ ] 44種類の企業テンプレート読み込み
- [ ] Cobb-Douglas生産関数統合
- [ ] 3つの意思決定モジュール
- [ ] 在庫管理
- [ ] 破産判定ロジック

**サブタスク - 企業テンプレート**:
- [ ] `src/data/firm_templates.json`作成
- [ ] OECD IOTable風のデータ準備
- [ ] テンプレート検証

### 2.3 政府エージェント
**ファイル**: `src/agents/government.py`

**タスク**:
- [ ] マクロ経済指標モニタリング
- [ ] 累進課税システム
- [ ] UBI配布ロジック
- [ ] 公共サービス建設判断

### 2.4 中央銀行エージェント
**ファイル**: `src/agents/central_bank.py`

**タスク**:
- [ ] Taylor rule実装
- [ ] 金利平滑化（ρ=0.8）
- [ ] 預金・貸出管理

### 2.5 投資プール
**ファイル**: `src/agents/investment_pool.py`

**タスク**:
- [ ] 資金プール管理
- [ ] VLM統合（企業配置決定）
- [ ] 新規企業設立ロジック
- [ ] 株式配分

**成果物**: 全エージェントが基本動作するプロトタイプ

---

## 🏪 Phase 3: 市場メカニズム実装（3-5日）

### 3.1 労働市場
**ファイル**: `src/environment/markets/labor_market.py`

```python
class LaborMarket:
    def match_workers_and_jobs(self, households: List[Household],
                               firms: List[Firm]) -> List[tuple]:
        """確率的マッチング（スキルベース）"""

    def calculate_matching_efficiency(self, worker_skills: dict,
                                     job_requirements: dict) -> float:
        """マッチング効率計算"""
```

**タスク**:
- [ ] 確率的マッチングアルゴリズム
- [ ] スキルベース効率計算
- [ ] 求人・求職リスト管理

**テスト**:
- [ ] マッチング確率検証
- [ ] スキル効率計算テスト

### 3.2 財市場
**ファイル**: `src/environment/markets/goods_market.py`

**タスク**:
- [ ] 44種類の異質財管理
- [ ] 価格メカニズム
- [ ] 需給マッチング
- [ ] 在庫追跡

### 3.3 金融市場
**ファイル**: `src/environment/markets/financial_market.py`

**タスク**:
- [ ] 預金・貸出システム
- [ ] 金利計算（政策金利 + マークアップ）
- [ ] 投資プール統合

**成果物**: 3つの市場が連動して動作

---

## 🗺️ Phase 4: 地理・可視化実装（3-4日）

### 4.1 地理システム
**ファイル**: `src/environment/geography.py`

```python
class CityMap:
    def __init__(self, width: int = 50, height: int = 50):
        """グリッドベースのマップ"""
        self.grid = np.zeros((width, height))

    def place_building(self, building_type: str, x: int, y: int) -> bool:
        """建物配置"""

    def find_empty_location(self, building_type: str) -> tuple[int, int]:
        """空き地検索"""
```

**タスク**:
- [ ] グリッドベースマップ
- [ ] 建物配置ロジック
- [ ] 距離計算（通勤距離等）
- [ ] VLM統合（配置決定）

### 4.2 マップ可視化
**ファイル**: `src/visualization/map_generator.py`

**タスク**:
- [ ] マップ画像生成
- [ ] 建物アイコン描画
- [ ] リアルタイム更新

### 4.3 Streamlitダッシュボード
**ファイル**: `src/visualization/dashboard.py`

**優先度: 高**

**タスク**:
- [ ] メインダッシュボードUI
- [ ] 4つのタブ実装
  - [ ] マクロトレンド
  - [ ] 市場データ
  - [ ] 都市マップ
  - [ ] 経済現象検証
- [ ] シミュレーション制御UI
- [ ] リアルタイムグラフ更新

### 4.4 グラフ生成
**ファイル**: `src/visualization/plots.py`

**タスク**:
- [ ] Phillips Curve
- [ ] Okun's Law
- [ ] Beveridge Curve
- [ ] Price Elasticity
- [ ] Engel's Law
- [ ] その他時系列グラフ

**成果物**: Streamlitで動作する完全なダッシュボード

---

## 📊 Phase 5: データ準備・初期化（2-3日）

### 5.1 スキルデータ
**ファイル**: `src/data/skill_types.py`

**タスク**:
- [ ] 58種類のスキル定義
- [ ] スキルカテゴリ分類

### 5.2 財データ
**ファイル**: `src/data/goods_types.py`

**タスク**:
- [ ] 44種類の財定義
- [ ] 必需品/奢侈品分類
- [ ] 初期価格設定

### 5.3 企業テンプレート
**ファイル**: `src/data/firm_templates.json`

**タスク**:
- [ ] 44種類の企業テンプレート作成
- [ ] 生産レシピ定義
- [ ] 職種・スキル要件定義

**オプション**: LLMで生成（論文Listing 1-2参照）

### 5.4 世帯プロファイル生成
**ファイル**: `src/data/profile_generator.py`

**タスク**:
- [ ] Lognormal分布実装
- [ ] 年齢分布実装
- [ ] スキルランダム割り当て
- [ ] 200世帯の初期データ生成

**成果物**: シミュレーション実行可能な全データセット

---

## 🧪 Phase 6: 統合テスト・検証（3-5日）

### 6.1 単体テスト補完
**ディレクトリ**: `tests/`

**タスク**:
- [ ] 全モジュールのカバレッジ80%以上
- [ ] エッジケーステスト
- [ ] パフォーマンステスト

### 6.2 統合テスト
**ファイル**: `tests/test_integration.py`

**タスク**:
- [ ] エージェント間相互作用テスト
- [ ] 市場メカニズム統合テスト
- [ ] 1年間（12ステップ）実行テスト
- [ ] 状態保存/復元テスト

### 6.3 経済現象検証
**ファイル**: `experiments/validation.py`

**タスク**:
- [ ] Phillips Curve検証
- [ ] Okun's Law検証
- [ ] Beveridge Curve検証
- [ ] Price Elasticity検証
- [ ] Engel's Law検証
- [ ] Investment Volatility検証
- [ ] Price Stickiness検証

**成果物**: 7つの経済現象が再現されることを確認

### 6.4 ロバストネステスト
**ファイル**: `experiments/robustness_test.py`

**タスク**:
- [ ] 3つの異なる乱数シードで実行
- [ ] 結果の定性的一致確認
- [ ] 統計的有意性検証

**成果物**: 論文Table 2相当の検証レポート

---

## 🚀 Phase 7: 実験・最適化（3-5日）

### 7.1 ベースライン実行
**ファイル**: `experiments/baseline_run.py`

**タスク**:
- [ ] 180ステップ（15年）実行
- [ ] 全指標記録
- [ ] 可視化生成

### 7.2 外生ショック実験
**ファイル**: `experiments/shock_experiments.py`

**タスク**:
- [ ] 価格ショック実験（±50%）
- [ ] 政策ショック実験（金利変更等）
- [ ] 人口ショック実験

### 7.3 パフォーマンス最適化

**タスク**:
- [ ] LLM呼び出し回数削減
- [ ] キャッシング戦略
- [ ] バッチ処理最適化
- [ ] メモリ使用量削減

### 7.4 ドキュメント整備

**タスク**:
- [ ] README更新
- [ ] API ドキュメント生成
- [ ] 実験結果まとめ
- [ ] 使い方ガイド作成

**成果物**: 完全動作する SimCity + ドキュメント

---

## 📦 Phase 8: 配布準備（1-2日）

### 8.1 パッケージング
**タスク**:
- [ ] `setup.py`作成
- [ ] `pyproject.toml`作成
- [ ] Docker化（オプション）

### 8.2 CI/CD設定
**タスク**:
- [ ] GitHub Actions設定
- [ ] 自動テスト実行
- [ ] コードカバレッジレポート

### 8.3 デモ環境
**タスク**:
- [ ] Streamlit Cloud デプロイ（オプション）
- [ ] デモ動画作成
- [ ] スクリーンショット準備

**成果物**: 公開可能なリポジトリ

---

## 🗓️ 全体スケジュール

### 最短パス（集中開発）: 20-25日
```
Phase 0: 1-2日   [セットアップ]
Phase 1: 3-5日   [コア基盤] ★最重要
Phase 2: 5-7日   [エージェント] ★最重要
Phase 3: 3-5日   [市場]
Phase 4: 3-4日   [可視化]
Phase 5: 2-3日   [データ準備]
Phase 6: 3-5日   [テスト・検証]
Phase 7: 3-5日   [実験]
Phase 8: 1-2日   [配布]
```

### 推奨パス（段階的開発）: 30-40日
- 各フェーズ間に1-2日のバッファ
- 週末はレビュー・リファクタリング
- 継続的なテスト・ドキュメント更新

### マイルストーン
- **M1 (7日目)**: LLM統合完了、簡単なエージェント動作
- **M2 (15日目)**: 全エージェント実装完了、基本的な市場動作
- **M3 (23日目)**: 統合完了、Streamlitで可視化
- **M4 (30日目)**: 経済現象検証完了、実験実行可能
- **M5 (35日目)**: 最終リリース

---

## 💰 コスト見積もり

### OpenAI API コスト（gpt-4o-mini）
```
料金:
- Input: $0.15/1M tokens
- Output: $0.60/1M tokens

見積もり（論文ベース）:
- 論文: 800K tokens/step（gpt-4ベース）
- gpt-4o-mini: 同等と仮定

1ステップあたり:
- Input: ~400K tokens × $0.15 = $0.06
- Output: ~100K tokens × $0.60 = $0.06
- 合計: ~$0.12/step

180ステップ: $0.12 × 180 = $21.6

実際は最適化で削減可能:
- プロンプト短縮化: -30%
- キャッシング: -20%
- 推定: $15-18/180ステップ
```

### 開発期間のコスト
```
開発・テスト（30日間）:
- 1日平均: 20ステップ × $0.12 = $2.4
- 月間: ~$50-70
```

### 総コスト見積もり
```
開発期間（1ヶ月）: $50-70
運用（180ステップ/回）: $15-18
年間（月1回実行）: $180-216

→ 論文（$180/回）の約1/10のコスト！
```

---

## 🛠️ 開発環境

### 必須
```bash
Python 3.10+
OpenAI API Key
Git
```

### 推奨
```bash
VS Code + Python extension
Black (フォーマッター)
Pytest (テスト)
```

---

## 📚 リファレンス

### 主要ドキュメント
- `CLAUDE.md` - アーキテクチャ詳細
- `2510.01297v1.md` - 論文全文
- `config/simulation_config.yaml` - シミュレーション設定
- `config/llm_config.yaml` - LLM設定

### 外部リソース
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Streamlit Docs: https://docs.streamlit.io/
- OECD IOTables: https://www.oecd.org/en/data/datasets/input-output-tables.html

---

## ✅ 次のアクション

### 今すぐ始める
1. Phase 0のタスクを実行
2. `requirements.txt`作成
3. OpenAI API Key取得・設定
4. 基本ディレクトリ構造作成

### この計画の使い方
- 各Phaseを順番に実行
- 各タスクにチェックマークを付けて進捗管理
- 問題が発生したらCLAUDE.mdを参照
- 必要に応じて計画を調整

**重要**: 完璧を目指さず、動くプロトタイプを早く作ることを優先してください。リファクタリングは後で行えます。