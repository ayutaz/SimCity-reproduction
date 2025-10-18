"""
LLM Interface for SimCity Economic Simulation

OpenAI APIとの統合を提供し、Function Callingによるエージェント行動決定を実現
"""

import json
import time
from typing import Any

from loguru import logger

try:
    from openai import AsyncOpenAI, OpenAI
except ImportError as e:
    raise ImportError("OpenAI package not found. Install with: uv add openai") from e


class LLMInterface:
    """
    OpenAI APIとのインターフェース

    Function Callingを使用してエージェントの行動を決定し、
    レスポンスの検証、リトライ、コスト追跡を提供

    Phase 10.3: 静的プロンプト最適化
    - システムプロンプトのキャッシュ
    - 静的コンテンツの事前構築
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
        enable_prompt_caching: bool = True,
    ):
        """
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
            temperature: サンプリング温度 (0.0-2.0)
            max_tokens: 最大トークン数
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
            timeout: APIタイムアウト（秒）
            enable_prompt_caching: プロンプト最適化を有効化（Phase 10.3）
        """
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.async_client = AsyncOpenAI(api_key=api_key, timeout=timeout)  # Phase 10.4
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_prompt_caching = enable_prompt_caching

        # コスト追跡
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

        # Phase 10.3: 静的プロンプトキャッシュ
        self._system_prompt_cache: dict[str, str] = {}
        self._static_content_cache: dict[str, str] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(
            f"LLMInterface initialized with model={model}, temperature={temperature}, "
            f"prompt_caching={enable_prompt_caching}, async=True"
        )

    def function_call(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: list[dict[str, Any]],
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """
        Function Callingを使用してLLMを呼び出す

        Args:
            system_prompt: システムプロンプト（エージェントの役割・ゴール）
            user_prompt: ユーザープロンプト（観察・状態）
            functions: 利用可能な関数のリスト（OpenAI形式）
            temperature: 温度（Noneの場合はデフォルト値を使用）

        Returns:
            Dict containing:
                - function_name: 呼び出された関数名
                - arguments: 関数の引数（dict）
                - raw_response: 生のレスポンス

        Raises:
            Exception: API呼び出しに失敗した場合
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        temp = temperature if temperature is not None else self.temperature

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=functions,
                    function_call="auto",
                    temperature=temp,
                    max_tokens=self.max_tokens,
                )

                # コスト追跡
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                self.call_count += 1

                # Function Callの抽出
                message = response.choices[0].message

                if message.function_call:
                    function_name = message.function_call.name
                    arguments = json.loads(message.function_call.arguments)

                    logger.debug(
                        f"LLM function call: {function_name} with args: {arguments}"
                    )

                    return {
                        "function_name": function_name,
                        "arguments": arguments,
                        "raw_response": response,
                    }
                else:
                    # Function Callがない場合（エラー）
                    logger.warning(f"No function call in response: {message.content}")
                    return {
                        "function_name": None,
                        "arguments": {},
                        "raw_response": response,
                        "error": "No function call returned",
                    }

            except Exception as e:
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts")
                    raise

    def validate_response(
        self,
        response: dict[str, Any],
        expected_functions: list[str],
        validation_rules: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """
        LLMレスポンスの検証

        Args:
            response: function_call()の戻り値
            expected_functions: 許可される関数名のリスト
            validation_rules: 追加の検証ルール

        Returns:
            (is_valid, error_message) のタプル
        """
        function_name = response.get("function_name")
        arguments = response.get("arguments", {})

        # 関数名のチェック
        if function_name is None:
            return False, "No function name returned"

        if function_name not in expected_functions:
            return False, f"Unexpected function: {function_name}"

        # カスタム検証ルール
        if validation_rules:
            for key, rule in validation_rules.items():
                if key not in arguments:
                    continue

                value = arguments[key]

                # 範囲チェック
                if "min" in rule and value < rule["min"]:
                    return False, f"{key}={value} is below minimum {rule['min']}"

                if "max" in rule and value > rule["max"]:
                    return False, f"{key}={value} exceeds maximum {rule['max']}"

                # 型チェック
                if "type" in rule and not isinstance(value, rule["type"]):
                    return False, f"{key} has wrong type: {type(value)}"

        return True, None

    def get_cost_summary(self) -> dict[str, float]:
        """
        コストサマリーを取得

        Returns:
            Dict containing:
                - total_calls: 総呼び出し回数
                - total_input_tokens: 総入力トークン数
                - total_output_tokens: 総出力トークン数
                - estimated_cost_usd: 推定コスト（USD）
        """
        # gpt-4o-miniの価格（2024年12月時点）
        input_price_per_1m = 0.15  # ドル/100万トークン
        output_price_per_1m = 0.60  # ドル/100万トークン

        input_cost = (self.total_input_tokens / 1_000_000) * input_price_per_1m
        output_cost = (self.total_output_tokens / 1_000_000) * output_price_per_1m
        total_cost = input_cost + output_cost

        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
        }

    def reset_cost_tracking(self):
        """コスト追跡をリセット"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        logger.info("Cost tracking reset")

    # Phase 10.3: プロンプト最適化メソッド

    def cache_system_prompt(self, agent_type: str, prompt: str):
        """
        システムプロンプトをキャッシュ（Phase 10.3）

        Args:
            agent_type: エージェントタイプ（household, firm等）
            prompt: システムプロンプト
        """
        if self.enable_prompt_caching:
            self._system_prompt_cache[agent_type] = prompt
            logger.debug(f"Cached system prompt for {agent_type}")

    def get_cached_system_prompt(self, agent_type: str) -> str | None:
        """
        キャッシュされたシステムプロンプトを取得（Phase 10.3）

        Args:
            agent_type: エージェントタイプ

        Returns:
            キャッシュされたプロンプト（存在しない場合None）
        """
        if self.enable_prompt_caching:
            prompt = self._system_prompt_cache.get(agent_type)
            if prompt:
                self._cache_hits += 1
                return prompt
            self._cache_misses += 1
        return None

    def cache_static_content(self, key: str, content: str):
        """
        静的コンテンツをキャッシュ（Phase 10.3）

        Args:
            key: キャッシュキー（例: "profile_household_1"）
            content: 静的コンテンツ
        """
        if self.enable_prompt_caching:
            self._static_content_cache[key] = content

    def get_cached_static_content(self, key: str) -> str | None:
        """
        キャッシュされた静的コンテンツを取得（Phase 10.3）

        Args:
            key: キャッシュキー

        Returns:
            キャッシュされたコンテンツ（存在しない場合None）
        """
        if self.enable_prompt_caching:
            content = self._static_content_cache.get(key)
            if content:
                self._cache_hits += 1
                return content
            self._cache_misses += 1
        return None

    def get_cache_stats(self) -> dict[str, int]:
        """
        キャッシュ統計を取得（Phase 10.3）

        Returns:
            キャッシュヒット・ミス統計
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 3),
            "system_prompts_cached": len(self._system_prompt_cache),
            "static_content_cached": len(self._static_content_cache),
        }

    def clear_cache(self):
        """キャッシュをクリア（Phase 10.3）"""
        self._system_prompt_cache.clear()
        self._static_content_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Prompt cache cleared")

    # Phase 10.4: 非同期バッチ処理メソッド

    async def function_call_async(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: list[dict[str, Any]],
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """
        非同期Function Calling（Phase 10.4）

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト
            functions: 利用可能な関数のリスト
            temperature: 温度

        Returns:
            LLMレスポンス
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        temp = temperature if temperature is not None else self.temperature

        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=functions,
                    function_call="auto",
                    temperature=temp,
                    max_tokens=self.max_tokens,
                )

                # コスト追跡
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                self.call_count += 1

                # Function Callの抽出
                message = response.choices[0].message

                if message.function_call:
                    function_name = message.function_call.name
                    import json

                    arguments = json.loads(message.function_call.arguments)

                    logger.debug(f"Async LLM function call: {function_name}")

                    return {
                        "function_name": function_name,
                        "arguments": arguments,
                        "raw_response": response,
                    }
                else:
                    return {
                        "function_name": None,
                        "arguments": {},
                        "raw_response": response,
                        "error": "No function call returned",
                    }

            except Exception as e:
                logger.warning(
                    f"Async API call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    import asyncio

                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"Async API call failed after {self.max_retries} attempts"
                    )
                    raise

    async def batch_function_calls(
        self,
        requests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        複数のFunction Callingを並列実行（Phase 10.4）

        Args:
            requests: リクエストのリスト
                各リクエストは以下を含む:
                - system_prompt: システムプロンプト
                - user_prompt: ユーザープロンプト
                - functions: 利用可能な関数のリスト
                - temperature: 温度（オプション）

        Returns:
            レスポンスのリスト
        """
        import asyncio

        tasks = [
            self.function_call_async(
                system_prompt=req["system_prompt"],
                user_prompt=req["user_prompt"],
                functions=req["functions"],
                temperature=req.get("temperature"),
            )
            for req in requests
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # エラーハンドリング
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch request {i} failed: {response}")
                valid_responses.append(
                    {
                        "function_name": None,
                        "arguments": {},
                        "error": str(response),
                    }
                )
            else:
                valid_responses.append(response)

        logger.info(
            f"Batch processing completed: {len(valid_responses)}/{len(requests)} successful"
        )

        return valid_responses


class LLMInterfaceFactory:
    """LLMInterfaceのファクトリークラス"""

    @staticmethod
    def create_from_config(
        api_key: str,
        config: dict[str, Any],
    ) -> LLMInterface:
        """
        設定ファイルからLLMInterfaceを生成

        Args:
            api_key: OpenAI APIキー
            config: LLM設定（llm_config.yamlのopenaiセクション）

        Returns:
            LLMInterface instance
        """
        return LLMInterface(
            api_key=api_key,
            model=config.get("model", "gpt-4o-mini"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
            max_retries=config.get("max_retries", 3),
            retry_delay=config.get("retry_delay", 1.0),
            timeout=config.get("timeout", 30),
        )
