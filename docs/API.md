# SimCity API リファレンス

このドキュメントは、SimCityプロジェクトの主要なクラスとメソッドのAPIリファレンスです。

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

#### コンストラクタ

```python
Simulation(config: SimulationConfig)
```

**パラメータ**:
- `config` (SimulationConfig): シミュレーション設定

**例**:
```python
from src.environment.simulation import Simulation
from src.utils.config import load_config

config = load_config("config/simulation_config.yaml")
sim = Simulation(config)
```

#### メソッド

##### `step()`

1ステップのシミュレーションを実行。

```python
def step() -> None
```

**実行順序**:
1. 政府フェーズ（税収、UBI配布）
2. 中央銀行フェーズ（金利決定）
3. エージェントフェーズ（家計・企業の意思決定）
4. 市場フェーズ（労働・財・金融市場のマッチング）

**例**:
```python
sim.step()
```

##### `get_metrics()`

現在の経済指標を取得。

```python
def get_metrics() -> dict
```

**戻り値**:
- `dict`: 経済指標の辞書
  - `gdp` (float): GDP
  - `unemployment_rate` (float): 失業率
  - `inflation` (float): インフレ率
  - `gini` (float): ジニ係数
  - `average_income` (float): 平均所得
  - `total_consumption` (float): 総消費
  - `total_investment` (float): 総投資

**例**:
```python
metrics = sim.get_metrics()
print(f"GDP: {metrics['gdp']:.2f}")
print(f"Unemployment: {metrics['unemployment_rate']:.2%}")
```

##### `save_results()`

シミュレーション結果を保存。

```python
def save_results(output_dir: str) -> None
```

**パラメータ**:
- `output_dir` (str): 出力ディレクトリパス

**生成されるファイル**:
- `results.json`: 全履歴とメタデータ
- `summary.json`: 最終的なサマリー

**例**:
```python
sim.save_results("experiments/outputs/run_001")
```

##### `load_state()`

保存されたシミュレーション状態を読み込み。

```python
def load_state(state_file: str) -> None
```

**パラメータ**:
- `state_file` (str): 状態ファイルのパス

**例**:
```python
sim.load_state("checkpoints/step_100.json")
```

---

## エージェント

### `BaseAgent`

**パス**: `src/agents/base_agent.py`

すべてのエージェントの基底クラス。

#### コンストラクタ

```python
BaseAgent(agent_id: str, agent_type: str)
```

**パラメータ**:
- `agent_id` (str): エージェントの一意な識別子
- `agent_type` (str): エージェントタイプ（"household", "firm", "government", "central_bank"）

#### メソッド

##### `add_memory()`

エージェントのメモリに情報を追加。

```python
def add_memory(key: str, value: Any, step: int) -> None
```

**パラメータ**:
- `key` (str): メモリキー
- `value` (Any): 保存する値
- `step` (int): 現在のステップ

##### `get_memory()`

メモリから情報を取得。

```python
def get_memory(key: str, steps: int = 5) -> list
```

**パラメータ**:
- `key` (str): メモリキー
- `steps` (int): 取得する過去のステップ数（デフォルト: 5）

**戻り値**:
- `list`: 過去の値のリスト

---

### `HouseholdAgent`

**パス**: `src/agents/household.py`

家計エージェント。5つの意思決定関数を持つ。

#### コンストラクタ

```python
HouseholdAgent(
    household_id: str,
    profile: HouseholdProfile,
    llm_interface: LLMInterface
)
```

**パラメータ**:
- `household_id` (str): 世帯ID
- `profile` (HouseholdProfile): 世帯プロファイル
- `llm_interface` (LLMInterface): LLMインターフェース

#### メソッド

##### `decide_labor_supply()`

労働供給を決定（求職活動）。

```python
def decide_labor_supply(market_state: dict) -> dict
```

**パラメータ**:
- `market_state` (dict): 市場の状態

**戻り値**:
- `dict`:
  - `desired_wage` (float): 希望賃金
  - `work_hours` (float): 労働時間
  - `job_search_effort` (float): 求職努力（0-1）

##### `decide_consumption()`

消費を決定。

```python
def decide_consumption(goods_market_state: dict) -> dict
```

