"""
Base Agent class for SimCity

全てのエージェント（家計、企業、政府、中央銀行）の基底クラス
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from src.llm.llm_interface import LLMInterface


class BaseAgent(ABC):
    """
    エージェントの基底クラス

    全てのエージェントが共通で持つべき機能を定義:
    - LLMによる意思決定
    - メモリ（過去の行動履歴）
    - プロンプト生成
    - 行動の実行
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        llm_interface: LLMInterface,
        system_prompt: str,
        memory_size: int = 5,
        decision_frequencies: dict[str, int] | None = None,
    ):
        """
        Args:
            agent_id: エージェントの一意なID
            agent_type: エージェントタイプ (household, firm, government, central_bank)
            llm_interface: LLMインターフェース
            system_prompt: システムプロンプト
            memory_size: 保持する過去の行動数
            decision_frequencies: 決定頻度の辞書 {"decision_name": frequency_steps}
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm = llm_interface
        self.system_prompt = system_prompt
        self.memory_size = memory_size

        # メモリ（過去の行動履歴）
        self.memory: list[dict[str, Any]] = []

        # エージェント固有の属性（サブクラスで設定）
        self.attributes: dict[str, Any] = {}

        # 決定頻度の設定（Phase 7.3.1: 最適化）
        self.decision_frequencies = decision_frequencies or {}
        self.last_decision_steps: dict[str, int] = {}

        logger.info(f"Agent {agent_id} ({agent_type}) initialized")

    @abstractmethod
    def get_profile_str(self) -> str:
        """
        エージェントのプロフィールを文字列で返す

        プロンプトの「Profile」セクションに使用
        サブクラスで実装必須

        Returns:
            プロフィール文字列
        """
        pass

    @abstractmethod
    def get_available_actions(self) -> list[dict[str, Any]]:
        """
        利用可能な行動のリストを返す（OpenAI Function Calling形式）

        Returns:
            関数定義のリスト
        """
        pass

    def get_memory_str(self) -> str:
        """
        過去の行動履歴を文字列で返す

        Returns:
            履歴文字列
        """
        if not self.memory:
            return "No previous actions recorded."

        memory_lines = []
        for i, action in enumerate(self.memory[-self.memory_size :], 1):
            step = action.get("step", "?")
            action_name = action.get("action", "unknown")
            result = action.get("result", "")

            memory_lines.append(f"{i}. Step {step}: {action_name} - {result}")

        return "\n".join(memory_lines)

    def build_user_prompt(self, observation: dict[str, Any]) -> str:
        """
        ユーザープロンプトを構築

        Args:
            observation: 環境からの観察情報

        Returns:
            ユーザープロンプト文字列
        """
        profile = self.get_profile_str()
        memory = self.get_memory_str()
        observation_str = self._format_observation(observation)

        user_prompt = f"""### Profile
{profile}

### Past Actions (Recent {self.memory_size} actions)
{memory}

### Current Observation
{observation_str}

### Available Actions
You must choose ONE action from the available functions and provide appropriate parameters.
Consider your profile, past actions, and current observation to make a rational decision.
"""
        return user_prompt

    def _format_observation(self, observation: dict[str, Any]) -> str:
        """
        観察情報をフォーマット

        Args:
            observation: 観察情報

        Returns:
            フォーマットされた文字列
        """
        lines = []
        for key, value in observation.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}: {', '.join(map(str, value))}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def decide_action(self, observation: dict[str, Any], step: int) -> dict[str, Any]:
        """
        LLMを使用して行動を決定

        Args:
            observation: 環境からの観察情報
            step: 現在のステップ数

        Returns:
            選択された行動と引数
        """
        # プロンプトの構築
        user_prompt = self.build_user_prompt(observation)
        functions = self.get_available_actions()

        # LLM呼び出し
        try:
            response = self.llm.function_call(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                functions=functions,
            )

            # 検証
            is_valid, error_msg = self.llm.validate_response(
                response, [f["name"] for f in functions]
            )

            if not is_valid:
                logger.warning(
                    f"Agent {self.agent_id} generated invalid action: {error_msg}"
                )
                # フォールバック行動
                return self._get_fallback_action(observation)

            # メモリに追加
            action_record = {
                "step": step,
                "action": response["function_name"],
                "arguments": response["arguments"],
                "observation": observation,
            }
            self.memory.append(action_record)

            # メモリサイズを制限
            if len(self.memory) > self.memory_size * 2:
                self.memory = self.memory[-self.memory_size :]

            logger.debug(f"Agent {self.agent_id} decided: {response['function_name']}")

            return {
                "function_name": response["function_name"],
                "arguments": response["arguments"],
            }

        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed to decide action: {e}")
            return self._get_fallback_action(observation)

    @abstractmethod
    def _get_fallback_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        """
        LLM呼び出しが失敗した場合のフォールバック行動

        サブクラスで実装必須

        Args:
            observation: 環境からの観察情報

        Returns:
            デフォルトの行動
        """
        pass

    def update_attributes(self, updates: dict[str, Any]):
        """
        エージェントの属性を更新

        Args:
            updates: 更新する属性の辞書
        """
        self.attributes.update(updates)

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """
        エージェントの属性を取得

        Args:
            key: 属性名
            default: デフォルト値

        Returns:
            属性値
        """
        return self.attributes.get(key, default)

    def record_action_result(self, result: str):
        """
        最後の行動の結果を記録

        Args:
            result: 行動の結果（成功/失敗の説明）
        """
        if self.memory:
            self.memory[-1]["result"] = result

    def should_make_decision(self, decision_name: str, current_step: int) -> bool:
        """
        特定の決定を行うべきかどうかを判断（Phase 7.3.1: 最適化）

        Args:
            decision_name: 決定の名前
            current_step: 現在のステップ

        Returns:
            決定を行うべきならTrue
        """
        # 決定頻度が設定されていない場合は常に決定を行う
        if decision_name not in self.decision_frequencies:
            return True

        frequency = self.decision_frequencies[decision_name]

        # 最後に決定を行ったステップを取得
        last_step = self.last_decision_steps.get(decision_name, -frequency)

        # 頻度に基づいて判断
        if current_step - last_step >= frequency:
            self.last_decision_steps[decision_name] = current_step
            return True

        return False


def load_prompt_template(template_path: str | Path) -> str:
    """
    プロンプトテンプレートファイルを読み込む

    Args:
        template_path: テンプレートファイルのパス

    Returns:
        テンプレート文字列

    Raises:
        FileNotFoundError: ファイルが存在しない場合
    """
    path = Path(template_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(path, encoding="utf-8") as f:
        return f.read()
