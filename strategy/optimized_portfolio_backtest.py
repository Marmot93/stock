#!/usr/bin/env python3
"""
优化版股债性价比策略回测
调整策略逻辑，减少过度保守的配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class OptimizedStockBondStrategy:
    """
    优化版股债性价比策略
    """
    
    def __init__(self, lookback_period: int = 252*2):  # 减少回看期到2年
        self.lookback_period = lookback_period
        # 调整配置规则，增加股票配置比例
        self.asset_allocation_rules = {
            (0, 10): {"stock": 90, "bond": 10, "suggestion": "股票极度低估，重配股票"},
            (11, 25): {"stock": 80, "bond": 20, "suggestion": "股票低估，增配股票"},
            (26, 40): {"stock": 70, "bond": 30, "suggestion": "股票合理偏低，偏股配置"},
            (41, 60): {"stock": 60, "bond": 40, "suggestion": "股债均衡配置"},
            (61, 75): {"stock": 45, "bond": 55, "suggestion": "股票偏贵，偏债配置"},
            (76, 90): {"stock": 30, "bond": 70, "suggestion": "股票高估，减配股票"},
            (91, 100): {"stock": 20, "bond": 80, "suggestion": "股票极度高估，大幅减配"}
        }
    
    def get_asset_allocation(self, ratio_index: float) -> dict:
        """根据优化后的规则获取配置建议"""
        for (min_val, max_val), allocation in self.asset_allocation_rules.items():
            if min_val <= ratio_index <= max_val:
                return {
                    "ratio_index": ratio_index,
                    "stock_ratio": allocation["stock"],
                    "bond_ratio": allocation["bond"],
                    "suggestion": allocation["suggestion"]
                }
        
        return {
            "ratio_index": ratio_index,
            "stock_ratio": 60,
            "bond_ratio": 40,
            "suggestion": "股债均衡配置"
        }
    
    def calculate_ratio_index(self, stock_data: pd.DataFrame, bond_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算优化的股债性价比指数
        """
        # 合并数据
        merged_data = pd.merge(stock_data, bond_data, on='date', how='inner')
        merged_data = merged_data.sort_values('date').reset_index(drop=True)
        
        # 计算股票收益率 (PE倒数)
        merged_data['stock_yield'] = 100 / merged_data['pe_ratio']
        
        # 计算股债利差 = 债券收益率 - 股票收益率
        merged_data['stock_bond_spread'] = merged_data['bond_yield'] - merged_data['stock_yield']
        
        # 计算性价比指数（优化版）
        merged_data['ratio_index'] = 0.0
        
        for i in range(len(merged_data)):
            if i < self.lookback_period:
                historical_spread = merged_data['stock_bond_spread'][:i+1]
            else:
                historical_spread = merged_data['stock_bond_spread'][i-self.lookback_period+1:i+1]
            
            if len(historical_spread) > 1:
                current_spread = merged_data['stock_bond_spread'].iloc[i]
                # 使用更敏感的百分位计算
                percentile = np.sum(historical_spread <= current_spread) / len(historical_spread) * 100
                # 平滑处理，避免过度波动
                if i > 0:
                    prev_index = merged_data['ratio_index'].iloc[i-1]
                    merged_data.at[i, 'ratio_index'] = 0.7 * percentile + 0.3 * prev_index
                else:
                    merged_data.at[i, 'ratio_index'] = percentile
        
        return merged_data


