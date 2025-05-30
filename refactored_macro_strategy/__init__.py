"""
重构后的宏观策略系统
Refactored macro strategy system

一个精简、模块化的宏观指标信号生成和回测系统
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"

# 公开主要的接口
from .workflows import MainWorkflow
from .config import SignalConfig, BacktestConfig, ExportConfig

__all__ = [
    'MainWorkflow',
    'SignalConfig', 
    'BacktestConfig',
    'ExportConfig'
] 