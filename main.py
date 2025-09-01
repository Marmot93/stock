import enum

import akshare as ak
import pandas as pd


def load_data(symbol="510300") -> pd.DataFrame:
    try:
        return pd.read_csv('hs300.csv')
    except FileNotFoundError:
        ak.fund_open_fund_info_em(symbol=symbol).to_csv('hs300.csv', index=False, encoding='utf_8_sig')
    return pd.read_csv('hs300.csv')


# 在start和end中间随机选择一天
def random_date(start, end):
    import random
    import time
    import datetime
    start = time.mktime(time.strptime(start, "%Y-%m-%d"))
    end = time.mktime(time.strptime(end, "%Y-%m-%d"))
    t = random.randint(start, end)
    date_touple = time.localtime(t)
    date = time.strftime("%Y-%m-%d", date_touple)
    return date


class StrEnum(enum.StrEnum):
    """Enum for str"""

    def __str__(self):
        return self.value

    # 买入
    BUY = 'buy'
    # 卖出
    SELL = 'sell'
    # 持有
    HOLD = 'hold'


def _print(*args, **kwargs):
    # print(*args, **kwargs)
    pass


def main(data):
    # 本金
    capital = 100000
    # 手续费
    commission = 0.0001
    # 下一天的动作
    next_action = StrEnum.HOLD
    # 持有股票数量
    stock = 0
    # 超过该涨幅买入
    buy_change = -10
    # 低于该涨幅卖出
    sell_change = -10
    #
    last_net_value = 0

    # data.to_csv('hs300.csv', index=False, encoding='utf_8_sig')
    for idx, row in data.iterrows():
        if idx == 0:
            continue
        # 日期，净值，涨跌幅度
        date, net_value, change = row.values
        datePY = pd.to_datetime(date)
        if datePY < pd.to_datetime("2021-01-01"):
            continue
        _print(f'{date} {net_value} {change}')
        last_net_value = net_value
        # 如果 change > 1 全仓买入, 最少需要买入 100 股
        if change > buy_change:
            if next_action == StrEnum.BUY:
                _print(f'{date} 持有 {stock} 股, 剩余资金 {capital}')
                continue
            next_action = StrEnum.BUY
            stock = int(capital / (net_value * (1 + commission)) / 100) * 100
            # 买入股票的资金
            money = stock * net_value
            # 手续费
            commission_money = money * commission
            capital -= money + commission_money
            _print(f'{date} 买入 {stock} 股, 剩余资金 {capital}')
        # 如果change < 1 全仓卖出
        elif change < sell_change:
            if next_action == StrEnum.SELL:
                _print(f'{date} 空仓, 剩余资金 {capital}')
                continue
            next_action = StrEnum.SELL
            # 卖出股票的资金
            money = stock * net_value
            # 手续费
            commission_money = money * commission
            capital += money - commission_money
            _print(f'{date} 卖出 {stock} 股, 剩余资金 {capital}')
            stock = 0
    # 持有市值
    hold_money = capital + stock * last_net_value
    print(f'最终资金 {hold_money}, 盈亏百分比{((hold_money / 100000) - 1) * 100}')
    return hold_money


if __name__ == '__main__':
    data = pd.read_csv('hs300.csv')
    money = main(data)
