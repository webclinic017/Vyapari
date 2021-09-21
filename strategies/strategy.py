from pathlib import Path


class Strategy(object):

    DATA = "data"

    def get_algo_name(self) -> str:
        pass

    def get_universe(self) -> None:
        pass

    def download_data(self):
        pass

    def define_buy_sell(self, data):
        pass

    @staticmethod
    def get_backtest_file_path(symbol) -> Path:
        return Path("/".join([Strategy.DATA, "back-test", symbol + ".pkl"]))