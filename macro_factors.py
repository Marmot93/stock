import akshare as ak
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime


def get_macro_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取宏观经济指标数据
    包含：10年期国债收益率、M1/M2增速、PMI指数、美元指数等
    :param start_date: 开始日期，格式为 'YYYY-MM-DD'
    :param end_date: 结束日期，格式为 'YYYY-MM-DD'
    :return: 包含宏观指标的DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if start_date is None:
        # 默认获取最近5年数据
        start_datetime = datetime.now() - pd.DateOffset(days=365*5)
        start_date = start_datetime.strftime('%Y-%m-%d')
    
    cache_file = f"data/macro_data_{start_date}_{end_date}.json"
    
    # 尝试读取缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty:
                print(f"使用缓存的宏观数据: {cache_file}")
                return df
        except Exception as e:
            print(f"读取宏观数据缓存失败: {e}")
    
    macro_data = []
    
    try:
        print("正在获取宏观经济数据...")
        
        # 1. 获取10年期国债收益率
        try:
            bond_10y = ak.bond_zh_us_rate()  # 不传参数，获取全部数据再筛选
            if not bond_10y.empty and '中国国债收益率10年' in bond_10y.columns:
                bond_10y = bond_10y.rename(columns={'日期': 'date', '中国国债收益率10年': 'bond_10y'})
                bond_10y['date'] = pd.to_datetime(bond_10y['date'])
                bond_10y = bond_10y[['date', 'bond_10y']].dropna()
                # 手动筛选日期范围
                bond_10y = bond_10y[(bond_10y['date'] >= start_date) & (bond_10y['date'] <= end_date)]
                print(f"获取到 {len(bond_10y)} 条国债收益率数据")
            else:
                print("未获取到国债收益率数据")
                bond_10y = pd.DataFrame(columns=['date', 'bond_10y'])
        except Exception as e:
            print(f"获取国债收益率失败: {e}")
            bond_10y = pd.DataFrame(columns=['date', 'bond_10y'])
        
        # 2. 获取M1/M2货币供应量（月度数据）
        try:
            # 尝试不同的API名称
            try:
                m0_data = ak.macro_china_m0()
                m1_data = ak.macro_china_m1_ml()
                m2_data = ak.macro_china_m2_ml()
            except:
                # 如果上述不存在，尝试其他接口
                m1_data = ak.macro_china_money_supply()
                m2_data = m1_data.copy()  # 货币供应量数据可能包含M1和M2
            
            if not m1_data.empty:
                # 检查列名并处理
                print(f"M1数据列名: {list(m1_data.columns)}")
                
                # 尝试找到正确的列名
                date_col = None
                m1_col = None
                m2_col = None
                
                for col in m1_data.columns:
                    if '月份' in str(col) or '时间' in str(col) or '日期' in str(col):
                        date_col = col
                    elif '货币(M1)-同比增长' == str(col):
                        m1_col = col
                    elif '货币和准货币(M2)-同比增长' == str(col):
                        m2_col = col
                
                if date_col and (m1_col or m2_col):
                    money_data = m1_data[[date_col]].copy()
                    money_data = money_data.rename(columns={date_col: 'date'})
                    # 处理中文日期格式，如 "2025年07月份"
                    def parse_chinese_date(date_str):
                        try:
                            if pd.isna(date_str):
                                return pd.NaT
                            # 移除"份"字，替换年月为标准格式
                            date_str = str(date_str).replace('份', '').replace('年', '-').replace('月', '-01')
                            return pd.to_datetime(date_str)
                        except:
                            return pd.NaT
                    
                    money_data['date'] = money_data['date'].apply(parse_chinese_date)
                    
                    if m1_col:
                        money_data['m1_growth'] = m1_data[m1_col]  # 直接使用同比增长率
                    
                    if m2_col:
                        money_data['m2_growth'] = m1_data[m2_col]  # 直接使用同比增长率
                    
                    money_data = money_data.dropna(subset=['date'])
                    print(f"获取到 {len(money_data)} 条货币供应量数据")
                else:
                    print("未找到正确的货币供应量列")
                    money_data = pd.DataFrame(columns=['date', 'm1_growth', 'm2_growth'])
            else:
                print("未获取到货币供应量数据")
                money_data = pd.DataFrame(columns=['date', 'm1_growth', 'm2_growth'])
        except Exception as e:
            print(f"获取货币供应量失败: {e}")
            money_data = pd.DataFrame(columns=['date', 'm1_growth', 'm2_growth'])
        
        # 3. 获取PMI指数
        try:
            pmi_data = ak.macro_china_pmi_yearly()
            if pmi_data.empty:
                # 尝试其他PMI接口
                pmi_data = ak.macro_china_pmi()
                
            if not pmi_data.empty:
                print(f"PMI数据列名: {list(pmi_data.columns)}")
                
                # 寻找正确的列名
                date_col = None
                pmi_col = None
                
                for col in pmi_data.columns:
                    if '日期' == str(col) or '时间' in str(col):
                        date_col = col
                    elif '今值' == str(col):  # PMI的今值就是PMI数据
                        pmi_col = col
                
                if date_col and pmi_col:
                    pmi_data = pmi_data[[date_col, pmi_col]].copy()
                    pmi_data = pmi_data.rename(columns={date_col: 'date', pmi_col: 'pmi'})
                    pmi_data['date'] = pd.to_datetime(pmi_data['date'])
                    pmi_data = pmi_data.dropna()
                    print(f"获取到 {len(pmi_data)} 条PMI数据")
                else:
                    print("未找到正确的PMI列")
                    pmi_data = pd.DataFrame(columns=['date', 'pmi'])
            else:
                print("未获取到PMI数据")
                pmi_data = pd.DataFrame(columns=['date', 'pmi'])
        except Exception as e:
            print(f"获取PMI失败: {e}")
            pmi_data = pd.DataFrame(columns=['date', 'pmi'])
        
        # 4. 获取美元指数
        try:
            # 尝试不同的美元指数API
            try:
                usd_index = ak.index_us_stock_sina(symbol=".DXY")  # 美元指数DXY
            except:
                try:
                    usd_index = ak.currency_usd_index()
                except:
                    # 如果以上都失败，创建空DataFrame
                    usd_index = pd.DataFrame()
            
            if not usd_index.empty:
                print(f"美元指数数据列名: {list(usd_index.columns)}")
                
                # 寻找正确的列名
                date_col = None
                usd_col = None
                
                for col in usd_index.columns:
                    if '日期' in str(col) or 'date' in str(col).lower():
                        date_col = col
                    elif '指数' in str(col) or 'close' in str(col).lower() or 'price' in str(col).lower():
                        usd_col = col
                
                if date_col and usd_col:
                    usd_index = usd_index[[date_col, usd_col]].copy()
                    usd_index = usd_index.rename(columns={date_col: 'date', usd_col: 'usd_index'})
                    usd_index['date'] = pd.to_datetime(usd_index['date'])
                    usd_index = usd_index.dropna()
                    
                    # 过滤日期范围
                    usd_index = usd_index[(usd_index['date'] >= start_date) & 
                                        (usd_index['date'] <= end_date)]
                    print(f"获取到 {len(usd_index)} 条美元指数数据")
                else:
                    print("未找到正确的美元指数列")
                    usd_index = pd.DataFrame(columns=['date', 'usd_index'])
            else:
                print("未获取到美元指数数据，将跳过此指标")
                usd_index = pd.DataFrame(columns=['date', 'usd_index'])
        except Exception as e:
            print(f"获取美元指数失败: {e}")
            usd_index = pd.DataFrame(columns=['date', 'usd_index'])
        
        # 合并所有宏观数据
        all_dfs = [bond_10y, money_data, pmi_data, usd_index]
        valid_dfs = [df for df in all_dfs if not df.empty]
        
        if valid_dfs:
            # 从第一个有效的DataFrame开始
            macro_df = valid_dfs[0]
            
            # 逐个合并其他DataFrame
            for df in valid_dfs[1:]:
                macro_df = pd.merge(macro_df, df, on='date', how='outer')
            
            # 按日期排序并前向填充
            macro_df = macro_df.sort_values('date').reset_index(drop=True)
            macro_df = macro_df.ffill()  # 使用新的前向填充方法
            
            # 过滤日期范围
            macro_df = macro_df[(macro_df['date'] >= start_date) & 
                              (macro_df['date'] <= end_date)]
            
            print(f"合并后得到 {len(macro_df)} 条宏观数据记录")
        else:
            print("没有获取到任何有效的宏观数据")
            macro_df = pd.DataFrame()
        
        # 缓存数据
        if not macro_df.empty:
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                macro_df.to_json(cache_file, orient='records', force_ascii=False, date_format='iso')
                print(f"宏观数据已缓存到: {cache_file}")
            except Exception as e:
                print(f"缓存宏观数据失败: {e}")
        
        return macro_df
        
    except Exception as e:
        print(f"获取宏观数据时发生异常: {e}")
        return pd.DataFrame()


