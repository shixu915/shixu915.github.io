"""图表生成模块 - 生成可视化图表并支持导出"""

import matplotlib
matplotlib.use('Agg')  # 非交互式后端，避免线程问题

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from pathlib import Path

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

# 图表配置
FIG_WIDTH = 12
FIG_HEIGHT = 6
FIG_DPI = 150


def _setup_chinese_font():
    """配置中文字体支持"""
    import platform
    if platform.system() == 'Windows':
        font_candidates = ['SimHei', 'Microsoft YaHei', 'STSong']
    else:
        font_candidates = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC']

    for font_name in font_candidates:
        try:
            matplotlib.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
            matplotlib.rcParams['axes.unicode_minus'] = False
            # 测试字体是否可用
            fig, ax = plt.subplots()
            ax.set_title("测试")
            plt.close(fig)
            return
        except Exception:
            continue

    logger.warning("未找到合适的中文字体，图表中文可能显示异常")


# 初始化中文字体
_setup_chinese_font()


class FundChartGenerator:
    """基金图表生成器"""

    def generate_trend_chart(
        self,
        history_df: pd.DataFrame,
        prediction_result: PredictionResult,
    ) -> Figure:
        """
        生成历史走势 + 预测趋势图

        Args:
            history_df: 历史数据 DataFrame
            prediction_result: 预测结果

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=FIG_DPI)

        # 历史数据
        hist_dates = pd.to_datetime(history_df["date"])
        hist_nav = history_df["nav"].values
        ax.plot(hist_dates, hist_nav, color="#2196F3", linewidth=1.5, label="历史净值")

        # 预测数据
        if prediction_result.dates and prediction_result.values:
            pred_dates = pd.to_datetime(prediction_result.dates)
            pred_values = prediction_result.values

            # 连接线：从最后一个历史点到第一个预测点
            if len(hist_dates) > 0 and len(pred_dates) > 0:
                ax.plot(
                    [hist_dates.iloc[-1], pred_dates[0]],
                    [hist_nav[-1], pred_values[0]],
                    color="#F44336", linewidth=1, linestyle="--", alpha=0.5,
                )

            ax.plot(pred_dates, pred_values, color="#F44336", linewidth=1.5,
                    linestyle="--", label=f"预测净值 ({prediction_result.model_type})")

            # 置信区间
            if prediction_result.upper_bound and prediction_result.lower_bound:
                ax.fill_between(
                    pred_dates,
                    prediction_result.upper_bound,
                    prediction_result.lower_bound,
                    color="#F44336", alpha=0.15, label="置信区间",
                )

        # 图表装饰
        fund_code = prediction_result.fund_code or "基金"
        ax.set_title(f"{fund_code} - 历史走势与趋势预测", fontsize=14, fontweight="bold")
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("单位净值 (元)", fontsize=11)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        fig.tight_layout()

        # 不确定性标注
        ax.text(
            0.02, 0.02, prediction_result.uncertainty_note,
            transform=ax.transAxes, fontsize=8, color="gray",
            verticalalignment="bottom",
        )

        logger.info("趋势图生成完成")
        return fig

    def generate_backtest_chart(self, backtest_result: BacktestResult) -> Figure:
        """
        生成回测对比图

        Args:
            backtest_result: 回测结果

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=FIG_DPI)

        if backtest_result.actual_dates:
            dates = pd.to_datetime(backtest_result.actual_dates)
            ax.plot(dates, backtest_result.actual_values, color="#2196F3",
                    linewidth=1.5, label="实际净值")
            ax.plot(dates, backtest_result.predicted_values, color="#FF9800",
                    linewidth=1.5, linestyle="--", label="回测预测值")

        fund_code = backtest_result.fund_code or "基金"
        ax.set_title(
            f"{fund_code} - 回测对比 (MAPE: {backtest_result.mape:.2f}%)",
            fontsize=14, fontweight="bold",
        )
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("单位净值 (元)", fontsize=11)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=45)
        fig.tight_layout()

        logger.info("回测对比图生成完成")
        return fig

    def generate_flow_chart(self, fund_info_df: pd.DataFrame) -> Figure:
        """
        生成资金流向图

        Args:
            fund_info_df: 包含日期和规模数据的 DataFrame

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=FIG_DPI)

        if fund_info_df is not None and not fund_info_df.empty and "date" in fund_info_df.columns:
            dates = pd.to_datetime(fund_info_df["date"])

            # 规模变化
            if "scale" in fund_info_df.columns:
                scales = fund_info_df["scale"].values
                ax.plot(dates, scales, color="#4CAF50", linewidth=1.5, label="基金规模 (亿元)")
                ax.fill_between(dates, scales, alpha=0.1, color="#4CAF50")

            # 净值变化（辅助参考）
            if "nav" in fund_info_df.columns:
                ax2 = ax.twinx()
                ax2.plot(dates, fund_info_df["nav"].values, color="#9C27B0",
                         linewidth=1, alpha=0.6, label="净值")
                ax2.set_ylabel("单位净值 (元)", fontsize=11, color="#9C27B0")
                ax2.legend(loc="upper right", fontsize=10)

        ax.set_title("资金流向趋势", fontsize=14, fontweight="bold")
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("基金规模 (亿元)", fontsize=11)
        ax.legend(loc="upper left", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=45)
        fig.tight_layout()

        logger.info("资金流向图生成完成")
        return fig

    def export_chart(self, figure: Figure, filepath: str, format: str = "png") -> bool:
        """
        导出图表为图片文件

        Args:
            figure: matplotlib Figure 对象
            filepath: 导出文件路径
            format: 图片格式 "png" 或 "jpg"

        Returns:
            是否导出成功
        """
        try:
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            figure.savefig(
                str(output_path),
                format=format,
                dpi=FIG_DPI,
                bbox_inches="tight",
                facecolor="white",
            )
            logger.info(f"图表已导出: {output_path}")
            return True
        except Exception as e:
            logger.error(f"图表导出失败: {e}")
            return False
