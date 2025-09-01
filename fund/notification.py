import json
import os
from msg import send_bark
from .drawdown_analyzer import analyze_drawdown_strategy
from .data_fetcher import update_fund_mapping


def get_fund_name(fund_code: str) -> str:
    """
    获取基金名称，优先从映射文件读取，如果未找到则尝试更新映射
    :param fund_code: 基金代码
    :return: 基金名称或基金代码
    """
    mapping_file = "data/fund_mapping.json"
    
    # 读取现有映射
    fund_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                fund_mapping = json.load(f)
        except Exception as e:
            print(f"读取基金映射文件失败: {e}")
    
    # 如果映射中已存在，直接返回
    if fund_code in fund_mapping:
        return fund_mapping[fund_code]
    
    # 如果不存在，尝试更新映射（会查询基金名称）
    return update_fund_mapping(fund_code)


def send_drawdown_analysis(bark_url: str, fund_code: str):
    """
    通过Bark发送基金回撤分析通知
    :param bark_url: Bark推送链接
    :param fund_code: 基金代码
    """
    # 获取回撤分析结果（静默模式）
    result = analyze_drawdown_strategy(fund_code, silent=True)
    if not result:
        print("无法获取基金分析结果")
        return False
    
    # 构建通知内容
    fund_name = get_fund_name(fund_code)
    title = f"{fund_name}({fund_code})回撤分析"
    content = f"""当前回撤率: {result['current_drawdown']:.2f}%
当前回撤百分位: {result['current_percentile']:.1f}%
最大回撤: {result['stats']['最大回撤']:.2f}%
平均回撤: {result['stats']['平均回撤']:.2f}%

买入建议: {result['suggestion']}
风险评估: {result['risk_level']}
理由: {result['reason']}"""
    
    # 使用通用的send_bark函数发送
    return send_bark(bark_url, title, content)