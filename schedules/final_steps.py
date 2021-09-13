from utils.broker import Broker
from utils.notification import Notification


class FinalSteps(object):

    def __init__(self, broker: Broker, notification: Notification):  # db, broker
        self.broker = broker
        self.notification = notification

    def show_portfolio_details(self):
        portfolio = self.broker.get_portfolio()
        self.notification.notify("Final portfolio value: ${:.2f}".format(float(portfolio.portfolio_value)))