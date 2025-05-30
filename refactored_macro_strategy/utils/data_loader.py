"""
数据加载工具
Data loading utilities
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import os


def read_clean_data(file_path: str, sheet_name: str, skiprows: int, nrows: int):
    """辅助函数：按照processed.py的方式读取和清理数据"""
    return (
        pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows, nrows=nrows)
        .rename(columns={'日期': 'Date'})
        .set_index('Date')
        .sort_index()
    )


def load_all_data(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    加载所有必要的数据 - 参考main_workflow.py的实现
    
    参数:
        file_path: Excel文件路径
        
    返回:
        包含所有数据的字典，键名与StabilityWorkflow兼容
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    
    print(f"正在加载数据: {file_path}")
    
    try:
        # 读取各个工作表
        with pd.ExcelFile(file_path) as excel_file:
            # 检查工作表名称
            sheet_names = excel_file.sheet_names
            print(f"发现工作表: {sheet_names}")
            
            # 1. 读取memo数据 (指标元数据)
            memo_df = None
            try:
                memo_raw = pd.read_excel(excel_file, sheet_name='Memo')
                memo_df = memo_raw.rename(columns={
                    '指标_EN': 'index', 
                    '分类': 'categories', 
                    '方向': 'direction'
                })
                idx_need = memo_df['index'].tolist()
                print(f"Memo数据加载成功: {memo_df.shape}, 需要的指标数量: {len(idx_need)}")
            except Exception as e:
                print(f"警告: 无法加载Memo数据: {e}")
                idx_need = None
            
            # 2. 读取宏观指标数据
            try:
                macro_data = read_clean_data(file_path, 'CLEAN_MACRO', skiprows=3, nrows=250)
                print(f"CLEAN_MACRO工作表加载成功: {macro_data.shape}")
            except Exception as e:
                print(f"警告: 无法加载CLEAN_MACRO工作表: {e}")
                macro_data = pd.DataFrame()
            
            # 3. 读取利率数据
            try:
                rate_data = read_clean_data(file_path, 'CLEAN_RATE', skiprows=0, nrows=250)
                print(f"CLEAN_RATE工作表加载成功: {rate_data.shape}")
            except Exception as e:
                print(f"警告: 无法加载CLEAN_RATE工作表: {e}")
                rate_data = pd.DataFrame()
            
            # 4. 合并宏观指标和利率数据
            if not macro_data.empty and not rate_data.empty:
                data_combined = pd.concat([macro_data, rate_data], axis=1)
            elif not macro_data.empty:
                data_combined = macro_data
            elif not rate_data.empty:
                data_combined = rate_data
            else:
                raise ValueError("无法加载任何宏观指标或利率数据")
            
            # 5. 根据memo筛选需要的指标
            if idx_need is not None:
                # 筛选存在于数据中的指标
                available_indicators = [idx for idx in idx_need if idx in data_combined.columns]
                if available_indicators:
                    final_macro_data = data_combined[available_indicators].ffill()
                    print(f"按memo筛选指标: {len(available_indicators)}/{len(idx_need)} 个指标可用")
                else:
                    print("警告: memo中的指标在数据中都不存在，使用所有可用指标")
                    final_macro_data = data_combined.ffill()
            else:
                final_macro_data = data_combined.ffill()
            
            # 6. 读取价格数据 (CLOSE工作表)
            try:
                price_data = (
                    pd.read_excel(file_path, sheet_name='CLOSE', skiprows=3)
                    .rename(columns={
                        '时间': 'Date',
                        '300收益': 'BigR', 
                        '中证1000全收益': 'SmallR',
                        '创成长R': 'GrowthR', 
                        '国信价值全收益': 'ValueR'
                    })
                    .set_index('Date')
                    .sort_index()
                )
                
                # 确保有ValueR和GrowthR列
                if 'ValueR' not in price_data.columns or 'GrowthR' not in price_data.columns:
                    raise ValueError("价格数据缺少必要的ValueR或GrowthR列")
                
                print(f"价格数据加载成功: {price_data.shape}")
                
            except Exception as e:
                raise ValueError(f"无法加载价格数据 (CLOSE工作表): {e}")
            
            print(f"数据加载完成:")
            print(f"  宏观指标数据: {final_macro_data.shape}")
            print(f"  价格数据: {price_data.shape}")
            print(f"  memo数据: {'可用' if memo_df is not None else '不可用'}")
            
            # 返回与StabilityWorkflow兼容的键名
            return {
                'indicator_data': final_macro_data,  # 兼容StabilityWorkflow
                'price_data': price_data,           # 兼容StabilityWorkflow
                'memo_data': memo_df,               # 兼容StabilityWorkflow
                'final_macro': final_macro_data,    # 保持向后兼容
                'price': price_data,                # 保持向后兼容
                'memo': memo_df                     # 保持向后兼容
            }
            
    except Exception as e:
        print(f"数据加载失败: {e}")
        raise


def load_specific_sheets(file_path: str, sheet_names: list) -> Dict[str, pd.DataFrame]:
    """
    加载指定的工作表
    
    参数:
        file_path: Excel文件路径
        sheet_names: 工作表名称列表
        
    返回:
        包含指定工作表数据的字典
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    
    data_dict = {}
    
    with pd.ExcelFile(file_path) as excel_file:
        for sheet_name in sheet_names:
            if sheet_name in excel_file.sheet_names:
                try:
                    data_dict[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
                except Exception as e:
                    print(f"警告: 无法加载工作表 {sheet_name}: {e}")
            else:
                print(f"警告: 工作表 {sheet_name} 不存在")
    
    return data_dict


def save_data_to_excel(data_dict: Dict[str, pd.DataFrame], output_path: str):
    """
    将数据字典保存到Excel文件
    
    参数:
        data_dict: 数据字典
        output_path: 输出文件路径
    """
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name)
        print(f"数据已保存到: {output_path}")
    except Exception as e:
        print(f"保存数据失败: {e}")
        raise