**パラメータ**:
- `goods_market_state` (dict): 財市場の状態

**戻り値**:
- `dict`:
  - `goods_demand` (dict): 財ごとの需要量 `{good_id: quantity}`
  - `total_budget` (float): 消費予算

##### `decide_savings()`

貯蓄を決定。

```python
def decide_savings(financial_state: dict) -> dict
```

**パラメータ**:
- `financial_state` (dict): 金融状態

**戻り値**:
- `dict`:
  - `savings_amount` (float): 貯蓄額
  - `savings_rate` (float): 貯蓄率

##### `decide_housing()`

住居を決定（移動判断）。

```python
def decide_housing(city_state: dict) -> dict
```

**パラメータ**:
- `city_state` (dict): 都市の状態

**戻り値**:
- `dict`:
  - `move` (bool): 移動するかどうか
  - `target_location` (tuple | None): 目標位置 `(x, y)`

##### `decide_skill_investment()`

スキル投資を決定。

```python
def decide_skill_investment(labor_market_state: dict) -> dict
```

**パラメータ**:
- `labor_market_state` (dict): 労働市場の状態

**戻り値**:
- `dict`:
  - `skill_to_improve` (str | None): 向上させるスキル
  - `investment_amount` (float): 投資額

---

### `FirmAgent`

**パス**: `src/agents/firm.py`

企業エージェント。生産・雇用・価格決定を行う。

#### コンストラクタ

```python
FirmAgent(
    firm_id: str,
    profile: FirmProfile,
    llm_interface: LLMInterface
)
```

**パラメータ**:
- `firm_id` (str): 企業ID
- `profile` (FirmProfile): 企業プロファイル
- `llm_interface` (LLMInterface): LLMインターフェース

#### メソッド

##### `decide_production()`

生産量を決定。

```python
def decide_production(market_state: dict) -> dict
```

**パラメータ**:
- `market_state` (dict): 市場の状態

**戻り値**:
- `dict`:
  - `target_output` (float): 目標生産量
  - `production_plan` (dict): 生産計画

##### `decide_labor_demand()`

労働需要を決定（求人）。

```python
def decide_labor_demand(labor_market_state: dict) -> dict
```

**パラメータ**:
- `labor_market_state` (dict): 労働市場の状態

**戻り値**:
- `dict`:
  - `num_workers_needed` (int): 必要な労働者数
  - `offered_wage` (float): 提示賃金
  - `required_skills` (list): 必要なスキル

##### `decide_pricing()`

価格を決定。

```python
def decide_pricing(goods_market_state: dict) -> dict
```

**パラメータ**:
- `goods_market_state` (dict): 財市場の状態

**戻り値**:
- `dict`:
  - `prices` (dict): 財ごとの価格 `{good_id: price}`
  - `price_adjustment` (float): 価格調整率

##### `decide_investment()`

投資を決定。

```python
def decide_investment(financial_state: dict) -> dict
```

**パラメータ**:
- `financial_state` (dict): 金融状態

**戻り値**:
- `dict`:
  - `investment_amount` (float): 投資額
  - `loan_request` (float): 融資希望額

##### `decide_location()`

立地を決定（移転判断）。

```python
def decide_location(city_state: dict) -> dict
```

**パラメータ**:
- `city_state` (dict): 都市の状態

**戻り値**:
- `dict`:
  - `relocate` (bool): 移転するかどうか
  - `target_location` (tuple | None): 目標位置 `(x, y)`

---

### `GovernmentAgent`

**パス**: `src/agents/government.py`

政府エージェント。税制・UBI・失業給付を管理。

#### コンストラクタ

```python
GovernmentAgent(
    agent_id: str,
    initial_state: GovernmentState,
    llm_interface: LLMInterface
)
```

#### メソッド

##### `collect_taxes()`

税金を徴収。

```python
def collect_taxes(households: list[HouseholdAgent], firms: list[FirmAgent]) -> float
```

**パラメータ**:
- `households` (list): 世帯エージェントのリスト
- `firms` (list): 企業エージェントのリスト

**戻り値**:
- `float`: 総税収

##### `distribute_ubi()`

UBI（ユニバーサル・ベーシック・インカム）を配布。

