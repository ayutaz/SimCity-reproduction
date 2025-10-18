"""Integration tests for Dashboard and Simulation startup"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.simulation import Simulation
from src.utils.config import get_api_key, load_config
from src.visualization.dashboard import SimCityDashboard


class TestDashboardIntegration:
    """Test Dashboard integration with Simulation"""

    def test_load_config_success(self):
        """Test loading simulation config file"""
        config = load_config("config/simulation_config.yaml")

        assert config is not None
        assert config.agents.households.initial >= 1
        assert config.agents.firms.initial >= 1
        assert config.simulation.max_steps >= 1

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml")

    def test_get_api_key_success(self):
        """Test getting API key from environment"""
        # This test assumes .env file exists with OPENAI_API_KEY
        try:
            api_key = get_api_key("OPENAI_API_KEY")
            assert api_key is not None
            assert len(api_key) > 0
        except ValueError:
            pytest.skip("OPENAI_API_KEY not set in .env file")

    def test_get_api_key_not_found(self):
        """Test getting non-existent API key"""
        # Temporarily unset environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_api_key("NONEXISTENT_API_KEY")

            assert "not found in environment variables" in str(exc_info.value)

    def test_dashboard_initialization(self):
        """Test dashboard can be initialized"""
        dashboard = SimCityDashboard()

        assert dashboard is not None
        assert dashboard.map_generator is not None
        assert dashboard.plots is not None

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set in environment",
    )
    def test_simulation_initialization_with_env(self):
        """Test Simulation can be initialized with API key"""
        config = load_config("config/simulation_config.yaml")

        # Use minimal config for faster testing
        config.agents.households.initial = 5
        config.agents.firms.initial = 2

        simulation = Simulation(config)

        assert simulation is not None
        assert simulation.llm_interface is not None
        assert len(simulation.households) == 5
        assert len(simulation.firms) == 2

    def test_simulation_initialization_without_env(self):
        """Test Simulation fails gracefully without API key"""
        config = load_config("config/simulation_config.yaml")

        # Use minimal config
        config.agents.households.initial = 5
        config.agents.firms.initial = 2

        # Temporarily rename .env file to simulate missing API key
        import shutil

        env_file = Path(".env")
        env_backup = Path(".env.backup_test")

        # Backup .env if it exists
        if env_file.exists():
            shutil.move(str(env_file), str(env_backup))

        try:
            # Clear environment and try to initialize
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                with pytest.raises(ValueError) as exc_info:
                    Simulation(config)

                assert "OPENAI_API_KEY" in str(exc_info.value)
        finally:
            # Restore .env
            if env_backup.exists():
                shutil.move(str(env_backup), str(env_file))

    def test_config_overrides(self):
        """Test config can be overridden programmatically"""
        config = load_config("config/simulation_config.yaml")

        # Override values
        config.agents.households.initial = 10
        config.agents.firms.initial = 3
        config.simulation.random_seed = 999

        assert config.agents.households.initial == 10
        assert config.agents.firms.initial == 3
        assert config.simulation.random_seed == 999


class TestSimulationStartup:
    """Test Simulation startup scenarios"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set in environment",
    )
    def test_simulation_step_execution(self):
        """Test a single simulation step can be executed"""
        config = load_config("config/simulation_config.yaml")

        # Minimal config
        config.agents.households.initial = 5
        config.agents.firms.initial = 2

        simulation = Simulation(config)

        # Execute one step
        indicators = simulation.step()

        # Check indicators are returned
        assert "gdp" in indicators
        assert "unemployment_rate" in indicators
        assert indicators["gdp"] >= 0
        assert 0 <= indicators["unemployment_rate"] <= 1

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set in environment",
    )
    def test_simulation_history_tracking(self):
        """Test simulation history is tracked correctly"""
        config = load_config("config/simulation_config.yaml")

        # Minimal config
        config.agents.households.initial = 5
        config.agents.firms.initial = 2

        simulation = Simulation(config)

        # Execute 3 steps
        for _ in range(3):
            simulation.step()

        # Check history
        history = simulation.state.history
        assert len(history["gdp"]) == 3
        assert len(history["unemployment_rate"]) == 3
        assert len(history["gini"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
