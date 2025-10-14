"""
LLM統合のテスト

Phase 1の動作確認:
- 設定の読み込み
- LLMInterfaceの初期化
- 簡単なエージェント意思決定
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.agents.base_agent import BaseAgent, load_prompt_template
from src.llm.llm_interface import LLMInterface
from src.utils.config import get_api_key
from src.utils.logger import setup_logger


class TestHouseholdAgent(BaseAgent):
    """テスト用の簡単な家計エージェント"""

    def __init__(self, agent_id: str, llm_interface: LLMInterface):
        # システムプロンプトの読み込み
        prompt_path = project_root / "src/llm/prompts/household_system.txt"
        system_prompt = load_prompt_template(prompt_path)

        super().__init__(
            agent_id=agent_id,
            agent_type="household",
            llm_interface=llm_interface,
            system_prompt=system_prompt,
            memory_size=3,
        )

        # テスト用の簡単な属性
        self.attributes = {
            "name": "Test Family",
            "age": 35,
            "education": "college",
            "savings": 10000,
            "monthly_income": 3000,
            "employed": True,
        }

    def get_profile_str(self) -> str:
        return f"""Name: {self.attributes['name']}
Age: {self.attributes['age']}
Education: {self.attributes['education']}
Current Savings: ${self.attributes['savings']:,.0f}
Monthly Income: ${self.attributes['monthly_income']:,.0f}
Employment Status: {'Employed' if self.attributes['employed'] else 'Unemployed'}
"""

    def get_available_actions(self):
        """簡略化された行動セット"""
        return [
            {
                "name": "purchase_goods",
                "description": "Purchase goods from the market",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "good_type": {
                            "type": "string",
                            "enum": ["food", "clothing", "electronics"],
                            "description": "Type of good to purchase",
                        },
                        "quantity": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Quantity to purchase",
                        },
                    },
                    "required": ["good_type", "quantity"],
                },
            },
            {
                "name": "save_money",
                "description": "Save money in the bank",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "minimum": 0,
                            "description": "Amount to save",
                        }
                    },
                    "required": ["amount"],
                },
            },
            {
                "name": "do_nothing",
                "description": "Take no action this period",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def _get_fallback_action(self, observation):
        """フォールバック行動: 何もしない"""
        return {"function_name": "do_nothing", "arguments": {}}


def test_llm_interface():
    """LLMInterfaceの基本テスト"""
    print("\n=== LLMInterface Test ===")

    # 環境変数の読み込み
    load_dotenv()

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print(
            "\n.envファイルにOPENAI_API_KEYを設定してください:"
        )
        print("  cp .env.example .env")
        print("  # .envを編集してAPIキーを追加")
        return False

    # LLMInterfaceの初期化
    llm = LLMInterface(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
    )

    # 簡単なFunction Calling
    functions = [
        {
            "name": "get_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"],
            },
        }
    ]

    try:
        response = llm.function_call(
            system_prompt="You are a helpful assistant.",
            user_prompt="What's the weather like in Tokyo?",
            functions=functions,
        )

        print(f"✓ Function called: {response['function_name']}")
        print(f"✓ Arguments: {response['arguments']}")

        # コスト確認
        cost = llm.get_cost_summary()
        print(f"✓ Cost: ${cost['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return False


def test_agent_decision():
    """エージェントの意思決定テスト"""
    print("\n=== Agent Decision Test ===")

    # 環境変数の読み込み
    load_dotenv()

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False

    # LLMとエージェントの初期化
    llm = LLMInterface(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7,
    )

    agent = TestHouseholdAgent(agent_id="test_household_001", llm_interface=llm)

    # 観察情報（簡略版）
    observation = {
        "step": 1,
        "available_goods": ["food", "clothing", "electronics"],
        "prices": {"food": 50, "clothing": 100, "electronics": 500},
        "your_budget": agent.attributes["savings"] + agent.attributes["monthly_income"],
    }

    try:
        # 行動決定
        action = agent.decide_action(observation, step=1)

        print(f"✓ Agent decided: {action['function_name']}")
        print(f"✓ Arguments: {action['arguments']}")

        # 結果を記録
        agent.record_action_result("Success")

        # コスト確認
        cost = llm.get_cost_summary()
        print(f"✓ Total cost so far: ${cost['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"❌ Agent decision failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("=" * 60)
    print("SimCity Phase 1 Integration Test")
    print("=" * 60)

    # ロガーのセットアップ
    setup_logger(log_level="INFO", enable_console=True)

    # テスト実行
    test_results = []

    # Test 1: LLMInterface
    test_results.append(("LLMInterface", test_llm_interface()))

    # Test 2: Agent Decision
    test_results.append(("Agent Decision", test_agent_decision()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in test_results)

    if all_passed:
        print("\n🎉 All tests passed! Phase 1 integration is working.")
        print("\nNext steps:")
        print("  1. Proceed to Phase 2: Agent implementation")
        print("  2. Implement HouseholdAgent, FirmAgent, etc.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