```python
def distribute_ubi(households: list[HouseholdAgent]) -> float
```

**パラメータ**:
- `households` (list): 世帯エージェントのリスト

**戻り値**:
- `float`: 総UBI支出

##### `pay_unemployment_benefits()`

失業給付を支払う。

```python
def pay_unemployment_benefits(households: list[HouseholdAgent]) -> float
```

**パラメータ**:
- `households` (list): 世帯エージェントのリスト

**戻り値**:
- `float`: 総失業給付支出

##### `decide_policy()`

政策を決定。

```python
def decide_policy(macro_state: dict) -> dict
```

**パラメータ**:
- `macro_state` (dict): マクロ経済状態

**戻り値**:
- `dict`:
  - `ubi_amount` (float): UBI金額
  - `tax_rate_adjustment` (float): 税率調整
  - `unemployment_benefit_rate` (float): 失業給付率

---

### `CentralBankAgent`

**パス**: `src/agents/central_bank.py`

中央銀行エージェント。金利政策を決定。

#### コンストラクタ

```python
CentralBankAgent(
    agent_id: str,
    initial_state: CentralBankState,
    llm_interface: LLMInterface
)
```

#### メソッド

##### `decide_interest_rate()`

金利を決定（Taylor rule）。

```python
def decide_interest_rate(macro_state: dict) -> dict
```

**パラメータ**:
- `macro_state` (dict): マクロ経済状態
  - `inflation` (float): インフレ率
  - `output_gap` (float): GDPギャップ

**戻り値**:
- `dict`:
  - `policy_rate` (float): 政策金利
  - `rationale` (str): 決定理由

---

## 市場メカニズム

### `LaborMarket`

**パス**: `src/environment/markets/labor_market.py`

労働市場。求職者と求人のマッチング。

#### コンストラクタ

```python
LaborMarket(config: dict)
```

**パラメータ**:
- `config` (dict): 労働市場の設定

#### メソッド

##### `match()`

求職者と求人をマッチング。

```python
def match(
    job_seekers: list[dict],
    job_postings: list[dict],
    city_map: Optional[CityMap] = None
) -> tuple[list[dict], dict]
```

**パラメータ**:
- `job_seekers` (list): 求職者のリスト
- `job_postings` (list): 求人のリスト
- `city_map` (Optional[CityMap]): 都市マップ（距離考慮時）

**戻り値**:
- `tuple`:
  - `list[dict]`: マッチングのリスト `[{household_id, firm_id, wage, ...}, ...]`
  - `dict`: マッチング統計

**例**:
```python
matches, stats = labor_market.match(job_seekers, job_postings)
print(f"Matches: {stats['num_matches']}")
print(f"Match rate: {stats['match_rate']:.2%}")
```

##### `calculate_match_score()`

マッチングスコアを計算。

```python
def calculate_match_score(
    seeker: dict,
    posting: dict,
    city_map: Optional[CityMap] = None
) -> float
```

**パラメータ**:
- `seeker` (dict): 求職者情報
- `posting` (dict): 求人情報
- `city_map` (Optional[CityMap]): 都市マップ

**戻り値**:
- `float`: マッチングスコア（0-1）

---

### `GoodsMarket`

**パス**: `src/environment/markets/goods_market.py`

財市場。財の売買とマッチング。

#### コンストラクタ

```python
GoodsMarket(config: dict)
```

#### メソッド

##### `match()`

買い手と売り手をマッチング。

```python
def match(
    buyers: list[dict],
    sellers: list[dict]
) -> tuple[list[dict], dict]
```

**パラメータ**:
- `buyers` (list): 買い手のリスト（世帯）
- `sellers` (list): 売り手のリスト（企業）

**戻り値**:
- `tuple`:
  - `list[dict]`: 取引のリスト `[{buyer_id, seller_id, good_id, quantity, price}, ...]`
  - `dict`: 市場統計

##### `update_prices()`

需給に基づいて価格を更新。

```python
def update_prices(transactions: list[dict]) -> dict
```

**パラメータ**:
- `transactions` (list): 取引のリスト

**戻り値**:
- `dict`: 更新された価格 `{good_id: new_price}`

---

### `FinancialMarket`

