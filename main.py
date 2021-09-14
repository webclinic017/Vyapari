import time
from datetime import datetime

import schedule
import ulid

from algorithms.lw_breakout_algo import LWBreakout
from schedules.cleanup import CleanUp
from schedules.final_steps import FinalSteps
from schedules.initial_steps import InitialSteps
from schedules.intermediate import Intermediate
from schedules.watchlist import WatchList
from utils.broker import AlpacaClient
from utils.notification import Notification
from utils.util import load_env_variables


class AppConfig(object):

    def __init__(self):
        load_env_variables()
        self.notification = Notification()
        self.broker = AlpacaClient(self.notification)
        self.watchlist = WatchList()
        self.initial_steps = InitialSteps(self.broker, self.notification)
        self.intermediate = Intermediate(self.broker)
        self.strategy = LWBreakout(self.broker)
        self.cleanup = CleanUp(self.broker)
        self.final_steps = FinalSteps(self.broker, self.notification)

    def run_initial_steps(self):
        return self.initial_steps.show_portfolio_details()

    def get_universe_of_stocks(self):
        print(self.watchlist.get_universe())

    def show_current_holdings(self):
        return self.intermediate.run_stats()

    def run_strategy(self):
        self.strategy.run()

    def run_before_market_close(self):
        self.cleanup.close_all_positions()

    def run_after_market_close(self):
        self.final_steps.show_portfolio_details()

    @staticmethod
    def generate_run_id() -> str:
        return ulid.new().str


if __name__ == "__main__":

    app_config = AppConfig()
    run_id = app_config.generate_run_id()
    # schedule.every(10).seconds.do(app_config.get_universe_of_stocks)

    # Run this only on weekdays : PST time
    if datetime.today().weekday() < 5:
        schedule.every().day.at("06:30").do(app_config.run_initial_steps)
        schedule.every().day.at("06:30").do(app_config.run_strategy)
        schedule.every(10).minutes.at(":00").until("11:00").do(app_config.show_current_holdings)
        schedule.every().day.at("10:00").do(app_config.run_before_market_close)
        schedule.every().day.at("13:00").do(app_config.run_after_market_close)

    while True:
        schedule.run_pending()
        time.sleep(10)  # change this if any of the above jobs are more frequent
