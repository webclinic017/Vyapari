# Vyapari
Vyapari means trader (in Sanskrit). This is designed to be highly customizable and configurable stock trading bot that 
runs on Alpaca and Pushover. 

Future PR intend to do the following:
- Persist the trades in a DB (Postgres/SQLite)
- Expose a set of interactive REST API interface
- Integrate Telegram to make it customizable
- GUI to visualize the trades

## Description
This project is highly customizable and is based on the following:
- Alpaca
- Pushover (to send push notifications)

## Architecture
![Vyapari](https://user-images.githubusercontent.com/4952220/134234830-a3ecd063-53ec-4a61-8a9e-72267e6e1794.jpeg)

## How to run
- Rename the `env.yaml.sample` to `env.yaml`
- Populate the required values for Alpaca and Pushover
- Run the following command `make clean run`

## Backtesting
- Run the `$ ptython3 backtest.py` with required params

## Concepts
To be filled up later

## Credits
- Concepts from Freqtrade (https://www.freqtrade.io/en/stable/)
- https://github.com/SC4RECOIN/simple-crypto-breakout-strategy

## Note
This is for educational purpose only. The author is not liable for any monetary loss during trading