def calculate_macro_signals(macro_df: pd.DataFrame, window_size: int = 252*2) -> pd.DataFrame:
    """
    计算宏观经济信号
    :param macro_df: 宏观数据DataFrame
    :param window_size: 历史百分位计算窗口
    :return: 包含宏观信号的DataFrame
    """
    if macro_df.empty:
        return macro_df
    
    df = macro_df.copy()
    
    # 初始化信号列
    df['interest_rate_signal'] = 0  # 利率信号
    df['money_policy_signal'] = 0  # 货币政策信号  
    df['economic_signal'] = 0      # 经济景气信号
    df['global_signal'] = 0        # 全球环境信号
    
    # 1. 利率环境信号（基于10年期国债收益率）
    if 'bond_10y' in df.columns:
        for i in range(len(df)):
            if i < window_size:
                historical_data = df['bond_10y'][:i+1].dropna()
            else:
                historical_data = df['bond_10y'][i-window_size+1:i+1].dropna()
            
            if len(historical_data) > 10:  # 至少需要10个数据点
                current_value = df['bond_10y'].iloc[i]
                if pd.notna(current_value):
                    percentile = np.sum(historical_data <= current_value) / len(historical_data) * 100
                    # 利率越低对股市越好
                    if percentile < 20:        # 极低利率
                        df.at[i, 'interest_rate_signal'] = 2
                    elif percentile < 40:      # 较低利率
                        df.at[i, 'interest_rate_signal'] = 1
                    elif percentile > 80:      # 较高利率
                        df.at[i, 'interest_rate_signal'] = -1
                    elif percentile > 90:      # 极高利率
                        df.at[i, 'interest_rate_signal'] = -2
    
    # 2. 货币政策信号（基于M1/M2增速）
    if 'm1_growth' in df.columns and 'm2_growth' in df.columns:
        for i in range(len(df)):
            m1_growth = df['m1_growth'].iloc[i]
            m2_growth = df['m2_growth'].iloc[i]
            
            if pd.notna(m1_growth) and pd.notna(m2_growth):
                # M1增速反映流动性，M2增速反映货币供应量
                if m1_growth > 15 or m2_growth > 12:      # 货币宽松
                    df.at[i, 'money_policy_signal'] = 1
                elif m1_growth > 20 or m2_growth > 15:    # 非常宽松
                    df.at[i, 'money_policy_signal'] = 2
                elif m1_growth < 5 or m2_growth < 6:      # 货币紧缩
                    df.at[i, 'money_policy_signal'] = -1
                elif m1_growth < 2 or m2_growth < 3:      # 非常紧缩
                    df.at[i, 'money_policy_signal'] = -2
    
    # 3. 经济景气信号（基于PMI）
    if 'pmi' in df.columns:
        for i in range(len(df)):
            pmi = df['pmi'].iloc[i]
            if pd.notna(pmi):
                if pmi > 52:       # 经济扩张强劲
                    df.at[i, 'economic_signal'] = 2
                elif pmi > 50:     # 经济扩张
                    df.at[i, 'economic_signal'] = 1
                elif pmi < 48:     # 经济收缩
                    df.at[i, 'economic_signal'] = -1
                elif pmi < 45:     # 经济衰退
                    df.at[i, 'economic_signal'] = -2
    
    # 4. 全球环境信号（基于美元指数变化）
    if 'usd_index' in df.columns:
        df['usd_change_20d'] = df['usd_index'].pct_change(20) * 100  # 20日变化率
        
        for i in range(20, len(df)):  # 从第20行开始计算
            usd_change = df['usd_change_20d'].iloc[i]
            if pd.notna(usd_change):
                if usd_change < -3:      # 美元大幅走弱，利好新兴市场
                    df.at[i, 'global_signal'] = 2
                elif usd_change < -1:    # 美元走弱
                    df.at[i, 'global_signal'] = 1
                elif usd_change > 3:     # 美元大幅走强
                    df.at[i, 'global_signal'] = -2
                elif usd_change > 1:     # 美元走强
                    df.at[i, 'global_signal'] = -1
    
    # 计算综合宏观信号
    df['macro_total_signal'] = (df['interest_rate_signal'] + 
                               df['money_policy_signal'] + 
                               df['economic_signal'] + 
                               df['global_signal'])
    
    return df


