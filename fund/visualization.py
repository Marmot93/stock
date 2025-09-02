import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from .data_fetcher import get_fund_nav_by_date, update_fund_mapping
from .drawdown_analyzer import calculate_fund_drawdown, analyze_drawdown_strategy

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_drawdown_hist(fund_code: str, recent_days: int = None, show_percentiles: bool = True):
    """
    获取基金净值并绘制回撤率与日期的折线图
    :param fund_code: 基金代码
    :param recent_days: 使用最近多少天的数据，默认365天
    :param show_percentiles: 是否显示百分位线
    """
    df = get_fund_nav_by_date(fund_code)
    try:
        df_to_use, drawdown = calculate_fund_drawdown(df, fund_code, recent_days=recent_days)
    except ValueError as e:
        print(f"无法绘制基金{fund_code}的回撤图，{e}")
        return
    
    # 获取基金名称
    fund_name = update_fund_mapping(fund_code)
    title = f"基金{fund_code}回撤率时间序列图"
    if fund_name and fund_name != fund_code:
        title = f"{fund_name}({fund_code})回撤率时间序列图"
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_to_use['净值日期'], drawdown, linewidth=1.5, color='red', label='回撤率')
    plt.fill_between(df_to_use['净值日期'], drawdown, 0, alpha=0.3, color='red')
    
    # 添加百分位线
    if show_percentiles:
        percentiles = [10, 25, 50, 75, 90]
        colors = ['orange', 'green', 'blue', 'purple', 'brown']
        
        for i, p in enumerate(percentiles):
            p_value = np.percentile(drawdown, p)
            plt.axhline(y=p_value, color=colors[i], linestyle='--', alpha=0.7, 
                       label=f'{p}%百分位: {p_value:.2f}%')
    
    # 获取策略分析结果
    strategy_result = analyze_drawdown_strategy(fund_code, silent=True, recent_days=recent_days)
    
    # 在右上角显示当前日期、回撤率和策略建议
    current_date = df_to_use['净值日期'].iloc[-1].strftime('%Y-%m-%d')
    current_drawdown = drawdown.iloc[-1]
    
    info_text = f'当前日期: {current_date}\n当前回撤: {current_drawdown:.2f}%\n\n'
    info_text += f'建议: {strategy_result["suggestion"]}\n'
    info_text += f'理由: {strategy_result["reason"]}\n'
    info_text += f'风险评估: {strategy_result["risk_level"]}'
    
    plt.text(0.98, 0.95, info_text, transform=plt.gca().transAxes, 
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             fontsize=9)
    
    plt.title(title)
    plt.xlabel("日期")
    plt.ylabel("回撤率 (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.show()