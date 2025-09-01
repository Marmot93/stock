import matplotlib.pyplot as plt
import pandas as pd
from .data_fetcher import get_fund_nav_by_date

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_drawdown_hist(fund_code: str):
    """
    获取基金净值并绘制回撤率与日期的折线图
    :param fund_code: 基金代码
    """
    df = get_fund_nav_by_date(fund_code)
    if df.empty or '单位净值' not in df.columns or '净值日期' not in df.columns:
        print(f"无法绘制基金{fund_code}的回撤图，数据无效。")
        return
    
    # 确保日期列为datetime格式（智能处理不同格式）
    try:
        # 尝试作为时间戳解析（毫秒）
        df['净值日期'] = pd.to_datetime(df['净值日期'], unit='ms')
    except ValueError:
        # 如果失败，尝试直接解析字符串格式日期
        df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df.sort_values('净值日期')
    
    nav = df['单位净值'].astype(float)
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax * 100  # 转换为百分比
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['净值日期'], drawdown, linewidth=1.5, color='red')
    plt.fill_between(df['净值日期'], drawdown, 0, alpha=0.3, color='red')
    plt.title(f"基金{fund_code}回撤率时间序列图")
    plt.xlabel("日期")
    plt.ylabel("回撤率 (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()