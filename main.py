import json
from fund import send_drawdown_analysis, analyze_drawdown_strategy, plot_drawdown_hist, plot_fund_price_change_distribution
from stock import analyze_stock_drawdown_strategy, plot_stock_drawdown_hist, plot_stock_price_change_distribution


def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return None


def send_all_notifications():
    """给所有Bark URL发送所有基金的分析通知"""
    config = load_config()
    if not config:
        return

    bark_urls = config.get('bark_urls', [])
    fund_codes = config.get('fund_codes', [])

    if not bark_urls:
        print("配置文件中没有找到Bark URL")
        return

    if not fund_codes:
        print("配置文件中没有找到基金代码")
        return

    total_notifications = len(bark_urls) * len(fund_codes)
    current = 0

    print(f"准备发送 {total_notifications} 个通知...")

    for bark_url in bark_urls:
        print(f"\n正在向 {bark_url} 发送通知...")
        for fund_code in fund_codes:
            current += 1
            print(f"[{current}/{total_notifications}] 发送基金 {fund_code} 的分析...")

            success = send_drawdown_analysis(bark_url, fund_code)
            if not success:
                print(f"发送失败: {fund_code} -> {bark_url}")

    print(f"\n通知发送完成！共发送 {total_notifications} 个通知。")


if __name__ == "__main__":
    # send_all_notifications()
    recent_days = 365*5
    # recent_days = None
    
    # 基金分析示例
    fund_code = "110017"
    print("=== 基金涨跌分布分析 ===")
    # analyze_drawdown_strategy(fund_code, False, recent_days=recent_days)
    # plot_drawdown_hist(fund_code, recent_days=recent_days)
    
    # 基金涨跌分布分析
    query_fund_drop = -0.36
    plot_fund_price_change_distribution(fund_code, recent_days=recent_days, query_value=query_fund_drop)
    
    # 股票分析示例
    # stock_code = "600519"
    # print("\n=== 股票回撤分析 ===")
    # analyze_stock_drawdown_strategy(stock_code, False, recent_days=recent_days)
    # 测试新的回撤查询功能，查询-5%回撤在历史中的位置
    # query_drawdown = -5.0
    # plot_stock_drawdown_hist(stock_code, recent_days=recent_days, query_drawdown=query_drawdown)
    
    # 股票涨跌分布分析
    # print("\n=== 股票涨跌分布分析 ===")
    # 普通分析
    # plot_stock_price_change_distribution(stock_code, recent_days=recent_days)
    
    # 查询特定跌幅的百分位
    # query_drop = -0.72
    # plot_stock_price_change_distribution(stock_code, recent_days=recent_days, query_value=query_drop)
