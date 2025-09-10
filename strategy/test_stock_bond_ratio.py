#!/usr/bin/env python3
"""
股债性价比策略测试文件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.stock_bond_ratio_strategy import StockBondRatioStrategy
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def test_strategy_basic():
    """测试策略基本功能"""
    print("=== 测试股债性价比策略基本功能 ===")
    
    strategy = StockBondRatioStrategy()
    
    # 测试当前配置建议
    current_allocation = strategy.analyze_current_allocation()
    print("\n当前资产配置建议:")
    print(f"日期: {current_allocation.get('date', 'N/A')}")
    print(f"股债性价比指数: {current_allocation.get('ratio_index', 'N/A')}")
    print(f"股票收益率: {current_allocation.get('stock_yield', 'N/A')}%")
    print(f"债券收益率: {current_allocation.get('bond_yield', 'N/A')}%")
    print(f"股债利差: {current_allocation.get('stock_bond_spread', 'N/A')}")
    
    allocation = current_allocation.get('recommended_allocation', {})
    print(f"\n推荐配置:")
    print(f"股票: {allocation.get('stock', 'N/A')}%")
    print(f"债券: {allocation.get('bond', 'N/A')}%")
    print(f"建议: {current_allocation.get('suggestion', 'N/A')}")
    print(f"风险水平: {current_allocation.get('risk_level', 'N/A')}")


def test_strategy_backtest():
    """测试策略回测功能"""
    print("\n=== 测试策略回测功能 ===")
    
    strategy = StockBondRatioStrategy()
    
    # 回测最近2年数据
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    
    print(f"回测期间: {start_date} 到 {end_date}")
    
    result_data = strategy.run_strategy(start_date, end_date)
    
    if not result_data.empty:
        print(f"\n回测数据点数: {len(result_data)}")
        print("\n最近5天的策略信号:")
        recent_data = result_data.tail(5)[['date', 'ratio_index', 'stock_allocation', 'bond_allocation', 'suggestion']]
        recent_data['date'] = recent_data['date'].dt.strftime('%Y-%m-%d')
        print(recent_data.to_string(index=False))
        
        # 统计配置建议分布
        print("\n\n配置建议分布:")
        suggestion_counts = result_data['suggestion'].value_counts()
        for suggestion, count in suggestion_counts.items():
            percentage = count / len(result_data) * 100
            print(f"{suggestion}: {count}次 ({percentage:.1f}%)")
        
        return result_data
    else:
        print("回测数据为空")
        return None


def plot_strategy_results(result_data):
    """绘制策略结果图表"""
    if result_data is None or result_data.empty:
        print("没有数据可以绘制")
        return
    
    print("\n=== 绘制策略分析图表 ===")
    
    # 创建更大的图表，提高可读性
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle('股债性价比策略分析 (牛市修正版)', fontsize=18, fontweight='bold')
    
    # 设置日期格式化
    from matplotlib.dates import DateFormatter, MonthLocator
    date_fmt = DateFormatter('%Y-%m')
    
    # 1. 股债收益率对比
    axes[0,0].plot(result_data['date'], result_data['stock_yield'], label='股票收益率(PE倒数)', 
                   color='red', linewidth=2.5, alpha=0.8)
    axes[0,0].plot(result_data['date'], result_data['yield_10y'], label='10年期国债收益率', 
                   color='blue', linewidth=2.5, alpha=0.8)
    axes[0,0].set_title('股债收益率对比', fontsize=14, fontweight='bold')
    axes[0,0].set_ylabel('收益率(%)', fontsize=12)
    axes[0,0].legend(fontsize=11)
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].xaxis.set_major_formatter(date_fmt)
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # 2. 股债利差
    axes[0,1].plot(result_data['date'], result_data['stock_bond_spread'], color='green', 
                   linewidth=2.5, alpha=0.8)
    axes[0,1].axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=1.5)
    axes[0,1].fill_between(result_data['date'], result_data['stock_bond_spread'], 0, 
                           alpha=0.3, color='green')
    axes[0,1].set_title('股债利差 (债券收益率 - 股票收益率)', fontsize=14, fontweight='bold')
    axes[0,1].set_ylabel('利差(%)', fontsize=12)
    axes[0,1].grid(True, alpha=0.3)
    axes[0,1].xaxis.set_major_formatter(date_fmt)
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # 3. 股债性价比指数
    axes[1,0].plot(result_data['date'], result_data['ratio_index'], color='purple', 
                   linewidth=2.5, alpha=0.8)
    axes[1,0].axhline(y=50, color='black', linestyle='--', alpha=0.7, label='中位数(50%)')
    axes[1,0].axhline(y=35, color='red', linestyle='--', alpha=0.7, label='偏股区间(35%)')
    axes[1,0].axhline(y=65, color='orange', linestyle='--', alpha=0.7, label='偏债区间(65%)')
    axes[1,0].fill_between(result_data['date'], 0, 35, alpha=0.2, color='red', label='高配股票区')
    axes[1,0].fill_between(result_data['date'], 65, 100, alpha=0.2, color='blue', label='高配债券区')
    axes[1,0].set_title('股债性价比指数', fontsize=14, fontweight='bold')
    axes[1,0].set_ylabel('指数值', fontsize=12)
    axes[1,0].set_ylim(0, 100)
    axes[1,0].legend(fontsize=10)
    axes[1,0].grid(True, alpha=0.3)
    axes[1,0].xaxis.set_major_formatter(date_fmt)
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # 4. 资产配置建议
    axes[1,1].plot(result_data['date'], result_data['stock_allocation'], label='股票配置%', 
                   color='red', linewidth=3, alpha=0.8)
    axes[1,1].plot(result_data['date'], result_data['bond_allocation'], label='债券配置%', 
                   color='blue', linewidth=3, alpha=0.8)
    axes[1,1].fill_between(result_data['date'], 0, result_data['stock_allocation'], 
                          alpha=0.3, color='red')
    axes[1,1].fill_between(result_data['date'], result_data['stock_allocation'], 100, 
                          alpha=0.3, color='blue')
    axes[1,1].set_title('资产配置建议', fontsize=14, fontweight='bold')
    axes[1,1].set_ylabel('配置比例(%)', fontsize=12)
    axes[1,1].set_ylim(0, 100)
    axes[1,1].legend(fontsize=11)
    axes[1,1].grid(True, alpha=0.3)
    axes[1,1].xaxis.set_major_formatter(date_fmt)
    axes[1,1].tick_params(axis='x', rotation=45)
    
    # 5. 指数分布直方图
    axes[2,0].hist(result_data['ratio_index'], bins=25, alpha=0.7, color='lightblue', 
                   edgecolor='darkblue', linewidth=1.2)
    axes[2,0].axvline(x=result_data['ratio_index'].mean(), color='red', linestyle='-', 
                     linewidth=2, label=f'均值: {result_data["ratio_index"].mean():.1f}')
    axes[2,0].axvline(x=result_data['ratio_index'].median(), color='orange', linestyle='--', 
                     linewidth=2, label=f'中位数: {result_data["ratio_index"].median():.1f}')
    axes[2,0].set_title('股债性价比指数分布', fontsize=14, fontweight='bold')
    axes[2,0].set_xlabel('指数值', fontsize=12)
    axes[2,0].set_ylabel('频次', fontsize=12)
    axes[2,0].legend(fontsize=11)
    axes[2,0].grid(True, alpha=0.3)
    
    # 6. 建议分布饼图
    suggestion_counts = result_data['suggestion'].value_counts()
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
    wedges, texts, autotexts = axes[2,1].pie(suggestion_counts.values, 
                                            labels=suggestion_counts.index, 
                                            autopct='%1.1f%%', 
                                            startangle=90, 
                                            colors=colors[:len(suggestion_counts)])
    axes[2,1].set_title('配置建议分布', fontsize=14, fontweight='bold')
    
    # 调整字体大小
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.subplots_adjust(hspace=0.3, wspace=0.3)
    
    # 保存图表
    try:
        plt.savefig('stock_bond_ratio_analysis.png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print("图表已保存为: stock_bond_ratio_analysis.png")
    except Exception as e:
        print(f"保存图表失败: {e}")
    
    plt.show()


def main():
    """主测试函数"""
    print("股债性价比策略测试")
    print("=" * 50)
    
    # 基本功能测试
    test_strategy_basic()
    
    # 回测功能测试
    result_data = test_strategy_backtest()
    
    # 绘制分析图表
    if result_data is not None:
        try:
            plot_strategy_results(result_data)
        except Exception as e:
            print(f"绘图过程中出现错误: {e}")
            print("请检查matplotlib配置")
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()