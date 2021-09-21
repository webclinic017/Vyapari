from datetime import datetime

from utils.broker import Broker
from utils.notification import Notification


class InitialSteps(object):
    def __init__(self, broker: Broker, notification: Notification):  # db, broker
        self.broker = broker
        self.notification = notification
        self.show_configuration()

    def show_portfolio_details(self):
        portfolio = self.broker.get_portfolio()
        self.notification.notify("Initial portfolio value: ${:.2f}".format(float(portfolio.portfolio_value)))

    @staticmethod
    def show_configuration():
        # TODO: Implement this
        print("{}: Starting to run ... ".format(datetime.now()))
