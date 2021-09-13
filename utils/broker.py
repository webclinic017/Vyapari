import abc
import datetime
import time
from enum import Enum
from typing import List

import alpaca_trade_api as alpaca_api
from alpaca_trade_api.entity import BarSet, Position, Account

from utils.notification import Notification


class Timeframe(Enum):
    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    DAY = 'day'


class Broker(abc.ABC):

    @abc.abstractmethod
    def get_portfolio(self):
        pass

    @abc.abstractmethod
    def get_barset(self, symbol: str, timeframe: Timeframe, limit: int):
        pass

    @abc.abstractmethod
    def get_positions(self):
        pass

    @abc.abstractmethod
    def await_market_open(self):
        pass

    @abc.abstractmethod
    def await_market_close(self):
        pass

    @abc.abstractmethod
    def place_bracket_order(self, symbol, qty, lower_limit, upper_limit):
        pass

    @abc.abstractmethod
    def cancel_open_orders(self):
        pass

    @abc.abstractmethod
    def close_all_positions(self):
        pass

    @abc.abstractmethod
    def is_tradable(self, symbol: str):
        pass

    @abc.abstractmethod
    def is_market_open(self):
        pass


class AlpacaClient(Broker):
    def __init__(self, notification: Notification):
        self.api = alpaca_api.REST()
        self.notification = notification
        self.account = self.api.get_account()
        self.positions = sorted([p.symbol for p in self.api.list_positions()])

    def get_portfolio(self) -> Account:
        return self.api.get_account()

    def get_barset(self, symbol: str, timeframe: Timeframe, limit: int) -> BarSet:
        return self.api.get_barset(symbol, timeframe.value, limit).df[symbol]

    def get_positions(self) -> List[Position]:
        return self.api.list_positions()

    def await_market_open(self):
        self._await_market(False)

    def await_market_close(self):
        self._await_market(True)

    def is_tradable(self, symbol: str) -> bool:
        return self.api.get_asset(symbol).tradable

    def is_market_open(self) -> bool:
        return self.api.get_clock().is_open

    def market_buy(self, symbol, qty):
        return self._place_market_order(symbol, qty, "buy")

    def market_sell(self, symbol, qty):
        return self._place_market_order(symbol, qty, "buy")

    def _place_market_order(self, symbol, qty, side):
        if self.is_market_open():
            resp = self.api.submit_order(symbol, qty, side, "market", "day")
            print("Order submitted to {}: {} : {}".format(side, symbol, qty))
            return resp
        else:
            print("{} Order could not be placed ...Market is NOT open.. !".format(side))

    def place_bracket_order(self, symbol, qty, lower_limit, upper_limit):
        side = "buy"
        print("Placing bracket order to {}: {} shares of {} -> ".format(side, qty, symbol))
        if self.is_market_open():
            resp = self.api.submit_order(symbol, qty, side, "market", "day",
                                         order_class="bracket",
                                         take_profit={"limit_price": upper_limit},
                                         stop_loss={"stop_price": lower_limit})
            self.notification.notify("Placing bracket order to {}: {} shares of {} -> ".format(side, qty, symbol))
            # return resp
        else:
            print("Order to {} could not be placed ...Market is NOT open.. !".format(side))

    def cancel_open_orders(self):
        if self.is_market_open():
            self.api.cancel_all_orders()
        else:
            print("Could not cancel open orders ...Market is NOT open.. !")

    def close_all_positions(self):
        if self.is_market_open():
            positions = self.api.list_positions()
            for position in positions:
                side = "sell" if position.side == "long" else "buy"
                qty = int(position.qty)
                self.api.submit_order(position.symbol, qty, side, "market", "day")

            # wait for orders to fill
            time.sleep(5)
        else:
            print("Positions cannot be closed ...Market is NOT open.. !")

    def _await_market(self, wait_close):
        event = "close" if wait_close else "open"
        print(f"waiting for market {event}")

        clock = self.api.get_clock()
        target_time = clock.next_close if wait_close else clock.next_open
        target_time = target_time.replace(tzinfo=datetime.timezone.utc).timestamp()

        while clock.is_open == wait_close:
            curr_time = clock.timestamp.replace(
                tzinfo=datetime.timezone.utc
            ).timestamp()
            time_to_open = (target_time - curr_time) // 60

            print(f"{time_to_open} minutes until market {event}")
            time.sleep(300)
            clock = self.api.get_clock()

        print(f"market {event}")
