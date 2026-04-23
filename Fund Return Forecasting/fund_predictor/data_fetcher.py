"""
基金数据获取模块
支持从多个数据源获取基金历史数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from config import DATA_DIR


class FundDataFetcher:
    """基金数据获取器"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        
    def generate_sample_data(self, fund_code, days=365, start_date=None):
        """
        生成模拟的基金历史数据（用于演示）
        实际使用时可以替换为真实数据源API
        
        参数:
            fund_code: 基金代码
            days: 历史数据天数
            start_date: 开始日期
            
        返回:
            DataFrame: 包含日期、净值等数据
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        else:
            start_date = pd.to_datetime(start_date)
            
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        
        # 生成模拟净值数据（随机游走模型）
        np.random.seed(int(fund_code) if fund_code.isdigit() else 42)
        initial_value = np.random.uniform(1.0, 3.0)
        
        # 使用几何布朗运动模拟基金净值
        returns = np.random.normal(0.0005, 0.02, days)  # 日收益率
        values = initial_value * np.exp(np.cumsum(returns))
        
        # 创建DataFrame
        df = pd.DataFrame({
            'date': dates,
            'nav': values,  # 单位净值
            'accumulated_nav': values * 1.1,  # 累计净值（模拟）
            'fund_code': fund_code
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # 保存数据
        self.save_data(df, fund_code)
        
        return df
    
    def save_data(self, df, fund_code):
        """保存数据到本地"""
        filename = os.path.join(self.data_dir, f'{fund_code}.csv')
        df.to_csv(filename, encoding='utf-8-sig')
        print(f"数据已保存到: {filename}")
        
    def load_data(self, fund_code):
        """从本地加载数据"""
        filename = os.path.join(self.data_dir, f'{fund_code}.csv')
        if os.path.exists(filename):
            df = pd.read_csv(filename, index_col='date', parse_dates=True)
            return df
        else:
            print(f"未找到基金 {fund_code} 的数据文件")
            return None
    
    def get_data(self, fund_code, days=365, force_refresh=False):
        """
        获取基金数据
        
        参数:
            fund_code: 基金代码
            days: 历史数据天数
            force_refresh: 是否强制刷新数据
            
        返回:
            DataFrame: 基金历史数据
        """
        if not force_refresh:
            df = self.load_data(fund_code)
            if df is not None:
                return df
        
        # 生成新数据
        return self.generate_sample_data(fund_code, days)
    
    def get_multiple_funds(self, fund_codes, days=365):
        """
        获取多个基金的数据
        
        参数:
            fund_codes: 基金代码列表
            days: 历史数据天数
            
        返回:
            dict: {基金代码: DataFrame}
        """
        data_dict = {}
        for code in fund_codes:
            print(f"正在获取基金 {code} 的数据...")
            data_dict[code] = self.get_data(code, days)
        return data_dict
    
    def calculate_returns(self, df):
        """计算收益率"""
        df = df.copy()
        df['daily_return'] = df['nav'].pct_change()
        df['cumulative_return'] = (df['nav'] / df['nav'].iloc[0] - 1) * 100
        return df


if __name__ == '__main__':
    # 测试数据获取
    fetcher = FundDataFetcher()
    
    # 获取单个基金数据
    df = fetcher.get_data('000001', days=365)
    print("\n基金数据示例:")
    print(df.head())
    
    # 计算收益率
    df = fetcher.calculate_returns(df)
    print("\n收益率数据:")
    print(df[['nav', 'daily_return', 'cumulative_return']].head())
