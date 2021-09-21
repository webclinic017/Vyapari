from utils.broker import Broker


class PortFolio(object):

    def __init__(self, broker: Broker):  # broker, db
        self.broker = broker

    def get_total_stake_amount(self):
        # get this from conf
        return float(self.get_portfolio_details().buying_power)

    def get_stake_amount_per_order(self):
        # get this from conf or calculate it
        return 1000.00

    def get_portfolio_details(self):
        # from broker
        return self.broker.get_portfolio()

    def get_trade_history(self):
        # from DB
        pass

    def get_all_trade_history(self):
        # from DB
        pass
