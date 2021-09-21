from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

import pandas

from schedules.watchlist import WatchList
from utils.broker import Broker, Timeframe


@dataclass
class LWStock:
    symbol: str
    yesterdays_change: float
    moved: float
    weightage: float
    lw_lower_bound: float
    lw_upper_bound: float
    step: float


class LWBreakout(object):
    """
        Larry Williams Breakout strategy :
        https://www.whselfinvest.com/en-lu/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free
    """

    # TODO : Move the constants to Algo config
    STOCK_MIN_PRICE = 20
    STOCK_MAX_PRICE = 1000
    MOVED_DAYS = 3
    BARSET_RECORDS = 5

    AMOUNT_PER_ORDER = 1000
    MAX_NUM_STOCKS = 40

    def __init__(self, broker: Broker):
        self.name = "LWBreakout"
        self.watchlist = WatchList()
        self.broker = broker

        self.trade_count = 0
        self.todays_stock_picks: List[LWStock] = []
        self.stocks_traded_today: List[str] = []

    def get_algo_name(self) -> str:
        return self.name

    def initialize(self):
        self.todays_stock_picks: List[LWStock] = self._get_todays_picks()
        self.broker.await_market_open()
        self.broker.close_all_positions()

    def run(self):

        if not self.broker.is_market_open():
            print("Market not open !")
            return

        # First check if stock not already purchased
        held_stocks = [x.symbol for x in self.broker.get_positions()]

        for stock in self.todays_stock_picks:

            # Open new positions on stocks only if not already held or if not traded today
            if stock.symbol not in held_stocks and stock.symbol not in self.stocks_traded_today:
                current_market_price = self.broker.get_current_price(stock.symbol)

                # long
                if stock.lw_upper_bound < current_market_price and self.trade_count < LWBreakout.MAX_NUM_STOCKS:
                    print("Long: Current market price.. {}: ${}".format(stock.symbol, current_market_price))
                    no_of_shares = int(LWBreakout.AMOUNT_PER_ORDER / current_market_price)
                    stop_loss = current_market_price - (2 * stock.step)
                    take_profit = current_market_price + (4 * stock.step)

                    self.broker.place_bracket_order(stock.symbol, "buy", no_of_shares, stop_loss, take_profit)
                    self.trade_count = self.trade_count + 1
                    self.stocks_traded_today.append(stock.symbol)

                # short
                if stock.lw_lower_bound > current_market_price and self.trade_count < LWBreakout.MAX_NUM_STOCKS:
                    print("Short: Current market price.. {}: ${}".format(stock.symbol, current_market_price))
                    no_of_shares = int(LWBreakout.AMOUNT_PER_ORDER / current_market_price)
                    stop_loss = current_market_price + (2 * stock.step)
                    take_profit = current_market_price - (4 * stock.step)

                    self.broker.place_bracket_order(stock.symbol, "sell", no_of_shares, stop_loss, take_profit)
                    self.trade_count = self.trade_count + 1
                    self.stocks_traded_today.append(stock.symbol)

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
            step = y_range * 0.25

            weightage = self._calculate_weightage(percent_change, y_change)
            lw_lower_bound = round(stock_price - (y_range * 0.25), 2)
            lw_upper_bound = round(stock_price + (y_range * 0.25), 2)

            stock_info.append(
                LWStock(stock, y_change, percent_change, weightage, lw_lower_bound, lw_upper_bound, step))

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
        return [x for x in biggest_movers if x.yesterdays_change > 6]
