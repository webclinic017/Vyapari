import time
from datetime import datetime

import schedule

from algorithms.lw_breakout_algo import LWBreakout
from schedules.cleanup import CleanUp
from schedules.final_steps import FinalSteps
from schedules.initial_steps import InitialSteps
from schedules.intermediate import Intermediate
from utils.broker import AlpacaClient
from utils.notification import Notification
from utils.util import load_env_variables


class Controller(object):

    def __init__(self):
        load_env_variables()
        self.notification = Notification()
        self.broker = AlpacaClient(self.notification)
        # self.watchlist = WatchList()
        self.initial_steps = InitialSteps(self.broker, self.notification)
        self.intermediate = Intermediate(self.broker)
        self.strategy = LWBreakout(self.broker)
        self.cleanup = CleanUp(self.broker)
        self.final_steps = FinalSteps(self.broker, self.notification)

    def run_initial_steps(self):
        return self.initial_steps.show_portfolio_details()

    # def get_watchlist_stocks(self):
    #     return self.watchlist.get_best()

    def show_current_holdings(self):
        return self.intermediate.run_stats()

    def run_strategy(self):
        self.strategy.run()

    def run_before_market_close(self):
        self.cleanup.close_all_positions()

    def run_after_market_close(self):
        self.final_steps.show_portfolio_details()


controller = Controller()
# schedule.every(60).seconds.do(get_watchlist_stocks)

# Run this on weekdays only
if datetime.today().weekday() < 5:
    schedule.every().day.at("06:30").do(controller.run_initial_steps)
    schedule.every().day.at("07:00").do(controller.run_strategy)
    schedule.every(10).minutes.at(":00").until("13:10").do(controller.show_current_holdings)
    schedule.every().day.at("12:30").do(controller.run_before_market_close)
    schedule.every().day.at("13:00").do(controller.run_after_market_close)

while True:
    schedule.run_pending()
    time.sleep(60)  # change this if any of the above jobs are more frequent
