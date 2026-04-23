"""
可视化模块
提供各种图表展示功能
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import seaborn as sns
import os

from config import PLOT_CONFIG, OUTPUT_DIR

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class FundVisualizer:
    """基金数据可视化类"""
    
    def __init__(self):
        self.config = PLOT_CONFIG
        self.output_dir = OUTPUT_DIR
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def plot_nav_history(self, df, fund_code, save=False):
        """
        绘制净值历史走势图
        
        参数:
            df: 包含净值数据的DataFrame
            fund_code: 基金代码
            save: 是否保存图片
            
        返回:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.config['figsize'])
        
        ax.plot(df.index, df['nav'], label='单位净值', linewidth=2, color='#1f77b4')
        if 'accumulated_nav' in df.columns:
            ax.plot(df.index, df['accumulated_nav'], label='累计净值', 
                   linewidth=2, color='#ff7f0e', alpha=0.7)
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('净值', fontsize=12)
        ax.set_title(f'基金 {fund_code} 净值走势', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save:
            filename = os.path.join(self.output_dir, f'{fund_code}_nav_history.png')
            plt.savefig(filename, dpi=self.config['dpi'], bbox_inches='tight')
            print(f"图表已保存: {filename}")
        
        return fig
    
    def plot_technical_indicators(self, df, fund_code, save=False):
        """
        绘制技术指标图表
        
        参数:
            df: 包含技术指标的DataFrame
            fund_code: 基金代码
            save: 是否保存图片
            
        返回:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(4, 1, figsize=(14, 12))
        
        # 子图1: 净值和移动平均线
        ax1 = axes[0]
        ax1.plot(df.index, df['nav'], label='净值', linewidth=2, color='#1f77b4')
        for period in [5, 20, 60]:
            col = f'MA{period}'
            if col in df.columns:
                ax1.plot(df.index, df[col], label=f'MA{period}', 
                        linewidth=1.5, alpha=0.8)
        ax1.set_title('净值与移动平均线', fontsize=12, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 子图2: RSI
        ax2 = axes[1]
        if 'RSI' in df.columns:
            ax2.plot(df.index, df['RSI'], label='RSI', linewidth=2, color='#2ca02c')
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='超买线')
            ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='超卖线')
            ax2.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
        ax2.set_title('相对强弱指标(RSI)', fontsize=12, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 100)
        
        # 子图3: MACD
        ax3 = axes[2]
        if 'MACD' in df.columns:
            ax3.plot(df.index, df['MACD'], label='MACD', linewidth=2, color='#1f77b4')
            ax3.plot(df.index, df['MACD_Signal'], label='信号线', 
                    linewidth=2, color='#ff7f0e')
            if 'MACD_Hist' in df.columns:
                colors = ['#d62728' if x < 0 else '#2ca02c' 
                         for x in df['MACD_Hist']]
                ax3.bar(df.index, df['MACD_Hist'], label='MACD柱', 
                       color=colors, alpha=0.5)
        ax3.set_title('MACD指标', fontsize=12, fontweight='bold')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # 子图4: 布林带
        ax4 = axes[3]
        ax4.plot(df.index, df['nav'], label='净值', linewidth=2, color='#1f77b4')
        if 'BB_Upper' in df.columns:
            ax4.plot(df.index, df['BB_Upper'], label='上轨', 
                    linewidth=1.5, color='#d62728', alpha=0.7)
            ax4.plot(df.index, df['BB_Middle'], label='中轨', 
                    linewidth=1.5, color='#ff7f0e', alpha=0.7)
            ax4.plot(df.index, df['BB_Lower'], label='下轨', 
                    linewidth=1.5, color='#2ca02c', alpha=0.7)
            ax4.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                           alpha=0.1, color='gray')
        ax4.set_title('布林带', fontsize=12, fontweight='bold')
        ax4.legend(loc='best', fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        # 格式化x轴
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.suptitle(f'基金 {fund_code} 技术分析', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save:
            filename = os.path.join(self.output_dir, f'{fund_code}_technical.png')
            plt.savefig(filename, dpi=self.config['dpi'], bbox_inches='tight')
            print(f"图表已保存: {filename}")
        
        return fig
    
    def plot_prediction(self, df, predictions, fund_code, save=False):
        """
        绘制预测结果图表
        
        参数:
            df: 历史数据
            predictions: 预测结果
            fund_code: 基金代码
            save: 是否保存图片
            
        返回:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 子图1: 净值预测
        ax1 = axes[0]
        ax1.plot(df.index, df['nav'], label='历史净值', 
                linewidth=2, color='#1f77b4')
        ax1.plot(predictions.index, predictions['predicted_nav'], 
                label='预测净值', linewidth=2, color='#d62728', linestyle='--')
        
        # 连接历史和预测
        ax1.plot([df.index[-1], predictions.index[0]], 
                [df['nav'].iloc[-1], predictions['predicted_nav'].iloc[0]],
                color='#d62728', linestyle='--', linewidth=2)
        
        ax1.set_title('净值预测', fontsize=12, fontweight='bold')
        ax1.set_xlabel('日期', fontsize=10)
        ax1.set_ylabel('净值', fontsize=10)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 子图2: 收益率预测
        ax2 = axes[1]
        if 'predicted_return' in predictions.columns:
            returns = predictions['predicted_return'].dropna()
            colors = ['#d62728' if x < 0 else '#2ca02c' for x in returns]
            ax2.bar(returns.index, returns, color=colors, alpha=0.7, 
                   label='日收益率')
        
        if 'predicted_cumulative_return' in predictions.columns:
            ax2_twin = ax2.twinx()
            ax2_twin.plot(predictions.index, predictions['predicted_cumulative_return'],
                         label='累计收益率', linewidth=2, color='#ff7f0e')
            ax2_twin.set_ylabel('累计收益率 (%)', fontsize=10)
            ax2_twin.legend(loc='upper right', fontsize=10)
        
        ax2.set_title('收益率预测', fontsize=12, fontweight='bold')
        ax2.set_xlabel('日期', fontsize=10)
        ax2.set_ylabel('日收益率 (%)', fontsize=10)
        ax2.legend(loc='upper left', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # 格式化x轴
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.suptitle(f'基金 {fund_code} 趋势预测', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save:
            filename = os.path.join(self.output_dir, f'{fund_code}_prediction.png')
            plt.savefig(filename, dpi=self.config['dpi'], bbox_inches='tight')
            print(f"图表已保存: {filename}")
        
        return fig
    
    def plot_comparison(self, data_dict, save=False):
        """
        绘制多基金对比图
        
        参数:
            data_dict: {基金代码: DataFrame}
            save: 是否保存图片
            
        返回:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        colors = self.config['color_palette']
        
        # 子图1: 净值对比
        ax1 = axes[0]
        for i, (code, df) in enumerate(data_dict.items()):
            color = colors[i % len(colors)]
            ax1.plot(df.index, df['nav'], label=f'{code}', 
                    linewidth=2, color=color)
        ax1.set_title('净值对比', fontsize=12, fontweight='bold')
        ax1.set_xlabel('日期', fontsize=10)
        ax1.set_ylabel('净值', fontsize=10)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 子图2: 累计收益率对比
        ax2 = axes[1]
        for i, (code, df) in enumerate(data_dict.items()):
            color = colors[i % len(colors)]
            cumulative_return = (df['nav'] / df['nav'].iloc[0] - 1) * 100
            ax2.plot(df.index, cumulative_return, label=f'{code}', 
                    linewidth=2, color=color)
        ax2.set_title('累计收益率对比', fontsize=12, fontweight='bold')
        ax2.set_xlabel('日期', fontsize=10)
        ax2.set_ylabel('累计收益率 (%)', fontsize=10)
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # 格式化x轴
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.suptitle('基金对比分析', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save:
            filename = os.path.join(self.output_dir, 'fund_comparison.png')
            plt.savefig(filename, dpi=self.config['dpi'], bbox_inches='tight')
            print(f"图表已保存: {filename}")
        
        return fig
    
    def plot_signals(self, df, fund_code, save=False):
        """
        绘制交易信号图
        
        参数:
            df: 包含交易信号的DataFrame
            fund_code: 基金代码
            save: 是否保存图片
            
        返回:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.config['figsize'])
        
        # 绘制净值
        ax.plot(df.index, df['nav'], label='净值', linewidth=2, color='#1f77b4')
        
        # 标记买入信号
        buy_signals = df[df['Signal'] == 1]
        if not buy_signals.empty:
            ax.scatter(buy_signals.index, buy_signals['nav'], 
                      marker='^', color='g', s=100, label='买入信号', zorder=5)
        
        # 标记卖出信号
        sell_signals = df[df['Signal'] == -1]
        if not sell_signals.empty:
            ax.scatter(sell_signals.index, sell_signals['nav'], 
                      marker='v', color='r', s=100, label='卖出信号', zorder=5)
        
        ax.set_title(f'基金 {fund_code} 交易信号', fontsize=14, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('净值', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save:
            filename = os.path.join(self.output_dir, f'{fund_code}_signals.png')
            plt.savefig(filename, dpi=self.config['dpi'], bbox_inches='tight')
            print(f"图表已保存: {filename}")
        
        return fig


if __name__ == '__main__':
    # 测试可视化
    from data_fetcher import FundDataFetcher
    from technical_analysis import TechnicalAnalysis
    
    # 获取数据
    fetcher = FundDataFetcher()
    df = fetcher.get_data('000001', days=365)
    
    # 计算技术指标
    ta = TechnicalAnalysis()
    df = ta.calculate_all_indicators(df)
    df = ta.generate_signals(df)
    
    # 可视化
    viz = FundVisualizer()
    
    # 绘制净值历史
    fig1 = viz.plot_nav_history(df, '000001', save=False)
    
    # 绘制技术指标
    fig2 = viz.plot_technical_indicators(df, '000001', save=False)
    
    # 绘制交易信号
    fig3 = viz.plot_signals(df, '000001', save=False)
    
    plt.show()
