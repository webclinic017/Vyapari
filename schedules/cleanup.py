from utils.broker import Broker


class CleanUp(object):

    def __init__(self, broker: Broker):
        self.broker = broker

    def close_all_positions(self):
        self.broker.cancel_open_orders()
        self.broker.close_all_positions()
