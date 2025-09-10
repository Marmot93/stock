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
    只获取累计净值走势数据（考虑分红再投资）。
    :param fund_code: 基金代码，如 '110022'
    :param date_str: 日期字符串，格式为 'YYYY-MM-DD'，如果为None则使用今日
    :return: 包含日期和累计净值的DataFrame，若失败则返回空DataFrame
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    cache_file = f"data/fund_{fund_code}_{date_str}_cumulative.json"
    # 优先尝试读取本地缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty and '累计净值' in df.columns:
                # 即使使用缓存，也尝试更新基金映射（如果映射不存在）
                update_fund_mapping(fund_code)
                return df
        except Exception as e:
            print(f"读取本地缓存{cache_file}失败: {e}")
    
    # 删除该基金的旧日期缓存文件
    old_cache_pattern = f"data/fund_{fund_code}_*_cumulative.json"
    for old_file in glob.glob(old_cache_pattern):
        if old_file != cache_file:  # 不删除当前日期的文件
            try:
                os.remove(old_file)
                print(f"删除旧缓存文件: {old_file}")
            except Exception as e:
                print(f"删除旧缓存文件{old_file}失败: {e}")
    
    # 本地无有效缓存，尝试akshare获取
    try:
        # 只获取累计净值走势
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
        
        if df is None or df.empty or '累计净值' not in df.columns:
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


def get_shanghai_volume_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取上证指数成交额数据
    :param start_date: 开始日期，格式为 'YYYY-MM-DD'，如果为None则获取最近1年数据
    :param end_date: 结束日期，格式为 'YYYY-MM-DD'，如果为None则使用今日
    :return: 包含日期、开盘价、收盘价、最高价、最低价、成交量、成交额的DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if start_date is None:
        # 默认获取最近1年数据
        start_datetime = datetime.now() - pd.DateOffset(days=365)
        start_date = start_datetime.strftime('%Y-%m-%d')
    
    cache_file = f"data/shanghai_volume_{start_date}_{end_date}.json"
    
    # 优先尝试读取本地缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty and '成交量' in df.columns and '成交额' in df.columns:
                return df
        except Exception as e:
            print(f"读取上证成交量缓存{cache_file}失败: {e}")
    
    # 本地无有效缓存，尝试akshare获取
    try:
        # 使用akshare获取上证指数历史数据（使用index_zh_a_hist接口，包含成交额）
        # 将日期格式转换为akshare需要的格式
        start_date_str = pd.to_datetime(start_date).strftime('%Y%m%d')
        end_date_str = pd.to_datetime(end_date).strftime('%Y%m%d')
        
        df = ak.index_zh_a_hist(symbol='000001', period='daily', start_date=start_date_str, end_date=end_date_str)
        
        if df is None or df.empty:
            print(f"未获取到上证指数数据，请检查网络连接或稍后重试。")
            return pd.DataFrame()
        
        # 转换日期格式
        df['日期'] = pd.to_datetime(df['日期'])
        
        # 检查是否有成交额列
        if '成交额' not in df.columns:
            print(f"数据中缺少成交额列，可用列名: {list(df.columns)}")
            return pd.DataFrame()
        
        # 按日期排序
        df = df.sort_values('日期').reset_index(drop=True)
        
        if df.empty:
            print(f"指定日期范围内没有上证指数数据")
            return pd.DataFrame()
        
        # 写入本地缓存
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            df.to_json(cache_file, orient='records', force_ascii=False, date_format='iso')
            print(f"上证成交量数据已缓存到: {cache_file}")
        except Exception as e:
            print(f"写入上证成交量缓存{cache_file}失败: {e}")
        
        return df
        
    except Exception as e:
        print(f"获取上证指数数据时发生异常: {e}")
        return pd.DataFrame()