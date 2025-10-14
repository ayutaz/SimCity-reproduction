# SimCity タスク管理・実装計画

## 📋 プロジェクト概要

**目標**: 論文「SIMCITY: MULTI-AGENT URBAN DEVELOPMENT SIMULATION WITH RICH INTERACTIONS」のLLMベース経済シミュレーションを実装

**技術選択**:
- **LLM**: OpenAI `gpt-4o-mini`（最安価: $0.15/1M input tokens, $0.60/1M output tokens）
- **UI**: Streamlit
- **言語**: Python 3.12
- **パッケージ管理**: uv
- **コードフォーマット**: ruff
- **ライセンス**: Apache 2.0

**リポジトリ**: https://github.com/ayutaz/SimCity-reproduction.git

---

## 📊 進捗サマリー

| Phase | タスク数 | 工数 | 優先度 | 状態 |
|-------|---------|------|--------|------|
| **Phase 0** | 11 | 1-2日 | - | ✅ **完了** |
| **Phase 1** | 32 | 3-5日 | 最高 | ✅ **完了** |
| **Phase 2** | 23 | 5-7日 | 最高 | ✅ **完了** |
| **Phase 3** | 10 | 3-5日 | 高 | ✅ **完了** |
| **Phase 4** | 15 | 3-4日 | 高 | 待機 |
| **Phase 5** | 8 | 2-3日 | 中 | ⏳ **部分完了 (6/8)** |
| **Phase 6** | 15 | 3-5日 | 高 | 待機 |
| **Phase 7** | 11 | 3-5日 | 中 | 待機 |
| **Phase 8** | 9 | 1-2日 | 低 | 待機 |
| **合計** | **134** | **22-38日** | - | **81/134 完了 (60%)** |

**現在の状態**:
- ✅ Phase 0 完了（プロジェクトセットアップ）
- ✅ Phase 1 完了（LLM統合、データモデル、経済モデル、シミュレーションエンジン基盤）
- ✅ Phase 2 完了（全エージェント実装）
- ✅ Phase 3 完了（市場メカニズム実装）
- ⏳ Phase 5 部分完了（スキル・財・企業データ定義完了）

---

## ✅ Phase 0: プロジェクトセットアップ（完了）

### 実装済み成果物
```
SimCity/
├── .env.example
├── .gitignore
├── LICENSE (Apache 2.0, Copyright 2025 ayutaz)
├── pyproject.toml (uv + ruff設定)
├── README.md
├── CLAUDE.md
├── TASKS.md (本ファイル)
├── config/
│   ├── simulation_config.yaml
│   └── llm_config.yaml
├── src/
│   ├── __init__.py
│   ├── llm/
│   ├── models/
│   ├── agents/
│   ├── environment/
│   ├── utils/
│   └── visualization/
└── tests/
    └── (20テスト、56%カバレッジ)
```

---

## ✅ Phase 1: コア基盤実装（完了）

### 実装済みコンポーネント

#### 1.1 LLM統合モジュール ✅
- **ファイル**: `src/llm/llm_interface.py` (263行)
- **機能**: OpenAI API統合、Function Calling、コスト追跡、リトライ機構

#### 1.2 プロンプトテンプレート ✅
- **ファイル**: `src/llm/prompts/` (4ファイル、163行)
- **内容**: household_system.txt, firm_system.txt, government_system.txt, central_bank_system.txt

#### 1.3 データモデル ✅
- **ファイル**: `src/models/data_models.py` (361行)
- **内容**: HouseholdProfile, FirmProfile, GovernmentState, CentralBankState, MarketState, SimulationState

#### 1.4 経済モデル ✅
- **ファイル**: `src/models/economic_models.py` (471行)
- **内容**: ProductionFunction (Cobb-Douglas), TaxationSystem, TaylorRule, MacroeconomicIndicators

#### 1.5 シミュレーションエンジン骨格 ✅
- **ファイル**: `src/environment/simulation.py` (355行)
- **内容**: 4段階シミュレーションループ、状態管理、保存/読み込み

