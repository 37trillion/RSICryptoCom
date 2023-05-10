import ssl
import requests
import time
import logging
import hashlib
import hmac
import json
import websocket
from CryptoCom import CryptoComAPI
from trade_strategy import *
from urllib.parse import urljoin
from logging_component import setup_logger
import threading

from urllib.parse import urlparse
# Set your API key and secret key
api_key = 
secret_key = 
api_url="https://api.crypto.com/v2/"

# Set the symbol and interval for the candlestick data
SYMBOL = "CRO_USD"
INTERVAL = "1m"

# Set the trade strategy parameters
STRATEGY_PARAMS = {
    "buy_threshold": 0.5,
    "sell_threshold": -0.5,
    "stop_loss": -5,
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_auth_headers(api_key, SECERET_KEY, method, endpoint, timestamp, body=None):
    parsed_url = urlparse(endpoint)
    if parsed_url.query:
        endpoint = f"{parsed_url.path}?{parsed_url.query}"
    else:
        endpoint = parsed_url.path
    message = f"{timestamp}{method.upper()}{endpoint}"
    if body:
        message += json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-PASSPHRASE": "passphrase"  # replace with your passphrase
    }

def generate_hmac_auth(method):
    """Generates an HMAC authentication string for API requests"""
    payload = {}
    payload['method'] = method
    payload['nonce'] = str(int(time.time() * 1000))
    payload_string = json.dumps(payload)
    sig = hmac.new(secret_key.encode(),
                         payload_string.encode(),
                         hashlib.sha256).hexdigest()
    auth = f"{api_key}:{sig}:{payload['nonce']}"
    return auth

def authenticate(ws):
    """Authenticate the websocket connection"""
    timestamp = str(api_url.time()["result"])
    sig = hmac.new(secret_key.encode(), timestamp.encode(), hashlib.sha256).hexdigest()
    ws.send('{"id": 2, "method": "public/auth", "params": {"api_key": "%s", "timestamp": "%s", "sign": "%s"}}'
            % (api_key, timestamp, sig))

def subscribe(ws, authenticate):
    """Subscribe to the specified symbol's candlestick data"""
    headers = {
        'HMAC': generate_hmac_auth('public/klines'),
    }
    ws.send(json.dumps({
        'id': 3,
        'method': 'public/klines',
        'params': {
            'channels': [f'kline.{SYMBOL}'],
        },
    }), header=headers)
    logging.info(f"{subscribe} status")

def connect(ws, self):
    
    """Establishes a websocket connection with the Crypto.com Exchange server"""
    auth = self.generate_hmac_auth()
    headers = {
        'Content-Type': 'application/json',
        'HMAC': auth,
    }
    websocket.enableTrace(True)
    self.ws = websocket.WebSocketApp("wss://stream.crypto.com/v2/user/public/heartbeat",
                                     "wss://stream.crypto.com/v2/user/public/respond-heartbeat",
                                      header=headers,
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_close=self.on_close,
                                      on_open=self.on_open)
    self.ws.run_forever(ping_interval=30)

def handle_heartbeat(ws):
    heartbeat_message = {
        "id": 1234,
        "method": "public/respond-heartbeat"
    }
    ws.send(json.dumps(heartbeat_message))

def on_message(ws, message):
    message = json.loads(message)

    if message['method'] == 'public/ticker':
        # Handle ticker updates
        symbol = message['params']['instrument_name']
        price = message['params']['last']
        print(f'{symbol} price: {price}')

    elif message['method'] == 'public/trades':
        # Handle trade updates
        symbol = message['params']['instrument_name']
        trades = message['params']['data']
        for trade in trades:
            print(f'{symbol} trade: {trade}')

    elif message['method'] == 'public/order_book':
        # Handle order book updates
        symbol = message['params']['instrument_name']
        bids = message['params']['bids']
        asks = message['params']['asks']
        print(f'{symbol} bids: {bids}')
        print(f'{symbol} asks: {asks}')

    elif message['method'] == 'public/heartbeat':
        # Handle heartbeat messages
        handle_heartbeat(ws)

    else:
        print(f'Unhandled message: {message}')

def on_error(ws, error):
    """
    Called when an error occurs on the WebSocket.
    """
    print(f"Error: {error}")
    
def on_close(close, error, disconnect):
    """
    Called when the WebSocket connection is closed.
    """
    print("WebSocket connection closed.")
    
def on_open(ws):
    api_key = 'Tkiz9QcT9SQMYxEMpobRmb'
    secret_key = 'xGTfqWzWu4zF7VizrF1Bg4'
    passphrase = "your_passphrase"
    timestamp = str(time.time())
    headers = get_auth_headers(api_key, secret_key, api_url, "GET", "/users/self/verify", timestamp)
    subscribe_request = {
        "type": "subscribe",
        "product_ids": ["CRO_USD"],
        "channels": [
            {
                "name": "ticker",
                "product_ids": [
                    "CRO_USD"
                ]
            }
        ]
    }
    print(f'Subscribe Request: {subscribe_request}')
    ws.send(json.dumps(subscribe_request))
    response = requests.get(api_url, secret_key)
    print(f'Response: {response}')
    if 'error' in response:
        print(f'Error: {response["error"]}')

def handle_message(message):
    if 'method' in message:
        if message['method'] == 'ERROR':
            error_data = json.loads(message['original'])
            print(f"Error: {error_data['message']}")
            # Resend subscription request with original data
            ws.send(error_data)
    else:
        # Handle other messages
        pass


if __name__ == "__main__":

    # Initialize the WebSocket connection.
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.crypto.com/v2/user/",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open,
                                keep_running=True)
crypocom = CryptoComAPI(api_key, secret_key, api_url)

CryptoComAPI(api_key, secret_key, api_url)

trade_strategy()
ws.run_forever()
if ws.run_forever() is True:
        ws.reconnect()
        ws.sleep(5)
        ws.run_forever()




    # Keep running the websocket connection
