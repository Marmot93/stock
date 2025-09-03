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


def plot_fund_price_change_distribution(fund_code: str, recent_days: int = None, query_value: float = None):
    """
    绘制基金在recent_days内的涨跌分布图，并显示分位值线
    :param fund_code: 基金代码
    :param recent_days: 使用最近多少天的数据
    :param query_value: 查询指定涨跌幅值在历史数据中的百分位（如-3.5表示跌幅3.5%）
    """
    df = get_fund_nav_by_date(fund_code)
    
    if df.empty or '累计净值' not in df.columns:
        print(f"无法获取基金{fund_code}的净值数据")
        return
    
    # 筛选recent_days的数据
    if recent_days is not None:
        df = df.tail(recent_days)
    
    if len(df) < 2:
        print(f"数据不足，无法计算涨跌幅")
        return
    
    # 计算每日涨跌幅
    df = df.sort_values('净值日期').reset_index(drop=True)
    daily_returns = df['累计净值'].pct_change().dropna() * 100  # 转换为百分比
    
    # 分开计算涨幅和跌幅
    gains = daily_returns[daily_returns > 0]  # 涨幅
    losses = daily_returns[daily_returns < 0]  # 跌幅
    
    # 获取基金名称
    fund_name = update_fund_mapping(fund_code)
    title = f"基金{fund_code}涨跌分布图"
    if fund_name and fund_name != fund_code:
        title = f"{fund_name}({fund_code})涨跌分布图"
    
    if recent_days:
        title += f"（最近{recent_days}天）"
    
    # 创建分布图
    plt.figure(figsize=(12, 8))
    
    # 绘制直方图
    n_bins = min(50, len(daily_returns) // 5)  # 动态调整bins数量
    plt.hist(daily_returns, bins=n_bins, alpha=0.7, color='skyblue', 
             edgecolor='black', density=True, label='涨跌幅分布')
    
    # 涨幅分位值
    if len(gains) > 0:
        gain_percentiles = [25, 50, 75, 90, 95]
        gain_colors = ['lightgreen', 'green', 'darkgreen', 'forestgreen', 'darkseagreen']
        
        for i, p in enumerate(gain_percentiles):
            p_value = np.percentile(gains, p)
            plt.axvline(x=p_value, color=gain_colors[i], linestyle='--', alpha=0.8, linewidth=2,
                       label=f'涨{p}%分位: {p_value:.2f}%')
    
    # 跌幅分位值
    if len(losses) > 0:
        loss_percentiles = [5, 10, 25, 50, 75]
        loss_colors = ['darkred', 'red', 'orange', 'coral', 'lightcoral']
        
        for i, p in enumerate(loss_percentiles):
            p_value = np.percentile(losses, p)
            plt.axvline(x=p_value, color=loss_colors[i], linestyle='--', alpha=0.8, linewidth=2,
                       label=f'跌{p}%分位: {p_value:.2f}%')
    
    # 添加0线作为参考
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.5, linewidth=1, label='零线')
    
    # 如果提供了查询值，添加查询线
    if query_value is not None:
        plt.axvline(x=query_value, color='magenta', linestyle=':', alpha=0.8, linewidth=3,
                   label=f'查询值: {query_value:.2f}%')
    
    # 添加统计信息
    mean_return = daily_returns.mean()
    std_return = daily_returns.std()
    max_return = daily_returns.max()
    min_return = daily_returns.min()
    
    # 计算涨跌统计
    gain_days = len(gains)
    loss_days = len(losses)
    flat_days = len(daily_returns) - gain_days - loss_days
    
    # 在图上显示统计信息
    stats_text = f'统计信息:\n'
    stats_text += f'均值: {mean_return:.2f}%\n'
    stats_text += f'标准差: {std_return:.2f}%\n'
    stats_text += f'最大涨幅: {max_return:.2f}%\n'
    stats_text += f'最大跌幅: {min_return:.2f}%\n'
    stats_text += f'上涨天数: {gain_days}天\n'
    stats_text += f'下跌天数: {loss_days}天\n'
    if flat_days > 0:
        stats_text += f'平盘天数: {flat_days}天\n'
    stats_text += f'总天数: {len(daily_returns)}天'
    
    plt.text(0.98, 0.95, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
             fontsize=10)
    
    # 如果提供了查询值，在图上添加交易建议
    if query_value is not None:
        # 计算交易建议（复制之前的逻辑）
        total_percentile = (daily_returns <= query_value).mean() * 100
        
        if query_value < 0:  # 跌幅
            worse_loss_pct = (losses < query_value).mean() * 100 if len(losses) > 0 else 0
            if total_percentile <= 5:
                suggestion = "强烈买入"
                color = "darkgreen"
            elif total_percentile <= 10:
                suggestion = "买入"
                color = "green"
            elif total_percentile <= 25:
                suggestion = "考虑买入"
                color = "lightgreen"
            elif total_percentile <= 50:
                suggestion = "观望"
                color = "orange"
            else:
                suggestion = "谨慎"
                color = "red"
            reason_short = f"超过{100-worse_loss_pct:.0f}%下跌日"
        elif query_value > 0:  # 涨幅
            gain_percentile = (gains <= query_value).mean() * 100 if len(gains) > 0 else 0
            if total_percentile >= 95:
                suggestion = "考虑卖出"
                color = "red"
            elif total_percentile >= 90:
                suggestion = "可以卖出"
                color = "orange"
            elif total_percentile >= 75:
                suggestion = "观望减仓"
                color = "yellow"
            elif total_percentile >= 50:
                suggestion = "持有"
                color = "lightgreen"
            else:
                suggestion = "可以买入"
                color = "green"
            reason_short = f"超过{gain_percentile:.0f}%上涨日"
        else:
            suggestion = "观望"
            color = "gray"
            reason_short = "平盘"
        
        # 在图表左下角添加交易建议框
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        advice_text = f'分析日期: {current_date}\n'
        advice_text += f'查询值: {query_value:.2f}%\n'
        advice_text += f'建议操作: {suggestion}\n'
        advice_text += f'{reason_short}'
        
        plt.text(0.02, 0.02, advice_text, transform=plt.gca().transAxes,
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.2, edgecolor=color),
                fontsize=10, weight='bold')

    plt.title(title, fontsize=14)
    plt.xlabel("涨跌幅 (%)", fontsize=12)
    plt.ylabel("概率密度", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.show()
    
    # 打印详细的分位值信息
    print(f"\n=== {title} 分位值统计 ===")
    
    # 涨幅分位值统计
    if len(gains) > 0:
        print(f"\n涨幅分位值统计 (共{len(gains)}个上涨日):")
        gain_percentiles = [25, 50, 75, 90, 95]
        for p in gain_percentiles:
            p_value = np.percentile(gains, p)
            print(f"  涨{p:2d}%分位值: {p_value:6.2f}%")
    else:
        print(f"\n无上涨日数据")
    
    # 跌幅分位值统计  
    if len(losses) > 0:
        print(f"\n跌幅分位值统计 (共{len(losses)}个下跌日):")
        loss_percentiles = [5, 10, 25, 50, 75]
        for p in loss_percentiles:
            p_value = np.percentile(losses, p)
            print(f"  跌{p:2d}%分位值: {p_value:6.2f}%")
    else:
        print(f"\n无下跌日数据")
    
    print(f"\n基本统计:")
    print(f"平均涨跌幅: {mean_return:6.2f}%")
    print(f"标准差:     {std_return:6.2f}%")
    print(f"最大涨幅:   {max_return:6.2f}%")
    print(f"最大跌幅:   {min_return:6.2f}%")
    print(f"上涨天数:   {gain_days:6d}天 ({gain_days/len(daily_returns)*100:.1f}%)")
    print(f"下跌天数:   {loss_days:6d}天 ({loss_days/len(daily_returns)*100:.1f}%)")
    if flat_days > 0:
        print(f"平盘天数:   {flat_days:6d}天 ({flat_days/len(daily_returns)*100:.1f}%)")
    print(f"数据期间:   {len(daily_returns)}个交易日")
    
    # 如果提供了查询值，计算其在历史数据中的百分位
    if query_value is not None:
        # 计算在全部数据中的百分位
        total_percentile = (daily_returns <= query_value).mean() * 100
        
        print(f"\n=== 查询值 {query_value:.2f}% 的百分位分析 ===")
        print(f"在全部数据中的百分位: {total_percentile:.1f}%")
        print(f"即有 {total_percentile:.1f}% 的交易日涨跌幅 <= {query_value:.2f}%")
        
        # 计算超越该值的整体概率
        exceed_total_percentile = 100 - total_percentile
        if query_value < 0:
            print(f"超越该跌幅的整体概率: {exceed_total_percentile:.1f}% (即跌幅更严重的情况)")
        elif query_value > 0:
            print(f"超越该涨幅的整体概率: {exceed_total_percentile:.1f}% (即涨幅更大的情况)")
        else:
            print(f"非零涨跌的概率: {exceed_total_percentile:.1f}%")
        
        # 如果是负值（跌幅），计算有多少下跌日比给定跌幅更大
        if query_value < 0 and len(losses) > 0:
            # 对于跌幅，query_value是负数(-1.13)，losses也都是负数
            # losses < query_value 表示跌得更严重的情况（因为更负的数字表示跌幅更大）
            worse_loss_percentile = (losses < query_value).mean() * 100
            print(f"在所有下跌日中:")
            print(f"  有 {worse_loss_percentile:.1f}% 的跌幅比 {abs(query_value):.2f}% 更大")
            print(f"  有 {100-worse_loss_percentile:.1f}% 的跌幅 <= {abs(query_value):.2f}%")
        
        # 如果是正值（涨幅），计算有多少上涨日比给定涨幅更大
        elif query_value > 0 and len(gains) > 0:
            # 对于涨幅，gains > query_value 表示涨得更好的情况
            better_gain_percentile = (gains > query_value).mean() * 100
            print(f"在所有上涨日中:")
            print(f"  有 {better_gain_percentile:.1f}% 的涨幅比 {query_value:.2f}% 更大")
            print(f"  有 {100-better_gain_percentile:.1f}% 的涨幅 <= {query_value:.2f}%")
        
        # 计算该值出现的频率
        exact_count = (daily_returns == query_value).sum()
        if exact_count > 0:
            print(f"该值在历史中出现过 {exact_count} 次")
        
        # 根据百分位提供交易建议
        print(f"\n=== 交易建议 ===")
        if query_value < 0:  # 跌幅
            worse_loss_pct = (losses < query_value).mean() * 100 if len(losses) > 0 else 0
            if total_percentile <= 5:
                suggestion = "强烈买入"
                reason = f"当前跌幅{abs(query_value):.2f}%超过了{100-worse_loss_pct:.1f}%的下跌日，属于极端下跌"
                risk = "低风险，但需注意是否有基本面恶化"
            elif total_percentile <= 10:
                suggestion = "买入"
                reason = f"当前跌幅{abs(query_value):.2f}%超过了{100-worse_loss_pct:.1f}%的下跌日，属于罕见下跌"
                risk = "中低风险"
            elif total_percentile <= 25:
                suggestion = "考虑买入"
                reason = f"当前跌幅{abs(query_value):.2f}%超过了{100-worse_loss_pct:.1f}%的下跌日，较为少见"
                risk = "中等风险"
            elif total_percentile <= 50:
                suggestion = "观望"
                reason = f"当前跌幅{abs(query_value):.2f}%超过了{100-worse_loss_pct:.1f}%的下跌日，属于正常范围"
                risk = "中等风险"
            else:
                suggestion = "谨慎，可能继续下跌"
                reason = f"当前跌幅{abs(query_value):.2f}%仅超过了{100-worse_loss_pct:.1f}%的下跌日，较为常见"
                risk = "中高风险"
        
        elif query_value > 0:  # 涨幅
            gain_percentile = (gains <= query_value).mean() * 100 if len(gains) > 0 else 0
            if total_percentile >= 95:
                suggestion = "考虑卖出"
                reason = f"当前涨幅{query_value:.2f}%超过了{gain_percentile:.1f}%的上涨日，属于极端上涨"
                risk = "高风险持有"
            elif total_percentile >= 90:
                suggestion = "可以卖出"
                reason = f"当前涨幅{query_value:.2f}%超过了{gain_percentile:.1f}%的上涨日，属于罕见上涨"
                risk = "中高风险"
            elif total_percentile >= 75:
                suggestion = "观望或小幅减仓"
                reason = f"当前涨幅{query_value:.2f}%超过了{gain_percentile:.1f}%的上涨日，涨幅较大"
                risk = "中等风险"
            elif total_percentile >= 50:
                suggestion = "持有"
                reason = f"当前涨幅{query_value:.2f}%超过了{gain_percentile:.1f}%的上涨日，属于正常范围"
                risk = "中低风险"
            else:
                suggestion = "可以买入"
                reason = f"当前涨幅{query_value:.2f}%仅超过了{gain_percentile:.1f}%的上涨日，涨幅较小"
                risk = "低风险"
        
        else:  # 平盘
            suggestion = "观望"
            reason = "当前无涨跌，建议观察市场趋势"
            risk = "低风险"

        print(f"建议操作: {suggestion}")
        print(f"分析依据: {reason}")
        print(f"风险评估: {risk}")