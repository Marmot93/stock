import akshare as ak
import pandas as pd
import os
import json
import glob
from datetime import datetime


def update_stock_mapping(stock_code: str, stock_name: str = None):
    """
    更新股票映射文件
    :param stock_code: 股票代码
    :param stock_name: 股票名称，如果为None则尝试查询
    """
    mapping_file = "data/stock_mapping.json"
    
    # 读取现有映射
    stock_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                stock_mapping = json.load(f)
        except Exception:
            pass
    
    # 如果映射中已存在，跳过
    if stock_code in stock_mapping:
        return stock_mapping[stock_code]
    
    # 如果没有提供股票名称，尝试查询
    if stock_name is None:
        try:
            stock_info = ak.stock_info_a_code_name()
            matching_stocks = stock_info[stock_info['code'] == stock_code]
            
            if not matching_stocks.empty:
                stock_name = matching_stocks.iloc[0]['name']
                print(f"查询到股票名称: {stock_name}")
        except Exception as e:
            print(f"查询股票{stock_code}名称失败: {e}")
            return stock_code
    
    # 更新映射并保存
    if stock_name and stock_name != stock_code:
        stock_mapping[stock_code] = stock_name
        try:
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(stock_mapping, f, ensure_ascii=False, indent=2)
            print(f"已将{stock_code}:{stock_name}保存到映射文件")
        except Exception as e:
            print(f"保存映射文件失败: {e}")
        return stock_name
    
    return stock_code


def get_stock_price_by_date(stock_code: str, date_str: str = None) -> pd.DataFrame:
    """
    优先从本地json缓存读取股票价格数据，如无则用akshare获取并缓存。
    获取股票历史价格数据（前复权）。
    :param stock_code: 股票代码，如 '000001'
    :param date_str: 日期字符串，格式为 'YYYY-MM-DD'，如果为None则使用今日
    :return: 包含日期和价格的DataFrame，若失败则返回空DataFrame
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    cache_file = f"data/stock_{stock_code}_{date_str}_price.json"
    # 优先尝试读取本地缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty and '收盘' in df.columns:
                # 即使使用缓存，也尝试更新股票映射（如果映射不存在）
                update_stock_mapping(stock_code)
                return df
        except Exception as e:
            print(f"读取本地缓存{cache_file}失败: {e}")
    
    # 删除该股票的旧日期缓存文件
    old_cache_pattern = f"data/stock_{stock_code}_*_price.json"
    for old_file in glob.glob(old_cache_pattern):
        if old_file != cache_file:  # 不删除当前日期的文件
            try:
                os.remove(old_file)
                print(f"删除旧缓存文件: {old_file}")
            except Exception as e:
                print(f"删除旧缓存文件{old_file}失败: {e}")
    
    # 本地无有效缓存，尝试akshare获取
    try:
        # 获取股票历史价格数据（前复权）
        df = ak.stock_zh_a_hist(symbol=stock_code, adjust="qfq")
        
        if df is None or df.empty or '收盘' not in df.columns:
            print(f"未获取到股票{stock_code}的有效价格数据，请检查代码或稍后重试。")
            return pd.DataFrame()
        
        # 重命名列以保持一致性
        df = df.rename(columns={'日期': '价格日期', '收盘': '收盘价'})
        
        # 尝试更新股票映射（利用已经获取的数据）
        update_stock_mapping(stock_code)
        
        # 写入本地缓存
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            df.to_json(cache_file, orient='records', force_ascii=False)
        except Exception as e:
            print(f"写入本地缓存{cache_file}失败: {e}")
        return df
    except Exception as e:
        print(f"获取股票{stock_code}价格数据时发生异常: {e}")
        return pd.DataFrame()