if __name__ == "__main__":
    # 测试宏观数据获取
    print("测试宏观数据获取功能...")
    
    # 获取最近2年的宏观数据
    macro_df = get_macro_data(start_date="2023-01-01", end_date="2025-09-10")
    
    if not macro_df.empty:
        print(f"\n成功获取 {len(macro_df)} 条宏观数据")
        print(f"数据列: {list(macro_df.columns)}")
        print(f"日期范围: {macro_df['date'].min()} 到 {macro_df['date'].max()}")
        
        # 计算宏观信号
        print("\n计算宏观经济信号...")
        macro_with_signals = calculate_macro_signals(macro_df)
        
        # 显示最新的信号
        if not macro_with_signals.empty:
            latest = macro_with_signals.iloc[-1]
            print(f"\n最新宏观信号 ({latest['date']}):")
            print(f"利率信号: {latest.get('interest_rate_signal', 'N/A')}")
            print(f"货币政策信号: {latest.get('money_policy_signal', 'N/A')}")
            print(f"经济景气信号: {latest.get('economic_signal', 'N/A')}")
            print(f"全球环境信号: {latest.get('global_signal', 'N/A')}")
            print(f"综合宏观信号: {latest.get('macro_total_signal', 'N/A')}")
            
            # 显示信号分布统计
            signal_counts = macro_with_signals['macro_total_signal'].value_counts().sort_index()
            print(f"\n宏观信号分布:")
            for score, count in signal_counts.items():
                print(f"  {score:+2.0f}分: {count:3d}次")
    else:
        print("未获取到宏观数据")