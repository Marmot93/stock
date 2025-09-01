import json
from fund import send_drawdown_analysis, analyze_drawdown_strategy, plot_drawdown_hist


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
    analyze_drawdown_strategy("110017", False)
    # plot_drawdown_hist("110017", 365*5)