class OptimizedPortfolioBacktest:
    """
    优化版组合回测
    """
    
    def __init__(self, initial_capital: float = 100000, transaction_cost: float = 0.0005):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost  # 降低交易成本
        self.strategy = OptimizedStockBondStrategy()
        self.min_rebalance_threshold = 0.05  # 只有当配置差异超过5%时才调仓
    
    def generate_realistic_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成更真实的市场数据，体现A股特点
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        n = len(dates)
        np.random.seed(2024)
        
        # 模拟A股实际走势特征
        returns = []
        pe_values = []
        bond_yields = []
        
        for i, date in enumerate(dates):
            progress = i / n
            year = date.year
            
            # A股收益率模拟（基于历史特征）
            if 2014 <= year <= 2015:  # 2014-2015年大牛市
                if year == 2014:
                    daily_return = np.random.normal(0.0015, 0.025)  # 牛市初期
                else:
                    daily_return = np.random.normal(0.003, 0.035)   # 牛市疯狂期
            elif year == 2016:  # 2016年调整
                daily_return = np.random.normal(-0.002, 0.03)
            elif year == 2017:  # 2017年价值回归
                daily_return = np.random.normal(0.001, 0.02)
            elif year == 2018:  # 2018年熊市
                daily_return = np.random.normal(-0.003, 0.035)
            elif 2019 <= year <= 2020:  # 2019-2020结构牛
                daily_return = np.random.normal(0.002, 0.025)
            elif year == 2021:  # 2021年震荡
                daily_return = np.random.normal(0.0005, 0.022)
            elif year == 2022:  # 2022年下跌
                daily_return = np.random.normal(-0.002, 0.028)
            else:  # 2023-2024年恢复
                daily_return = np.random.normal(0.0015, 0.02)
                
            returns.append(daily_return)
            
            # PE值模拟（更贴近A股实际）
            if 2014 <= year <= 2015:
                base_pe = 25 if year == 2015 else 18
            elif year == 2016:
                base_pe = 16
            elif year == 2017:
                base_pe = 17
            elif year == 2018:
                base_pe = 12
            elif 2019 <= year <= 2020:
                base_pe = 20
            elif year == 2021:
                base_pe = 16
            elif year == 2022:
                base_pe = 13
            else:
                base_pe = 15
                
            pe_noise = 3 * np.sin(i * 0.015) + np.random.normal(0, 2)
            pe = base_pe + pe_noise
            pe_values.append(max(8, min(pe, 35)))
            
            # 国债收益率（基于实际利率环境）
            if year <= 2016:
                base_yield = 3.5
            elif year <= 2018:
                base_yield = 3.8
            elif year <= 2020:
                base_yield = 3.2
            elif year <= 2022:
                base_yield = 2.9
            else:
                base_yield = 2.7
                
            yield_noise = 0.4 * np.sin(i * 0.025) + np.random.normal(0, 0.08)
            bond_yield = base_yield + yield_noise
            bond_yields.append(max(2.0, min(bond_yield, 4.5)))
        
        # 计算累积价格
        cumulative_returns = np.cumprod(1 + np.array(returns))
        prices = 3000 * cumulative_returns  # 2014年初沪深300约3000点
        
        return pd.DataFrame({
            'date': dates,
            'hs300_price': prices,
            'hs300_return': returns,
            'pe_ratio': pe_values,
            'bond_yield': bond_yields
        })
    
    def run_backtest(self, start_date: str, end_date: str) -> pd.DataFrame:
        """运行优化回测"""
        print("正在生成优化的市场数据...")
        market_data = self.generate_realistic_market_data(start_date, end_date)
        
        print("正在计算优化的股债性价比指数...")
        stock_data = pd.DataFrame({
            'date': market_data['date'],
            'close': market_data['hs300_price'],
            'pe_ratio': market_data['pe_ratio']
        })
        
        bond_data = pd.DataFrame({
            'date': market_data['date'],
            'bond_yield': market_data['bond_yield']
        })
        
        strategy_data = self.strategy.calculate_ratio_index(stock_data, bond_data)
        full_data = pd.merge(market_data, strategy_data[['date', 'ratio_index']], on='date')
        
        print("正在进行优化组合回测...")
        return self.smart_rebalance_backtest(full_data)
    
    def smart_rebalance_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        智能调仓回测 - 只在配置差异较大时调仓
        """
        # 每月末数据
        data['year_month'] = data['date'].dt.to_period('M')
        monthly_data = data.groupby('year_month').last().reset_index()
        
        results = []
        
        # 初始状态
        total_value = self.initial_capital
        current_stock_ratio = 0.6  # 初始60%股票配置
        current_bond_ratio = 0.4   # 初始40%债券配置
        
        stock_shares = 0
        cash_for_bonds = 0
        
        for i, row in monthly_data.iterrows():
            # 获取目标配置
            allocation = self.strategy.get_asset_allocation(row['ratio_index'])
            target_stock_ratio = allocation['stock_ratio'] / 100
            target_bond_ratio = allocation['bond_ratio'] / 100
            
            # 更新资产价值
            if i > 0:
                # 股票价值变化
                price_change = row['hs300_price'] / prev_price
                stock_value = stock_shares * row['hs300_price']
                
                # 债券价值变化（按月收益）
                monthly_bond_return = (prev_bond_yield / 100) / 12
                bond_value = cash_for_bonds * (1 + monthly_bond_return)
                
                total_value = stock_value + bond_value
                current_stock_ratio = stock_value / total_value
                current_bond_ratio = bond_value / total_value
            else:
                # 初始配置
                stock_value = total_value * current_stock_ratio
                bond_value = total_value * current_bond_ratio
                stock_shares = stock_value / row['hs300_price']
                cash_for_bonds = bond_value
                total_value = stock_value + bond_value
            
            # 智能调仓：只有当偏离超过阈值时才调仓
            stock_diff = abs(target_stock_ratio - current_stock_ratio)
            need_rebalance = stock_diff > self.min_rebalance_threshold
            
            if need_rebalance and i > 0:
                # 计算交易成本
                trade_amount = abs(target_stock_ratio * total_value - stock_value)
                cost = trade_amount * self.transaction_cost
                total_value -= cost
                
                # 重新配置
                stock_value = total_value * target_stock_ratio
                bond_value = total_value * target_bond_ratio
                stock_shares = stock_value / row['hs300_price']
                cash_for_bonds = bond_value
                
                current_stock_ratio = target_stock_ratio
                current_bond_ratio = target_bond_ratio
            
            # 计算基准（纯沪深300）
            if i == 0:
                benchmark_value = self.initial_capital
            else:
                benchmark_change = row['hs300_price'] / monthly_data.iloc[0]['hs300_price']
                benchmark_value = self.initial_capital * benchmark_change
            
            # 记录结果
            results.append({
                'date': row['date'],
                'ratio_index': row['ratio_index'],
                'target_stock_ratio': allocation['stock_ratio'],
                'target_bond_ratio': allocation['bond_ratio'],
                'actual_stock_ratio': current_stock_ratio * 100,
                'actual_bond_ratio': current_bond_ratio * 100,
                'rebalanced': need_rebalance,
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
        """生成绩效报告"""
        final_portfolio_value = backtest_results.iloc[-1]['total_value']
        final_benchmark_value = backtest_results.iloc[-1]['benchmark_value']
        
        portfolio_return = (final_portfolio_value - self.initial_capital) / self.initial_capital * 100
        benchmark_return = (final_benchmark_value - self.initial_capital) / self.initial_capital * 100
        excess_return = portfolio_return - benchmark_return
        
        years = len(backtest_results) / 12
        portfolio_annual_return = (final_portfolio_value / self.initial_capital) ** (1/years) - 1
        benchmark_annual_return = (final_benchmark_value / self.initial_capital) ** (1/years) - 1
        
        # 计算其他指标
        portfolio_cummax = backtest_results['total_value'].cummax()
        portfolio_drawdown = (backtest_results['total_value'] - portfolio_cummax) / portfolio_cummax * 100
        max_drawdown = portfolio_drawdown.min()
        
        benchmark_cummax = backtest_results['benchmark_value'].cummax()
        benchmark_drawdown = (backtest_results['benchmark_value'] - benchmark_cummax) / benchmark_cummax * 100
        benchmark_max_drawdown = benchmark_drawdown.min()
        
        portfolio_returns = backtest_results['total_value'].pct_change().dropna()
        benchmark_returns = backtest_results['benchmark_value'].pct_change().dropna()
        
        portfolio_volatility = portfolio_returns.std() * np.sqrt(12) * 100
        benchmark_volatility = benchmark_returns.std() * np.sqrt(12) * 100
        
        risk_free_rate = 0.03
        portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / (portfolio_volatility / 100)
        benchmark_sharpe = (benchmark_annual_return - risk_free_rate) / (benchmark_volatility / 100)
        
        # 计算调仓次数
        rebalance_count = backtest_results['rebalanced'].sum()
        
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
            'years': years,
            'rebalance_count': rebalance_count
        }
    
    def plot_backtest_results(self, backtest_results: pd.DataFrame, performance_report: dict):
        """绘制优化回测结果"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('优化版股债性价比策略10年回测结果', fontsize=18, fontweight='bold')
        
        from matplotlib.dates import DateFormatter
        date_fmt = DateFormatter('%Y')
        
        # 1. 资产价值对比
        axes[0,0].plot(backtest_results['date'], backtest_results['total_value'], 
                      label=f'优化策略 ({performance_report["portfolio_total_return"]:.1f}%)', 
                      color='red', linewidth=3)
        axes[0,0].plot(backtest_results['date'], backtest_results['benchmark_value'], 
                      label=f'沪深300 ({performance_report["benchmark_total_return"]:.1f}%)', 
                      color='blue', linewidth=3)
        axes[0,0].axhline(y=100000, color='black', linestyle='--', alpha=0.7)
        axes[0,0].set_title('投资组合价值对比', fontsize=14, fontweight='bold')
        axes[0,0].set_ylabel('资产价值(元)')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].xaxis.set_major_formatter(date_fmt)
        
        # 2. 超额收益
        axes[0,1].plot(backtest_results['date'], backtest_results['excess_return'], 
                      color='green', linewidth=2.5)
        axes[0,1].axhline(y=0, color='black', linestyle='--', alpha=0.7)
        axes[0,1].fill_between(backtest_results['date'], backtest_results['excess_return'], 0, 
                              alpha=0.3, color='green')
        axes[0,1].set_title('超额收益 (策略 - 基准)', fontsize=14, fontweight='bold')
        axes[0,1].set_ylabel('超额收益(%)')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].xaxis.set_major_formatter(date_fmt)
        
        # 3. 动态配置
        axes[1,0].plot(backtest_results['date'], backtest_results['actual_stock_ratio'], 
                      label='实际股票配置%', color='red', linewidth=2.5)
        axes[1,0].plot(backtest_results['date'], backtest_results['actual_bond_ratio'], 
                      label='实际债券配置%', color='blue', linewidth=2.5)
        
        # 标记调仓点
        rebalance_dates = backtest_results[backtest_results['rebalanced']]['date']
        rebalance_stock = backtest_results[backtest_results['rebalanced']]['actual_stock_ratio']
        axes[1,0].scatter(rebalance_dates, rebalance_stock, color='red', s=20, alpha=0.7, zorder=5)
        
        axes[1,0].set_title(f'资产配置变化 (共调仓{performance_report["rebalance_count"]}次)', fontsize=14, fontweight='bold')
        axes[1,0].set_ylabel('配置比例(%)')
        axes[1,0].set_ylim(0, 100)
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].xaxis.set_major_formatter(date_fmt)
        
        # 4. 回撤对比
        portfolio_cummax = backtest_results['total_value'].cummax()
        portfolio_drawdown = (backtest_results['total_value'] - portfolio_cummax) / portfolio_cummax * 100
        
        benchmark_cummax = backtest_results['benchmark_value'].cummax()
        benchmark_drawdown = (backtest_results['benchmark_value'] - benchmark_cummax) / benchmark_cummax * 100
        
        axes[1,1].fill_between(backtest_results['date'], portfolio_drawdown, 0, 
                              alpha=0.6, color='red', label='策略回撤')
        axes[1,1].fill_between(backtest_results['date'], benchmark_drawdown, 0, 
                              alpha=0.6, color='blue', label='基准回撤')
        axes[1,1].set_title('回撤对比', fontsize=14, fontweight='bold')
        axes[1,1].set_ylabel('回撤幅度(%)')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        axes[1,1].xaxis.set_major_formatter(date_fmt)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig('optimized_portfolio_backtest.png', dpi=300, bbox_inches='tight')
        print("优化回测图表已保存为: optimized_portfolio_backtest.png")
        plt.show()
    
    def print_performance_report(self, report: dict):
        """打印优化版绩效报告"""
        print("\n" + "="*60)
        print("优化版股债性价比策略10年回测报告")
        print("="*60)
        print(f"回测期间: {report['years']:.1f}年")
        print(f"初始资金: ¥{report['initial_capital']:,.0f}")
        print(f"调仓次数: {report['rebalance_count']}次 (智能调仓)")
        print()
        
        print("【收益对比】")
        print(f"策略终值: ¥{report['final_portfolio_value']:,.0f}")
        print(f"基准终值: ¥{report['final_benchmark_value']:,.0f}")
        print(f"策略收益: {report['portfolio_total_return']:+.2f}%")
        print(f"基准收益: {report['benchmark_total_return']:+.2f}%")
        print(f"超额收益: {report['excess_return']:+.2f}%")
        print()
        
        print("【年化指标】")
        print(f"策略年化: {report['portfolio_annual_return']:+.2f}%")
        print(f"基准年化: {report['benchmark_annual_return']:+.2f}%")
        print()
        
        print("【风险控制】")
        print(f"策略波动: {report['portfolio_volatility']:.2f}%")
        print(f"基准波动: {report['benchmark_volatility']:.2f}%")
        print(f"策略回撤: {report['portfolio_max_drawdown']:.2f}%")
        print(f"基准回撤: {report['benchmark_max_drawdown']:.2f}%")
        print()
        
        print("【夏普比率】")
        print(f"策略夏普: {report['portfolio_sharpe']:.3f}")
        print(f"基准夏普: {report['benchmark_sharpe']:.3f}")


def main():
    print("优化版股债性价比策略10年投资组合回测")
    print("="*50)
    
    backtest = OptimizedPortfolioBacktest(initial_capital=100000, transaction_cost=0.0005)
    results = backtest.run_backtest("2014-01-01", "2024-12-31")
    
    performance_report = backtest.generate_performance_report(results)
    backtest.print_performance_report(performance_report)
    backtest.plot_backtest_results(results, performance_report)
    
    print(f"\n最近5次调仓:")
    recent = results.tail(5)[['date', 'ratio_index', 'actual_stock_ratio', 'total_value', 'excess_return']]
    recent['date'] = recent['date'].dt.strftime('%Y-%m')
    print(recent.to_string(index=False))


if __name__ == "__main__":
    main()