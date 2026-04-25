"""数据模型定义 - 所有模块间传递的结构化数据"""

from dataclasses import dataclass, field


@dataclass
class PredictionResult:
    """预测结果"""
    fund_code: str
    dates: list = field(default_factory=list)          # 预测日期列表 (YYYY-MM-DD)
    values: list = field(default_factory=list)          # 预测净值列表
    upper_bound: list = field(default_factory=list)     # 置信上界列表
    lower_bound: list = field(default_factory=list)     # 置信下界列表
    model_type: str = "MA"                              # 模型类型 ("MA" / "LSTM")
    uncertainty_note: str = "预测值存在不确定性，仅供参考，不构成投资建议"


@dataclass
class BacktestResult:
    """回测结果"""
    fund_code: str
    actual_dates: list = field(default_factory=list)        # 实际日期
    actual_values: list = field(default_factory=list)       # 实际净值
    predicted_values: list = field(default_factory=list)    # 回测预测净值
    mape: float = 0.0                                      # 平均绝对百分比误差
    model_type: str = "MA"


@dataclass
class StrategyAdvice:
    """策略建议"""
    fund_code: str
    action: str = "持有"            # 建议类型 ("买入" / "卖出" / "持有")
    reason: str = ""                # 建议理由 (不超过200字)
    disclaimer: str = "投资有风险，决策需谨慎，本建议不构成投资指导"


@dataclass
class FundInfo:
    """基金基本信息"""
    code: str = ""
    name: str = ""                  # 基金名称
    fund_type: str = ""             # 基金类型
    scale: float = 0.0              # 基金规模 (亿元)
    current_nav: float = 0.0        # 当前净值
    nav_date: str = ""              # 净值日期
