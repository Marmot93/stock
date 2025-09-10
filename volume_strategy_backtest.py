import pandas as pd
import numpy as np
from fund.data_fetcher import get_shanghai_volume_data
from macro_factors import get_macro_data, calculate_macro_signals
import matplotlib.pyplot as plt
from datetime import datetime

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def volume_percentile_strategy_backtest(start_date: str = "2020-01-01", end_date: str = None, enable_macro: bool = True):
    """
    多因子择时策略（含宏观增强）：
    1. 估值择时：价格百分位 < 30% 时加大投入
    2. 趋势择时：MA250上方正常投入，下方减少投入  
    3. 情绪择时：成交额百分位 < 20% 时抄底，> 95% 时止盈
    4. 动量择时：MA20/MA60排列关系
    5. 宏观择时：利率环境、货币政策、经济景气、全球环境（可选）
    - 初始资金0元（模拟工资分批投入）
    """
    # 获取数据
    df = get_shanghai_volume_data(start_date=start_date, end_date=end_date)
    if df.empty:
        print("无法获取数据")
        return
    
    # 获取宏观数据（如果启用）
    macro_signals = {}
    if enable_macro:
        print("正在获取宏观经济数据...")
        macro_df = get_macro_data(start_date=start_date, end_date=end_date)
        if not macro_df.empty:
            macro_df = calculate_macro_signals(macro_df)
            # 将宏观数据转换为日期索引的字典，便于快速查找
            macro_signals = {}
            for _, row in macro_df.iterrows():
                if pd.notna(row['date']):  # 只处理有效日期
                    # 确保日期是datetime对象
                    if isinstance(row['date'], str):
                        date_obj = pd.to_datetime(row['date'])
                    else:
                        date_obj = row['date']
                    
                    date_key = date_obj.strftime('%Y-%m-%d')
                    macro_signals[date_key] = {
                        'interest_rate_signal': row.get('interest_rate_signal', 0),
                        'money_policy_signal': row.get('money_policy_signal', 0),
                        'economic_signal': row.get('economic_signal', 0),
                        'global_signal': row.get('global_signal', 0),
                        'macro_total_signal': row.get('macro_total_signal', 0)
                    }
            print(f"成功获取宏观信号，覆盖 {len(macro_signals)} 个交易日")
        else:
            print("未获取到宏观数据，将跳过宏观因子")
    
    # 数据预处理
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 计算技术指标
    df['MA20'] = df['收盘'].rolling(20).mean()
    df['MA60'] = df['收盘'].rolling(60).mean()
    df['MA250'] = df['收盘'].rolling(250).mean()
    
    # 计算价格百分位（使用2年窗口）
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
        
        # 添加宏观信号（如果启用且有数据）
        macro_signal = 0
        date_key = date.strftime('%Y-%m-%d')
        if enable_macro and date_key in macro_signals:
            macro_data = macro_signals[date_key]
            macro_signal = macro_data['macro_total_signal']
            signals['macro'] = macro_signal
        
        # 综合信号得分 (-4 到 +4，如果有宏观则-8到+8)
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
        
        # 根据信号强度决定投入金额（考虑宏观因子后信号范围更大）
        max_signal = 8 if enable_macro else 4  # 有宏观因子时最大信号为8
        min_signal = -8 if enable_macro else -4  # 有宏观因子时最小信号为-8
        
        if total_signal >= max_signal * 0.5:  # 极强买入信号 (>=4 or >=2)
            if profit_pool >= 15000:
                investment_amount = 15000
                profit_pool -= 15000
                salary_used = 0
                fund_source = "止盈资金池"
            else:
                investment_amount = 8000  # 工资加大投入
                salary_used = 8000
                fund_source = "工资"
        
        elif total_signal >= max_signal * 0.2:  # 偏多信号 (>=1.6 or >=0.8)
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
        
        elif total_signal >= min_signal * 0.2:  # 中性信号
            investment_amount = 5000
            salary_used = 5000
            fund_source = "工资"
        
        else:  # 偏空信号 (< -1.6 or < -0.8)
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
    
    # 转换为DataFrame便于分析
    portfolio_df = pd.DataFrame(portfolio_value)
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    
    # 计算最终收益
    final_portfolio_value = portfolio_df['组合总价值'].iloc[-1]
    strategy_return = (final_portfolio_value - total_invested) / total_invested * 100
    
    # 计算基准收益（固定月投5000元）
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
    
    # 绘制组合价值走势图
    plt.figure(figsize=(15, 10))
    
    # 子图1：组合价值走势
    plt.subplot(3, 1, 1)
    plt.plot(portfolio_df['日期'], portfolio_df['组合总价值'], label='智能定投组合价值', linewidth=2, color='blue')
    
    # 计算固定定投策略的每日价值
    fixed_daily_value = []
    fixed_shares_accumulated = 0
    fixed_invested_accumulated = 0
    
    for _, row in df.iterrows():
        if row['是月初']:
            fixed_invested_accumulated += 5000
            fixed_shares_accumulated += 5000 / row['收盘']
        current_value = fixed_shares_accumulated * row['收盘']
        fixed_daily_value.append(current_value)
    
    plt.plot(df['日期'], fixed_daily_value, label='固定定投组合价值', linewidth=2, color='red', alpha=0.7)
    
    # 标记不同投入金额的交易点
    if not trades_df.empty:
        for _, trade in trades_df.iterrows():
            if trade['金额'] == 6000:
                color = 'darkgreen'
                size = 60
            elif trade['金额'] == 4000:
                color = 'orange' 
                size = 40
            elif trade['金额'] == 3000:
                color = 'red'
                size = 30
            else:
                color = 'lightgreen'
                size = 50
            plt.scatter(trade['日期'], portfolio_df[portfolio_df['日期'] == trade['日期']]['组合总价值'].iloc[0], 
                       color=color, s=size, alpha=0.8, zorder=5)
    
    plt.title('智能定投策略 vs 固定定投策略', fontsize=14)
    plt.ylabel('组合价值 (元)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图2：成交额百分位走势
    plt.subplot(3, 1, 2)
    plt.plot(portfolio_df['日期'], portfolio_df['成交额百分位'], color='purple', alpha=0.7)
    plt.axhline(y=30, color='green', linestyle='--', alpha=0.8, label='买入阈值 (30%)')
    plt.axhline(y=95, color='red', linestyle='--', alpha=0.8, label='卖出阈值 (95%)')
    plt.fill_between(portfolio_df['日期'], 0, 30, alpha=0.2, color='green', label='买入区间')
    plt.fill_between(portfolio_df['日期'], 95, 100, alpha=0.2, color='red', label='卖出区间')
    plt.title('成交额历史百分位走势', fontsize=14)
    plt.ylabel('百分位 (%)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图3：上证指数走势
    plt.subplot(3, 1, 3)
    plt.plot(df['日期'], df['收盘'], color='black', linewidth=1)
    plt.title('上证指数走势', fontsize=14)
    plt.ylabel('指数点位', fontsize=12)
    plt.xlabel('日期', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
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
    print("多因子择时策略测试（含宏观增强）")
    print("=" * 80)
    
    # 测试不同配置的效果
    test_configs = [
        ("2023-2025 (无宏观)", "2023-01-01", "2025-09-10", False),
        ("2023-2025 (含宏观)", "2023-01-01", "2025-09-10", True),
        ("2015-2025 (无宏观)", "2015-01-01", "2025-09-10", False),
        ("2015-2025 (含宏观)", "2015-01-01", "2025-09-10", True),
    ]
    
    results = []
    for name, start, end, enable_macro in test_configs:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = volume_percentile_strategy_backtest(start_date=start, end_date=end, enable_macro=enable_macro)
            if result:
                results.append((name, result))
        except Exception as e:
            print(f"策略 {name} 执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 汇总对比
    if results:
        print(f"\n{'='*80}")
        print("策略对比汇总")
        print(f"{'='*80}")
        print(f"{'策略配置':<20} {'收益率':<10} {'固定定投':<10} {'超额收益':<10}")
        print("-" * 60)
        
        for name, result in results:
            strategy_ret = result['strategy_return']
            fixed_ret = result['fixed_return']
            excess_ret = result['excess_return']
            print(f"{name:<20} {strategy_ret:>8.2f}% {fixed_ret:>8.2f}% {excess_ret:>8.2f}%")