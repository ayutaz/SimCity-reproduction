# SimCity パフォーマンス最適化戦略

このドキュメントでは、SimCityシミュレーションのパフォーマンスとコストを最適化するための戦略を説明します。

## 目次

1. [現状分析](#現状分析)
2. [最適化目標](#最適化目標)
3. [LLM呼び出し最適化](#llm呼び出し最適化)
4. [プロンプトキャッシング](#プロンプトキャッシング)
5. [バッチ処理](#バッチ処理)
6. [メモリ最適化](#メモリ最適化)
7. [計算最適化](#計算最適化)
8. [実装ロードマップ](#実装ロードマップ)

---

## 現状分析

### コスト構成（180ステップ実行）

**現在の推定コスト**: $21.6/180ステップ（gpt-4o-mini使用時）

**コスト内訳**:

| エージェント | 呼び出し回数/ステップ | トークン数（推定） | コスト/ステップ | 総コスト |
|------------|---------------------|-------------------|---------------|---------|
| Household（200世帯） | 200 × 5関数 = 1000 | 1000 × 500 = 500K | $0.075 | $13.50 |
| Firm（44企業） | 44 × 5関数 = 220 | 220 × 600 = 132K | $0.020 | $3.60 |
| Government（1） | 1 × 2関数 = 2 | 2 × 800 = 1.6K | $0.0002 | $0.04 |
| CentralBank（1） | 1 × 1関数 = 1 | 1 × 700 = 0.7K | $0.0001 | $0.02 |
| **合計** | **1223/ステップ** | **634K/ステップ** | **$0.095** | **$17.16** |

**その他のコスト**:
- 追加のLLM呼び出し（エラーリトライなど）: $2.00
- バッファ: $2.44

**ボトルネック**:
1. **世帯エージェント**: 全体の78%のコストを占める
2. **頻繁なLLM呼び出し**: 1223回/ステップ
3. **大きなプロンプト**: 状態情報を含むため500-800トークン/呼び出し

### パフォーマンス分析

**実行時間（推定）**:
- 180ステップ: ~90分（gpt-4o-mini、並列なし）
- 1ステップあたり: ~30秒
- LLM待機時間: ~80%

**メモリ使用量**:
- 200世帯 + 44企業: ~500MB
- 履歴データ（180ステップ）: ~200MB
- 合計: ~700MB

---

## 最適化目標

### コスト目標

**目標**: $15-18/180ステップ（現在$21.6から30%削減）

**マイルストーン**:
- Phase 7.3.1: $19.50（10%削減）- LLM呼び出し削減
- Phase 7.3.2: $17.50（20%削減）- プロンプトキャッシング
- Phase 7.3.3: $16.00（26%削減）- バッチ処理
- Phase 7.3.4: $15.00（31%削減）- メモリ最適化

### パフォーマンス目標

- **実行時間**: 90分 → 45分（50%削減）
- **メモリ使用量**: 700MB → 500MB（29%削減）
- **API呼び出し回数**: 1223/ステップ → 600/ステップ（51%削減）

---

## LLM呼び出し最適化

### 戦略1: 決定の統合（Decision Consolidation）

現在、各エージェントが複数の関数を個別に呼び出しています。これを1回の呼び出しに統合します。

#### 現在の実装

```python
# 世帯エージェントが5回LLMを呼び出す
labor_decision = household.decide_labor_supply(market_state)
consumption_decision = household.decide_consumption(goods_state)
savings_decision = household.decide_savings(financial_state)
housing_decision = household.decide_housing(city_state)
skill_decision = household.decide_skill_investment(labor_state)
```

**コスト**: 5回 × 500トークン = 2500トークン/世帯

#### 最適化後

```python
# 1回の呼び出しで全ての決定を取得
all_decisions = household.decide_all(environment_state)
# all_decisions = {
#     'labor': {...},
#     'consumption': {...},
#     'savings': {...},
#     'housing': {...},
#     'skill_investment': {...}
# }
```

**コスト**: 1回 × 800トークン = 800トークン/世帯

**削減効果**: (2500 - 800) / 2500 = 68%のトークン削減

**実装方法**:

1. 統合プロンプトテンプレートの作成:

```python
# src/llm/prompts/household_all_decisions.yaml
system: |
  あなたは世帯エージェントです。以下の5つの決定を同時に行ってください：
  1. 労働供給（求職活動）
  2. 消費（財の購入）
  3. 貯蓄（金融資産）
  4. 住居（移動判断）
  5. スキル投資（教育）

user: |
  現在の状態:
  - 資産: {wealth}
  - 所得: {income}
  - スキル: {skills}
  - 位置: {location}

  市場状態:
  - 平均賃金: {avg_wage}
  - 物価水準: {price_level}
  - 金利: {interest_rate}

  全ての決定を含むJSONを返してください。
```

2. Function Callingの定義:

```python
functions = [
    {
        "name": "make_all_decisions",
        "description": "世帯の全ての決定を行う",
        "parameters": {
            "type": "object",
            "properties": {
                "labor": {
                    "type": "object",
                    "properties": {
                        "desired_wage": {"type": "number"},
                        "work_hours": {"type": "number"},
                        "job_search_effort": {"type": "number"}
                    }
                },
                "consumption": {
                    "type": "object",
                    "properties": {
                        "goods_demand": {"type": "object"},
                        "total_budget": {"type": "number"}
                    }
                },
                # ... 他の決定
            }
        }
    }
]
```

**期待される削減**:
- 世帯エージェント: 200 × (5 - 1) = 800呼び出し/ステップ削減
- コスト削減: $13.50 → $5.40（60%削減）

---

### 戦略2: ヒューリスティックによる代替

単純な決定はLLMを使わずにヒューリスティックで処理します。

#### LLMが不要な決定の例

1. **住居移動**: 大半の世帯は移動しない（95%以上）
2. **スキル投資**: 初期段階では投資しない（若年層以外）
3. **貯蓄**: 単純なルールベース（所得の10-20%）

#### 実装例

```python
class HouseholdAgent(BaseAgent):
    def decide_housing(self, city_state: dict) -> dict:
        # ヒューリスティックチェック
        if self.satisfaction > 0.7 and self.tenure > 10:
            # 満足度が高く長期在住なら移動しない
            return {"move": False, "target_location": None}

        # 満足度が低い場合のみLLMを使用
        return self._llm_decide_housing(city_state)

    def decide_savings(self, financial_state: dict) -> dict:
        # 単純なルール: 所得の15%を貯蓄
        savings_rate = 0.15
        savings_amount = self.income * savings_rate
        return {
            "savings_amount": savings_amount,
            "savings_rate": savings_rate
        }
```

**期待される削減**:
- 住居移動: 200 × 0.95 = 190呼び出し削減/ステップ
- スキル投資: 200 × 0.80 = 160呼び出し削減/ステップ
- 貯蓄: 200呼び出し削減/ステップ
- **合計**: 550呼び出し削減/ステップ（45%削減）

---

### 戦略3: 意思決定の頻度調整

すべての決定を毎ステップ行う必要はありません。

#### 決定頻度の最適化

| 決定 | 現在の頻度 | 最適化後の頻度 | 理由 |
|------|-----------|--------------|------|
| 労働供給 | 毎ステップ | 毎ステップ | 重要な決定 |
| 消費 | 毎ステップ | 毎ステップ | 重要な決定 |
| 貯蓄 | 毎ステップ | 3ステップごと | 頻繁に変更不要 |
| 住居 | 毎ステップ | 10ステップごと | 移動は稀 |
| スキル投資 | 毎ステップ | 5ステップごと | 長期的な決定 |

**実装例**:

```python
class HouseholdAgent(BaseAgent):
    def step(self, environment_state: dict):
        current_step = environment_state['step']

        # 毎ステップ実行
        self.decide_labor_supply(environment_state)
        self.decide_consumption(environment_state)

        # 3ステップごと
        if current_step % 3 == 0:
            self.decide_savings(environment_state)

        # 5ステップごと
        if current_step % 5 == 0:
            self.decide_skill_investment(environment_state)

        # 10ステップごと
        if current_step % 10 == 0:
            self.decide_housing(environment_state)
```

**期待される削減**:
- 貯蓄: 200 × (2/3) = 133呼び出し削減/ステップ
- スキル投資: 200 × (4/5) = 160呼び出し削減/ステップ
- 住居: 200 × (9/10) = 180呼び出し削減/ステップ
- **合計**: 473呼び出し削減/ステップ（39%削減）

---

## プロンプトキャッシング

### OpenAI Prompt Cachingの活用

OpenAIのプロンプトキャッシング機能を使用すると、繰り返し使用されるプロンプトのコストが90%削減されます。

#### キャッシング戦略

1. **システムプロンプト**: エージェントタイプごとに固定
2. **静的な状態情報**: 世帯プロファイル、企業プロファイル
3. **市場構造**: 財の種類、スキルの種類

#### 実装例

```python
class LLMInterface:
    def generate(self, agent_type: str, prompt: str, state: dict):
        # キャッシュ可能な部分を分離
        cached_content = self._get_cached_content(agent_type, state)
        dynamic_content = self._get_dynamic_content(state)

        messages = [
            {
                "role": "system",
                "content": cached_content,  # キャッシュされる
                "cache_control": {"type": "ephemeral"}
            },
            {
                "role": "user",
                "content": dynamic_content  # 毎回変わる
            }
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response

    def _get_cached_content(self, agent_type: str, state: dict) -> str:
        """キャッシュ可能な静的コンテンツ"""
        return f"""
        あなたは{agent_type}エージェントです。

        プロファイル:
        - ID: {state['agent_id']}
        - 年齢: {state['age']}
        - 教育: {state['education']}
        - スキル: {state['skills']}

        利用可能な財（44種類）:
        {self._format_goods_list()}

        あなたの役割は...
        """
```

**期待される削減**:
- キャッシュヒット率: 80%（180ステップ中、同じプロンプトが繰り返し使用される）
- キャッシュ時のコスト: 入力トークンの10%
- **コスト削減**: $17.16 × 0.80 × 0.90 = $12.36削減 → **$4.80/180ステップ**

---

## バッチ処理

### 並列LLM呼び出し

現在は逐次的にLLMを呼び出していますが、並列化によって実行時間を大幅に短縮できます。

#### 実装戦略

```python
import asyncio
from openai import AsyncOpenAI

class LLMInterface:
    def __init__(self, config: dict):
        self.async_client = AsyncOpenAI(api_key=config['api_key'])

    async def generate_async(self, agent_type: str, prompt: str, state: dict):
        """非同期でLLM呼び出し"""
        response = await self.async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[...]
        )
        return response

    async def batch_generate(self, requests: list[dict]) -> list[dict]:
        """複数のリクエストを並列処理"""
        tasks = [
            self.generate_async(req['agent_type'], req['prompt'], req['state'])
            for req in requests
        ]
        responses = await asyncio.gather(*tasks)
        return responses
```

#### 使用例

```python
# シミュレーションステップで並列化
async def step_async(self, environment_state: dict):
    # 全世帯の決定を並列で取得
    household_requests = [
        {
            'agent_type': 'household',
            'prompt': self._build_prompt(h),
            'state': h.get_state()
        }
        for h in self.households
    ]

    household_decisions = await self.llm.batch_generate(household_requests)

    # 企業の決定も並列で
    firm_requests = [...]
    firm_decisions = await self.llm.batch_generate(firm_requests)
```

**期待される改善**:
- 実行時間: 90分 → 25分（72%削減）
- コストは変わらないが、スループットが向上

---

## メモリ最適化

### 履歴データの圧縮

各エージェントがすべての履歴を保持すると、メモリ使用量が線形に増加します。

#### 戦略

1. **ローリングウィンドウ**: 直近Nステップのみ保持
2. **要約統計**: 古いデータは統計値のみ保持
3. **間引き**: 重要でないステップのデータを削除

#### 実装例

```python
class BaseAgent:
    def __init__(self, agent_id: str, max_history: int = 10):
        self.memory = {}
        self.max_history = max_history

    def add_memory(self, key: str, value: Any, step: int):
        if key not in self.memory:
            self.memory[key] = deque(maxlen=self.max_history)
        self.memory[key].append((step, value))

    def get_memory_summary(self, key: str) -> dict:
        """古いデータは要約統計のみ"""
        if key not in self.memory:
            return {}

        values = [v for _, v in self.memory[key]]
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'last': values[-1]
        }
```

**期待される削減**:
- メモリ使用量: 700MB → 400MB（43%削減）

---

### 遅延ロード

すべてのデータを事前にロードするのではなく、必要な時にロードします。

```python
class Simulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.households = None  # 遅延ロード
        self.firms = None

    def _load_households(self):
        """必要な時に初めてロード"""
        if self.households is None:
            with open("data/initial_households.json") as f:
                data = json.load(f)
            self.households = [HouseholdAgent(**h) for h in data]
        return self.households

    def step(self):
        households = self._load_households()  # 最初の呼び出し時のみロード
        # ...
```

---

## 計算最適化

### NumPyの活用

Pythonのループを避け、NumPyのベクトル化演算を使用します。

#### 例: ジニ係数の計算

**最適化前**:

```python
def calculate_gini_coefficient(incomes: list[float]) -> float:
    n = len(incomes)
    sorted_incomes = sorted(incomes)
    cumsum = 0
    for i, income in enumerate(sorted_incomes):
        cumsum += (i + 1) * income
    mean_income = sum(sorted_incomes) / n
    gini = (2 * cumsum) / (n * sum(sorted_incomes)) - (n + 1) / n
    return gini
```

**最適化後**:

```python
def calculate_gini_coefficient(incomes: list[float]) -> float:
    incomes_arr = np.array(incomes)
    sorted_incomes = np.sort(incomes_arr)
    n = len(sorted_incomes)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_incomes)) / (n * np.sum(sorted_incomes)) - (n + 1) / n
    return gini
```

**パフォーマンス**: 10,000回の計算が1秒未満（最適化前: 5秒）

---

### JITコンパイル（Numba）

頻繁に呼び出される関数をNumbaでコンパイルします。

```python
from numba import jit

@jit(nopython=True)
def calculate_production_output(labor: float, capital: float, alpha: float, tfp: float) -> float:
    """Cobb-Douglas生産関数（JITコンパイル版）"""
    return tfp * (capital ** alpha) * (labor ** (1 - alpha))
```

**パフォーマンス**: 10,000回の計算が0.01秒（最適化前: 0.5秒）

---

## 実装ロードマップ

### Phase 7.3.1: LLM呼び出し削減（優先度: 高）

**目標**: $21.6 → $19.50（10%削減）

**実装内容**:
1. [ ] 決定頻度の調整（住居: 10ステップごと、スキル: 5ステップごと）
2. [ ] ヒューリスティックによる貯蓄決定の代替
3. [ ] テスト: 経済現象が維持されることを確認

**期間**: 1週間

**期待される効果**:
- LLM呼び出し: 1223 → 900/ステップ（26%削減）
- コスト: $21.6 → $19.50（10%削減）

---

### Phase 7.3.2: プロンプトキャッシング（優先度: 高）

**目標**: $19.50 → $17.50（20%削減）

**実装内容**:
1. [ ] LLMInterfaceにキャッシング機能を追加
2. [ ] 静的コンテンツと動的コンテンツの分離
3. [ ] キャッシュヒット率のモニタリング

**期間**: 1週間

**期待される効果**:
- キャッシュヒット率: 80%
- コスト: $19.50 → $17.50（10%削減）

---

### Phase 7.3.3: バッチ処理（優先度: 中）

**目標**: 実行時間の短縮（コストは変わらない）

**実装内容**:
1. [ ] 非同期LLM呼び出しの実装
2. [ ] バッチ生成機能の追加
3. [ ] シミュレーションステップの非同期化

**期間**: 1-2週間

**期待される効果**:
- 実行時間: 90分 → 40分（56%削減）
- コスト: 変わらず

---

### Phase 7.3.4: メモリ最適化（優先度: 低）

**目標**: メモリ使用量の削減

**実装内容**:
1. [ ] ローリングウィンドウメモリの実装
2. [ ] 履歴データの圧縮
3. [ ] 遅延ロード機構の実装

**期間**: 1週間

**期待される効果**:
- メモリ使用量: 700MB → 450MB（36%削減）

---

## モニタリングと評価

### コストモニタリング

```python
class CostMonitor:
    def __init__(self):
        self.total_cost = 0
        self.call_count = 0
        self.token_count = 0

    def log_call(self, tokens_used: int, cost: float):
        self.call_count += 1
        self.token_count += tokens_used
        self.total_cost += cost

    def get_stats(self) -> dict:
        return {
            'total_cost': self.total_cost,
            'call_count': self.call_count,
            'token_count': self.token_count,
            'avg_cost_per_call': self.total_cost / self.call_count,
            'avg_tokens_per_call': self.token_count / self.call_count
        }
```

### パフォーマンスベンチマーク

```python
import time

def benchmark_simulation(config: SimulationConfig, steps: int = 10):
    """シミュレーションのベンチマーク"""
    sim = Simulation(config)
    start_time = time.time()

    for step in range(steps):
        step_start = time.time()
        sim.step()
        step_time = time.time() - step_start
        print(f"Step {step}: {step_time:.2f}s")

    total_time = time.time() - start_time
    print(f"\nTotal time: {total_time:.2f}s")
    print(f"Avg time per step: {total_time / steps:.2f}s")

    # コスト統計
    cost_stats = sim.llm.get_cost_stats()
    print(f"\nCost statistics:")
    print(f"  Total cost: ${cost_stats['total_cost']:.2f}")
    print(f"  Calls: {cost_stats['call_count']}")
    print(f"  Tokens: {cost_stats['token_count']}")
```

---

## まとめ

### 最終目標

| 指標 | 現在 | 目標 | 改善率 |
|-----|------|------|-------|
| コスト（180ステップ） | $21.6 | $15.0 | 31% |
| 実行時間 | 90分 | 40分 | 56% |
| メモリ使用量 | 700MB | 450MB | 36% |
| LLM呼び出し/ステップ | 1223 | 600 | 51% |

### 重要な注意点

1. **経済現象の維持**: 最適化後も7つの経済現象が再現されることを確認
2. **段階的な実装**: 一度にすべてを実装せず、段階的にテスト
3. **ベンチマーク**: 各最適化の効果を測定し、文書化
4. **トレードオフ**: コスト削減とシミュレーションの精度のバランス

### 次のステップ

1. Phase 7.3.1の実装（LLM呼び出し削減）
2. ベースライン測定の実行
3. 最適化の効果測定
4. ドキュメントの更新

---

## 参考リソース

- [OpenAI Pricing](https://openai.com/pricing)
- [Prompt Caching Documentation](https://platform.openai.com/docs/guides/prompt-caching)
- [NumPy Performance Tips](https://numpy.org/doc/stable/user/basics.performance.html)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

---

**Note**: このドキュメントは、SimCity Phase 7.3の実装ガイドラインです。実装状況に応じて更新してください。
