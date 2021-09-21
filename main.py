import time
from datetime import datetime

import schedule
import ulid

from strategies.lw_breakout_strategy import LWBreakout
from schedules.cleanup import CleanUp
from schedules.final_steps import FinalSteps
from schedules.initial_steps import InitialSteps
from schedules.intermediate import Intermediate
from schedules.watchlist import WatchList
from utils.broker import AlpacaClient
from utils.pushover import Pushover
from utils.util import load_env_variables


class AppConfig(object):

    def __init__(self):
        load_env_variables()
        self.notification = Pushover()
        self.broker = AlpacaClient(self.notification)
        self.watchlist = WatchList()
        self.initial_steps = InitialSteps(self.broker, self.notification)
        self.intermediate = Intermediate(self.broker)
        self.strategy = LWBreakout(self.broker)
        self.cleanup = CleanUp(self.broker)
        self.final_steps = FinalSteps(self.broker, self.notification)

    def run_initial_steps(self):
        self.initial_steps.show_portfolio_details()
        return self.strategy.initialize()

    def run_strategy(self):
        self.strategy.run()

    def show_current_holdings(self):
        return self.intermediate.run_stats()

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
    start_trading = "06:30"
    stop_trading = "12:30"
    end_time = "13:00"

    # Run this only on weekdays : PST time
    if datetime.today().weekday() < 5:
        schedule.every().day.at(start_trading).do(app_config.run_initial_steps)
        schedule.every(1).minutes.at(":00").until(stop_trading).do(app_config.run_strategy)
        schedule.every(5).minutes.at(":00").until(end_time).do(app_config.show_current_holdings)
        schedule.every().day.at(stop_trading).do(app_config.run_before_market_close)
        schedule.every().day.at(end_time).do(app_config.run_after_market_close)

    while True:
        schedule.run_pending()
        time.sleep(10)  # change this if ny of the above jobs are more frequent