**パス**: `src/environment/markets/financial_market.py`

金融市場。預金と貸出を管理。

#### コンストラクタ

```python
FinancialMarket(config: dict)
```

#### メソッド

##### `process_deposits()`

預金を処理。

```python
def process_deposits(deposits: list[dict]) -> dict
```

**パラメータ**:
- `deposits` (list): 預金のリスト `[{agent_id, amount}, ...]`

**戻り値**:
- `dict`: 処理結果

##### `process_loans()`

融資を処理。

```python
def process_loans(loan_requests: list[dict]) -> list[dict]
```

**パラメータ**:
- `loan_requests` (list): 融資申請のリスト

**戻り値**:
- `list[dict]`: 承認された融資のリスト

##### `update_interest_rates()`

金利を更新。

```python
def update_interest_rates(policy_rate: float) -> None
```

**パラメータ**:
- `policy_rate` (float): 政策金利

---

## 経済モデル

### `MacroeconomicIndicators`

**パス**: `src/models/economic_models.py`

マクロ経済指標を計算。

#### メソッド

##### `calculate_gdp()`

GDPを計算。

```python
def calculate_gdp(
    consumption: float,
    investment: float,
    government_spending: float,
    net_exports: float = 0
) -> float
```

**パラメータ**:
- `consumption` (float): 消費
- `investment` (float): 投資
- `government_spending` (float): 政府支出
- `net_exports` (float): 純輸出（デフォルト: 0）

**戻り値**:
- `float`: GDP

##### `calculate_unemployment_rate()`

失業率を計算。

```python
def calculate_unemployment_rate(
    unemployed: int,
    labor_force: int
) -> float
```

**パラメータ**:
- `unemployed` (int): 失業者数
- `labor_force` (int): 労働力人口

**戻り値**:
- `float`: 失業率（0-1）

##### `calculate_inflation()`

インフレ率を計算。

```python
def calculate_inflation(
    current_price_level: float,
    previous_price_level: float
) -> float
```

**パラメータ**:
- `current_price_level` (float): 現在の物価水準
- `previous_price_level` (float): 前期の物価水準

**戻り値**:
- `float`: インフレ率

##### `calculate_gini_coefficient()`

ジニ係数を計算。

```python
def calculate_gini_coefficient(incomes: list[float]) -> float
```

**パラメータ**:
- `incomes` (list[float]): 所得のリスト

**戻り値**:
- `float`: ジニ係数（0-1）

---

### `ProductionFunction`

**パス**: `src/models/economic_models.py`

Cobb-Douglas生産関数。

#### コンストラクタ

```python
ProductionFunction(alpha: float = 0.33, tfp: float = 1.0)
```

**パラメータ**:
- `alpha` (float): 資本分配率（デフォルト: 0.33）
- `tfp` (float): 全要素生産性（デフォルト: 1.0）

#### メソッド

##### `calculate_output()`

生産量を計算。

```python
def calculate_output(labor: float, capital: float) -> float
```

**パラメータ**:
- `labor` (float): 労働投入量
- `capital` (float): 資本投入量

**戻り値**:
- `float`: 生産量

**数式**: `Y = A * K^α * L^(1-α)`

---

### `TaxationSystem`

**パス**: `src/models/economic_models.py`

累進課税システム。

#### メソッド

##### `calculate_income_tax()`

所得税を計算。

```python
def calculate_income_tax(income: float, brackets: list[dict]) -> float
```

**パラメータ**:
- `income` (float): 所得
- `brackets` (list[dict]): 税率ブラケット

**戻り値**:
- `float`: 所得税額

---

### `TaylorRule`

**パス**: `src/models/economic_models.py`

Taylor ruleによる金利決定。

#### メソッド

##### `calculate_rate()`

金利を計算。

```python
def calculate_rate(
    inflation: float,
    target_inflation: float,
    output_gap: float,
    natural_rate: float = 0.02,
    alpha: float = 1.5,
    beta: float = 0.5,
    rho: float = 0.8,
    previous_rate: float = None
) -> float
```

