"""
基金收益趋势预测工具 - 主程序
提供命令行交互界面
"""
import argparse
import pandas as pd
from datetime import datetime

from config import PREDICTION_CONFIG
from data_fetcher import FundDataFetcher
from technical_analysis import TechnicalAnalysis
from predictor import FundPredictor, SimplePredictor
from visualizer import FundVisualizer


class FundAnalysisApp:
    """基金分析应用主类"""
    
    def __init__(self):
        self.fetcher = FundDataFetcher()
        self.ta = TechnicalAnalysis()
        self.predictor = FundPredictor()
        self.simple_predictor = SimplePredictor()
        self.visualizer = FundVisualizer()
        
    def analyze_fund(self, fund_code, days=365, show_plots=True, save_plots=False):
        """
        分析单个基金
        
        参数:
            fund_code: 基金代码
            days: 历史数据天数
            show_plots: 是否显示图表
            save_plots: 是否保存图表
        """
        print(f"\n{'='*60}")
        print(f"基金 {fund_code} 分析报告")
        print(f"{'='*60}\n")
        
        # 1. 获取数据
        print("1. 获取历史数据...")
        df = self.fetcher.get_data(fund_code, days=days)
        df = self.fetcher.calculate_returns(df)
        print(f"   数据时间范围: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   数据天数: {len(df)}")
        
        # 2. 技术分析
        print("\n2. 计算技术指标...")
        df = self.ta.calculate_all_indicators(df)
        df = self.ta.generate_signals(df)
        
        # 显示最新指标
        latest = df.iloc[-1]
        print(f"   最新净值: {latest['nav']:.4f}")
        print(f"   MA5: {latest['MA5']:.4f}, MA20: {latest['MA20']:.4f}, MA60: {latest['MA60']:.4f}")
        print(f"   RSI: {latest['RSI']:.2f}")
        print(f"   MACD: {latest['MACD']:.4f}")
        
        # 3. 趋势预测
        print("\n3. 训练预测模型...")
        self.predictor.train(df, model_type='rf')
        
        print("\n4. 预测未来趋势...")
        predictions = self.predictor.predict(df, days=30)
        
        # 评估趋势
        evaluation = self.predictor.evaluate_trend(df, predictions)
        print(f"\n趋势预测结果:")
        print(f"   当前净值: {evaluation['current_nav']:.4f}")
        print(f"   预测净值(30天后): {evaluation['predicted_nav']:.4f}")
        print(f"   预测趋势: {evaluation['trend']}")
        print(f"   预期变化: {evaluation['change_pct']:.2f}%")
        print(f"   趋势强度: {evaluation['trend_strength']:.1f}%")
        
        # 4. 可视化
        if show_plots or save_plots:
            print("\n5. 生成可视化图表...")
            self.visualizer.plot_nav_history(df, fund_code, save=save_plots)
            self.visualizer.plot_technical_indicators(df, fund_code, save=save_plots)
            self.visualizer.plot_prediction(df, predictions, fund_code, save=save_plots)
            self.visualizer.plot_signals(df, fund_code, save=save_plots)
            
            if show_plots:
                import matplotlib.pyplot as plt
                plt.show()
        
        return df, predictions, evaluation
    
    def compare_funds(self, fund_codes, days=365, show_plots=True, save_plots=False):
        """
        对比多个基金
        
        参数:
            fund_codes: 基金代码列表
            days: 历史数据天数
            show_plots: 是否显示图表
            save_plots: 是否保存图表
        """
        print(f"\n{'='*60}")
        print(f"基金对比分析")
        print(f"{'='*60}\n")
        
        # 获取所有基金数据
        data_dict = self.fetcher.get_multiple_funds(fund_codes, days=days)
        
        # 计算统计数据
        print("\n基金表现统计:")
        print(f"{'基金代码':<10} {'最新净值':<12} {'累计收益率':<12} {'年化收益率':<12}")
        print("-" * 50)
        
        for code, df in data_dict.items():
            latest = df.iloc[-1]
            cumulative_return = (latest['nav'] / df.iloc[0]['nav'] - 1) * 100
            annual_return = cumulative_return * 252 / len(df)
            
            print(f"{code:<10} {latest['nav']:<12.4f} {cumulative_return:<12.2f}% {annual_return:<12.2f}%")
        
        # 可视化对比
        if show_plots or save_plots:
            print("\n生成对比图表...")
            self.visualizer.plot_comparison(data_dict, save=save_plots)
            
            if show_plots:
                import matplotlib.pyplot as plt
                plt.show()
        
        return data_dict
    
    def quick_predict(self, fund_code, days=30):
        """
        快速预测（使用简单模型）
        
        参数:
            fund_code: 基金代码
            days: 预测天数
        """
        print(f"\n{'='*60}")
        print(f"基金 {fund_code} 快速预测")
        print(f"{'='*60}\n")
        
        # 获取数据
        df = self.fetcher.get_data(fund_code, days=365)
        
        # 使用简单预测器
        predictions_ma = self.simple_predictor.predict_by_ma(df, days=days)
        predictions_reg = self.simple_predictor.predict_by_regression(df, days=days)
        
        # 显示结果
        print(f"当前净值: {df['nav'].iloc[-1]:.4f}")
        print(f"\n移动平均预测 ({days}天后): {predictions_ma['predicted_nav'].iloc[-1]:.4f}")
        print(f"线性回归预测 ({days}天后): {predictions_reg['predicted_nav'].iloc[-1]:.4f}")
        
        return predictions_ma, predictions_reg


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='基金收益趋势预测工具')
    parser.add_argument('fund_codes', nargs='+', help='基金代码（可多个）')
    parser.add_argument('--days', type=int, default=365, help='历史数据天数（默认365天）')
    parser.add_argument('--predict-days', type=int, default=30, help='预测天数（默认30天）')
    parser.add_argument('--no-plots', action='store_true', help='不显示图表')
    parser.add_argument('--save-plots', action='store_true', help='保存图表到文件')
    parser.add_argument('--compare', action='store_true', help='对比模式（多个基金）')
    parser.add_argument('--quick', action='store_true', help='快速预测模式')
    
    args = parser.parse_args()
    
    app = FundAnalysisApp()
    
    try:
        if args.quick:
            # 快速预测模式
            for code in args.fund_codes:
                app.quick_predict(code, days=args.predict_days)
        
        elif args.compare and len(args.fund_codes) > 1:
            # 对比模式
            app.compare_funds(
                args.fund_codes,
                days=args.days,
                show_plots=not args.no_plots,
                save_plots=args.save_plots
            )
        
        else:
            # 单基金分析模式
            for code in args.fund_codes:
                app.analyze_fund(
                    code,
                    days=args.days,
                    show_plots=not args.no_plots,
                    save_plots=args.save_plots
                )
    
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 如果没有命令行参数，运行交互模式
    import sys
    if len(sys.argv) == 1:
        print("\n" + "="*60)
        print("基金收益趋势预测工具")
        print("="*60)
        print("\n使用示例:")
        print("  python main.py 000001                    # 分析单个基金")
        print("  python main.py 000001 000002 --compare   # 对比多个基金")
        print("  python main.py 000001 --quick            # 快速预测")
        print("  python main.py 000001 --days 180         # 使用180天历史数据")
        print("  python main.py 000001 --save-plots       # 保存图表到文件")
        print("\n现在运行演示模式...\n")
        
        # 演示模式
        app = FundAnalysisApp()
        app.analyze_fund('000001', days=365, show_plots=False, save_plots=True)
    else:
        main()
