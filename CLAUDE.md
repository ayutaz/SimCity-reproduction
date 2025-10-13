# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは、論文「SIMCITY: MULTI-AGENT URBAN DEVELOPMENT SIMULATION WITH RICH INTERACTIONS」の実装を目指すプロジェクトです。LLMを活用したマルチエージェント経済シミュレーションフレームワークで、世帯、企業、中央銀行、政府の4つの主要エージェントが相互作用し、マクロ経済現象を再現します。

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
- **生産関数**: Cobb-Douglas型
  - `Y_i = A * L_i^(1-α) * K_i^α`
- **意思決定**:
  1. 生産量と価格設定
  2. 労働市場行動（採用、解雇、賃金調整）
  3. 投資判断（借入、資本購入）

#### 2.3 Government（政府エージェント）
- **役割**:
  - マクロ経済指標のモニタリング（GDP、インフレ率、失業率、ジニ係数）
  - 税収管理（累進課税、VAT）
  - 福祉政策（UBI配布、公共サービス建設）
- **税制**:
  - 所得税（世帯）：累進課税
  - 付加価値税（企業）

#### 2.4 Central Bank（中央銀行エージェント）
- **役割**: 金融政策の実行
- **金利設定**: 修正Taylor rule
  - `r̂ = max{r^n + π^t + α(π - π^t) + β(Y - Y^n), 0}`
- **金利平滑化**:
  - `r_t = ρ * r_{t-1} + (1-ρ) * r̂_t`（ρ = 0.8）

### 3. Investment Pool（投資プール）
- VLMを使用した投資判断
- 十分な資本が蓄積されると新規企業を設立
- 44種類の企業テンプレートから選択
- OECD Input-Output Tablesに基づく生産レシピ

### 4. 可視化システム
- Webベースのレンダリングモジュール
- VLMが新規企業の地理的配置を決定
- 都市拡大のダイナミクスを可視化

## 実装の構成方針

### 推奨ディレクトリ構造

```
SimCity/
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # 基底エージェントクラス
│   │   ├── household.py           # 世帯エージェント
│   │   ├── firm.py                # 企業エージェント
│   │   ├── government.py          # 政府エージェント
│   │   └── central_bank.py        # 中央銀行エージェント
│   ├── environment/
│   │   ├── simulation.py          # シミュレーション実行エンジン
│   │   ├── markets/
│   │   │   ├── goods_market.py    # 財市場
│   │   │   ├── labor_market.py    # 労働市場
│   │   │   └── financial_market.py # 金融市場
│   │   └── geography.py           # 地理情報管理
│   ├── llm/
│   │   ├── llm_interface.py       # LLM API インターフェース
│   │   ├── prompts.py             # プロンプトテンプレート
│   │   └── function_calling.py    # Function Calling実装
│   ├── models/
│   │   ├── economic_models.py     # 経済モデル（Cobb-Douglas等）
│   │   ├── indicators.py          # マクロ経済指標計算
│   │   └── tax_system.py          # 税制システム
│   ├── data/
│   │   ├── firm_templates.py      # 44種類の企業テンプレート
│   │   ├── skill_types.py         # スキルタイプ定義
│   │   └── goods_types.py         # 財の種類定義
│   ├── visualization/
│   │   ├── dashboard.py           # UIダッシュボード（Streamlit推奨）
│   │   ├── map_generator.py       # マップ生成（VLM使用）
│   │   └── plots.py               # グラフ生成関数
│   └── utils/
│       ├── config.py              # 設定管理
│       └── logger.py              # ログ管理
├── tests/
│   ├── test_agents.py
│   ├── test_markets.py
│   └── test_simulation.py
├── experiments/
│   ├── baseline_run.py            # 基本実行
│   ├── shock_experiments.py       # 外生ショック実験
│   └── analysis.py                # 結果分析
├── docs/
│   └── 2510.01297v1.md           # 論文Markdown版
├── config/
│   ├── simulation_config.yaml     # シミュレーション設定
│   └── llm_config.yaml           # LLM設定
└── requirements.txt
```

### 主要技術スタック

#### 必須ライブラリ
- **LLM統合**: `openai` または `anthropic` API
- **数値計算**: `numpy`, `scipy`
- **データ処理**: `pandas`
- **可視化**: `matplotlib`, `plotly`
- **Web UI（選択肢）**:
  - **推奨**: `streamlit`（最もシンプル、リアルタイム対応）
  - 代替1: `jupyter` + `ipywidgets`（開発・プロトタイピング向き）
  - 代替2: `dash` + `plotly`（インタラクティブ可視化）
  - 代替3: 静的HTML出力（最小構成）
  - 論文版: `flask` + `flask-socketio` + `Vue.js`（高度な可視化）
