"""
Configuration loader for SimCity

YAML設定ファイルの読み込みと検証を提供
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class SimulationConfig(BaseModel):
    """シミュレーション設定"""

    max_steps: int = Field(default=180, ge=1)
    phase1_steps: int = Field(default=36, ge=1)
    phase2_steps: int = Field(default=144, ge=1)
    random_seed: Optional[int] = 42


class AgentsConfig(BaseModel):
    """エージェント数設定"""

    class HouseholdsConfig(BaseModel):
        initial: int = Field(default=10, ge=1)
        max: int = Field(default=200, ge=1)
        monthly_inflow: int = Field(default=5, ge=0)

    class FirmsConfig(BaseModel):
        initial: int = Field(default=3, ge=1)
        max: int = Field(default=50, ge=1)

    households: HouseholdsConfig = HouseholdsConfig()
    firms: FirmsConfig = FirmsConfig()
    government: int = 1
    central_bank: int = 1


class EconomyConfig(BaseModel):
    """経済パラメータ設定"""

    class ProductionConfig(BaseModel):
        alpha: float = Field(default=0.33, ge=0, le=1)
        total_factor_productivity: float = Field(default=1.0, gt=0)

    class FinancialConfig(BaseModel):
        initial_interest_rate: float = Field(default=0.02, ge=0)
        interest_rate_smoothing: float = Field(default=0.8, ge=0, le=1)

        class TaylorRuleConfig(BaseModel):
            natural_rate: float = 0.02
            inflation_target: float = 0.02
            inflation_coefficient: float = 1.5
            output_coefficient: float = 0.5

        taylor_rule: TaylorRuleConfig = TaylorRuleConfig()

    class TaxationConfig(BaseModel):
        vat_rate: float = Field(default=0.1, ge=0, le=1)
        income_tax_brackets: list = []

    class WelfareConfig(BaseModel):
        ubi_enabled: bool = True
        ubi_amount: float = 500.0
        unemployment_benefit_rate: float = 0.5

    production: ProductionConfig = ProductionConfig()
    financial: FinancialConfig = FinancialConfig()
    taxation: TaxationConfig = TaxationConfig()
    welfare: WelfareConfig = WelfareConfig()


class MarketsConfig(BaseModel):
    """市場設定"""

    class LaborMarketConfig(BaseModel):
        matching_probability: float = Field(default=0.7, ge=0, le=1)
        minimum_wage: float = Field(default=1000, ge=0)

    class GoodsMarketConfig(BaseModel):
        num_categories: int = Field(default=10, ge=1)
        initial_price_range: list = [10, 1000]

    class FinancialMarketConfig(BaseModel):
        deposit_rate_spread: float = -0.01
        loan_rate_spread: float = 0.02

    labor: LaborMarketConfig = LaborMarketConfig()
    goods: GoodsMarketConfig = GoodsMarketConfig()
    financial: FinancialMarketConfig = FinancialMarketConfig()


class GeographyConfig(BaseModel):
    """地理・都市設定"""

    city_size: list = [100, 100]
    initial_center: list = [50, 50]
    use_vlm_placement: bool = True


class DataConfig(BaseModel):
    """データファイル設定"""

    skills_file: str = "data/skills.json"
    goods_file: str = "data/goods.json"
    household_profiles: str = "data/household_profiles.json"


class LoggingConfig(BaseModel):
    """ログ設定"""

    level: str = "INFO"
    save_interval: int = 12
    output_dir: str = "experiments/logs"


class VisualizationConfig(BaseModel):
    """可視化設定"""

    enable_streamlit: bool = True
    update_interval: int = 1
    save_plots: bool = True
    plot_dir: str = "experiments/plots"


class SimCityConfig(BaseModel):
    """SimCity全体設定"""

    simulation: SimulationConfig = SimulationConfig()
    agents: AgentsConfig = AgentsConfig()
    economy: EconomyConfig = EconomyConfig()
    markets: MarketsConfig = MarketsConfig()
    geography: GeographyConfig = GeographyConfig()
    data: DataConfig = DataConfig()
    logging: LoggingConfig = LoggingConfig()
    visualization: VisualizationConfig = VisualizationConfig()


class LLMConfig(BaseModel):
    """LLM設定"""

    class OpenAIConfig(BaseModel):
        model: str = "gpt-4o-mini"
        api_key_env: str = "OPENAI_API_KEY"
        temperature: float = 0.7
        max_tokens: int = 2000
        top_p: float = 1.0
        frequency_penalty: float = 0.0
        presence_penalty: float = 0.0
        max_retries: int = 3
        retry_delay: float = 1.0
        timeout: int = 30

    class VLMConfig(BaseModel):
        model: str = "gpt-4o-mini"
        temperature: float = 0.5
        max_tokens: int = 1000

    class AgentLLMConfig(BaseModel):
        model: str = "gpt-4o-mini"
        temperature: float = 0.7
        max_tokens: int = 1500
        system_prompt_template: str = ""
        user_prompt_template: str = ""

    openai: OpenAIConfig = OpenAIConfig()
    vlm: VLMConfig = VLMConfig()
    agents: Dict[str, AgentLLMConfig] = {}


def load_yaml(file_path: str | Path) -> Dict[str, Any]:
    """
    YAMLファイルを読み込む

    Args:
        file_path: YAMLファイルのパス

    Returns:
        Dict: 読み込まれた設定

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        yaml.YAMLError: YAML解析エラー
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: str | Path) -> SimCityConfig:
    """
    シミュレーション設定を読み込む

    Args:
        config_path: simulation_config.yamlのパス

    Returns:
        SimCityConfig: 検証済み設定オブジェクト

    Raises:
        ValidationError: 設定が不正な場合
    """
    config_dict = load_yaml(config_path)

    try:
        return SimCityConfig(**config_dict)
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
        raise


def load_llm_config(config_path: str | Path) -> LLMConfig:
    """
    LLM設定を読み込む

    Args:
        config_path: llm_config.yamlのパス

    Returns:
        LLMConfig: 検証済みLLM設定オブジェクト

    Raises:
        ValidationError: 設定が不正な場合
    """
    config_dict = load_yaml(config_path)

    try:
        return LLMConfig(**config_dict)
    except ValidationError as e:
        print(f"LLM configuration validation error: {e}")
        raise


def get_api_key(env_var: str = "OPENAI_API_KEY") -> str:
    """
    環境変数からAPIキーを取得

    Args:
        env_var: 環境変数名

    Returns:
        str: APIキー

    Raises:
        ValueError: APIキーが見つからない場合
    """
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(
            f"{env_var} not found in environment variables. "
            f"Please set it in your .env file or environment."
        )
    return api_key


def get_project_root() -> Path:
    """
    プロジェクトルートディレクトリを取得

    Returns:
        Path: プロジェクトルートディレクトリ
    """
    # このファイルは src/utils/config.py にあるので、2階層上がルート
    return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """設定ディレクトリを取得"""
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """データディレクトリを取得"""
    return get_project_root() / "data"


def get_experiments_dir() -> Path:
    """実験ディレクトリを取得"""
    return get_project_root() / "experiments"
