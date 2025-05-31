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
    
    # 多信号投票策略配置
    VOTING_STRATEGIES: Dict[str, List[Dict]] = None
    
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
        
        if self.VOTING_STRATEGIES is None:
            self.VOTING_STRATEGIES = {
                'value_growth': [
                    {
                        'indicator': 'long_loan_newadded_MA12_yoy',
                        'signal_type': 'exceed_expectation',
                        'parameter_n': 3,
                        'assumed_direction': -1,
                        'combination_id': 'long_loan_newadded_MA12_yoy_exceed_expectation_3_-1',
                        'description': '中长期贷款增量(MA12)当月同比超预期3月-1方向'
                    },
                    {
                        'indicator': 'M2_M1',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'M2_M1_historical_new_high_3_1',
                        'description': 'M2-M1历史新高3月1方向'
                    },
                    {
                        'indicator': 'newstarts_area_yoy',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'newstarts_area_yoy_historical_new_high_3_1',
                        'description': '房屋新开工面积当月同比历史新高3月1方向'
                    },
                    {
                        'indicator': 'CPI_PPI',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 6,
                        'assumed_direction': -1,
                        'combination_id': 'CPI_PPI_historical_new_high_6_-1',
                        'description': 'CPI-PPI历史新高6月-1方向'
                    },
                    {
                        'indicator': 'US_BOND_5Y',
                        'signal_type': 'exceed_expectation',
                        'parameter_n': 12,
                        'assumed_direction': 1,
                        'combination_id': 'US_BOND_5Y_exceed_expectation_12_1',
                        'description': '美国5年期国债收益率超预期12月1方向'
                    },
                    {
                        'indicator': 'TSF_newadded_MA12_yoy',
                        'signal_type': 'historical_high',
                        'parameter_n': 12,
                        'assumed_direction': -1,
                        'combination_id': 'TSF_newadded_MA12_yoy_historical_high_12_-1',
                        'description': '社融规模增量(MA12)当月同比历史高位12月-1方向'
                    },
                    {
                        'indicator': 'US_BOND_10Y',
                        'signal_type': 'exceed_expectation',
                        'parameter_n': 12,
                        'assumed_direction': 1,
                        'combination_id': 'US_BOND_10Y_exceed_expectation_12_1',
                        'description': '美国10年期国债收益率超预期12月1方向'
                    },
                    {
                        'indicator': 'fixedasset_investment_yoy',
                        'signal_type': 'exceed_expectation',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'fixedasset_investment_yoy_exceed_expectation_3_1',
                        'description': '固定资产投资完成额当月同比超预期3月1方向'
                    },
                    {
                        'indicator': 'M1',
                        'signal_type': 'exceed_expectation',
                        'parameter_n': 9,
                        'assumed_direction': -1,
                        'combination_id': 'M1_exceed_expectation_9_-1',
                        'description': 'M1超预期9月-1方向'
                    },
                    {
                        'indicator': 'M2',
                        'signal_type': 'historical_high',
                        'parameter_n': 12,
                        'assumed_direction': -1,
                        'combination_id': 'M2_historical_high_12_-1',
                        'description': 'M2历史高位12月-1方向'
                    },
                    {
                        'indicator': 'pmi_manufacturing_neworder',
                        'signal_type': 'historical_new_low',
                        'parameter_n': 6,
                        'assumed_direction': 1,
                        'combination_id': 'pmi_manufacturing_neworder_historical_new_low_6_1',
                        'description': '制造业PMI新订单历史新低6月1方向'
                    }
                ],
                'big_small': [
                    {
                        'indicator': 'local_gov_budget_MA12_yoy',
                        'signal_type': 'historical_high',
                        'parameter_n': 6,
                        'assumed_direction': 1,
                        'combination_id': 'local_gov_budget_MA12_yoy_historical_high_6_1',
                        'description': '地方政府预算收入(MA12)当月同比历史高位6月1方向'
                    },
                    {
                        'indicator': 'pmi_manufacturing_neworder',
                        'signal_type': 'historical_new_low',
                        'parameter_n': 6,
                        'assumed_direction': 1,
                        'combination_id': 'pmi_manufacturing_neworder_historical_new_low_6_1',
                        'description': '制造业PMI新订单历史新低6月1方向'
                    },
                    {
                        'indicator': 'pmi_manufacturing',
                        'signal_type': 'historical_high',
                        'parameter_n': 6,
                        'assumed_direction': 1,
                        'combination_id': 'pmi_manufacturing_historical_high_6_1',
                        'description': '制造业PMI历史高位6月1方向'
                    },
                    {
                        'indicator': 'completed_yoy',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': -1,
                        'combination_id': 'completed_yoy_historical_new_high_3_-1',
                        'description': '房屋竣工面积当月同比历史新高3月-1方向'
                    },
                    {
                        'indicator': 'CN_BOND_1Y',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'CN_BOND_1Y_historical_new_high_3_1',
                        'description': '中国1年期国债收益率历史新高3月1方向'
                    },
                    {
                        'indicator': 'PPI',
                        'signal_type': 'historical_new_low',
                        'parameter_n': 9,
                        'assumed_direction': 1,
                        'combination_id': 'PPI_historical_new_low_9_1',
                        'description': 'PPI历史新低9月1方向'
                    },
                    {
                        'indicator': 'newstarts_area_yoy',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'newstarts_area_yoy_historical_new_high_3_1',
                        'description': '房屋新开工面积当月同比历史新高3月1方向'
                    },
                    {
                        'indicator': 'CPI_PPI',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 6,
                        'assumed_direction': -1,
                        'combination_id': 'CPI_PPI_historical_new_high_6_-1',
                        'description': 'CPI-PPI历史新高6月-1方向'
                    },
                    {
                        'indicator': 'core_CPI_PPI',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 9,
                        'assumed_direction': -1,
                        'combination_id': 'core_CPI_PPI_historical_new_high_9_-1',
                        'description': '核心CPI-PPI历史新高9月-1方向'
                    },
                    {
                        'indicator': 'fixedasset_investment_ytd_yoy',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': 1,
                        'combination_id': 'fixedasset_investment_ytd_yoy_historical_new_high_3_1',
                        'description': '固定资产投资累计同比历史新高3月1方向'
                    },
                    {
                        'indicator': 'TSF_yoy',
                        'signal_type': 'historical_new_high',
                        'parameter_n': 3,
                        'assumed_direction': -1,
                        'combination_id': 'TSF_yoy_historical_new_high_3_-1',
                        'description': '社融存量同比历史新高3月-1方向'
                    }
                ]
            }
    
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
    
    def get_voting_strategy_signals(self, strategy_type: str) -> List[Dict]:
        """获取多信号投票策略的信号配置"""
        return self.VOTING_STRATEGIES.get(strategy_type, [])
    
    def get_voting_strategy_indicators(self, strategy_type: str) -> List[str]:
        """获取多信号投票策略使用的指标列表"""
        signals = self.get_voting_strategy_signals(strategy_type)
        return list(set([signal['indicator'] for signal in signals]))
    
    def get_all_voting_indicators(self) -> List[str]:
        """获取所有投票策略使用的指标列表"""
        all_indicators = []
        for strategy_signals in self.VOTING_STRATEGIES.values():
            for signal in strategy_signals:
                all_indicators.append(signal['indicator'])
        return list(set(all_indicators))
    
    def add_voting_signal(self, strategy_type: str, signal_config: Dict) -> None:
        """添加新的投票信号配置"""
        if strategy_type not in self.VOTING_STRATEGIES:
            self.VOTING_STRATEGIES[strategy_type] = []
        
        # 验证信号配置的必要字段
        required_fields = ['indicator', 'signal_type', 'parameter_n', 'assumed_direction']
        for field in required_fields:
            if field not in signal_config:
                raise ValueError(f"信号配置缺少必要字段: {field}")
        
        # 自动生成combination_id如果未提供
        if 'combination_id' not in signal_config:
            signal_config['combination_id'] = f"{signal_config['indicator']}_{signal_config['signal_type']}_{signal_config['parameter_n']}_{signal_config['assumed_direction']}"
        
        self.VOTING_STRATEGIES[strategy_type].append(signal_config)
    
    def remove_voting_signal(self, strategy_type: str, combination_id: str) -> bool:
        """移除指定的投票信号配置"""
        if strategy_type not in self.VOTING_STRATEGIES:
            return False
        
        original_length = len(self.VOTING_STRATEGIES[strategy_type])
        self.VOTING_STRATEGIES[strategy_type] = [
            signal for signal in self.VOTING_STRATEGIES[strategy_type]
            if signal.get('combination_id') != combination_id
        ]
        
        return len(self.VOTING_STRATEGIES[strategy_type]) < original_length
    
    def update_voting_signal(self, strategy_type: str, combination_id: str, updates: Dict) -> bool:
        """更新指定的投票信号配置"""
        if strategy_type not in self.VOTING_STRATEGIES:
            return False
        
        for signal in self.VOTING_STRATEGIES[strategy_type]:
            if signal.get('combination_id') == combination_id:
                signal.update(updates)
                return True
        
        return False
    
    def get_top_n_voting_signals(self, strategy_type: str, n: int) -> List[Dict]:
        """
        获取策略的前N个投票信号（用于敏感性测试）
        
        参数:
            strategy_type: 策略类型 ('value_growth' 或 'big_small')
            n: 需要获取的信号数量
            
        返回:
            前N个信号配置的列表
        """
        all_signals = self.get_voting_strategy_signals(strategy_type)
        return all_signals[:n] if n <= len(all_signals) else all_signals
    
    def get_signal_ranking_info(self, strategy_type: str) -> Dict:
        """
        获取信号排序信息
        
        参数:
            strategy_type: 策略类型
            
        返回:
            包含信号排序信息的字典
        """
        signals = self.get_voting_strategy_signals(strategy_type)
        
        ranking_info = {
            'total_signals': len(signals),
            'signal_order': [],
            'indicator_order': []
        }
        
        for i, signal in enumerate(signals, 1):
            ranking_info['signal_order'].append({
                'rank': i,
                'combination_id': signal['combination_id'],
                'indicator': signal['indicator'],
                'signal_type': signal['signal_type'],
                'parameter_n': signal['parameter_n'],
                'assumed_direction': signal['assumed_direction'],
                'description': signal.get('description', '')
            })
            ranking_info['indicator_order'].append(signal['indicator'])
        
        return ranking_info 