#### 1.6 BaseAgent ✅
- **ファイル**: `src/agents/base_agent.py` (283行)
- **内容**: エージェント基底クラス、メモリ管理、プロンプト生成

#### 1.7 ユーティリティ ✅
- **ファイル**: `src/utils/config.py` (285行) - Pydantic設定管理
- **ファイル**: `src/utils/logger.py` (114行) - Loguru統合

#### 1.8 テスト ✅
- **ファイル**: `tests/test_economic_models.py` (18テスト)
- **ファイル**: `tests/test_llm_integration.py` (2テスト)
- **カバレッジ**: 56%（コアモジュールは80%+）

---

## ✅ Phase 2: エージェント実装（完了）

### 概要
**目標**: 4種類のLLM駆動エージェントを完全実装し、シミュレーションを実行可能にする ✅

**依存関係**: Phase 1完了（✅）

**成果物**: 全エージェントが基本動作するプロトタイプ ✅

**実装成果**:
- `src/agents/household.py` (528行) - 5つの意思決定関数
- `src/agents/firm.py` (396行) - 3つの意思決定関数
- `src/agents/government.py` (307行) - 4つの政策決定関数
- `src/agents/central_bank.py` (288行) - 3つの金融政策関数
- `tests/test_household_agent.py` (14テスト成功)
- `tests/test_phase2_agents.py` (27テスト成功)
- **合計**: 41/41テスト成功 ✅

### 2.1 世帯エージェント（HouseholdAgent） ✅
**優先度**: 最高（最も複雑）
**ファイル**: `src/agents/household.py` (528行)
**工数**: 2-3日

#### タスク (8項目)
- [x] プロファイル生成器実装（Lognormal分布）
- [x] スキルシステム（58種類のスキル対応）
- [x] 意思決定1: 消費バンドル決定
- [x] 意思決定2: 労働市場行動（求職/受諾/辞職）
- [x] 意思決定3: 住居選択
- [x] 意思決定4: 金融意思決定（貯蓄/借入/投資）
- [x] メモリ管理（過去行動の記憶）
- [x] Function定義（find_job, modify_needs, purchase_goods等）

#### テスト (3項目)
- [x] プロファイル生成分布検証（Lognormalチェック）
- [x] 4つの意思決定の妥当性テスト
- [x] メモリ管理・履歴保存テスト

**実装済み機能**:
- HouseholdProfileGenerator（Lognormal分布）
- 5つのFunction Calling定義
- BaseAgentを継承した統一インターフェース

---

### 2.2 企業エージェント（FirmAgent） ✅
**優先度**: 高
**ファイル**: `src/agents/firm.py` (396行)
**工数**: 1-2日

#### タスク (7項目)
- [x] 44種類の企業テンプレート読み込み
- [x] Cobb-Douglas生産関数統合
- [x] 意思決定1: 生産量・価格決定
- [x] 意思決定2: 労働市場行動（雇用/解雇/賃金）
- [x] 意思決定3: 投資決定（借入/資本購入）
- [x] 在庫管理システム
- [x] 破産判定ロジック

#### サブタスク: 企業テンプレート (3項目)
- [x] `src/data/firm_templates.json`作成（44企業テンプレート）
- [x] OECD IOTable風のデータ準備
- [x] テンプレート検証（44企業×スキル要件）

**実装済み機能**:
- FirmTemplateLoader（JSON読み込み）
- 生産能力計算（Cobb-Douglas）
- 破産判定（3ヶ月連続マイナスで破産）

---

### 2.3 政府エージェント（GovernmentAgent） ✅
**優先度**: 中
**ファイル**: `src/agents/government.py` (307行)
**工数**: 0.5-1日

#### タスク (4項目)
- [x] マクロ経済指標モニタリング（GDP, インフレ, 失業率, Gini）
- [x] 累進課税システム実装（TaxationSystem統合）
- [x] UBI配布ロジック
- [x] 公共サービス建設判断

