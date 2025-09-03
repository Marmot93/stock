import pandas as pd
from datetime import datetime, timedelta
from .data_fetcher import get_stock_price_by_date


def calculate_stock_drawdown(df, stock_code: str = "", silent: bool = False, recent_days: int = None):
    """
    通用的股票回撤计算函数
    :param df: 包含价格数据的DataFrame，必须有'收盘价'和'价格日期'列
    :param stock_code: 股票代码，用于提示信息
    :param silent: 是否静默模式（不打印输出）
    :param recent_days: 如果指定，则只使用最近N天的数据；如果为None则使用所有数据
    :return: (df_to_use, drawdown) 使用的数据和回撤率序列
    """
    if df.empty or '收盘价' not in df.columns or '价格日期' not in df.columns:
        raise ValueError(f"数据无效，缺少必要列")
    
    # 确保日期列为datetime格式
    try:
        # 尝试作为时间戳解析（毫秒）
        df['价格日期'] = pd.to_datetime(df['价格日期'], unit='ms')
    except ValueError:
        try:
            # 如果失败，尝试直接解析字符串格式日期
            df['价格日期'] = pd.to_datetime(df['价格日期'])
        except Exception as e:
            raise ValueError(f"日期解析失败: {e}")
    
    df = df.sort_values('价格日期')
    
    # 如果指定了recent_days，则只取最近N天的数据；否则使用所有数据
    if recent_days is not None:
        df_to_use = df.tail(recent_days)
        if not silent and stock_code:
            print(f"使用股票{stock_code}最近{recent_days}天的数据计算回撤。")
    else:
        df_to_use = df
        if not silent and stock_code:
            print(f"使用股票{stock_code}所有历史数据计算回撤。")
    
    price = df_to_use['收盘价'].astype(float)
    # 计算到当前日期为止的历史最高价格（包括当前日期）
    running_max = price.expanding().max()
    # 回撤率 = (历史最高价格 - 当前价格) / 历史最高价格 * 100%
    drawdown = (running_max - price) / running_max * 100
    
    return df_to_use, drawdown


def analyze_stock_drawdown_strategy(stock_code: str, silent: bool = False, recent_days: int = None):
    """
    分析股票回撤率统计信息，提供买入建议
    :param recent_days:
    :param stock_code: 股票代码
    :param silent: 是否静默模式（不打印输出）
    """
    df = get_stock_price_by_date(stock_code)
    try:
        df_to_use, drawdown = calculate_stock_drawdown(df, stock_code, silent, recent_days)
    except ValueError as e:
        print(f"无法分析股票{stock_code}，{e}")
        return
    
    
    # 当前回撤率
    current_drawdown = drawdown.iloc[-1]
    
    # 历史回撤统计 - 使用非零回撤数据计算分位数
    non_zero_drawdown = drawdown[drawdown > 0]
    zero_ratio = (drawdown == 0).mean()
    
    drawdown_stats = {
        '最大回撤': drawdown.max(),
        '平均回撤': drawdown.mean(),
        '回撤标准差': drawdown.std(),
        '5%分位数': non_zero_drawdown.quantile(0.05) if len(non_zero_drawdown) > 0 else 0.0,
        '10%分位数': non_zero_drawdown.quantile(0.10) if len(non_zero_drawdown) > 0 else 0.0,
        '25%分位数': non_zero_drawdown.quantile(0.25) if len(non_zero_drawdown) > 0 else 0.0,
        '50%分位数': non_zero_drawdown.median() if len(non_zero_drawdown) > 0 else 0.0,
        '75%分位数': non_zero_drawdown.quantile(0.75) if len(non_zero_drawdown) > 0 else 0.0,
        '零回撤比例': zero_ratio * 100,
        '当前回撤': current_drawdown
    }
    
    # 计算当前回撤的百分位排名
    current_percentile = (non_zero_drawdown <= current_drawdown).mean() * 100

    # 买入建议逻辑（百分位越高越值得买入）
    if current_percentile >= 75:
        suggestion = "强烈建议买入"
        reason = "当前回撤处于历史最深25%区间，极具投资价值"
        risk_level = "低风险"
    elif current_percentile >= 50:
        suggestion = "建议买入"
        reason = "当前回撤处于历史较深50%区间，具有较好投资机会"
        risk_level = "较低风险"
    elif 15 < current_percentile <= 30:
        suggestion = "可以考虑买入"
        reason = "当前回撤处于历史中等偏深区间，有一定投资价值"
        risk_level = "中等风险"
    elif 0 <  current_percentile <= 15:  # 百分位很低，接近高点
        suggestion = "观望"
        reason = "当前回撤水平一般，建议继续观察"
        risk_level = "中等风险"
    else: # current_percentile == 0，当前无回撤
        suggestion = "不建议买入"
        reason = "当前价格处于历史高点，无回撤空间"
        risk_level = "高风险"

    
    if not silent:
        print(f"\n=== 股票 {stock_code} 回撤分析 ===")
        print(f"当前回撤率: {current_drawdown:.2f}%")
        print(f"当前回撤百分位: {current_percentile:.1f}% (越高表示回撤越大)")
        print(f"\n历史回撤统计:")
        for key, value in drawdown_stats.items():
            print(f"  {key}: {value:.2f}%")
        print(f"\n=== 买入建议 ===")
        print(f"建议: {suggestion}")
        print(f"理由: {reason}")
        print(f"风险评估: {risk_level}")
    
    return {
        'current_drawdown': current_drawdown,
        'current_percentile': current_percentile,
        'suggestion': suggestion,
        'risk_level': risk_level,
        'reason': reason,
        'stats': drawdown_stats
    }