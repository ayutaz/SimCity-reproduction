# SimCity API リファレンス

SimCityプロジェクトの主要クラスとメソッドのAPIリファレンスです。

**実装状況**: Phase 10完了（207テスト、86%カバレッジ、ruff 100%準拠）

---

## クイックリファレンス

| コンポーネント | パス | 主要機能 |
|------------|------|---------|
| **Simulation** | `src/environment/simulation.py` | シミュレーション実行エンジン |
| **HouseholdAgent** | `src/agents/household.py` | 世帯エージェント（5つの意思決定） |
| **FirmAgent** | `src/agents/firm.py` | 企業エージェント（生産・雇用・価格決定） |
| **GovernmentAgent** | `src/agents/government.py` | 政府エージェント（税制・UBI・失業給付） |
| **CentralBankAgent** | `src/agents/central_bank.py` | 中央銀行（Taylor rule金利決定） |
| **LaborMarket** | `src/environment/markets/labor_market.py` | 労働市場（スキルベースマッチング） |
| **GoodsMarket** | `src/environment/markets/goods_market.py` | 財市場（44財の取引） |
| **FinancialMarket** | `src/environment/markets/financial_market.py` | 金融市場（預金・貸出） |
| **LLMInterface** | `src/llm/llm_interface.py` | LLM統合（Function Calling、コスト追跡） |
| **EconomicPhenomenaValidator** | `experiments/validation.py` | 経済現象検証（7現象） |

---

## 目次

