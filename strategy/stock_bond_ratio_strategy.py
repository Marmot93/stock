import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class StockBondRatioStrategy:
    """
    股债性价比策略
    
    基于股债利差模型，通过对比股票潜在收益率和债券无风险利率的差值，
    来判断股票和债券的相对投资价值。
    """
    
    def __init__(self, lookback_period: int = 252*3):
        """
        初始化策略
        
        Args:
            lookback_period: 历史数据回看期，默认3年(252*3个交易日)
        """
        self.lookback_period = lookback_period
        self.asset_allocation_rules = {
            (0, 5): {"stock": 100, "bond": 0, "suggestion": "适当增配偏股类基金"},
            (6, 15): {"stock": 90, "bond": 10, "suggestion": "适当增配偏股类基金"},
            (16, 35): {"stock": 80, "bond": 20, "suggestion": "适当增配偏股类基金"},
            (36, 65): {"stock": 50, "bond": 50, "suggestion": "股债平衡配置"},
            (66, 85): {"stock": 30, "bond": 70, "suggestion": "适当增配偏债类基金"},
            (86, 95): {"stock": 20, "bond": 80, "suggestion": "适当增配偏债类基金"},
            (96, 100): {"stock": 10, "bond": 90, "suggestion": "适当增配偏债类基金"}
        }
    
    def get_csi_all_share_data(self, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        获取中证全指数据(用沪深300代替)
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含价格和PE数据的DataFrame
        """
        # 直接使用模拟数据 (简化版本，生产环境应接入真实数据)
        print("使用模拟中证全指数据")
        return self._generate_mock_csi_data(start_date, end_date)
    
    def get_10y_treasury_yield(self, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        获取10年期国债收益率数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含10年期国债收益率的DataFrame
        """
        # 直接使用模拟数据 (简化版本，生产环境应接入真实数据)
        print("使用模拟10年期国债收益率数据")
        return self._generate_mock_bond_data(start_date, end_date)
    
    def _generate_mock_csi_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟中证全指数据 - 反映当前牛市高估值情况"""
        dates = pd.date_range(start=start_date, end=end_date or datetime.now().date(), freq='D')
        # dates = dates[dates.dayofweek < 5]  # 只保留工作日，简化处理保留所有日期
        
        n = len(dates)
        np.random.seed(42)
        
        # 模拟价格走势 - 牛市特征，近期上涨较多
        price_base = 2500
        # 前期稳定，近期快速上涨
        price_changes = []
        for i in range(n):
            progress = i / n
            if progress < 0.7:  # 前70%时间稳定增长
                daily_return = np.random.normal(0.0003, 0.015)
            else:  # 后30%时间快速上涨(牛市)
                daily_return = np.random.normal(0.002, 0.025)  # 更高收益更高波动
            price_changes.append(daily_return)
        
        price_trend = np.cumsum(price_changes)
        prices = price_base * np.exp(price_trend)
        
        # 模拟PE值 - 牛市期间估值较高
        pe_base = []
        for i in range(n):
            progress = i / n
            if progress < 0.7:  # 前期PE合理
                base_pe = 15
            else:  # 后期PE偏高(牛市高估值特征)
                base_pe = 22
            pe_base.append(base_pe)
        
        pe_noise = 5 * np.sin(np.arange(n) * 0.015) + np.random.normal(0, 2, n)
        pe_values = np.array(pe_base) + pe_noise
        pe_values = np.clip(pe_values, 10, 35)  # PE范围扩大
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'pe_ratio': pe_values
        })
    
    def _generate_mock_bond_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟10年期国债收益率数据 - 反映当前较低利率环境"""
        dates = pd.date_range(start=start_date, end=end_date or datetime.now().date(), freq='D')
        # dates = dates[dates.dayofweek < 5]  # 只保留工作日，简化处理保留所有日期
        
        n = len(dates)
        np.random.seed(24)
        
        # 模拟收益率走势 - 当前低利率环境
        yield_changes = []
        for i in range(n):
            progress = i / n
            if progress < 0.5:  # 前期收益率较高
                base_yield = 3.2
            elif progress < 0.8:  # 中期下降
                base_yield = 2.8
            else:  # 近期低位
                base_yield = 2.4  # 当前较低的收益率水平
            yield_changes.append(base_yield)
        
        yield_trend = np.array(yield_changes) + np.cumsum(np.random.normal(0, 0.003, n))
        yields = yield_trend + 0.3 * np.sin(np.arange(n) * 0.025)
        yields = np.clip(yields, 2.0, 4.0)  # 当前合理的收益率区间
        
        return pd.DataFrame({
            'date': dates,
            'yield_10y': yields
        })
    
    def calculate_stock_bond_spread(self, stock_data: pd.DataFrame, bond_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算股债利差
        
        Args:
            stock_data: 股票数据，包含date, close, pe_ratio列
            bond_data: 债券数据，包含date, yield_10y列
            
        Returns:
            包含股债利差的DataFrame
        """
        # 合并数据，按日期对齐
        merged_data = pd.merge(stock_data, bond_data, on='date', how='inner')
        merged_data = merged_data.sort_values('date').reset_index(drop=True)
        
        # 计算股票收益率 (PE倒数)
        merged_data['stock_yield'] = 100 / merged_data['pe_ratio']  # 转换为百分比
        
        # 计算股债利差 = 债券收益率 - 股票收益率
        merged_data['stock_bond_spread'] = merged_data['yield_10y'] - merged_data['stock_yield']
        
        return merged_data
    
    def calculate_ratio_index(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算股债性价比指数
        
        Args:
            data: 包含股债利差的数据
            
        Returns:
            包含性价比指数的数据
        """
        data = data.copy()
        
        # 计算滚动窗口内的百分位数
        data['ratio_index'] = 0.0
        
        for i in range(len(data)):
            if i < self.lookback_period:
                historical_spread = data['stock_bond_spread'][:i+1]
            else:
                historical_spread = data['stock_bond_spread'][i-self.lookback_period+1:i+1]
            
            if len(historical_spread) > 1:
                current_spread = data['stock_bond_spread'].iloc[i]
                # 计算当前值在历史分布中的百分位 (使用numpy实现)
                percentile = np.sum(historical_spread <= current_spread) / len(historical_spread) * 100
                data.at[i, 'ratio_index'] = percentile
        
        return data
    
    def get_asset_allocation(self, ratio_index: float) -> Dict:
        """
        根据股债性价比指数获取资产配置建议
        
        Args:
            ratio_index: 股债性价比指数 (0-100)
            
        Returns:
            包含股票债券配置比例和建议的字典
        """
        for (min_val, max_val), allocation in self.asset_allocation_rules.items():
            if min_val <= ratio_index <= max_val:
                return {
                    "ratio_index": ratio_index,
                    "stock_ratio": allocation["stock"],
                    "bond_ratio": allocation["bond"],
                    "suggestion": allocation["suggestion"],
                    "risk_level": self._get_risk_level(ratio_index)
                }
        
        # 默认返回平衡配置
        return {
            "ratio_index": ratio_index,
            "stock_ratio": 50,
            "bond_ratio": 50,
            "suggestion": "股债平衡配置",
            "risk_level": "中等"
        }
    
    def _get_risk_level(self, ratio_index: float) -> str:
        """根据指数值判断风险水平"""
        if ratio_index <= 35:
            return "高风险高收益"
        elif ratio_index <= 65:
            return "中等风险"
        else:
            return "低风险低收益"
    
    def run_strategy(self, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        运行完整的股债性价比策略
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            完整的策略结果数据
        """
        print("正在获取股票数据...")
        stock_data = self.get_csi_all_share_data(start_date, end_date)
        
        print("正在获取债券数据...")
        bond_data = self.get_10y_treasury_yield(start_date, end_date)
        
        print("正在计算股债利差...")
        spread_data = self.calculate_stock_bond_spread(stock_data, bond_data)
        
        print("正在计算股债性价比指数...")
        result_data = self.calculate_ratio_index(spread_data)
        
        # 添加配置建议列
        result_data['stock_allocation'] = 0
        result_data['bond_allocation'] = 0
        result_data['suggestion'] = ""
        result_data['risk_level'] = ""
        
        for i, row in result_data.iterrows():
            allocation = self.get_asset_allocation(row['ratio_index'])
            result_data.at[i, 'stock_allocation'] = allocation['stock_ratio']
            result_data.at[i, 'bond_allocation'] = allocation['bond_ratio']
            result_data.at[i, 'suggestion'] = allocation['suggestion']
            result_data.at[i, 'risk_level'] = allocation['risk_level']
        
        return result_data
    
    def analyze_current_allocation(self, end_date: str = None) -> Dict:
        """
        分析当前的最佳资产配置
        
        Args:
            end_date: 分析截止日期
            
        Returns:
            当前配置建议
        """
        # 获取最近1年的数据进行分析
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
        
        result_data = self.run_strategy(start_date, end_date)
        
        if result_data.empty:
            return {"error": "无法获取数据"}
        
        # 获取最新的配置建议
        latest_data = result_data.iloc[-1]
        
        return {
            "date": latest_data['date'].strftime("%Y-%m-%d"),
            "ratio_index": round(latest_data['ratio_index'], 2),
            "stock_yield": round(latest_data['stock_yield'], 2),
            "bond_yield": round(latest_data['yield_10y'], 2),
            "stock_bond_spread": round(latest_data['stock_bond_spread'], 2),
            "recommended_allocation": {
                "stock": latest_data['stock_allocation'],
                "bond": latest_data['bond_allocation']
            },
            "suggestion": latest_data['suggestion'],
            "risk_level": latest_data['risk_level']
        }