- **設定管理**: `pyyaml`, `python-dotenv`

#### オプションライブラリ
- **分析**: `statsmodels`（経済指標の相関分析）
- **並列処理**: `multiprocessing`（論文ではオプション機能）
- **画像処理**: `pillow`（VLM用）

### Streamlitによる可視化実装例

```python
# src/visualization/dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="SimCity Simulation", layout="wide")

# サイドバー：シミュレーション制御
with st.sidebar:
    st.header("Simulation Control")

    if st.button("Run Step"):
        # 1ステップ実行
        simulation.step()
        st.rerun()

    if st.button("Run 12 Steps (1 year)"):
        # 1年分実行
        for _ in range(12):
            simulation.step()
        st.rerun()

    current_step = st.session_state.get('step', 0)
    st.metric("Current Step", f"{current_step} (Year {current_step//12})")

# メインエリア：ダッシュボード
st.title("🏙️ SimCity Economic Simulation Dashboard")

# 主要指標
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("GDP", f"${gdp:,.0f}", delta=f"{gdp_change:+.1%}")
with col2:
    st.metric("Unemployment", f"{unemployment:.1%}", delta=f"{unemp_change:+.2%}")
with col3:
    st.metric("Inflation", f"{inflation:.2%}", delta=f"{infl_change:+.2%}")
with col4:
    st.metric("Population", f"{population}", delta=f"+{pop_change}")

# グラフエリア
tab1, tab2, tab3, tab4 = st.tabs(["📈 Macro Trends", "🏢 Markets", "🗺️ City Map", "📊 Analysis"])

with tab1:
    # マクロ経済指標の時系列
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("GDP", "Unemployment Rate", "Inflation Rate", "Gini Coefficient")
    )

    fig.add_trace(go.Scatter(x=df['step'], y=df['gdp'], name='GDP'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['step'], y=df['unemployment'], name='Unemployment'), row=1, col=2)
    fig.add_trace(go.Scatter(x=df['step'], y=df['inflation'], name='Inflation'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['step'], y=df['gini'], name='Gini'), row=2, col=2)

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # 市場データ
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Labor Market")
        st.dataframe(labor_market_df, use_container_width=True)
    with col2:
        st.subheader("Goods Prices")
        st.bar_chart(goods_prices_df)

with tab3:
    # 都市マップ
    st.subheader("City Layout")
    st.image(city_map_image, use_container_width=True)

    # 建物統計
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Residential Buildings", len(residential_buildings))
    with col2:
        st.metric("Firms", len(firms))
    with col3:
        st.metric("Public Buildings", len(public_buildings))

with tab4:
    # 経済現象の検証
    st.subheader("Macroeconomic Phenomena Validation")

    # Phillips Curve
    fig_phillips = go.Figure()
    fig_phillips.add_trace(go.Scatter(
        x=df['unemployment'], y=df['inflation'],
        mode='markers', name='Data'
    ))
    fig_phillips.update_layout(
        title="Phillips Curve",
        xaxis_title="Unemployment Rate",
        yaxis_title="Inflation Rate"
    )
    st.plotly_chart(fig_phillips)

    # 相関係数表示
    corr = df[['unemployment', 'inflation']].corr().iloc[0, 1]
    st.metric("Correlation", f"{corr:.3f}")
```

### 実装順序の推奨

#### Phase 1: コア基盤
1. **基本データ構造**
   - エージェント基底クラス
   - 市場インターフェース
   - 経済モデル（Cobb-Douglas等）

2. **LLM統合**
   - Function Calling実装
   - プロンプトテンプレート
   - JSON検証機構

3. **シミュレーションエンジン**
   - ステップ実行ループ
   - フェーズ管理（Move-in / Development）
   - イベント順序管理

#### Phase 2: エージェント実装
1. **Household エージェント**
   - プロファイル生成（ACS microdataベース）
   - 4つの意思決定モジュール
   - メモリとコンテキスト管理

2. **Firm エージェント**
   - 44種類のテンプレート読み込み
   - 生産関数実装
   - 価格・生産決定ロジック

3. **Government & Central Bank**
   - 指標計算（GDP、インフレ、Gini等）
   - Taylor rule実装
   - 税制システム

#### Phase 3: 市場メカニズム
1. **Labor Market**
   - 確率的マッチング
   - スキルベースのマッチング効率

2. **Goods Market**
   - 異質財の取引
   - 価格メカニズム
   - 在庫管理

3. **Financial Market**
   - 預金・貸出
   - 投資プール
   - 金利計算

