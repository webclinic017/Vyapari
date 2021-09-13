from colorama import Fore, Style

from utils.broker import Broker


class Intermediate(object):
    def __init__(self, broker: Broker):  # db, broker
        self.broker = broker

    def run_stats(self):
        for count, position in enumerate(self.broker.get_positions()):
            print(
                f"{(count + 1):<4}: {position.symbol:<5} - ${float(position.current_price):<8}"
                f"{Fore.GREEN if float(position.unrealized_pl) > 0 else Fore.RED}"
                f" -> ${float(position.unrealized_pl):<8}"
                f"% gain: {float(position.unrealized_plpc) * 100:.2f}%"
                f"{Style.RESET_ALL}"
            )