**実装済み機能**:
- 累進課税徴収（TaxationSystem統合）
- UBI配布（enabled/disabled切り替え）
- 失業給付計算（6ヶ月上限）
- 4つの政策決定関数

---

### 2.4 中央銀行エージェント（CentralBankAgent） ✅
**優先度**: 中
**ファイル**: `src/agents/central_bank.py` (288行)
**工数**: 0.5-1日

#### タスク (3項目)
- [x] Taylor rule実装（TaylorRuleクラス統合）
- [x] 金利平滑化（ρ=0.8）
- [x] 預金・貸出管理

**実装済み機能**:
- Taylor rule統合（インフレ・産出ギャップ反応）
- 金利平滑化（smoothing_factor=0.8）
- 金利構造管理（預金/政策/貸出金利）
- 3つの金融政策関数

---

### 2.5 投資プール（InvestmentPool）
**優先度**: 低（オプション）
**ファイル**: `src/agents/investment_pool.py`
**工数**: 1日
**ステータス**: ⏭️ **スキップ（Phase 6以降で必要に応じて実装）**

#### タスク (4項目)
- [ ] 資金プール管理（家計の投資を集約）
- [ ] VLM統合（企業配置決定）
- [ ] 新規企業設立ロジック
- [ ] 株式配分（配当計算）

**備考**: オプション機能のためPhase 3に進む

---

## ✅ Phase 3: 市場メカニズム実装（完了）

### 概要
**目標**: 3つの市場を実装し、エージェント間の取引を実現 ✅

**依存関係**: Phase 2完了 ✅

**成果物**: 3つの市場が連動して動作 ✅

**実装成果**:
- `src/environment/markets/labor_market.py` (297行) - 確率的マッチングアルゴリズム
- `src/environment/markets/goods_market.py` (262行) - 44財の取引メカニズム
- `src/environment/markets/financial_market.py` (172行) - 預金・貸出システム
- `tests/test_labor_market.py` (8テスト成功)
- `tests/test_goods_market.py` (4テスト成功)
- `tests/test_financial_market.py` (5テスト成功)
- **合計**: 17/17テスト成功 ✅

### 3.1 労働市場（LaborMarket） ✅
**ファイル**: `src/environment/markets/labor_market.py` (297行)
**工数**: 1-2日 → 完了

#### タスク (3項目)
- [x] 確率的マッチングアルゴリズム
- [x] スキルベース効率計算（calculate_effective_labor統合）
- [x] 求人・求職リスト管理

#### テスト (2項目)
- [x] マッチング確率検証
- [x] スキル効率計算テスト

**実装済み機能**:
- スキル・賃金ベーススコアリング（70/30重み付け）
- 距離考慮オプション
- 統計追跡（fill_rate, rejection_reasons）
- 8テスト成功 ✅

---

### 3.2 財市場（GoodsMarket） ✅
**ファイル**: `src/environment/markets/goods_market.py` (262行)
**工数**: 1-2日 → 完了

#### タスク (4項目)
- [x] 44種類の異質財管理
- [x] 価格メカニズム（需給調整）
- [x] 需給マッチング
- [x] 在庫追跡

**実装済み機能**:
- 価格ベースマッチングアルゴリズム
- 需給ミスマッチ追跡（unmet_demand, unsold_supply）
- 財IDごとのグループ化処理
- 4テスト成功 ✅

---

### 3.3 金融市場（FinancialMarket） ✅
**ファイル**: `src/environment/markets/financial_market.py` (172行)
**工数**: 1日 → 完了

#### タスク (3項目)
- [x] 預金・貸出システム
- [x] 金利計算（政策金利 + spread）
- [x] 統計追跡（loan_to_deposit_ratio）

**実装済み機能**:
- 預金金利 = 政策金利 + deposit_spread (-0.01)
- 貸出金利 = 政策金利 + loan_spread (+0.02)
- 預貸率追跡
- 5テスト成功 ✅

---

## 🗺️ Phase 4: 地理・可視化実装（3-4日）

### 概要
**目標**: Streamlitダッシュボードと都市マップの可視化

