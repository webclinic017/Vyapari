import time
from random import randint
from typing import List
from urllib.parse import urlparse

import requests
from requests import ConnectTimeout, HTTPError, ReadTimeout, Timeout


class WatchList(object):
    nasdaq = "https://api.nasdaq.com/api/screener/stocks?tableonly=true"
    no_of_stocks = 3000
    stocks_type = ["mega", "large", "mid", "small"]
    recommendation_type = ["strong_buy", "buy"]

    def __init__(self):
        self.NASDAQ_API_URL = "&".join([WatchList.nasdaq, "=".join(["limit", str(WatchList.no_of_stocks)]),
                                        "=".join(["marketcap", "|".join(WatchList.stocks_type)]),
                                        "=".join(["recommendation", "|".join(WatchList.recommendation_type)])
                                        ])

    def get_universe(self) -> List[str]:

        # for stock_type in self.stock_types:
        print("Fetching the best {} {} recommended {} stocks from NASDAQ"
              .format(self.no_of_stocks, self.recommendation_type, self.stocks_type))
        data = self._get_nasdaq_buy_stocks()
        nasdaq_records = data['data']['table']['rows']
        all_stocks = [rec['symbol'].strip().upper() for rec in nasdaq_records]
        print("Stocks from NASDAQ: ", all_stocks)
        return all_stocks

    def _get_nasdaq_buy_stocks(self):
        # api used by https://www.nasdaq.com/market-activity/stocks/screener
        parsed_uri = urlparse(self.NASDAQ_API_URL)
        # stagger requests to avoid connection issues to nasdaq.com
        time.sleep(randint(1, 3))
        headers = {
            'authority': parsed_uri.netloc,
            'method': 'GET',
            'scheme': 'https',
            'path': parsed_uri.path + '?' + parsed_uri.params,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-laguage': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }
        try:
            return requests.get(self.NASDAQ_API_URL, headers=headers).json()
        except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
            # TODO: colorama
            print('NASDAQ CONNECTION ERROR: {}'.format(e))
            time.sleep(randint(2, 5))
            self._get_nasdaq_buy_stocks()