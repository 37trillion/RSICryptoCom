import requests
import numpy as np
import hmac
import time
# define the endpoint and instrument name for the Crypto.com Exchange API
endpoint = 'https://api.crypto.com/v2/public/get-ticker'
instrument_name = 'CRO_USD'
api_key = 'Tkiz9QcT9SQMYxEMpobRmb'
secret_key = 'xGTfqWzWu4zF7VizrF1Bg4'

# define the parameters for the GET request
params = {'instrument_name': instrument_name}

def get_market_data():
    """
    Retrieves market data for the specified cryptocurrency pair from the Crypto.com Exchange API.
    """
    response = requests.get(endpoint, params=params)
    data = response.json()['result']
    return data

def calculate_moving_average(data, period):
    """
    Calculates the moving average for the specified period using the closing price from the market data.
    """
    closing_prices = np.array([float(d['c']) for d in data])
    moving_average = np.mean(closing_prices[-period:])
    return moving_average

def calculate_rsi(data, period):
    """
    Calculates the RSI for the specified period using the closing price from the market data.
    """
    closing_prices = np.array([float(d['c']) for d in data])
    delta = np.diff(closing_prices)
    gain = delta * (delta > 0)
    loss = -delta * (delta < 0)
    average_gain = np.mean(gain[-period:])
    average_loss = np.mean(loss[-period:])
    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def place_order(order_type, price, quantity):
    """
    Places an order of the specified type (buy or sell) at the specified price and quantity.
    """
    payload = {
        'instrument_name': 'BTC_USDT',
        'side': order_type,
        'type': 'LIMIT',
        'price': price,
        'quantity': quantity,
        'client_oid': 'YOUR_CLIENT_OID',
    }

    timestamp = str(int(time.time() * 1000))
    signature_payload = timestamp + 'POST' + '/private/create-order' + json.dumps(payload)
    signature = hmac.new(secret_key.encode(), signature_payload.encode(), hashlib.sha256).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'API-Key': api_key,
        'API-Timestamp': timestamp,
        'API-Signature': signature,
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code == 200:
        print(f'Successfully placed {order_type} order: {response.json()}')
    else:
        print(f'Failed to place {order_type} order: {response.json()}')

def trade_strategy():
    """
    Implements the automated trading strategy based on crossover margin averages and market data.
    """
    # Define the parameters for the trading strategy
    buy_threshold = 0.5
    sell_threshold = -0.5
    stop_loss = -5

    # Retrieve market data
    market_data = get_market_data()
    if market_data:
        # Extract necessary data from the market data
        asks = market_data['asks']
        bids = market_data['bids']
        highs = market_data['highs']
        lows = market_data['lows']
        current_price = market_data['current_price']

        # Calculate the crossover margin averages
        ask_avg = np.mean(asks)
        bid_avg = np.mean(bids)
        margin_avg = ask_avg - bid_avg

        # Calculate the RSI (Relative Strength Index)
        rsi = calculate_rsi(highs, lows, current_price)

        # Perform trading decisions based on the strategy parameters and calculated values
        if rsi < buy_threshold and margin_avg > 0:
            # Place a buy order
            place_order('buy', current_price, 1)

        if rsi > sell_threshold or margin_avg < 0:
            # Place a sell order
            place_order('sell', current_price, 1)

        if current_price <= stop_loss:
            # Place a stop-loss sell order
            place_order('sell', current_price, 1)

def calculate_rsi(highs, lows, current_price):
    """
    Calculates the Relative Strength Index (RSI) based on the given high, low, and current price data.
    """
    # Calculate the price changes
    price_changes = np.diff(lows + highs)

    # Calculate the positive and negative price changes
    positive_changes = price_changes[price_changes > 0]
    negative_changes = np.abs(price_changes[price_changes < 0])

    # Calculate the average gains and losses
    avg_gain = np.mean(positive_changes) if len(positive_changes) > 0 else 0
    avg_loss = np.mean(negative_changes) if len(negative_changes) > 0 else 0

    # Calculate the relative strength (RS)
    rs = avg_gain / avg_loss if avg_loss > 0 else 0

    # Calculate the RSI
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_market_data():
    """
    Retrieves the market data from the Crypto.com Exchange API.
    """
    endpoint = 'https://api.crypto.com/v2/public/get-market-data'
    params = {
        'instrument_name': 'CRO_USD',
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        market_data = response.json()
        return market_data
    else:
        print(f'Failed to retrieve market data: {response.json()}')
        return None

if __name__ == '__main__':
    # Execute the trade strategy
    trade_strategy()