**パラメータ**:
- `inflation` (float): 現在のインフレ率
- `target_inflation` (float): 目標インフレ率
- `output_gap` (float): GDPギャップ
- `natural_rate` (float): 自然利子率（デフォルト: 0.02）
- `alpha` (float): インフレ反応係数（デフォルト: 1.5）
- `beta` (float): GDPギャップ反応係数（デフォルト: 0.5）
- `rho` (float): 金利平滑化係数（デフォルト: 0.8）
- `previous_rate` (float): 前期の金利

**戻り値**:
- `float`: 政策金利

**数式**: `i_t = ρ * i_{t-1} + (1-ρ) * [r* + α(π - π*) + β * y_gap]`

---

## データモデル

### `HouseholdProfile`

**パス**: `src/models/data_models.py`

世帯プロファイル。

#### フィールド

- `household_id` (str): 世帯ID
- `age` (int): 年齢
- `education_level` (str): 教育レベル（"low", "medium", "high"）
- `skills` (dict): スキルレベル `{skill_id: level}`
- `initial_wealth` (float): 初期資産
- `risk_aversion` (float): リスク回避度（0-1）
- `time_preference` (float): 時間選好率

---

### `FirmProfile`

**パス**: `src/models/data_models.py`

企業プロファイル。

#### フィールド

- `firm_id` (str): 企業ID
- `industry` (str): 産業
- `goods_produced` (list[str]): 生産する財のリスト
- `required_skills` (dict): 必要なスキル
- `initial_capital` (float): 初期資本
- `production_technology` (dict): 生産技術パラメータ

---

## LLM統合

### `LLMInterface`

**パス**: `src/llm/llm_interface.py`

LLM APIとの統合インターフェース。

#### コンストラクタ

```python
LLMInterface(config: dict)
```

**パラメータ**:
- `config` (dict): LLM設定

#### メソッド

##### `generate()`

LLMに問い合わせて応答を生成。

```python
def generate(
    agent_type: str,
    prompt: str,
    state: dict,
    functions: list[dict] = None,
    temperature: float = None
) -> dict
```

**パラメータ**:
- `agent_type` (str): エージェントタイプ
- `prompt` (str): プロンプト
- `state` (dict): 現在の状態
- `functions` (list[dict]): Function Calling用の関数定義
- `temperature` (float): 生成のランダム性

**戻り値**:
- `dict`: LLMの応答

##### `get_total_cost()`

累計コストを取得。

```python
def get_total_cost() -> float
```

**戻り値**:
- `float`: 累計コスト（USD）

##### `get_total_tokens()`

累計トークン数を取得。

```python
def get_total_tokens() -> int
```

**戻り値**:
- `int`: 累計トークン数

---

## 検証・テスト

### `EconomicPhenomenaValidator`

**パス**: `experiments/validation.py`

経済現象を統計的に検証。

#### コンストラクタ

```python
EconomicPhenomenaValidator(simulation_result: dict)
```

**パラメータ**:
- `simulation_result` (dict): シミュレーション結果

#### メソッド

##### `validate_all()`

すべての経済現象を検証。

```python
def validate_all() -> dict
```

**戻り値**:
- `dict`: 検証結果
  - `phillips_curve` (dict): Phillips Curve検証結果
  - `okuns_law` (dict): Okun's Law検証結果
  - `beveridge_curve` (dict): Beveridge Curve検証結果
  - `price_elasticity` (dict): Price Elasticity検証結果
  - `engels_law` (dict): Engel's Law検証結果
  - `investment_volatility` (dict): Investment Volatility検証結果
  - `price_stickiness` (dict): Price Stickiness検証結果
  - `summary` (dict): サマリー

##### `validate_phillips_curve()`

Phillips Curveを検証。

```python
def validate_phillips_curve() -> dict
```

**戻り値**:
- `dict`:
  - `valid` (bool): 検証結果
  - `correlation` (float): 相関係数
  - `p_value` (float): p値

##### `generate_report()`

検証レポートを生成。

```python
def generate_report(output_path: str) -> None
```

**パラメータ**:
- `output_path` (str): 出力ファイルパス

---

### `RobustnessTest`

**パス**: `experiments/robustness_test.py`

ロバストネステスト。

#### コンストラクタ

```python
RobustnessTest(simulation_results: list[dict])
```

