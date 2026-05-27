"""
Configuration management with YAML and environment variables
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration from YAML and environment variables.
    Environment variables override YAML values.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config.yaml file
        """
        load_dotenv()
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from YAML file.
        """
        if not self.config_path.exists():
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Configuration loaded from {self.config_path}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with environment variable override.

        Args:
            key: Configuration key (dot notation supported: 'telegram.token')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Check environment variable first
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        # Navigate nested dictionary
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        # Handle environment variable placeholders
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, default)

        return value if value is not None else default

    def get_telegram_token(self) -> str:
        """
        Get Telegram token from config or environment.

        Returns:
            Telegram token

        Raises:
            ValueError: If token is not configured
        """
        token = self.get("telegram.token") or os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError(
                "TELEGRAM_TOKEN not configured. "
                "Set environment variable: export TELEGRAM_TOKEN=your_token"
            )
        return token

    def get_telegram_chat_id(self) -> str:
        """
        Get Telegram chat ID from config or environment.

        Returns:
            Telegram chat ID

        Raises:
            ValueError: If chat ID is not configured
        """
        chat_id = self.get("telegram.chat_id") or os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id:
            raise ValueError(
                "TELEGRAM_CHAT_ID not configured. "
                "Set environment variable: export TELEGRAM_CHAT_ID=your_chat_id"
            )
        return chat_id

    def is_test_mode(self) -> bool:
        """
        Check if system is in test mode.

        Returns:
            True if test mode is enabled
        """
        return self.get("system.test_mode", False)

    def is_debug_mode(self) -> bool:
        """
        Check if system is in debug mode.

        Returns:
            True if debug mode is enabled
        """
        return self.get("system.debug_mode", False)

    def get_database_path(self) -> str:
        """
        Get database file path.

        Returns:
            Database path
        """
        return self.get("database.path", "data/analytics.db")

    def get_timezone(self) -> str:
        """
        Get configured timezone.

        Returns:
            Timezone string
        """
        return self.get("system.timezone", "Europe/Istanbul")

    def get_crypto_symbols(self) -> list:
        """
        Get cryptocurrency symbols to monitor.

        Returns:
            List of cryptocurrency symbols
        """
        return self.get("cryptocurrencies.symbols", [])

    def get_bist_symbols(self) -> dict:
        """
        Get BIST symbols to monitor.

        Returns:
            Dictionary of BIST symbols
        """
        return self.get("bist.symbols", {})

    def __repr__(self) -> str:
        return f"ConfigManager(path={self.config_path})"
