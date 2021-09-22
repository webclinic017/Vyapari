from pathlib import Path

import pandas as pd
from alpaca_trade_api.entity import BarSet

from schedules.watchlist import WatchList
from strategies.strategy import Strategy
from utils.broker import AlpacaClient, Timeframe
from utils.notification import NoOpNotification
from utils.util import load_env_variables


class LWBreakout(object):
    MOVED_DAYS = 3
    INVESTMENT_PER_STOCK = 1000
    MIN_PERCENT_CHANGE = -5.0

    def __init__(self, backtest_days: int, start_fresh=False):
        LWBreakout._set_pandas_options()
        load_env_variables()
        self.backtest_days = backtest_days
        self.start_fresh = start_fresh  # fresh download and backtest
        self.symbols = WatchList().get_universe()
        self.broker = AlpacaClient(NoOpNotification())
        self.results = {}

    def download_data(self) -> None:

        for symbol in self.symbols:
            df_path = Strategy.get_backtest_file_path(symbol)
            df_path.parent.mkdir(parents=True, exist_ok=True)

            if self.start_fresh or not df_path.exists():
                print("Downloading data for {} for {} days".format(symbol, self.backtest_days))
                if self.broker.is_tradable(symbol):
                    df: BarSet = self.broker.get_bars(symbol, Timeframe.DAY, limit=self.backtest_days)
                    df.to_pickle(df_path)
                else:
                    print("{} is not tradable with broker".format(symbol))
            else:
                print("Data already exists for {}".format(symbol))

    def _calculate_profit_per_symbol(self, symbol):
        df_path = Strategy.get_backtest_file_path(symbol)
        df = None
        if df_path.exists():
            try:
                df = pd.read_pickle(df_path)
            except Exception as ex:
                print("exception occurred while reading pickle file {}: {}".format(df_path.name, ex))

            df['pct_change'] = round(((df['close'] - df['open']) / df['open']) * 100, 2).shift(1).fillna(0.0)
            df['decision'] = df['pct_change'] < LWBreakout.MIN_PERCENT_CHANGE

            # df['profit_per_share']
            df.loc[df['decision'], 'profit_per_share'] = df['close'] - df['open']
            df.loc[not df['decision'], 'profit_per_share'] = 0

            df['profit_amt'] = (LWBreakout.INVESTMENT_PER_STOCK / df['close']) * df['profit_per_share']
            self.results[symbol] = pd.Series(df['profit_amt'], index=df.index)

    def populate_results(self):
        for symbol in self.symbols:
            self._calculate_profit_per_symbol(symbol)
        final_df = pd.DataFrame(self.results)
        final_df['profit'] = final_df.sum(axis=1, skipna=True)
        # print("final DF", final_df)
        print(final_df['profit'].iloc[-200:].to_json)

    @staticmethod
    def _set_pandas_options():
        pd.set_option('display.max_columns', None)  # or 1000
        pd.set_option('display.max_rows', None)  # or 1000
        pd.set_option('display.max_colwidth', None)  # or 19
