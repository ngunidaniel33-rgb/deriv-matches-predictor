"""Configuration management for Deriv Matches Predictor."""

import os
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class DerivConfig:
    """Deriv API Configuration."""
    api_token: str = os.getenv("DERIV_API_TOKEN", "")
    app_id: str = os.getenv("DERIV_APP_ID", "")
    api_endpoint: str = os.getenv("DERIV_API_ENDPOINT", "wss://ws.derivws.com/websockets/v3")
    
    def is_valid(self) -> bool:
        """Validate Deriv configuration."""
        return bool(self.api_token and self.app_id)


@dataclass
class AnalysisConfig:
    """Analysis Configuration."""
    # Tick window sizes
    tick_windows: list = None
    default_tick_window: int = int(os.getenv("TICK_WINDOW_SIZE", "1000"))
    
    # Update intervals (milliseconds)
    analysis_update_interval: int = int(os.getenv("ANALYSIS_UPDATE_INTERVAL", "1000"))
    signal_check_interval: int = int(os.getenv("SIGNAL_CHECK_INTERVAL", "5000"))
    
    # Confidence thresholds
    min_sample_size: int = int(os.getenv("MIN_SAMPLE_SIZE", "50"))
    high_confidence_threshold: float = float(os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.75"))
    medium_confidence_threshold: float = float(os.getenv("MEDIUM_CONFIDENCE_THRESHOLD", "0.50"))
    
    # Signal generation
    signal_probability_threshold: float = float(os.getenv("SIGNAL_PROBABILITY_THRESHOLD", "0.12"))
    enable_strong_watch: bool = os.getenv("ENABLE_STRONG_WATCH", "true").lower() == "true"
    
    # Weighting factors
    recent_weight: float = float(os.getenv("RECENT_WEIGHT", "0.6"))
    historical_weight: float = float(os.getenv("HISTORICAL_WEIGHT", "0.4"))
    momentum_weight: float = float(os.getenv("MOMENTUM_WEIGHT", "0.3"))
    
    def __post_init__(self):
        if self.tick_windows is None:
            self.tick_windows = [50, 100, 250, 500, 1000, 5000]


@dataclass
class DatabaseConfig:
    """Database Configuration."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")
    enable_migrations: bool = os.getenv("ENABLE_MIGRATIONS", "true").lower() == "true"
    pool_size: int = int(os.getenv("POOL_SIZE", "5"))
    max_overflow: int = int(os.getenv("MAX_OVERFLOW", "10"))


@dataclass
class RiskConfig:
    """Risk Management Configuration."""
    # Bankroll management
    enable_bankroll_tracking: bool = os.getenv("ENABLE_BANKROLL_TRACKING", "false").lower() == "true"
    initial_bankroll: float = float(os.getenv("INITIAL_BANKROLL", "1000.0"))
    
    # Limits
    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", "100.0"))
    max_consecutive_losses: int = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5"))
    max_exposure_percentage: float = float(os.getenv("MAX_EXPOSURE_PERCENTAGE", "5.0"))
    
    # Mode
    trading_enabled: bool = os.getenv("TRADING_ENABLED", "false").lower() == "true"
    demo_mode_only: bool = os.getenv("DEMO_MODE_ONLY", "true").lower() == "true"
    require_manual_confirmation: bool = os.getenv("REQUIRE_MANUAL_CONFIRMATION", "true").lower() == "true"


@dataclass
class UIConfig:
    """UI Configuration."""
    theme: str = os.getenv("UI_THEME", "dark")
    default_chart_type: str = os.getenv("DEFAULT_CHART_TYPE", "line")
    enable_sound_alerts: bool = os.getenv("ENABLE_SOUND_ALERTS", "true").lower() == "true"
    enable_notifications: bool = os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"


@dataclass
class LogConfig:
    """Logging Configuration."""
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    log_max_bytes: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    enable_console_logging: bool = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"


class Config:
    """Main configuration class."""
    
    deriv = DerivConfig()
    analysis = AnalysisConfig()
    database = DatabaseConfig()
    risk = RiskConfig()
    ui = UIConfig()
    logging = LogConfig()
    
    # Application settings
    app_name: str = "Deriv Matches Predictor"
    app_version: str = "1.0.0-alpha"
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = app_env == "development"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5000"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # API
    api_prefix: str = "/api"
    api_title: str = "Deriv Matches Predictor API"
    api_version: str = app_version
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all configuration."""
        if not cls.deriv.is_valid():
            print("❌ Invalid Deriv configuration. Set DERIV_API_TOKEN and DERIV_APP_ID.")
            return False
        return True
    
    @classmethod
    def get_settings_dict(cls) -> dict:
        """Get all settings as dictionary."""
        return {
            "deriv": {
                "api_endpoint": cls.deriv.api_endpoint,
            },
            "analysis": {
                "tick_windows": cls.analysis.tick_windows,
                "default_tick_window": cls.analysis.default_tick_window,
                "min_sample_size": cls.analysis.min_sample_size,
                "signal_probability_threshold": cls.analysis.signal_probability_threshold,
            },
            "risk": {
                "trading_enabled": cls.risk.trading_enabled,
                "demo_mode_only": cls.risk.demo_mode_only,
                "max_daily_loss": cls.risk.max_daily_loss,
                "max_consecutive_losses": cls.risk.max_consecutive_losses,
            },
            "ui": {
                "theme": cls.ui.theme,
                "enable_sound_alerts": cls.ui.enable_sound_alerts,
            },
            "app": {
                "name": cls.app_name,
                "version": cls.app_version,
                "env": cls.app_env,
            },
        }
