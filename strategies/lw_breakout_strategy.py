"""
    Larry Williams Breakout strategy :
    https://www.whselfinvest.com/en-lu/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

import pandas

from schedules.watchlist import WatchList
from utils.broker import Broker, Timeframe
from utils.portfolio import PortFolio


@dataclass
class LWStock:
    symbol: str
    yesterdays_change: float
    moved: float
    weightage: float
    stop_loss: float
    market_price: float
    take_profit: float
    lw_lower_bound: float
    lw_upper_bound: float


class LWBreakout(object):
    MAX_NUM_STOCKS = 40
    STOCK_MIN_PRICE = 20
    STOCK_MAX_PRICE = 1000
    MOVED_DAYS = 3
    BARSET_RECORDS = 5

    def __init__(self, broker: Broker):
        self.name = "LWBreakout"
        self.watchlist = WatchList()
        self.broker = broker
        self.portfolio = PortFolio(broker)

        self.trade_count = 0
        self.todays_stock_picks: List[LWStock] = []

    def get_algo_name(self) -> str:
        return self.name

    def initialize(self):
        self.todays_stock_picks: List[LWStock] = self._get_todays_picks()
        self.broker.close_all_positions()

    def run(self):

        if not self.broker.is_market_open():
            print("Market not open !")
            return

        # First check if stock not already purchased
        held_stocks = [x.symbol for x in self.broker.get_positions()]

        for stock in self.todays_stock_picks:
            if stock.symbol not in held_stocks:
                print("Checking .. {}: ${}".format(stock.symbol, stock.market_price))
                current_market_price = self.broker.get_current_price(stock.symbol)

                if current_market_price > stock.lw_upper_bound and self.trade_count < LWBreakout.MAX_NUM_STOCKS:
                    no_of_shares = int(self.portfolio.get_stake_amount_per_order() / current_market_price)
                    self.broker.place_bracket_order(stock.symbol, no_of_shares, stock.stop_loss, stock.take_profit)
                    self.trade_count = self.trade_count + 1

    def _get_stock_df(self, stock):
        data_folder = "data"
        today = date.today().isoformat()
        df_path = Path("/".join([data_folder, today, stock + ".pkl"]))
        df_path.parent.mkdir(parents=True, exist_ok=True)

        if df_path.exists():
            df = pandas.read_pickle(df_path)
        else:
            if self.broker.is_tradable(stock):
                df = self.broker.get_barset(stock, Timeframe.DAY, limit=LWBreakout.BARSET_RECORDS)
                # df['pct_change'] = round(((df['close'] - df['open']) / df['open']) * 100, 4)
                # df['net_change'] = 1 + (df['pct_change'] / 100)
                # df['cum_change'] = df['net_change'].cumprod()
                df.to_pickle(df_path)

            else:
                print('stock symbol {} is not tradable with broker'.format(stock))
                return None

        return df

    def _get_todays_picks(self) -> List[LWStock]:
        # get the best buy and strong buy stock from Nasdaq.com and sort them by the best stocks

        from_watchlist = self.watchlist.get_universe()
        stock_info = []

        for count, stock in enumerate(from_watchlist):

            df = self._get_stock_df(stock)
            if df is None:
                continue

            stock_price = df.iloc[-1]['close']
            print(df.iloc[-1])
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
            lw_lower_bound = round(stock_price - (y_range * 0.25), 2)
            lw_upper_bound = round(stock_price + (y_range * 0.25), 2)

            stop_loss = round(stock_price - (2 * (y_range * 0.25)), 2)
            take_profit = round(stock_price + (3 * (y_range * 0.25)), 2)

            stock_info.append(
                LWStock(stock, y_change, percent_change, weightage, stop_loss, stock_price,
                        take_profit, lw_lower_bound, lw_upper_bound))

        biggest_movers = sorted(stock_info, key=lambda i: i.weightage, reverse=True)
        stock_picks = self._select_best(biggest_movers)
        print('today\'s picks: ')
        [print(stock_pick) for stock_pick in stock_picks]
        print('\n')
        return stock_picks

    @staticmethod
    def _calculate_weightage(moved: float, change_low_to_market: float):
        return moved + (change_low_to_market * 2)

    @staticmethod
    def _select_best(biggest_movers):
        return [x for x in biggest_movers if x.weightage > 10 and x.yesterdays_change > 5]
