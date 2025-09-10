import pandas as pd
import numpy as np
from fund.data_fetcher import get_shanghai_volume_data
import matplotlib.pyplot as plt
from datetime import datetime

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def advanced_timing_strategy_backtest(start_date: str = "2015-01-01", end_date: str = None):
    """
    改进版择时策略：
    1. 估值择时：PE百分位 < 30% 时加大投入
    2. 趋势择时：MA250上方正常投入，下方减少投入  
    3. 情绪择时：成交额百分位 < 20% 时抄底，> 95% 时止盈
    4. 动态仓位：根据多个指标综合决定仓位
    """
    # 获取数据
    df = get_shanghai_volume_data(start_date=start_date, end_date=end_date)
    if df.empty:
        print("无法获取数据")
        return
    
    # 数据预处理
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 计算技术指标
    df['MA20'] = df['收盘'].rolling(20).mean()
    df['MA60'] = df['收盘'].rolling(60).mean()
    df['MA250'] = df['收盘'].rolling(250).mean()
    
    # 计算估值百分位（这里用价格代替，实际应该用PE）
    df['价格百分位'] = 0.0
    window_size = 252 * 2  # 2年窗口
    
    for i in range(len(df)):
        if i < window_size:
            historical_data = df['收盘'][:i+1]
        else:
            historical_data = df['收盘'][i-window_size+1:i+1]
        
        if len(historical_data) > 1:
            current_value = df['收盘'].iloc[i]
            percentile = np.sum(historical_data <= current_value) / len(historical_data) * 100
            df.at[i, '价格百分位'] = percentile
    
    # 计算成交额百分位
    df['成交额_百分位'] = 0.0
    for i in range(len(df)):
        if i < window_size:
            historical_data = df['成交额'][:i+1]
        else:
            historical_data = df['成交额'][i-window_size+1:i+1]
        
        if len(historical_data) > 1:
            current_value = df['成交额'].iloc[i]
            percentile = np.sum(historical_data <= current_value) / len(historical_data) * 100
            df.at[i, '成交额_百分位'] = percentile
    
    # 初始化变量
    cash = 0
    shares = 0
    total_invested = 0
    profit_pool = 0
    
    trades = []
    portfolio_value = []
    
    # 获取每月首个交易日
    df['年月'] = df['日期'].dt.to_period('M')
    monthly_first_days = df.groupby('年月')['日期'].first().reset_index()
    monthly_first_days['是月初'] = True
    df = df.merge(monthly_first_days[['日期', '是月初']], on='日期', how='left')
    df['是月初'] = df['是月初'].fillna(False)
    
    for idx, row in df.iterrows():
        date = row['日期']
        price = row['收盘']
        ma20 = row['MA20']
        ma60 = row['MA60'] 
        ma250 = row['MA250']
        price_percentile = row['价格百分位']
        volume_percentile = row['成交额_百分位']
        is_first_day = row['是月初']
        
        # 计算当前组合价值
        current_portfolio_value = cash + shares * price + profit_pool
        portfolio_value.append({
            '日期': date,
            '现金': cash,
            '持股数量': shares,
            '股票价值': shares * price,
            '止盈资金池': profit_pool,
            '组合总价值': current_portfolio_value,
            '价格百分位': price_percentile,
            '成交额百分位': volume_percentile,
            'MA20': ma20,
            'MA250': ma250
        })
        
        # 只在每月首日进行交易
        if not is_first_day or pd.isna(ma250):
            continue
        
        # 计算收益率
        if total_invested > 0:
            current_return_rate = ((shares * price + profit_pool) - total_invested) / total_invested
        else:
            current_return_rate = 0
        
        # 多因子择时策略
        signals = {
            'trend': 1 if price > ma250 else -1,  # 趋势信号
            'valuation': 1 if price_percentile < 30 else (-1 if price_percentile > 80 else 0),  # 估值信号
            'sentiment': 1 if volume_percentile < 20 else (-1 if volume_percentile > 95 else 0),  # 情绪信号
            'momentum': 1 if price > ma20 > ma60 else (-1 if price < ma20 < ma60 else 0)  # 动量信号
        }
        
        # 综合信号得分 (-4 到 +4)
        total_signal = sum(signals.values())
        
        # 止盈操作
        sell_action = ""
        if volume_percentile > 98 and current_return_rate > 0.3 and shares > 0:
            sell_shares = shares * 0.3  # 激进止盈
            sell_amount = sell_shares * price
            shares -= sell_shares
            profit_pool += sell_amount
            sell_action = f"激进止盈 {sell_shares:.2f}股，获得 {sell_amount:.2f}元"
            
            trades.append({
                '日期': date,
                '操作': '激进止盈',
                '价格': price,
                '数量': sell_shares,
                '金额': sell_amount,
                '信号得分': total_signal,
                '综合信号': signals
            })
        
        elif volume_percentile > 90 and total_signal <= -2 and shares > 0:
            sell_shares = shares * 0.2  # 信号止盈
            sell_amount = sell_shares * price
            shares -= sell_shares
            profit_pool += sell_amount
            sell_action = f"信号止盈 {sell_shares:.2f}股，获得 {sell_amount:.2f}元"
            
            trades.append({
                '日期': date,
                '操作': '信号止盈',
                '价格': price,
                '数量': sell_shares,
                '金额': sell_amount,
                '信号得分': total_signal,
                '综合信号': signals
            })
        
        # 根据信号强度决定投入金额
        if total_signal >= 3:  # 极强买入信号
            if profit_pool >= 15000:
                investment_amount = 15000
                profit_pool -= 15000
                salary_used = 0
                fund_source = "止盈资金池"
            else:
                investment_amount = 8000  # 工资加大投入
                salary_used = 8000
                fund_source = "工资"
        
        elif total_signal >= 1:  # 偏多信号
            if profit_pool >= 8000:
                pool_amount = min(profit_pool, 8000)
                salary_amount = 5000
                investment_amount = pool_amount + salary_amount
                profit_pool -= pool_amount
                salary_used = salary_amount
                fund_source = f"资金池{pool_amount:.0f}元+工资{salary_amount:.0f}元"
            else:
                investment_amount = 6000
                salary_used = 6000
                fund_source = "工资"
        
        elif total_signal >= -1:  # 中性信号
            investment_amount = 5000
            salary_used = 5000
            fund_source = "工资"
        
        else:  # 偏空信号
            investment_amount = 2000  # 大幅减少投入
            salary_used = 2000
            fund_source = "工资"
        
        # 执行买入
        if investment_amount > 0:
            buy_shares = investment_amount / price
            shares += buy_shares
            total_invested += salary_used
            
            buy_action = f"买入 {buy_shares:.2f}股，投入 {investment_amount}元 ({fund_source})"
            
            trades.append({
                '日期': date,
                '操作': '买入',
                '价格': price,
                '数量': buy_shares,
                '金额': investment_amount,
                '工资投入': salary_used,
                '信号得分': total_signal,
                '综合信号': signals,
                '资金来源': fund_source
            })
            
            # 打印交易信息
            if sell_action:
                print(f"{date.strftime('%Y-%m-%d')}: {sell_action}")
            print(f"{date.strftime('%Y-%m-%d')}: {buy_action}, 信号: {total_signal}")
    
    # 转换为DataFrame
    portfolio_df = pd.DataFrame(portfolio_value)
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    
    # 计算最终收益
    final_portfolio_value = portfolio_df['组合总价值'].iloc[-1]
    strategy_return = (final_portfolio_value - total_invested) / total_invested * 100
    
    # 计算基准收益（固定定投5000元）
    fixed_investment_value = 0
    fixed_total_invested = 0
    for _, row in df.iterrows():
        if row['是月初'] and not pd.isna(row['MA250']):
            fixed_total_invested += 5000
            fixed_investment_value += 5000 / row['收盘']
    
    fixed_final_value = fixed_investment_value * df['收盘'].iloc[-1]
    fixed_return = (fixed_final_value - fixed_total_invested) / fixed_total_invested * 100
    
    # 打印结果
    print(f"\n=== 多因子择时策略回测结果 ===")
    print(f"测试期间: {df['日期'].iloc[0].strftime('%Y-%m-%d')} 至 {df['日期'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"累计投入金额: {total_invested:,.0f}元")
    print(f"最终组合价值: {final_portfolio_value:,.2f}元")
    print(f"多因子策略收益率: {strategy_return:.2f}%")
    print(f"固定定投收益率: {fixed_return:.2f}%")
    print(f"策略超额收益: {strategy_return - fixed_return:.2f}%")
    print(f"剩余资金池: {portfolio_df['止盈资金池'].iloc[-1]:,.2f}元")
    
    if not trades_df.empty:
        buy_trades = trades_df[trades_df['操作'] == '买入']
        sell_trades = trades_df[trades_df['操作'].str.contains('止盈')]
        
        print(f"\n交易统计:")
        print(f"总交易次数: {len(trades_df)}次")
        print(f"买入次数: {len(buy_trades)}次")
        print(f"止盈次数: {len(sell_trades)}次")
        
        if len(sell_trades) > 0:
            print(f"累计止盈金额: {sell_trades['金额'].sum():,.2f}元")
        
        # 信号分布统计
        signal_counts = buy_trades['信号得分'].value_counts().sort_index()
        print(f"\n信号得分分布:")
        for score, count in signal_counts.items():
            print(f"  {score:+2d}分: {count:2d}次")
    
    return {
        'portfolio_df': portfolio_df,
        'trades_df': trades_df,
        'strategy_return': strategy_return,
        'fixed_return': fixed_return,
        'excess_return': strategy_return - fixed_return,
        'total_invested': total_invested,
        'final_value': final_portfolio_value
    }


if __name__ == "__main__":
    print("=" * 80)
    print("多因子择时策略测试")
    print("=" * 80)
    
    # 测试不同时间周期
    periods = [
        ("2015-2025", "2015-01-01", "2025-09-10"),
        ("2010-2025", "2010-01-01", "2025-09-10")
    ]
    
    results = []
    for name, start, end in periods:
        print(f"\n{'='*20} {name} {'='*20}")
        result = advanced_timing_strategy_backtest(start_date=start, end_date=end)
        if result:
            results.append((name, result))
    
    # 汇总对比
    if results:
        print(f"\n{'='*80}")
        print("策略对比汇总")
        print(f"{'='*80}")
        print(f"{'时间周期':<15} {'多因子策略':<12} {'固定定投':<12} {'超额收益':<12}")
        print("-" * 60)
        
        for name, result in results:
            strategy_ret = result['strategy_return']
            fixed_ret = result['fixed_return']
            excess_ret = result['excess_return']
            print(f"{name:<15} {strategy_ret:>10.2f}% {fixed_ret:>10.2f}% {excess_ret:>10.2f}%")