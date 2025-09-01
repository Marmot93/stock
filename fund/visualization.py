import matplotlib.pyplot as plt
import pandas as pd
from .data_fetcher import get_fund_nav_by_date, update_fund_mapping
from .drawdown_analyzer import calculate_fund_drawdown

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_drawdown_hist(fund_code: str, recent_days: int = None):
    """
    获取基金净值并绘制回撤率与日期的折线图
    :param fund_code: 基金代码
    :param recent_days: 使用最近多少天的数据，默认365天
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
    plt.plot(df_to_use['净值日期'], drawdown, linewidth=1.5, color='red')
    plt.fill_between(df_to_use['净值日期'], drawdown, 0, alpha=0.3, color='red')
    plt.title(title)
    plt.xlabel("日期")
    plt.ylabel("回撤率 (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()