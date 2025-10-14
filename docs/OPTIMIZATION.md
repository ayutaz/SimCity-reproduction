# SimCity パフォーマンス最適化ガイド

SimCityシミュレーションのパフォーマンスとコストを最適化するための実践的なガイドです。

## 目次

1. [現状分析](#現状分析)
2. [実装済み最適化](#実装済み最適化)
3. [今後の最適化案](#今後の最適化案)
4. [モニタリング方法](#モニタリング方法)

---

## 現状分析

### コスト構成（180ステップ実行）

**推定コスト**: $20-25/180ステップ（gpt-4o-mini使用時）

**コスト内訳:**

| エージェント | 呼び出し回数/ステップ | 推定コスト/ステップ | 総コスト（180ステップ） |
|------------|---------------------|-------------------|----------------------|
| Household（200世帯） | ~800-1000 | $0.08-0.10 | $14-18 |
| Firm（44企業） | ~200-220 | $0.02 | $3-4 |
| Government（1） | ~2 | $0.0002 | $0.04 |
| CentralBank（1） | ~1 | $0.0001 | $0.02 |
| **合計** | **~1000-1223** | **$0.10-0.12** | **$18-22** |

**ボトルネック:**
1. **世帯エージェント**: 全体の70-80%のコストを占める
2. **頻繁なLLM呼び出し**: ~1000回/ステップ
3. **大きなプロンプト**: 500-800トークン/呼び出し

### パフォーマンス

**実行時間:**
- **180ステップ**: ~60-90分（並列なし）
- **1ステップあたり**: ~20-30秒
- **LLM待機時間**: 全体の80-90%

**メモリ使用量:**
- **エージェント（200世帯 + 44企業）**: ~400MB
- **履歴データ（180ステップ）**: ~200MB
- **合計**: ~600-700MB

---

## 実装済み最適化

### ✅ Phase 7.3.1: 部分的なLLM呼び出し削減

**実装内容:**
1. **ヒューリスティック貯蓄決定**: 単純なルールベース（所得の10-20%）で代替
2. **データ構造最適化**: Enum統一、from_dict()メソッド使用
3. **コード品質改善**: ruffによる最適化、未使用コード削除

**効果:**
- コスト: $21.6 → $20-22（約5-10%削減）
- コード品質: 100%（ruff準拠）

### ✅ Phase 10.1: 意思決定頻度の最適化（2025-10-14実装）

**実装内容:**
1. **住居決定**: 12ステップ（1年）ごとに変更（10→12ステップ）
2. **スキル投資決定**: 6ステップ（半年）ごとに変更（5→6ステップ）
3. **貯蓄決定**: ヒューリスティックのまま維持

**実装箇所:**
- `src/agents/household.py:70-74` - decision_frequencies設定更新
- `src/agents/base_agent.py:264-289` - should_make_decision()メソッド（既存）

**期待される効果:**
- LLM呼び出し削減: ~350呼び出し/ステップ（35%削減）
  * 住居決定: 200 × (11/12) = 183呼び出し削減
  * スキル投資: 200 × (5/6) = 167呼び出し削減
- コスト削減: $20-22 → $13-15/180ステップ（30-35%削減見込み）

**テスト結果:**
- ✅ 206 passed, 1 skipped
- ✅ 既存機能に影響なし

### ✅ テスト・検証システム

**実装済み:**
- 207テスト（100%成功）
- カバレッジ: 88%
- 経済現象検証システム（7現象）
- ロバストネステスト

---

## 今後の最適化案

### 提案1: 決定の統合（高優先度）

**現状:** 各エージェントが複数の関数を個別に呼び出し

```python
# 世帯エージェントが5回LLMを呼び出す
labor = household.decide_labor_supply(market_state)
consumption = household.decide_consumption(goods_state)
savings = household.decide_savings(financial_state)
housing = household.decide_housing(city_state)
skill = household.decide_skill_investment(labor_state)
```

**提案:** 1回の呼び出しで全決定を取得

```python
# 1回の呼び出しで全て取得
all_decisions = household.decide_all(environment_state)
# all_decisions = {
#     'labor': {...},
#     'consumption': {...},
#     'savings': {...},  # ヒューリスティックで処理済み
#     'housing': {...},
#     'skill_investment': {...}
# }
```

**期待される効果:**
- 呼び出し回数: 1000 → 200-300/ステップ（70-80%削減）
- トークン削減: プロンプトオーバーヘッドの削減
- コスト: $20 → $12-15/180ステップ（25-40%削減）

---

### 提案2: 意思決定の頻度調整（高優先度）

すべての決定を毎ステップ行う必要はありません。

**最適化案:**

| 決定 | 現在の頻度 | 提案頻度 | 理由 |
|------|-----------|---------|------|
| 労働供給 | 毎ステップ | 毎ステップ | 重要な決定 |
| 消費 | 毎ステップ | 毎ステップ | 重要な決定 |
| 貯蓄 | 毎ステップ | ヒューリスティック | 単純なルールで代替可能 ✅ |
| 住居 | 毎ステップ | 12ステップごと | 移動は年1回程度 |
| スキル投資 | 毎ステップ | 6ステップごと | 半年ごとで十分 |

**実装例:**

```python
def step(self, current_step: int, environment_state: dict):
    # 毎ステップ実行
    self.decide_labor_supply(environment_state)
    self.decide_consumption(environment_state)

    # ヒューリスティック貯蓄（LLM不使用）
    self.savings_rate = 0.15  # 所得の15%
    self.savings_amount = self.income * self.savings_rate

    # 12ステップ（1年）ごと
    if current_step % 12 == 0:
        self.decide_housing(environment_state)

    # 6ステップ（半年）ごと
    if current_step % 6 == 0:
        self.decide_skill_investment(environment_state)
```

**期待される効果:**
- 住居決定: 200 × (11/12) = 183呼び出し削減/ステップ
- スキル投資: 200 × (5/6) = 167呼び出し削減/ステップ
- **合計**: 350呼び出し削減/ステップ（35%削減）
- コスト: $20 → $13-15/180ステップ

---

### 提案3: プロンプトキャッシング（中優先度）

**OpenAI Prompt Caching:** 繰り返し使用されるプロンプトのコストが90%削減

**実装戦略:**

1. **システムプロンプト**: エージェントタイプごとに固定
2. **静的プロファイル**: 世帯・企業プロファイル
3. **市場構造**: 財の種類、スキルの種類

```python
messages = [
    {
        "role": "system",
        "content": static_system_prompt,  # キャッシュされる
        "cache_control": {"type": "ephemeral"}
    },
    {
        "role": "user",
        "content": dynamic_state_info  # 毎回変わる
    }
]
```

**期待される効果:**
- キャッシュヒット率: 70-80%
- キャッシュ時のコスト: 入力トークンの10%
- コスト: $15 → $10-12/180ステップ（20-30%削減）

---

### 提案4: 非同期バッチ処理（中優先度）

**現状:** LLM呼び出しが逐次的

**提案:** 並列化による実行時間短縮

```python
import asyncio
from openai import AsyncOpenAI

class LLMInterface:
    async def batch_generate(self, requests: list[dict]):
        """複数のリクエストを並列処理"""
        tasks = [self.generate_async(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        return responses

# 使用例
household_requests = [
    {'agent_type': 'household', 'prompt': ..., 'state': h.get_state()}
    for h in self.households
]
decisions = await llm.batch_generate(household_requests)
```

**期待される効果:**
- 実行時間: 90分 → 20-30分（67-78%削減）
- コスト: 変わらず
- スループット: 3-4倍向上

---

### 提案5: NumPy最適化（低優先度）

**Pythonループを避け、NumPyのベクトル化演算を使用**

```python
# 最適化前
def calculate_gini(incomes: list[float]) -> float:
    n = len(incomes)
    sorted_incomes = sorted(incomes)
    cumsum = sum((i + 1) * income for i, income in enumerate(sorted_incomes))
    # ...

# 最適化後
def calculate_gini(incomes: list[float]) -> float:
    incomes_arr = np.array(incomes)
    sorted_incomes = np.sort(incomes_arr)
    n = len(sorted_incomes)
    index = np.arange(1, n + 1)
    cumsum = np.sum(index * sorted_incomes)
    # ...
```

**期待される効果:**
- 計算速度: 5-10倍向上
- 実行時間: ステップあたり1-2秒削減

---

## モニタリング方法

### コスト監視

```python
from src.llm.llm_interface import LLMInterface

llm = LLMInterface(config)
# ... シミュレーション実行 ...

# コスト統計
print(f"Total cost: ${llm.get_total_cost():.2f}")
print(f"Total tokens: {llm.get_total_tokens()}")
print(f"Total calls: {llm.get_total_calls()}")
print(f"Avg cost/call: ${llm.get_total_cost() / llm.get_total_calls():.4f}")
```

### パフォーマンスベンチマーク

```python
import time

start_time = time.time()

for step in range(180):
    step_start = time.time()
    sim.step()
    step_time = time.time() - step_start

    if step % 30 == 0:
        print(f"Step {step}: {step_time:.2f}s")

total_time = time.time() - start_time
print(f"\nTotal: {total_time / 60:.1f} min")
print(f"Avg: {total_time / 180:.2f} s/step")
```

---

## 最適化ロードマップ

### ✅ Phase 1: 意思決定頻度調整（完了 - 2025-10-14）

**実装:**
- 住居決定: 12ステップごと ✅
- スキル投資: 6ステップごと ✅

**実績**: 1日で完了
**期待効果**: コスト30-35%削減（実測は180ステップ実行後に確認）

### Phase 2: 決定の統合（高インパクト）

**実装:**
- 統合プロンプトテンプレート作成
- Function Calling定義更新

**期間**: 3-5日
**期待効果**: コスト60-70%削減（累積）

### Phase 3: プロンプトキャッシング（中インパクト）

**実装:**
- LLMInterfaceにキャッシング機能追加
- 静的/動的コンテンツ分離

**期間**: 2-3日
**期待効果**: さらに20-30%削減

### Phase 4: 非同期バッチ処理（速度向上）

**実装:**
- AsyncOpenAI統合
- 非同期シミュレーションループ

**期間**: 5-7日
**期待効果**: 実行時間67-78%削減

---

## 最適化目標

| 指標 | 現在（Phase 9完了） | 目標（Phase 10） | 改善率 |
|-----|-----------------|----------------|-------|
| コスト（180ステップ） | $20-22 | $10-12 | 45-55% |
| 実行時間 | 60-90分 | 20-30分 | 67-78% |
| メモリ使用量 | 600-700MB | 400-500MB | 29-43% |
| LLM呼び出し/ステップ | ~1000-1200 | ~300-400 | 67-75% |

---

## 重要な注意点

1. **経済現象の維持**: 最適化後も7つの経済現象が再現されることを確認
2. **段階的な実装**: 一度にすべてを実装せず、段階的にテスト
3. **ベンチマーク**: 各最適化の効果を測定し、文書化
4. **トレードオフ**: コスト削減とシミュレーションの精度のバランス

**検証方法:**
```bash
# 最適化前後で経済現象検証を実行
uv run python scripts/run_baseline.py --steps 30 --validate
```

---

## 参考リソース

- [OpenAI Pricing](https://openai.com/pricing)
- [Prompt Caching Documentation](https://platform.openai.com/docs/guides/prompt-caching)
- [NumPy Performance Tips](https://numpy.org/doc/stable/user/basics.performance.html)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

---

**Note**: このドキュメントは Phase 9完了時点（2025-10-14）の情報です。実装状況に応じて更新してください。
