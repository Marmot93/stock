#!/usr/bin/env python3
"""
股债性价比策略投资组合回测
10万元资金，每月根据股债性价比指数调仓
股票：沪深300指数
债券：10年期国债收益率
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from strategy.stock_bond_ratio_strategy import StockBondRatioStrategy

plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class PortfolioBacktest:
    """
    投资组合回测类
    """
    
    def __init__(self, initial_capital: float = 100000, transaction_cost: float = 0.001):
        """
        初始化回测参数
        
        Args:
            initial_capital: 初始资金，默认10万元
            transaction_cost: 交易成本，默认0.1%
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.strategy = StockBondRatioStrategy()
    
    def generate_realistic_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成更真实的10年市场数据
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        n = len(dates)
        np.random.seed(2024)  # 固定随机种子，确保结果可重现
        
        # 模拟沪深300指数走势（更真实的10年数据）
        # 2015-2017年：牛市后调整
        # 2018年：大幅下跌
        # 2019-2021年：结构性牛市
        # 2022年：震荡下跌  
        # 2023-2024年：复苏上涨
        
        hs300_returns = []
        pe_values = []
        bond_yields = []
        
        for i, date in enumerate(dates):
            progress = i / n
            year = date.year
            
            # 沪深300收益率模拟
            if year <= 2016:  # 2015-2016年牛市尾部+调整
                if progress < 0.1:  # 牛市尾部
                    daily_return = np.random.normal(0.001, 0.025)
                else:  # 调整期
                    daily_return = np.random.normal(-0.0005, 0.02)
            elif year == 2017:  # 2017年结构性行情
                daily_return = np.random.normal(0.0008, 0.015)
            elif year == 2018:  # 2018年大跌
                daily_return = np.random.normal(-0.002, 0.025)
            elif 2019 <= year <= 2021:  # 2019-2021结构性牛市
                daily_return = np.random.normal(0.0012, 0.02)
            elif year == 2022:  # 2022年震荡下跌
                daily_return = np.random.normal(-0.001, 0.022)
            else:  # 2023-2024复苏
                daily_return = np.random.normal(0.0008, 0.018)
            
            hs300_returns.append(daily_return)
            
            # PE值模拟（与市场行情相关）
            if year <= 2016:
                base_pe = 14 if progress > 0.1 else 18
            elif year == 2017:
                base_pe = 16
            elif year == 2018:
                base_pe = 12
            elif 2019 <= year <= 2021:
                base_pe = 19
            elif year == 2022:
                base_pe = 14
            else:
                base_pe = 17
                
            pe_noise = 3 * np.sin(i * 0.01) + np.random.normal(0, 1.5)
            pe = base_pe + pe_noise
            pe_values.append(max(8, min(pe, 30)))
            
            # 10年期国债收益率模拟
            if year <= 2016:
                base_yield = 3.2
            elif year <= 2018:
                base_yield = 3.8
            elif year <= 2020:
                base_yield = 3.0
            elif year <= 2022:
                base_yield = 2.8
            else:
                base_yield = 2.6
                
            yield_noise = 0.5 * np.sin(i * 0.02) + np.random.normal(0, 0.1)
            bond_yield = base_yield + yield_noise
            bond_yields.append(max(1.5, min(bond_yield, 5.0)))
        
        # 计算沪深300价格（累计收益）
        hs300_price = 3000 * np.cumprod(1 + np.array(hs300_returns))
        
        return pd.DataFrame({
            'date': dates,
            'hs300_price': hs300_price,
            'hs300_return': hs300_returns,
            'pe_ratio': pe_values,
            'bond_yield': bond_yields
        })
    
    def run_backtest(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        运行投资组合回测
        """
        print("正在生成市场数据...")
        market_data = self.generate_realistic_market_data(start_date, end_date)
        
        print("正在计算股债性价比指数...")
        # 准备策略所需的数据格式
        stock_data = pd.DataFrame({
            'date': market_data['date'],
            'close': market_data['hs300_price'],
            'pe_ratio': market_data['pe_ratio']
        })
        
        bond_data = pd.DataFrame({
            'date': market_data['date'],
            'yield_10y': market_data['bond_yield']
        })
        
        # 计算策略信号
        spread_data = self.strategy.calculate_stock_bond_spread(stock_data, bond_data)
        strategy_data = self.strategy.calculate_ratio_index(spread_data)
        
        # 合并数据
        full_data = pd.merge(market_data, strategy_data[['date', 'ratio_index']], on='date')
        
        # 每月调仓回测
        print("正在进行组合回测...")
        return self.monthly_rebalance_backtest(full_data)
    
    def monthly_rebalance_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        每月调仓回测
        """
        # 筛选每月最后一个交易日
        data['year_month'] = data['date'].dt.to_period('M')
        monthly_data = data.groupby('year_month').last().reset_index()
        
        results = []
        
        # 初始状态
        total_value = self.initial_capital
        stock_value = 0
        bond_value = 0
        stock_shares = 0
        
        for i, row in monthly_data.iterrows():
            # 获取当前配置建议
            allocation = self.strategy.get_asset_allocation(row['ratio_index'])
            target_stock_ratio = allocation['stock_ratio'] / 100
            target_bond_ratio = allocation['bond_ratio'] / 100
            
            # 计算当前资产价值
            if i > 0:
                # 更新股票价值
                price_change = row['hs300_price'] / prev_price
                stock_value = stock_shares * row['hs300_price']
                
                # 债券价值按月息计算（简化处理）
                monthly_bond_return = (prev_bond_yield / 100) / 12
                bond_value *= (1 + monthly_bond_return)
                
                total_value = stock_value + bond_value
            
            # 计算目标配置
            target_stock_value = total_value * target_stock_ratio
            target_bond_value = total_value * target_bond_ratio
            
            # 调仓（计算交易成本）
            if i == 0:  # 初始配置
                stock_value = target_stock_value
                bond_value = target_bond_value
                stock_shares = stock_value / row['hs300_price']
            else:
                # 计算需要调整的金额
                stock_adjust = target_stock_value - stock_value
                bond_adjust = target_bond_value - bond_value
                
                # 考虑交易成本
                transaction_cost = abs(stock_adjust) * self.transaction_cost
                total_value -= transaction_cost
                
                # 重新计算调整后的配置
                target_stock_value = total_value * target_stock_ratio
                target_bond_value = total_value * target_bond_ratio
                
                stock_value = target_stock_value
                bond_value = target_bond_value
                stock_shares = stock_value / row['hs300_price']
            
            # 计算基准收益（沪深300指数收益）
            if i == 0:
                benchmark_value = self.initial_capital
            else:
                benchmark_change = row['hs300_price'] / monthly_data.iloc[0]['hs300_price']
                benchmark_value = self.initial_capital * benchmark_change
            
            # 记录结果
            results.append({
                'date': row['date'],
                'ratio_index': row['ratio_index'],
                'stock_ratio': allocation['stock_ratio'],
                'bond_ratio': allocation['bond_ratio'],
                'suggestion': allocation['suggestion'],
                'total_value': total_value,
                'stock_value': stock_value,
                'bond_value': bond_value,
                'hs300_price': row['hs300_price'],
                'bond_yield': row['bond_yield'],
                'benchmark_value': benchmark_value,
                'portfolio_return': (total_value - self.initial_capital) / self.initial_capital * 100,
                'benchmark_return': (benchmark_value - self.initial_capital) / self.initial_capital * 100,
                'excess_return': ((total_value - self.initial_capital) / self.initial_capital * 100) - 
                                ((benchmark_value - self.initial_capital) / self.initial_capital * 100)
            })
            
            prev_price = row['hs300_price']
            prev_bond_yield = row['bond_yield']
        
        return pd.DataFrame(results)
    
    def generate_performance_report(self, backtest_results: pd.DataFrame) -> dict:
        """
        生成绩效报告
        """
        final_portfolio_value = backtest_results.iloc[-1]['total_value']
        final_benchmark_value = backtest_results.iloc[-1]['benchmark_value']
        
        portfolio_return = (final_portfolio_value - self.initial_capital) / self.initial_capital * 100
        benchmark_return = (final_benchmark_value - self.initial_capital) / self.initial_capital * 100
        excess_return = portfolio_return - benchmark_return
        
        # 计算年化收益率
        years = len(backtest_results) / 12
        portfolio_annual_return = (final_portfolio_value / self.initial_capital) ** (1/years) - 1
        benchmark_annual_return = (final_benchmark_value / self.initial_capital) ** (1/years) - 1
        
        # 计算最大回撤
        portfolio_cummax = backtest_results['total_value'].cummax()
        portfolio_drawdown = (backtest_results['total_value'] - portfolio_cummax) / portfolio_cummax * 100
        max_drawdown = portfolio_drawdown.min()
        
        benchmark_cummax = backtest_results['benchmark_value'].cummax()
        benchmark_drawdown = (backtest_results['benchmark_value'] - benchmark_cummax) / benchmark_cummax * 100
        benchmark_max_drawdown = benchmark_drawdown.min()
        
        # 计算波动率（月度标准差年化）
        portfolio_returns = backtest_results['total_value'].pct_change().dropna()
        benchmark_returns = backtest_results['benchmark_value'].pct_change().dropna()
        
        portfolio_volatility = portfolio_returns.std() * np.sqrt(12) * 100
        benchmark_volatility = benchmark_returns.std() * np.sqrt(12) * 100
        
        # 计算夏普比率（假设无风险利率3%）
        risk_free_rate = 0.03
        portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / (portfolio_volatility / 100)
        benchmark_sharpe = (benchmark_annual_return - risk_free_rate) / (benchmark_volatility / 100)
        
        return {
            'initial_capital': self.initial_capital,
            'final_portfolio_value': final_portfolio_value,
            'final_benchmark_value': final_benchmark_value,
            'portfolio_total_return': portfolio_return,
            'benchmark_total_return': benchmark_return,
            'excess_return': excess_return,
            'portfolio_annual_return': portfolio_annual_return * 100,
            'benchmark_annual_return': benchmark_annual_return * 100,
            'portfolio_volatility': portfolio_volatility,
            'benchmark_volatility': benchmark_volatility,
            'portfolio_max_drawdown': max_drawdown,
            'benchmark_max_drawdown': benchmark_max_drawdown,
            'portfolio_sharpe': portfolio_sharpe,
            'benchmark_sharpe': benchmark_sharpe,
            'years': years
        }
    
    def plot_backtest_results(self, backtest_results: pd.DataFrame, performance_report: dict):
        """
        绘制回测结果图表
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('股债性价比策略10年回测结果 (10万元初始资金)', fontsize=18, fontweight='bold')
        
        from matplotlib.dates import DateFormatter
        date_fmt = DateFormatter('%Y')
        
        # 1. 组合价值vs基准对比
        axes[0,0].plot(backtest_results['date'], backtest_results['total_value'], 
                      label=f'股债策略组合 ({performance_report["portfolio_total_return"]:.1f}%)', 
                      color='red', linewidth=3, alpha=0.8)
        axes[0,0].plot(backtest_results['date'], backtest_results['benchmark_value'], 
                      label=f'沪深300基准 ({performance_report["benchmark_total_return"]:.1f}%)', 
                      color='blue', linewidth=3, alpha=0.8)
        axes[0,0].axhline(y=100000, color='black', linestyle='--', alpha=0.7, label='初始资金')
        axes[0,0].set_title('投资组合价值对比', fontsize=14, fontweight='bold')
        axes[0,0].set_ylabel('资产价值(元)', fontsize=12)
        axes[0,0].legend(fontsize=11)
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].xaxis.set_major_formatter(date_fmt)
        
        # 2. 超额收益
        axes[0,1].plot(backtest_results['date'], backtest_results['excess_return'], 
                      color='green', linewidth=2.5, alpha=0.8)
        axes[0,1].axhline(y=0, color='black', linestyle='--', alpha=0.7)
        axes[0,1].fill_between(backtest_results['date'], backtest_results['excess_return'], 0, 
                              alpha=0.3, color='green')
        axes[0,1].set_title('超额收益 (策略 - 基准)', fontsize=14, fontweight='bold')
        axes[0,1].set_ylabel('超额收益(%)', fontsize=12)
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].xaxis.set_major_formatter(date_fmt)
        
        # 3. 资产配置变化
        axes[1,0].plot(backtest_results['date'], backtest_results['stock_ratio'], 
                      label='股票配置%', color='red', linewidth=2.5, alpha=0.8)
        axes[1,0].plot(backtest_results['date'], backtest_results['bond_ratio'], 
                      label='债券配置%', color='blue', linewidth=2.5, alpha=0.8)
        axes[1,0].fill_between(backtest_results['date'], 0, backtest_results['stock_ratio'], 
                              alpha=0.3, color='red')
        axes[1,0].fill_between(backtest_results['date'], backtest_results['stock_ratio'], 100, 
                              alpha=0.3, color='blue')
        axes[1,0].set_title('资产配置变化', fontsize=14, fontweight='bold')
        axes[1,0].set_ylabel('配置比例(%)', fontsize=12)
        axes[1,0].set_ylim(0, 100)
        axes[1,0].legend(fontsize=11)
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].xaxis.set_major_formatter(date_fmt)
        
        # 4. 回撤对比
        portfolio_cummax = backtest_results['total_value'].cummax()
        portfolio_drawdown = (backtest_results['total_value'] - portfolio_cummax) / portfolio_cummax * 100
        
        benchmark_cummax = backtest_results['benchmark_value'].cummax()
        benchmark_drawdown = (backtest_results['benchmark_value'] - benchmark_cummax) / benchmark_cummax * 100
        
        axes[1,1].fill_between(backtest_results['date'], portfolio_drawdown, 0, 
                              alpha=0.6, color='red', label='策略组合回撤')
        axes[1,1].fill_between(backtest_results['date'], benchmark_drawdown, 0, 
                              alpha=0.6, color='blue', label='沪深300回撤')
        axes[1,1].set_title('最大回撤对比', fontsize=14, fontweight='bold')
        axes[1,1].set_ylabel('回撤幅度(%)', fontsize=12)
        axes[1,1].legend(fontsize=11)
        axes[1,1].grid(True, alpha=0.3)
        axes[1,1].xaxis.set_major_formatter(date_fmt)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 保存图表
        try:
            plt.savefig('portfolio_backtest_10years.png', dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print("回测图表已保存为: portfolio_backtest_10years.png")
        except Exception as e:
            print(f"保存图表失败: {e}")
        
        plt.show()
    
    def print_performance_report(self, report: dict):
        """
        打印绩效报告
        """
        print("\n" + "="*60)
        print("股债性价比策略10年回测绩效报告")
        print("="*60)
        print(f"回测期间: {report['years']:.1f}年")
        print(f"初始资金: ¥{report['initial_capital']:,.0f}")
        print()
        
        print("【最终收益对比】")
        print(f"策略组合终值: ¥{report['final_portfolio_value']:,.0f}")
        print(f"基准终值: ¥{report['final_benchmark_value']:,.0f}")
        print(f"策略总收益: {report['portfolio_total_return']:+.2f}%")
        print(f"基准总收益: {report['benchmark_total_return']:+.2f}%")
        print(f"超额收益: {report['excess_return']:+.2f}%")
        print()
        
        print("【年化收益率】")
        print(f"策略年化收益: {report['portfolio_annual_return']:+.2f}%")
        print(f"基准年化收益: {report['benchmark_annual_return']:+.2f}%")
        print()
        
        print("【风险指标】")
        print(f"策略波动率: {report['portfolio_volatility']:.2f}%")
        print(f"基准波动率: {report['benchmark_volatility']:.2f}%")
        print(f"策略最大回撤: {report['portfolio_max_drawdown']:.2f}%")
        print(f"基准最大回撤: {report['benchmark_max_drawdown']:.2f}%")
        print()
        
        print("【夏普比率】")
        print(f"策略夏普比率: {report['portfolio_sharpe']:.3f}")
        print(f"基准夏普比率: {report['benchmark_sharpe']:.3f}")
        
        # 策略评价
        print("\n【策略评价】")
        if report['excess_return'] > 0:
            print("✅ 策略跑赢基准，产生正超额收益")
        else:
            print("❌ 策略跑输基准，产生负超额收益")
            
        if report['portfolio_max_drawdown'] > report['benchmark_max_drawdown']:
            print("⚠️  策略最大回撤大于基准")
        else:
            print("✅ 策略最大回撤小于基准，风险控制较好")
            
        if report['portfolio_sharpe'] > report['benchmark_sharpe']:
            print("✅ 策略夏普比率优于基准，风险调整后收益更好")
        else:
            print("⚠️  策略夏普比率低于基准")


def main():
    """
    主函数：运行10年回测
    """
    print("股债性价比策略10年投资组合回测")
    print("初始资金: 10万元")
    print("策略: 每月根据股债性价比指数调仓")
    print("股票标的: 沪深300指数")
    print("债券标的: 10年期国债")
    print("="*50)
    
    # 设置回测期间（2014-2024年，10年数据）
    start_date = "2014-01-01"
    end_date = "2024-12-31"
    
    # 创建回测实例
    backtest = PortfolioBacktest(initial_capital=100000, transaction_cost=0.001)
    
    # 运行回测
    results = backtest.run_backtest(start_date, end_date)
    
    # 生成绩效报告
    performance_report = backtest.generate_performance_report(results)
    
    # 打印绩效报告
    backtest.print_performance_report(performance_report)
    
    # 绘制结果图表
    backtest.plot_backtest_results(results, performance_report)
    
    print(f"\n回测完成! 共{len(results)}个调仓周期")
    print("\n最近5次调仓记录:")
    recent_results = results.tail(5)[['date', 'ratio_index', 'stock_ratio', 'bond_ratio', 
                                     'total_value', 'portfolio_return', 'excess_return']]
    recent_results['date'] = recent_results['date'].dt.strftime('%Y-%m')
    recent_results['total_value'] = recent_results['total_value'].round(0).astype(int)
    print(recent_results.to_string(index=False))


if __name__ == "__main__":
    main()