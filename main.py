from binance.client import Client
from config import api_key, api_secret
import time
from binance.enums import *

"""
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]
"""

import decimal

# create a new context for this task
ctx = decimal.Context()
# 20 digits should be enough for everyone :D
ctx.prec = 15
def float_to_str(f):
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


# 0.000011645
symbol = 'BCCBTC'
quantity = '20'
period = 10
delta = .00000001
client = Client(api_key, api_secret)
info = client.get_symbol_info(symbol)
holdings = 50.
moving_avg = 0
trade_placed = False
trade_type = False
# gamma = .001
gamma = 0.00001
sell_gamma = 0.00018
buy_gamma = -0.0000008
exit_gamma = 0.00042
long_exit_gamma = 0.0003
short_exit_gamma = 0.00005
# gamma = 0.0

while True:
    ticker = client.get_ticker(symbol=symbol)
    ask_price = float(ticker['askPrice'])
    last_price = float(ticker['lastPrice'])
    weightedAvgPrice = float(ticker['weightedAvgPrice'])
    moving_avg = (ask_price + last_price) / 2.0
    active_avg = 0.98 * moving_avg + .02 * weightedAvgPrice
    order = False
    balance = client.get_asset_balance(asset='BCC')
    # if len(client.get_open_orders()) == 0:
    #     trade_placed = False
    #     trade_type = False
    if not trade_placed:
        if ask_price/active_avg > 1.0 - sell_gamma and ask_price/last_price < 1.0 + sell_gamma:
            balance = float(client.get_asset_balance(asset='BCC')['free'])
            if balance > 0.02:
                order = client.create_order(
                    symbol=symbol,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=.02,
                    price=ticker['bidPrice'])
                print(client.get_open_orders())
                print("SELL")
                trade_placed = True
                trade_type = "short"
        elif ask_price/active_avg < 1.0 - buy_gamma and ask_price/last_price > 1.0 + buy_gamma:
            balance = float(client.get_asset_balance(asset='BTC')['free'])
            if balance > 0.002:
                order = client.create_order(
                    symbol=symbol,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=.02,
                    price=ticker['askPrice'])
                # print(order)
                print(client.get_open_orders())
                print("BUY")
                trade_placed = True
                trade_type = "long"
    elif trade_type == "short":
        if ask_price/moving_avg < 1.0 - short_exit_gamma:
            print("Exit Trade")
            if len(client.get_open_orders()) > 0:
                client.cancel_order(symbol=symbol, orderId=client.get_open_orders()[0]['orderId'])
            trade_placed = False
            trade_type = False
    elif trade_type == 'long':
        if ask_price/moving_avg > 1.0 + long_exit_gamma:
            print("Exit Trade")
            if len(client.get_open_orders()) > 0:
                client.cancel_order(symbol=symbol, orderId=client.get_open_orders()[0]['orderId'])
            trade_placed = False
            trade_type = False
    print("-"*50)
    print(f"Active Average: {float_to_str(active_avg)}   Ask Price: {float_to_str(ask_price)}   Last Price: {float_to_str(last_price)}")
    time.sleep(3)