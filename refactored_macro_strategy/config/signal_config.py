"""
信号生成配置
Signal generation configuration
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class SignalConfig:
    """信号生成配置类"""
    
    # 默认信号参数
    DEFAULT_SIGNAL_PARAMS: Dict[str, int] = None
    
    # 测试参数范围
    TEST_PARAMS: Dict[str, List[int]] = None
    
    # 指标分类
    INDICATOR_CATEGORIES: Dict[str, List[str]] = None
    
    # 信号类型列表
    SIGNAL_TYPES: List[str] = None
    
    def __post_init__(self):
        if self.DEFAULT_SIGNAL_PARAMS is None:
            self.DEFAULT_SIGNAL_PARAMS = {
                'historical_high': 12,
                'marginal_improvement': 3,
                'exceed_expectation': 12,
                'historical_new_high': 12,
                'historical_new_low': 12
            }
        
        if self.TEST_PARAMS is None:
            self.TEST_PARAMS = {
                'historical_high': [3, 6, 9, 12, 24, 36],
                'marginal_improvement': [3, 6, 9],
                'exceed_expectation': [3, 6, 9, 12, 24, 36],
                'historical_new_high': [3, 6, 9, 12, 24, 36],
                'historical_new_low': [3, 6, 9, 12, 24, 36]
            }
        
        if self.INDICATOR_CATEGORIES is None:
            self.INDICATOR_CATEGORIES = {
                '实体经济': [
                    'electricity_yoy', 'electricity_ytd_yoy', 'industrial_value_added_yoy',
                    'fixed_asset_investment_yoy', 'retail_sales_yoy', 'export_yoy', 'import_yoy'
                ],
                '价格指标': ['CPI_yoy', 'PPI_yoy', 'house_price_yoy'],
                '货币金融': ['M1_yoy', 'M2_yoy', 'social_financing_yoy', 'DR007', 'CREDIT_SPREAD'],
                '外部环境': ['USD_INDEX', 'oil_price', 'copper_price'],
                '股市指标': ['CSI300', 'CSI500', 'CHINEXT']
            }
        
        if self.SIGNAL_TYPES is None:
            self.SIGNAL_TYPES = [
                'historical_high', 'marginal_improvement', 'exceed_expectation',
                'historical_new_high', 'historical_new_low'
            ]
    
    def get_signal_weights(self) -> Dict[str, float]:
        """获取信号权重配置"""
        return {
            'historical_high': 0.2,
            'marginal_improvement': 0.25,
            'exceed_expectation': 0.25,
            'historical_new_high': 0.15,
            'historical_new_low': -0.15  # 负权重，因为新低是负面信号
        }
    
    def get_indicators_by_category(self, category: str) -> List[str]:
        """根据分类获取指标列表"""
        return self.INDICATOR_CATEGORIES.get(category, [])
    
    def get_all_indicators(self) -> List[str]:
        """获取所有指标列表"""
        all_indicators = []
        for indicators in self.INDICATOR_CATEGORIES.values():
            all_indicators.extend(indicators)
        return all_indicators 