**パラメータ**:
- `simulation_results` (list[dict]): 複数のシミュレーション結果

#### メソッド

##### `test_qualitative_consistency()`

定性的一致を検証。

```python
def test_qualitative_consistency() -> dict
```

**戻り値**:
- `dict`: 一致性の検証結果

##### `test_statistical_significance()`

統計的有意性を検証。

```python
def test_statistical_significance() -> dict
```

**戻り値**:
- `dict`: 統計的検証結果

##### `test_trend_consistency()`

トレンドの一致性を検証。

```python
def test_trend_consistency() -> dict
```

**戻り値**:
- `dict`: トレンド一致性の検証結果

##### `generate_report()`

ロバストネステストレポートを生成。

```python
def generate_report(output_path: str) -> dict
```

**パラメータ**:
- `output_path` (str): 出力ファイルパス

**戻り値**:
- `dict`: レポート

---

## 可視化

### `MapGenerator`

**パス**: `src/visualization/map_generator.py`

都市マップの可視化。

#### コンストラクタ

```python
MapGenerator(city_map: CityMap)
```

**パラメータ**:
- `city_map` (CityMap): 都市マップ

#### メソッド

##### `generate_building_type_map()`

建物タイプマップを生成。

```python
def generate_building_type_map() -> Figure
```

**戻り値**:
- `Figure`: Matplotlibの図

##### `generate_occupancy_heatmap()`

占有率ヒートマップを生成。

```python
def generate_occupancy_heatmap() -> Figure
```

**戻り値**:
- `Figure`: Matplotlibの図

##### `generate_density_map()`

密度マップを生成。

```python
def generate_density_map() -> Figure
```

**戻り値**:
- `Figure`: Matplotlibの図

---

### Plots

**パス**: `src/visualization/plots.py`

経済グラフの生成。

#### 関数

##### `plot_economic_indicators()`

経済指標の時系列グラフ。

```python
def plot_economic_indicators(history: dict) -> Figure
```

**パラメータ**:
- `history` (dict): シミュレーション履歴

**戻り値**:
- `Figure`: Matplotlibの図

##### `plot_phillips_curve()`

Phillips Curveの散布図。

```python
def plot_phillips_curve(history: dict) -> Figure
```

##### `plot_okuns_law()`

Okun's Lawの散布図。

```python
def plot_okuns_law(history: dict) -> Figure
```

##### `plot_beveridge_curve()`

Beveridge Curveの散布図。

```python
def plot_beveridge_curve(history: dict) -> Figure
```

##### `plot_income_distribution()`

所得分布のヒストグラム。

```python
def plot_income_distribution(incomes: list[float]) -> Figure
```

---

## ユーティリティ

### `load_config()`

**パス**: `src/utils/config.py`

YAML設定ファイルを読み込み。

```python
def load_config(config_path: str) -> SimulationConfig
```

**パラメータ**:
- `config_path` (str): 設定ファイルのパス

**戻り値**:
- `SimulationConfig`: 設定オブジェクト

**例**:
```python
from src.utils.config import load_config

config = load_config("config/simulation_config.yaml")
```

---

### `setup_logger()`

**パス**: `src/utils/logger.py`

ロガーを設定。

```python
def setup_logger(
    log_level: str = "INFO",
    log_file: str = None
) -> None
```

**パラメータ**:
- `log_level` (str): ログレベル（"DEBUG", "INFO", "WARNING", "ERROR"）
- `log_file` (str): ログファイルパス（Noneの場合は標準出力のみ）

**例**:
```python
from src.utils.logger import setup_logger

setup_logger(log_level="DEBUG", log_file="simulation.log")
```

---

## 型定義

### BuildingType (Enum)

**パス**: `src/environment/geography.py`

建物タイプの列挙型。

```python
class BuildingType(Enum):
    EMPTY = "empty"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    PUBLIC = "public"
```

---

## さらなるリソース

- [docs/USAGE.md](USAGE.md): 詳細な使い方ガイド
- [README.md](../README.md): プロジェクト概要
- [CLAUDE.md](../CLAUDE.md): アーキテクチャガイド

---

**Note**: このAPIリファレンスは、SimCity v1.0の時点の情報です。最新の情報は、ソースコードを参照してください。
