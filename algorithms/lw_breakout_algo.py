"""
    Larry Williams Breakout algo :
    https://www.whselfinvest.com/en-lu/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free
"""
from dataclasses import dataclass
from typing import List

from algorithms.algorithm import Algorithm
from schedules.watchlist import WatchList
from utils.broker import Broker, Timeframe
from utils.portfolio import PortFolio


@dataclass
class LWStock:
    symbol: str
    yesterdays_change: float
    moved: float
    weightage: float
    lower_limit: float
    market_price: float
    upper_limit: float


class LWBreakout(Algorithm):
    MAX_NUM_STOCKS = 20
    STOCK_MIN_PRICE = 20
    STOCK_MAX_PRICE = 1000
    MOVED_DAYS = 3
    BARSET_RECORDS = 5

    def __init__(self, broker: Broker):
        self.name = "LWBreakout"
        self.watchlist = WatchList()
        self.broker = broker
        self.portfolio = PortFolio(broker)

    def get_algo_name(self) -> str:
        return self.name

    def run(self):
        stock_picks = self._get_todays_picks()

        for stock in stock_picks:
            no_of_shares = int(self.portfolio.get_stake_amount_per_order() / stock.market_price)
            self.broker.place_bracket_order(stock.symbol, no_of_shares, stock.lower_limit, stock.upper_limit)

    def _get_stock_df(self, stock):
        df = self.broker.get_barset(stock, Timeframe.DAY, limit=LWBreakout.BARSET_RECORDS)
        # df['pct_change'] = round(((df['close'] - df['open']) / df['open']) * 100, 4)
        # df['net_change'] = 1 + (df['pct_change'] / 100)
        # df['cum_change'] = df['net_change'].cumprod()
        return df

    def _get_todays_picks(self) -> List[LWStock]:
        # get the best buy and strong buy stock from Nasdaq.com and sort them by the best stocks

        from_watchlist = self.watchlist.get_best()
        stock_info = []

        for count, record in enumerate(from_watchlist):

            stock = record.upper()
            if not self.broker.is_tradable(stock):
                print('stock symbol {} is not tradable with broker'.format(stock))
                continue

            df = self._get_stock_df(stock)
            stock_price = df.iloc[-1]['close']
            if stock_price > LWBreakout.STOCK_MAX_PRICE or stock_price < LWBreakout.STOCK_MIN_PRICE:
                continue

            df = self._get_stock_df(stock)
            price_open = df.iloc[-LWBreakout.MOVED_DAYS]['open']
            price_close = df.iloc[-1]['close']
            percent_change = round((price_close - price_open) / price_open * 100, 3)
            print('[{}/{}] -> {} moved {}% over the last {} days'.format(count + 1, len(from_watchlist),
                                                                         stock, percent_change, LWBreakout.MOVED_DAYS))

            yesterdays_record = df.iloc[-2]
            y_stock_open = yesterdays_record['open']
            y_stock_high = yesterdays_record['high']
            y_stock_low = yesterdays_record['low']
            y_stock_close = yesterdays_record['close']

            y_change = round((y_stock_close - y_stock_open) / y_stock_open * 100, 3)
            y_range = y_stock_high - y_stock_low  # yesterday's range

            weightage = self._calculate_weightage(percent_change, y_change)
            lower_limit = round(stock_price - (y_range * 0.25), 2)
            upper_limit = round(stock_price + (3 * (y_range * 0.25)), 2)

            stock_info.append(
                LWStock(stock, y_change, percent_change, weightage, lower_limit, stock_price, upper_limit))

        biggest_movers = sorted(stock_info, key=lambda i: i.weightage, reverse=True)
        stock_picks = self._select_best(biggest_movers)
        print('today\'s picks {}'.format(stock_picks))
        print('\n')
        return stock_picks

    @staticmethod
    def _calculate_weightage(moved: float, change_low_to_market: float):
        return moved + (change_low_to_market * 2)

    @staticmethod
    def _select_best(biggest_movers):
        return [x for x in biggest_movers if x.weightage > 10 and x.yesterdays_change > 4][:LWBreakout.MAX_NUM_STOCKS]
