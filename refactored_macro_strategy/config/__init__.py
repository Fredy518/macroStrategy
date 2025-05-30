"""
重构后的宏观策略配置模块
Configuration module for refactored macro strategy
"""

from .signal_config import SignalConfig
from .backtest_config import BacktestConfig
from .export_config import ExportConfig

__all__ = ['SignalConfig', 'BacktestConfig', 'ExportConfig'] 