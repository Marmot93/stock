import akshare as ak
import pandas as pd
import os
import json
import glob
from datetime import datetime


def update_fund_mapping(fund_code: str, fund_name: str = None):
    """
    更新基金映射文件
    :param fund_code: 基金代码
    :param fund_name: 基金名称，如果为None则尝试查询
    """
    mapping_file = "data/fund_mapping.json"
    
    # 读取现有映射
    fund_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                fund_mapping = json.load(f)
        except Exception:
            pass
    
    # 如果映射中已存在，跳过
    if fund_code in fund_mapping:
        return fund_mapping[fund_code]
    
    # 如果没有提供基金名称，尝试查询
    if fund_name is None:
        try:
            fund_name_info = ak.fund_name_em()
            matching_funds = fund_name_info[fund_name_info['基金代码'] == fund_code]
            
            if not matching_funds.empty:
                fund_name = matching_funds.iloc[0]['基金简称']
                print(f"查询到基金名称: {fund_name}")
        except Exception as e:
            print(f"查询基金{fund_code}名称失败: {e}")
            return fund_code
    
    # 更新映射并保存
    if fund_name and fund_name != fund_code:
        fund_mapping[fund_code] = fund_name
        try:
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(fund_mapping, f, ensure_ascii=False, indent=2)
            print(f"已将{fund_code}:{fund_name}保存到映射文件")
        except Exception as e:
            print(f"保存映射文件失败: {e}")
        return fund_name
    
    return fund_code


def get_fund_nav_by_date(fund_code: str, date_str: str = None) -> pd.DataFrame:
    """
    优先从本地json缓存读取基金净值数据，如无则用akshare获取并缓存。
    :param fund_code: 基金代码，如 '110022'
    :param date_str: 日期字符串，格式为 'YYYY-MM-DD'，如果为None则使用今日
    :return: 包含日期和净值的DataFrame，若失败则返回空DataFrame
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    cache_file = f"data/fund_{fund_code}_{date_str}.json"
    # 优先尝试读取本地缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty and '单位净值' in df.columns:
                # 即使使用缓存，也尝试更新基金映射（如果映射不存在）
                update_fund_mapping(fund_code)
                return df
        except Exception as e:
            print(f"读取本地缓存{cache_file}失败: {e}")
    
    # 删除该基金的旧日期缓存文件
    old_cache_pattern = f"data/fund_{fund_code}_*.json"
    for old_file in glob.glob(old_cache_pattern):
        if old_file != cache_file:  # 不删除当前日期的文件
            try:
                os.remove(old_file)
                print(f"删除旧缓存文件: {old_file}")
            except Exception as e:
                print(f"删除旧缓存文件{old_file}失败: {e}")
    
    # 本地无有效缓存，尝试akshare获取
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df is None or df.empty or '单位净值' not in df.columns:
            print(f"未获取到基金{fund_code}的有效净值数据，请检查代码或稍后重试。")
            return pd.DataFrame()
        
        # 尝试更新基金映射（利用已经获取的数据）
        update_fund_mapping(fund_code)
        
        # 写入本地缓存
        try:
            df.to_json(cache_file, orient='records', force_ascii=False)
        except Exception as e:
            print(f"写入本地缓存{cache_file}失败: {e}")
        return df
    except Exception as e:
        print(f"获取基金{fund_code}净值数据时发生异常: {e}")
        return pd.DataFrame()