**依存関係**: Phase 2-3完了（基本機能のみならPhase 2のみでも可）

**成果物**: Streamlitで動作する完全なダッシュボード

### 4.1 地理システム（CityMap）
**ファイル**: `src/environment/geography.py`
**工数**: 1日

#### タスク (4項目)
- [ ] グリッドベースマップ（100×100）
- [ ] 建物配置ロジック
- [ ] 距離計算（通勤距離等）
- [ ] VLM統合（配置決定）※オプション

---

### 4.2 マップ可視化（MapGenerator）
**ファイル**: `src/visualization/map_generator.py`
**工数**: 0.5-1日

#### タスク (3項目)
- [ ] マップ画像生成
- [ ] 建物アイコン描画
- [ ] リアルタイム更新

---

### 4.3 Streamlitダッシュボード ★重要
**ファイル**: `src/visualization/dashboard.py`
**工数**: 1-2日

#### タスク (7項目)
- [ ] メインダッシュボードUI
- [ ] タブ1: マクロトレンド（GDP, インフレ, 失業率）
- [ ] タブ2: 市場データ（労働、財、金融）
- [ ] タブ3: 都市マップ
- [ ] タブ4: 経済現象検証（7つの曲線）
- [ ] シミュレーション制御UI（開始/停止/リセット）
- [ ] リアルタイムグラフ更新

**重要ポイント**:
- Streamlit + Plotly使用
- st.rerun()でリアルタイム更新
- サイドバーで制御パネル

---

### 4.4 グラフ生成（Plots）
**ファイル**: `src/visualization/plots.py`
**工数**: 0.5-1日

#### タスク (6項目)
- [ ] Phillips Curve（失業率 vs インフレ）
- [ ] Okun's Law（失業率変化 vs GDP成長率）
- [ ] Beveridge Curve（求人率 vs 失業率）
- [ ] Price Elasticity（価格 vs 需要量）
- [ ] Engel's Law（所得 vs 食料支出割合）
- [ ] その他時系列グラフ（GDP, 人口等）

---

## 📊 Phase 5: データ準備・初期化（部分完了 6/8）

### 概要
**目標**: シミュレーション実行に必要な全データを準備

**依存関係**: なし（Phase 2と並行可能）

**成果物**: 58スキル、44商品、44企業、200世帯のデータセット

**完了状況**: Phase 2と並行して5.1-5.3完了 ✅

### 5.1 スキルデータ ✅
**ファイル**: `src/data/skill_types.py` (410行)
**工数**: 0.5日

#### タスク (2項目)
- [x] 58種類のスキル定義
- [x] スキルカテゴリ分類

**実装済み**:
- 10カテゴリ × 58スキル
- 賃金乗数計算（多様性ボーナス付き）
- カテゴリ: Technology, Business, Creative, Healthcare, Education, Manufacturing, Service, Construction, Transport, Agriculture

---

### 5.2 財データ ✅
**ファイル**: `src/data/goods_types.py` (342行)
**工数**: 0.5日

#### タスク (3項目)
- [x] 44種類の財定義
- [x] 必需品/奢侈品分類
- [x] 初期価格設定

**実装済み**:
- 10カテゴリ × 44財
- 価格弾力性（需要関数）
- 必需品22財、奢侈品22財
- カテゴリ: Food, Clothing, Housing, Transportation, Healthcare, Education, Entertainment, Utilities, Furniture, Other

---

### 5.3 企業テンプレート ✅
**ファイル**: `src/data/firm_templates.json` (1,144行)
**工数**: 1日

#### タスク (3項目)
- [x] 44種類の企業テンプレート作成
- [x] 生産レシピ定義（投入・産出）
- [x] 職種・スキル要件定義

**実装済み**:
- 全44財に対応する企業テンプレート（JSON）
- 初期資本、TFP、賃金、スキル要件を定義
- FirmTemplateLoaderで読み込み可能
- Phase 2.2で使用済み

---