def create_default_memo_data(indicators: list) -> pd.DataFrame:
    """
    为指标列表创建默认的memo数据
    
    参数:
        indicators: 指标名称列表
        
    返回:
        默认memo DataFrame
    """
    memo_data = {
        'index': indicators,
        'categories': ['未分类'] * len(indicators),
        'direction': [1] * len(indicators)  # 默认方向为正
    }
    
    return pd.DataFrame(memo_data)


def align_data(macro_data: pd.DataFrame, price_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    对齐宏观数据和价格数据的时间索引
    
    参数:
        macro_data: 宏观指标数据
        price_data: 价格数据
        
    返回:
        对齐后的数据元组
    """
    # 找到共同的时间索引
    common_index = macro_data.index.intersection(price_data.index)
    
    if len(common_index) == 0:
        raise ValueError("宏观数据和价格数据没有共同的时间索引")
    
    # 对齐数据
    aligned_macro = macro_data.loc[common_index].sort_index()
    aligned_price = price_data.loc[common_index].sort_index()
    
    print(f"数据对齐完成: 共同时间点 {len(common_index)} 个")
    
    return aligned_macro, aligned_price


def validate_data_quality(data: pd.DataFrame, min_valid_ratio: float = 0.7) -> bool:
    """
    验证数据质量
    
    参数:
        data: 待验证的数据
        min_valid_ratio: 最小有效数据比例
        
    返回:
        数据质量是否合格
    """
    if data.empty:
        print("数据为空")
        return False
    
    # 计算有效数据比例
    valid_ratio = (1 - data.isnull().sum() / len(data)).mean()
    
    if valid_ratio < min_valid_ratio:
        print(f"数据质量不合格: 有效数据比例 {valid_ratio:.2%} < {min_valid_ratio:.2%}")
        return False
    
    print(f"数据质量验证通过: 有效数据比例 {valid_ratio:.2%}")
    return True 