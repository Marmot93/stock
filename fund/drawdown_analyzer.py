import pandas as pd
from .data_fetcher import get_fund_nav_by_date


def analyze_drawdown_strategy(fund_code: str, silent: bool = False):
    """
    分析基金回撤率统计信息，提供买入建议
    :param fund_code: 基金代码
    :param silent: 是否静默模式（不打印输出）
    """
    df = get_fund_nav_by_date(fund_code)
    if df.empty or '单位净值' not in df.columns or '净值日期' not in df.columns:
        print(f"无法分析基金{fund_code}，数据无效。")
        return
    
    # 数据预处理 - 智能日期解析
    try:
        # 尝试作为时间戳解析（毫秒）
        df['净值日期'] = pd.to_datetime(df['净值日期'], unit='ms')
    except ValueError:
        try:
            # 如果失败，尝试直接解析字符串格式日期
            df['净值日期'] = pd.to_datetime(df['净值日期'])
        except Exception as e:
            print(f"日期解析失败: {e}")
            return None
    
    df = df.sort_values('净值日期')
    
    nav = df['单位净值'].astype(float)
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax * 100
    
    
    # 当前回撤率
    current_drawdown = drawdown.iloc[-1]
    
    # 历史回撤统计
    drawdown_stats = {
        '最大回撤': drawdown.min(),
        '平均回撤': drawdown.mean(),
        '回撤标准差': drawdown.std(),
        '5%分位数': drawdown.quantile(0.05),
        '10%分位数': drawdown.quantile(0.10),
        '25%分位数': drawdown.quantile(0.25),
        '50%分位数': drawdown.median(),
        '当前回撤': current_drawdown
    }
    
    # 计算当前回撤的百分位排名
    current_percentile = (drawdown <= current_drawdown).mean() * 100
    
    # 买入建议逻辑
    if current_drawdown <= drawdown_stats['5%分位数']:
        suggestion = "强烈建议买入"
        reason = "当前回撤处于历史最深5%区间，具有很高的投资价值"
        risk_level = "低风险"
    elif current_drawdown <= drawdown_stats['10%分位数']:
        suggestion = "建议买入"
        reason = "当前回撤处于历史较深10%区间，具有较好投资机会"
        risk_level = "较低风险"
    elif current_drawdown <= drawdown_stats['25%分位数']:
        suggestion = "可以考虑买入"
        reason = "当前回撤处于历史中等偏深区间，有一定投资价值"
        risk_level = "中等风险"
    elif current_drawdown > -1:  # 回撤小于1%，接近高点
        suggestion = "谨慎买入"
        reason = "当前净值接近历史高点，建议等待更好的买入时机"
        risk_level = "较高风险"
    else:
        suggestion = "观望"
        reason = "当前回撤水平一般，建议继续观察"
        risk_level = "中等风险"
    
    if not silent:
        print(f"\n=== 基金 {fund_code} 回撤分析 ===")
        print(f"当前回撤率: {current_drawdown:.2f}%")
        print(f"当前回撤百分位: {current_percentile:.1f}% (越低表示回撤越深)")
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