### 5.4 世帯プロファイル生成 ⏭️
**ファイル**: `src/agents/household.py` (HouseholdProfileGenerator実装済み)
**工数**: 0.5-1日
**ステータス**: Phase 2.1で基本機能実装済み、Phase 6で拡張予定

#### タスク (4項目)
- [x] Lognormal分布実装（所得分布） - Phase 2.1で実装済み
- [ ] 年齢分布実装
- [ ] スキルランダム割り当て
- [ ] 200世帯の初期データ生成

**備考**: 基本機能は実装済み、Phase 6で詳細化

---

## 🧪 Phase 6: 統合テスト・検証（3-5日）

### 概要
**目標**: 7つの経済現象を検証し、ロバスト性を確認

**依存関係**: Phase 2-5完了

**成果物**: 論文Table 2相当の検証レポート

### 6.1 単体テスト補完
**ディレクトリ**: `tests/`
**工数**: 1-2日

#### タスク (3項目)
- [ ] 全モジュールのカバレッジ80%以上
- [ ] エッジケーステスト
- [ ] パフォーマンステスト

---

### 6.2 統合テスト
**ファイル**: `tests/test_integration.py`
**工数**: 1日

#### タスク (4項目)
- [ ] エージェント間相互作用テスト
- [ ] 市場メカニズム統合テスト
- [ ] 1年間（12ステップ）実行テスト
- [ ] 状態保存/復元テスト

---

### 6.3 経済現象検証 ★最重要
**ファイル**: `experiments/validation.py`
**工数**: 1-2日

#### タスク (7項目)
- [ ] Phillips Curve検証（r < 0, 負の相関）
- [ ] Okun's Law検証（r < 0, 負の相関）
- [ ] Beveridge Curve検証（r < -0.5, 強い負の相関）
- [ ] Price Elasticity検証（必需品: -1<E<0, 贅沢品: E<-1）
- [ ] Engel's Law検証（所得上昇→食料割合減少）
- [ ] Investment Volatility検証（投資>消費のボラティリティ）
- [ ] Price Stickiness検証（価格調整の遅延）

**重要ポイント**:
- 180ステップ（15年）実行
- 統計的有意性の検証
- 論文Figure 4-7との比較

---

### 6.4 ロバストネステスト
**ファイル**: `experiments/robustness_test.py`
**工数**: 0.5-1日

#### タスク (3項目)
- [ ] 3つの異なる乱数シードで実行
- [ ] 結果の定性的一致確認
- [ ] 統計的有意性検証

---

## 🚀 Phase 7: 実験・最適化（3-5日）

### 概要
**目標**: 論文の実験を再現し、最適化

**依存関係**: Phase 6完了

**成果物**: 完全動作するSimCity + ドキュメント

### 7.1 ベースライン実行
**ファイル**: `experiments/baseline_run.py`
**工数**: 0.5-1日

#### タスク (3項目)
- [ ] 180ステップ（15年）実行
- [ ] 全指標記録
- [ ] 可視化生成

---

### 7.2 外生ショック実験
**ファイル**: `experiments/shock_experiments.py`
**工数**: 1日

#### タスク (3項目)
- [ ] 価格ショック実験（±50%）
- [ ] 政策ショック実験（金利変更等）
- [ ] 人口ショック実験

---

### 7.3 パフォーマンス最適化
**工数**: 1-2日

#### タスク (4項目)
- [ ] LLM呼び出し回数削減
- [ ] キャッシング戦略（プロンプト再利用）
- [ ] バッチ処理最適化
- [ ] メモリ使用量削減

**目標コスト**: $15-18/180ステップ（現在: $21.6）

---

### 7.4 ドキュメント整備
**工数**: 1日

#### タスク (4項目)
- [ ] README更新
- [ ] API ドキュメント生成（Sphinx等）
- [ ] 実験結果まとめ
- [ ] 使い方ガイド作成

---

## 📦 Phase 8: 配布準備（1-2日）

### 概要
**目標**: 公開可能なリポジトリに整備

**依存関係**: Phase 7完了

**成果物**: 公開可能なリポジトリ

