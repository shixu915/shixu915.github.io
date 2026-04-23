"""
技术分析模块
计算各种技术指标用于趋势分析
"""
import pandas as pd
import numpy as np
from config import INDICATOR_CONFIG


class TechnicalAnalysis:
    """技术分析类"""
    
    def __init__(self):
        self.config = INDICATOR_CONFIG
    
    def calculate_ma(self, df, periods=None):
        """
        计算移动平均线
        
        参数:
            df: 包含净值数据的DataFrame
            periods: 移动平均周期列表
            
        返回:
            DataFrame: 添加了移动平均线的数据
        """
        if periods is None:
            periods = self.config['ma_periods']
            
        df = df.copy()
        for period in periods:
            df[f'MA{period}'] = df['nav'].rolling(window=period).mean()
        
        return df
    
    def calculate_ema(self, df, period=20):
        """计算指数移动平均线"""
        df = df.copy()
        df[f'EMA{period}'] = df['nav'].ewm(span=period, adjust=False).mean()
        return df
    
    def calculate_rsi(self, df, period=None):
        """
        计算相对强弱指标(RSI)
        
        参数:
            df: DataFrame
            period: RSI周期
            
        返回:
            DataFrame: 添加了RSI的数据
        """
        if period is None:
            period = self.config['rsi_period']
            
        df = df.copy()
        
        # 计算价格变化
        delta = df['nav'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 计算RS和RSI
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_macd(self, df, fast=None, slow=None, signal=None):
        """
        计算MACD指标
        
        参数:
            df: DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        返回:
            DataFrame: 添加了MACD的数据
        """
        if fast is None:
            fast = self.config['macd_fast']
        if slow is None:
            slow = self.config['macd_slow']
        if signal is None:
            signal = self.config['macd_signal']
            
        df = df.copy()
        
        # 计算EMA
        ema_fast = df['nav'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['nav'].ewm(span=slow, adjust=False).mean()
        
        # MACD线
        df['MACD'] = ema_fast - ema_slow
        
        # 信号线
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        
        # MACD柱状图
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        return df
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """
        计算布林带
        
        参数:
            df: DataFrame
            period: 周期
            std_dev: 标准差倍数
            
        返回:
            DataFrame: 添加了布林带的数据
        """
        df = df.copy()
        
        # 中轨（移动平均线）
        df['BB_Middle'] = df['nav'].rolling(window=period).mean()
        
        # 标准差
        std = df['nav'].rolling(window=period).std()
        
        # 上轨和下轨
        df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)
        
        return df
    
    def calculate_volatility(self, df, period=20):
        """
        计算波动率
        
        参数:
            df: DataFrame
            period: 周期
            
        返回:
            DataFrame: 添加了波动率的数据
        """
        df = df.copy()
        
        # 计算日收益率
        returns = df['nav'].pct_change()
        
        # 计算滚动标准差（年化）
        df['Volatility'] = returns.rolling(window=period).std() * np.sqrt(252) * 100
        
        return df
    
    def calculate_momentum(self, df, period=10):
        """
        计算动量指标
        
        参数:
            df: DataFrame
            period: 周期
            
        返回:
            DataFrame: 添加了动量的数据
        """
        df = df.copy()
        df['Momentum'] = df['nav'] / df['nav'].shift(period) * 100 - 100
        return df
    
    def calculate_all_indicators(self, df):
        """
        计算所有技术指标
        
        参数:
            df: 原始数据
            
        返回:
            DataFrame: 包含所有指标的数据
        """
        df = df.copy()
        
        # 移动平均线
        df = self.calculate_ma(df)
        
        # RSI
        df = self.calculate_rsi(df)
        
        # MACD
        df = self.calculate_macd(df)
        
        # 布林带
        df = self.calculate_bollinger_bands(df)
        
        # 波动率
        df = self.calculate_volatility(df)
        
        # 动量
        df = self.calculate_momentum(df)
        
        return df
    
    def generate_signals(self, df):
        """
        生成交易信号
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            DataFrame: 添加了交易信号的数据
        """
        df = df.copy()
        df['Signal'] = 0  # 0: 持有, 1: 买入, -1: 卖出
        
        # RSI信号
        rsi_buy = df['RSI'] < 30  # 超卖
        rsi_sell = df['RSI'] > 70  # 超买
        
        # MACD信号
        macd_buy = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        macd_sell = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        # 布林带信号
        bb_buy = df['nav'] < df['BB_Lower']
        bb_sell = df['nav'] > df['BB_Upper']
        
        # 综合信号（多数投票）
        buy_signals = (rsi_buy.astype(int) + macd_buy.astype(int) + bb_buy.astype(int))
        sell_signals = (rsi_sell.astype(int) + macd_sell.astype(int) + bb_sell.astype(int))
        
        df.loc[buy_signals >= 2, 'Signal'] = 1
        df.loc[sell_signals >= 2, 'Signal'] = -1
        
        return df


if __name__ == '__main__':
    # 测试技术分析
    from data_fetcher import FundDataFetcher
    
    # 获取数据
    fetcher = FundDataFetcher()
    df = fetcher.get_data('000001', days=365)
    
    # 计算技术指标
    ta = TechnicalAnalysis()
    df = ta.calculate_all_indicators(df)
    
    # 生成交易信号
    df = ta.generate_signals(df)
    
    print("技术指标计算结果:")
    print(df[['nav', 'MA5', 'MA20', 'RSI', 'MACD', 'Signal']].tail(10))