#### Phase 4: 可視化と評価
1. **Web UI**
   - マップ表示
   - リアルタイム統計
   - VLMによる配置決定

2. **評価指標**
   - Phillips Curve
   - Okun's Law
   - Beveridge Curve
   - Price Elasticity
   - Engel's Law

### LLM統合の重要ポイント

#### プロンプト構造（論文Appendix Eより）
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

#### Function Calling設計
- **アクション例**（Household）:
  - `find_job(position_id: int)`
  - `modify_needs_percentage(name: str, percentage: float)`
  - `borrow(amount: float)`
  - `move_to_home(building_id: int)`

- **アクション例**（Firm）:
  - `adjust_salary(position_id, new_salary)`
  - `adjust_price(name, new_price)`
  - `capital_invest(amount)`
  - `equity_finance(amount)`

#### 異常動作対策
論文6章より：
- LLMが極端な意思決定をする可能性
- ヒューリスティックベースのチェック機構が必要
- 価格変更は数桁の変化を防ぐ制約

### データソースと初期化

#### 世帯プロファイル生成
- **所得分布**: Lognormal分布
  - `ln(m_i,0) ~ N(μ=11.1496, σ²=1.1455)`
  - 2023 ACS IPUMS microdataからMLE推定

- **年齢分布**: U.S. Census Bureau DHCテーブル

- **スキル**: 58種類（論文Table 3）
  - 各スキル: `s_i,j ~ U(s_min, s_max)`

#### 企業テンプレート
- **データソース**: OECD Input-Output Tables
- **生成方法**:
  1. 各財カテゴリの投入物を正規化
  2. 累積75%以上の投入物を選択
  3. LLMで企業テンプレート生成（論文Listing 1）
  4. スキル要件をLLMでマージ（論文Listing 2）

### パラメータ設定（論文より）

#### シミュレーション設定
- 世帯数: 200
- Phase 1: 36ステップ（3年）
- Phase 2: 144ステップ（12年、48四半期）
- LLM: `gpt-4o-mini`（通常推論）、`gpt-4`（VLM）
- サンプリング: デフォルトパラメータ

#### 経済パラメータ
- 生産関数: α（資本シェア）は企業ごとに設定
- Taylor rule: α（インフレ応答）、β（産出ギャップ応答）
- 金利平滑化: ρ = 0.8
- 初期価格: 全財50（具体値は影響小）

### 検証方法

#### マクロ経済現象のチェックリスト
1. **Phillips Curve**: 失業率とインフレ率の負の相関
2. **Okun's Law**: 失業率変化とGDP成長率の負の相関
3. **Beveridge Curve**: 求人率と失業率の負の相関
4. **Price Elasticity**: 需要の価格弾力性（必需品: -1<E<0、奢侈品: E<-1）
5. **Engel's Law**: 所得上昇に伴う食費割合の減少
6. **Investment Volatility**: 投資 > 消費のボラティリティ
7. **Price Stickiness**: 価格調整の遅延

#### ロバストネス検証
- 異なる乱数シードで3回実行
- 定性的パターンの再現性を確認

#### 外生ショック実験
- 44財のうち7財をランダム選択
- ±50%の価格ショック
- 6年間（72ステップ）の追跡

### コスト見積もり

論文Appendix Bより：
- 約800,000トークン/ステップ
- 約$0.25/ステップ
- 180ステップで約$180

### 重要な設計上の注意点

1. **エージェント数の制約**
   - 世帯200は計算コストとのバランス
   - 並列処理は無効化可能（論文記載）

2. **情報アクセス制約**
   - エージェントは前ステップの情報のみアクセス可能
   - 同時意思決定を避ける

3. **VLMの役割**
   - 企業配置決定
   - プロンプトなしで自然にクラスタ構造形成

4. **金融市場の簡略化**
   - 債券、株式、デリバティブは未実装
   - 数理最適化は使用せず

5. **メモリ管理**
   - 構造化メモリでコンテキスト保持
   - 長期記憶と短期記憶の分離が推奨

## 追加資料

- 論文全文: `2510.01297v1.pdf`
- 論文Markdown版: `2510.01297v1.md`
- プロンプト例: 論文Appendix E（Listing 3-17）

## 開発時の留意事項

1. **再現性**: 乱数シードの固定、LLMパラメータの記録
2. **ログ**: 各エージェントの意思決定理由をログ化
3. **検証**: 各ステップでマクロ経済指標を計算・記録
4. **モジュール化**: エージェント、市場、環境を疎結合に
5. **設定ファイル**: ハードコード避け、YAMLで管理