### 8.1 パッケージング
**工数**: 0.5日

#### タスク (3項目)
- [ ] `setup.py`作成（すでにpyproject.tomlあり）
- [ ] パッケージメタデータ更新
- [ ] Docker化（オプション）

---

### 8.2 CI/CD設定
**工数**: 0.5-1日

#### タスク (3項目)
- [ ] GitHub Actions設定
- [ ] 自動テスト実行
- [ ] コードカバレッジレポート

---

### 8.3 デモ環境
**工数**: 0.5日

#### タスク (3項目)
- [ ] Streamlit Cloud デプロイ（オプション）
- [ ] デモ動画作成
- [ ] スクリーンショット準備

---

## 🎯 推奨実装順序

### クリティカルパス（最短ルート）

1. **Phase 2.1-2.4**: エージェント実装 (5-7日) ★
2. **Phase 3.1-3.3**: 市場実装 (3-5日)
3. **Phase 5**: データ準備 (2-3日) - Phase 2と並行可能
4. **Phase 6.2-6.3**: 統合テスト・検証 (2-3日)
5. **Phase 4.3**: Streamlitダッシュボード (1-2日)
6. **Phase 6.3**: 経済現象検証 (1-2日) ★
7. **Phase 7.1-7.2**: 実験実行 (1-2日)

**最短完了**: 15-24日

### 推奨順序（品質重視）

1. **Phase 2 + Phase 5並行**: エージェント + データ (5-7日)
2. **Phase 3**: 市場メカニズム (3-5日)
3. **Phase 6.1-6.2**: テスト補完 (2日)
4. **Phase 4**: 可視化 (3-4日)
5. **Phase 6.3-6.4**: 経済現象検証 (2-3日)
6. **Phase 7**: 実験・最適化 (3-5日)
7. **Phase 8**: 配布準備 (1-2日)

**推奨完了**: 19-28日

---

## 💡 重要な注意事項

### Phase 2の重要性
- **最も重要**: Phase 2が完了しないと他のPhaseに進めない
- **最も複雑**: HouseholdAgentは4つの意思決定を持つ
- **LLMコスト**: 開発中は多くのAPI呼び出しが発生

### データ準備のタイミング
- Phase 5はPhase 2と並行して実装可能
- 企業テンプレート（Phase 5.3）はPhase 2.2で必要

### テストの重要性
- Phase 6の経済現象検証が論文再現の核心
- 7つの現象すべてを再現する必要がある

### コスト管理
- 開発中: 1日20ステップ × $0.12 = $2.4/日
- 月間: 約$50-70
- Phase 7で最適化してコスト削減

---

## 📈 マイルストーン

| マイルストーン | Phase | 完了条件 | 日数 | 状態 |
|--------------|-------|---------|------|------|
| M1 | Phase 0-1 | LLM統合完了、基盤実装 | 7日 | ✅ **完了** |
| M2 | Phase 2-3 | 全エージェント・市場動作 | +8-12日 | ✅ **完了** |
| M3 | Phase 4-5 | 可視化・データ完備 | +5-7日 | ⏳ **Phase 5部分完了** |
| M4 | Phase 6 | 経済現象検証完了 | +3-5日 | 待機 |
| M5 | Phase 7-8 | 最終リリース | +4-7日 | 待機 |

**現在**:
- ✅ M1完了（Phase 0-1）
- ✅ M2完了（Phase 2-3）
- ⏳ M3部分進行（Phase 5の6/8完了）

**予想完了**: あと12-26日（可視化、データ準備、統合テストが残り）

---

## 💰 コスト見積もり

### OpenAI API コスト（gpt-4o-mini）

**料金**:
- Input: $0.15/1M tokens
- Output: $0.60/1M tokens

**見積もり（論文ベース）**:
- 論文: 800K tokens/step（gpt-4ベース）
- gpt-4o-mini: 同等と仮定

**1ステップあたり**:
- Input: ~400K tokens × $0.15 = $0.06
- Output: ~100K tokens × $0.60 = $0.06
- 合計: ~$0.12/step