1. [シミュレーションエンジン](#シミュレーションエンジン)
2. [エージェント](#エージェント)
3. [市場メカニズム](#市場メカニズム)
4. [経済モデル](#経済モデル)
5. [データモデル](#データモデル)
6. [LLM統合](#llm統合)
7. [検証・テスト](#検証テスト)
8. [可視化](#可視化)
9. [ユーティリティ](#ユーティリティ)

---

## シミュレーションエンジン

### `Simulation`

**パス**: `src/environment/simulation.py`

シミュレーション全体を管理するメインクラス。

```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

config = load_config("config/simulation_config.yaml")
sim = Simulation(config)
```

#### 主要メソッド

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `step()` | 1ステップ実行（政府→中央銀行→エージェント→市場） | `dict` (経済指標) |
| `get_metrics()` | 経済指標取得（GDP、失業率、インフレ率、ジニ係数等） | `dict` |
| `save_results(output_dir)` | 結果保存（results.json、summary.json） | `None` |
| `load_state(state_file)` | 状態復元（チェックポイントから再開） | `None` |

**実行順序（step()）**:
1. 政府フェーズ（税収、UBI配布）
2. 中央銀行フェーズ（金利決定）
3. エージェントフェーズ（意思決定）
4. 市場フェーズ（マッチング）

---

## エージェント

### `BaseAgent`

**パス**: `src/agents/base_agent.py`

すべてのエージェントの基底クラス。

```python
BaseAgent(agent_id: str, agent_type: str)
```

| メソッド | 説明 |
|---------|------|
| `add_memory(key, value, step)` | メモリに情報追加 |
| `get_memory(key, steps=5)` | メモリから過去の値を取得 |

---

### `HouseholdAgent`

**パス**: `src/agents/household.py`

世帯エージェント。5つの意思決定関数を持つ。

```python
HouseholdAgent(household_id: str, profile: HouseholdProfile, llm_interface: LLMInterface)
```

#### 意思決定メソッド

| メソッド | 説明 | 主要な戻り値 |
|---------|------|------------|
| `decide_labor_supply(market_state)` | 労働供給決定 | `desired_wage`, `work_hours`, `job_search_effort` |
| `decide_consumption(goods_market_state)` | 消費決定 | `goods_demand` (dict), `total_budget` |
| `decide_savings(financial_state)` | 貯蓄決定 | `savings_amount`, `savings_rate` |
| `decide_housing(city_state)` | 住居決定 | `move` (bool), `target_location` (tuple) |
| `decide_skill_investment(labor_market_state)` | スキル投資決定 | `skill_to_improve`, `investment_amount` |

---

### `FirmAgent`

**パス**: `src/agents/firm.py`

企業エージェント。Cobb-Douglas生産関数を使用。

```python
FirmAgent(firm_id: str, profile: FirmProfile, llm_interface: LLMInterface)
```

#### 意思決定メソッド

| メソッド | 説明 | 主要な戻り値 |
|---------|------|------------|
| `decide_production(market_state)` | 生産量決定 | `target_output`, `production_plan` |
| `decide_labor_demand(labor_market_state)` | 労働需要決定 | `num_workers_needed`, `offered_wage`, `required_skills` |
| `decide_pricing(goods_market_state)` | 価格決定 | `prices` (dict), `price_adjustment` |
| `decide_investment(financial_state)` | 投資決定 | `investment_amount`, `loan_request` |
| `decide_location(city_state)` | 立地決定 | `relocate` (bool), `target_location` (tuple) |

---

### `GovernmentAgent`

**パス**: `src/agents/government.py`

政府エージェント。税制・UBI・失業給付を管理。

```python
GovernmentAgent(agent_id: str, initial_state: GovernmentState, llm_interface: LLMInterface)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `collect_taxes(households, firms)` | 税金徴収（累進課税） | `float` (総税収) |
| `distribute_ubi(households)` | UBI配布 | `float` (総UBI支出) |
| `pay_unemployment_benefits(households)` | 失業給付支払 | `float` (総失業給付支出) |
| `decide_policy(macro_state)` | 政策決定 | `dict` (ubi_amount, tax_rate_adjustment等) |

---

### `CentralBankAgent`

**パス**: `src/agents/central_bank.py`

中央銀行エージェント。Taylor ruleによる金利決定。

```python
CentralBankAgent(agent_id: str, initial_state: CentralBankState, llm_interface: LLMInterface)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `decide_interest_rate(macro_state)` | 金利決定（Taylor rule、ρ=0.8） | `dict` (policy_rate, rationale) |

**金利式**: `i_t = ρ * i_{t-1} + (1-ρ) * [r* + α(π - π*) + β * y_gap]`

---

## 市場メカニズム

### `LaborMarket`

**パス**: `src/environment/markets/labor_market.py`

労働市場。スキルベース確率的マッチング。

```python
LaborMarket(config: dict)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `match(job_seekers, job_postings, city_map=None)` | 求職者と求人をマッチング | `tuple` (matches list, stats dict) |
| `calculate_match_score(seeker, posting, city_map=None)` | マッチングスコア計算（70%スキル+30%賃金） | `float` (0-1) |

**マッチング確率**: 0.7（設定可能）

---

### `GoodsMarket`

**パス**: `src/environment/markets/goods_market.py`

財市場。44種類の財の取引。

```python
GoodsMarket(enable_price_adjustment: bool = False)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `match(listings, orders)` | 出品と注文をマッチング（価格ベース） | `list[Transaction]` |
| `get_market_prices()` | 市場価格取得（直近取引の平均） | `dict` {good_id: price} |
| `get_market_demands()` | 市場需要取得 | `dict` {good_id: demand} |
| `get_statistics()` | 市場統計（取引数、未充足需要等） | `dict` |

---

### `FinancialMarket`

**パス**: `src/environment/markets/financial_market.py`

金融市場。預金と貸出を管理。

```python
FinancialMarket(config: dict)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `process_deposits(deposits)` | 預金処理 | `dict` |
| `process_loans(loan_requests)` | 融資処理 | `list[dict]` |
| `update_interest_rates(policy_rate)` | 金利更新（預金=政策金利-0.01、貸出=政策金利+0.02） | `None` |

---

## 経済モデル

### `MacroeconomicIndicators`

**パス**: `src/models/economic_models.py`

マクロ経済指標を計算。

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `calculate_gdp(C, I, G, NX=0)` | GDP計算 | `float` |
| `calculate_unemployment_rate(unemployed, labor_force)` | 失業率計算 | `float` (0-1) |
| `calculate_inflation(current_price, previous_price)` | インフレ率計算 | `float` |
| `calculate_gini_coefficient(incomes)` | ジニ係数計算 | `float` (0-1) |

---

### `ProductionFunction`

**パス**: `src/models/economic_models.py`

Cobb-Douglas生産関数。

```python
ProductionFunction(alpha: float = 0.33, tfp: float = 1.0)
```

| メソッド | 数式 | 戻り値 |
|---------|------|--------|
| `calculate_output(labor, capital)` | `Y = A * K^α * L^(1-α)` | `float` |
| `marginal_product_labor(labor, capital)` | `∂Y/∂L = (1-α) * Y / L` | `float` |
| `marginal_product_capital(labor, capital)` | `∂Y/∂K = α * Y / K` | `float` |

---

### `TaxationSystem`

**パス**: `src/models/economic_models.py`

累進課税システム。

```python
calculate_income_tax(income: float, brackets: list[dict]) -> float
```

**brackets形式**: `[{"threshold": 0, "rate": 0.1}, {"threshold": 50000, "rate": 0.2}, ...]`

---

### `TaylorRule`

**パス**: `src/models/economic_models.py`

Taylor ruleによる金利決定。

```python
calculate_rate(
    inflation: float,
    target_inflation: float,
    output_gap: float,
    natural_rate: float = 0.02,
    alpha: float = 1.5,  # インフレ反応係数
    beta: float = 0.5,   # GDPギャップ反応係数
    rho: float = 0.8,    # 金利平滑化係数
    previous_rate: float = None
) -> float
```

**数式**: `i_t = ρ * i_{t-1} + (1-ρ) * [r* + α(π - π*) + β * y_gap]`

---

## データモデル

### `HouseholdProfile`

**パス**: `src/models/data_models.py`

世帯プロファイル。

| フィールド | 型 | 説明 |
|-----------|----|----|
| `household_id` | `str` | 世帯ID |
| `age` | `int` | 年齢 |
| `education_level` | `str` | 教育レベル（low/medium/high） |
| `skills` | `dict` | スキルレベル {skill_id: level} |
| `initial_wealth` | `float` | 初期資産 |
| `risk_aversion` | `float` | リスク回避度（0-1） |
| `time_preference` | `float` | 時間選好率 |

**生成方法**: Lognormal分布（`ln(income) ~ N(10.5, 0.5)`）

---

### `FirmProfile`

**パス**: `src/models/data_models.py`

企業プロファイル。

| フィールド | 型 | 説明 |
|-----------|----|----|
| `firm_id` | `str` | 企業ID |
| `name` | `str` | 企業名 |
| `goods_type` | `str` | 生産する財 |
| `industry` | `str` | 産業 |
| `required_skills` | `list` | 必要スキル |
| `initial_capital` | `float` | 初期資本 |
| `tfp` | `float` | 全要素生産性 |
| `capital_share` | `float` | 資本分配率（α） |

**データソース**: 44企業テンプレート（`data/firm_templates/`）

---

## LLM統合

### `LLMInterface`

**パス**: `src/llm/llm_interface.py`

OpenAI APIとの統合インターフェース。

```python
LLMInterface(config: dict)
```

#### 主要メソッド

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `generate(agent_type, prompt, state, functions=None, temperature=None)` | LLM呼び出し（Function Calling対応） | `dict` |
| `get_total_cost()` | 累計コスト取得 | `float` (USD) |
| `get_total_tokens()` | 累計トークン数取得 | `int` |
| `get_total_calls()` | 累計呼び出し回数取得 | `int` |

**機能**:
- Function Calling実装
- コスト追跡（入力/出力トークン別）
- 自動リトライ（max_retries=3）
- タイムアウト設定（30秒）

**推奨モデル**: `gpt-4o-mini`（$20-25/180ステップ）

---

## 検証・テスト

### `EconomicPhenomenaValidator`

**パス**: `experiments/validation.py`

7つの経済現象を統計的に検証。

```python
from experiments.validation import EconomicPhenomenaValidator

validator = EconomicPhenomenaValidator(simulation_result)
results = validator.validate_all()
```

#### 検証される7つの経済現象

| 現象 | メソッド | 検証基準 |
|-----|---------|---------|
| Phillips Curve | `validate_phillips_curve()` | 失業率とインフレ率の負の相関（r<0, p<0.05） |
| Okun's Law | `validate_okuns_law()` | 失業率変化とGDP成長率の負の相関（r<0, p<0.05） |
| Beveridge Curve | `validate_beveridge_curve()` | 求人率と失業率の負の相関（r<-0.5, p<0.05） |
| Price Elasticity | `validate_price_elasticity()` | 必需品は非弾力的、奢侈品は弾力的 |
| Engel's Law | `validate_engels_law()` | 所得上昇で食料支出割合減少（r<0, p<0.05） |
| Investment Volatility | `validate_investment_volatility()` | 投資のボラティリティ > 消費 |
| Price Stickiness | `validate_price_stickiness()` | 価格調整が需要変化より遅い |

**戻り値**:
```python
{
    "phenomenon_name": {
        "valid": bool,
        "correlation": float,
        "p_value": float,
        "details": {...}
    },
    "summary": {
        "total": 7,
        "valid": int,
        "success_rate": float
    }
}
```

#### その他のメソッド

| メソッド | 説明 |
|---------|------|
| `generate_report(output_path)` | 検証レポートをJSON形式で保存 |

---

### `RobustnessTest`

**パス**: `experiments/robustness_test.py`

複数シード実行の結果からロバストネスを検証。

```python
from experiments.robustness_test import run_robustness_test

report = run_robustness_test(
    simulation_data_paths=["seed_42/results.json", "seed_123/results.json", ...],
    output_path="robustness_report.json"
)
```

#### 検証項目

| メソッド | 説明 |
|---------|------|
| `test_qualitative_consistency()` | 7つの経済現象の定性的一致を検証 |
| `test_statistical_significance()` | 統計的有意性を検証（変動係数CV<0.5） |
| `test_trend_consistency()` | トレンドの一致性を検証（相関>0.7） |

**戻り値**:
```python
{
    "qualitative_consistency": {...},
    "statistical_stability": {...},
    "trend_consistency": {...},
    "overall_assessment": {
        "robust": bool,
        "qualitative_consistency": bool,
        "statistical_stability": bool,
        "trend_consistency": bool
    }
}
```

---

## 可視化

### `MapGenerator`

**パス**: `src/visualization/map_generator.py`

都市マップの可視化。

```python
from src.visualization.map_generator import MapGenerator

generator = MapGenerator(city_map)
```

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `generate_building_type_map()` | 建物タイプマップ | `Figure` |
| `generate_occupancy_heatmap()` | 占有率ヒートマップ | `Figure` |
| `generate_density_map()` | 密度マップ | `Figure` |
| `generate_composite_view()` | 複合ビュー | `Figure` |

---

### `EconomicPlots`

**パス**: `src/visualization/plots.py`

経済グラフの生成。

| 関数 | 説明 |
|------|------|
| `plot_time_series(history)` | 経済指標の時系列グラフ |
| `plot_phillips_curve(unemployment, inflation)` | Phillips Curve散布図 |
| `plot_okuns_law(unemployment_change, gdp_growth)` | Okun's Law散布図 |
| `plot_beveridge_curve(vacancy_rate, unemployment)` | Beveridge Curve散布図 |
| `plot_engels_law(income, food_ratio)` | Engel's Law散布図 |
| `plot_income_distribution(incomes)` | 所得分布ヒストグラム |

**すべての関数**: `matplotlib.figure.Figure`を戻り値として返す

---

### Streamlitダッシュボード

**パス**: `src/visualization/dashboard.py`, `app.py`

インタラクティブWeb UI。

```bash
streamlit run app.py
```

**4つのタブ**:
1. **Overview**: シミュレーション概要、リアルタイムメトリクス
2. **City Map**: 都市マップ（建物配置、占有率、密度）
3. **Economic Indicators**: 経済指標の時系列グラフ
4. **Analysis**: 経済現象の分析（散布図、相関）

**データソース**:
- Demo Data: デモデータで機能試用
- Upload Results: 既存の結果ファイル（results.json）をアップロード
- Live Simulation: リアルタイムでシミュレーション実行

---

## ユーティリティ

### `load_config()`

**パス**: `src/utils/config.py`

YAML設定ファイルを読み込み。

```python
from src.utils.config import load_config

config = load_config("config/simulation_config.yaml")
```

**戻り値**: `SimulationConfig`オブジェクト（Pydanticモデル）

---

### `setup_logger()`

**パス**: `src/utils/logger.py`

Loguruロガーを設定。

```python
from src.utils.logger import setup_logger

setup_logger(log_level="INFO", log_file="simulation.log")
```

**ログレベル**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

---

## 型定義

### 主要なEnum

**BuildingType** (`src/environment/geography.py`):
```python
class BuildingType(Enum):
    EMPTY = "empty"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    PUBLIC = "public"
```

**SkillCategory** (`src/data/skill_types.py`):
- STEM, Business, Creative, Healthcare, Education, Legal, Service, Construction, Transportation, Agriculture

**GoodsCategory** (`src/data/goods_types.py`):
- Food, Housing, Transportation, Healthcare, Education, Entertainment, Clothing, Technology, Services, Luxury

---

## データファイル

| ファイル | パス | 説明 |
|---------|------|------|
| 企業テンプレート | `data/firm_templates/` | 44企業テンプレート（JSON） |
| 初期世帯データ | `data/initial_households.json` | 200世帯の初期データ（224.8 KB） |
| スキル定義 | `src/data/skill_types.py` | 58種類のスキル定義 |
| 財定義 | `src/data/goods_types.py` | 44種類の財定義 |

---

## さらなるリソース

- **[USAGE.md](USAGE.md)**: 詳細な使い方ガイド（クイックスタート、実験実行、検証方法）
- **[OPTIMIZATION.md](OPTIMIZATION.md)**: パフォーマンス最適化ガイド（コスト削減戦略）
- **[README.md](../README.md)**: プロジェクト概要
- **[CLAUDE.md](../CLAUDE.md)**: アーキテクチャと設計ガイド
- **[論文](../2510.01297v1.md)**: 元論文（マークダウン版）

---

**実装状況**: Phase 10完了（2025-10-19）
- **テスト**: 207テスト、100%成功
- **カバレッジ**: 86%
- **コード品質**: ruff 100%準拠
- **CI/CD**: GitHub Actions (Tests & Lint) 成功
- **経済現象検証**: 7現象すべて実装
- **ロバストネステスト**: 3指標検証システム実装
- **Phase 10実装**: LLM消費決定統合、失業率変動性、価格変動、投資計算、消費平滑化、180ステップ検証完了