**180ステップ**: $0.12 × 180 = $21.6

**実際は最適化で削減可能**:
- プロンプト短縮化: -30%
- キャッシング: -20%
- 推定: $15-18/180ステップ

### 開発期間のコスト

**開発・テスト（30日間）**:
- 1日平均: 20ステップ × $0.12 = $2.4
- 月間: ~$50-70

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
- Python 3.12+
- OpenAI API Key
- Git
- uv (パッケージマネージャ)

### 推奨
- VS Code + Python extension
- ruff (コードフォーマッター・リンター)
- pytest (テスト)

### セットアップ
```bash
# uvのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv pip install -e .
uv pip install -e ".[dev]"

# テスト実行
uv run pytest

# コード品質チェック
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

---

## 📚 リファレンス

### 主要ドキュメント
- `CLAUDE.md` - アーキテクチャ詳細
- `2510.01297v1.md` - 論文全文
- `config/simulation_config.yaml` - シミュレーション設定
- `config/llm_config.yaml` - LLM設定
- `README.md` - プロジェクト概要・使い方

### 実装済みコード
- `src/llm/llm_interface.py:66` - Function Calling実装
- `src/models/economic_models.py:15` - Cobb-Douglas生産関数
- `src/models/economic_models.py:149` - Taylor rule実装
- `src/environment/simulation.py:90` - シミュレーションループ

### 外部リソース
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Streamlit Docs](https://docs.streamlit.io/)
- [OECD IOTables](https://www.oecd.org/en/data/datasets/input-output-tables.html)
- [uv Documentation](https://github.com/astral-sh/uv)
- [ruff Documentation](https://docs.astral.sh/ruff/)

---

## ✅ 次のアクション

### 現在のタスク
**Phase 4: 地理・可視化実装** または **Phase 5.4: 世帯プロファイル生成**

Phase 3完了により、次のフェーズに進めます：

#### オプション1: Phase 4（地理・可視化）
1. **Phase 4.1**: 地理システム（CityMap） - 100×100グリッドマップ
2. **Phase 4.3**: Streamlitダッシュボード - UI実装（推奨！）
3. **Phase 4.4**: グラフ生成 - 経済指標の可視化

#### オプション2: Phase 5.4（データ準備完了）
- 世帯プロファイル生成器の拡張
- 200世帯の初期データ生成
- Phase 5完全完了（8/8）

#### オプション3: Phase 6（統合テスト）
- Phase 2-3の統合テスト
- エージェント間相互作用テスト

### Phase 3完了成果

✅ **完了項目**:
- 3つの市場実装（Labor, Goods, Financial）
- スキルベース確率的マッチング
- 44財の取引メカニズム
- 預金・貸出システム
- 17/17テスト成功 ✅
- コード品質: ruff軽微な警告のみ

### Phase 2+3完了成果

✅ **完了項目**:
- 4種類のエージェント実装（Household, Firm, Government, CentralBank）
- 3つの市場実装（LaborMarket, GoodsMarket, FinancialMarket）
- 58スキルシステム + 44財データ + 44企業テンプレート
- 58/58テスト成功（41 Phase2 + 17 Phase3）
- コード品質: ruff全体的にクリア

📄 **ドキュメント**:
- `PHASE2_VERIFICATION.md` - Phase 2実装検証レポート（468行）

### この計画の使い方
- 各Phaseを順番に実行
- 各タスクにチェックマークを付けて進捗管理
- 問題が発生したらCLAUDE.mdを参照
- 必要に応じて計画を調整
- 定期的にGitコミット・プッシュ

**重要**: 完璧を目指さず、動くプロトタイプを早く作ることを優先してください。リファクタリングは後で行えます。

---

**最終更新**: 2025-10-14
**現在のマイルストーン**: M2 完了 ✅ (Phase 2-3完了)
**次のマイルストーン**: M3（Phase 4-5: 可視化・データ完備）
**総合進捗**: 81/134タスク完了 (60%)
