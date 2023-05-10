import requests
import time
import logging
import hashlib
import hmac
import json
import websocket
from CryptoCom import CryptoComAPI
from trade_strategy import TradeStrategy
from urllib.parse import urljoin
from logging_component import setup_logger

# Set your API key and secret key
API_KEY = 'place your api_key here'
SECRET_KEY = "place your secret_key here"

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

def authenticate(ws):
    """Authenticate the websocket connection"""
    timestamp = str(api.time()["result"])
    signature = hmac.new(SECRET_KEY.encode(), timestamp.encode(), hashlib.sha256).hexdigest()
    ws.send('{"id": 2, "method": "public/auth", "params": {"api_key": "%s", "timestamp": "%s", "sign": "%s"}}'
            % (API_KEY, timestamp, signature))

def subscribe(ws):
    """Subscribe to the specified symbol's candlestick data"""
    ws.send('{"id": 3, "method": "public/subscribe", "params": {"channels": ["kline.%s"]}}' % SYMBOL)
    logging.INFO(f"{subscribe} status")

def on_message(ws, message):
    """Callback function for incoming websocket messages"""
    logging.info(f"Received message: {message}")
    if message:
        message_json = json.loads(message)
        if message_json and message_json.get('id'):
            request_id = message_json['id']
            response = requests.get(request_id)
            if response:
                response['result'] = message_json.get('result')
                response['error'] = message_json.get('error')
                response['status'] = 'done'
                logging.info(f"Response received for request id: {request_id}")
                del requests[request_id]
        else:
            logging.warning(f"Unrecognized WebSocket message: {message_json}")
    else:
        logging.warning("Received an empty message from WebSocket server.")


def on_open(ws):
    """Callback function for websocket connection"""
    logging.info("Websocket opened")
    subscribe(ws)

def on_message(ws, message):
    """Callback function for websocket messages"""
    logging.info(message)
    data = json.loads(message)
    # Handle authentication response
    if "result" in data and data["id"] == 2:
        if data["result"]:
            logging.info("Authentication successful")
        else:
            logging.error("Authentication failed")
            ws.close()
    # Handle subscription response
    elif "result" in data and data["id"] == 3:
        if data["result"]:
            logging.info("Subscription successful")
        else:
            logging.error("Subscription failed")
            ws.close()
    # Handle incoming data using the trade strategy object
    else:
        strategy.handle_message(message)

def on_error(ws, error):
    """Callback function for websocket errors"""
    logging.error(error)

def on_close(ws):
    """Callback function for websocket close"""
    logging.info("Websocket closed")

if __name__ == "__main__":
    api = CryptoComAPI(API_KEY, SECRET_KEY)

# Connect to WebSocket and start listening for messages
    api_ws = CryptoComAPI(api, ['trade.CRO_USD'], api.parse_ws_message)
    api_ws.connect()

    # Create the TradeStrategy object
    strategy = TradeStrategy(api, SYMBOL, INTERVAL, STRATEGY_PARAMS)

    # Connect to the websocket
    ws = websocket.WebSocketApp("wss://stream.crypto.com/v2/market",
                                on_open=on_open,
                                on_message=None,
                                on_error=on_error,
                                on_close=None,
                                keep_running=True)

    ws.run_forever()
    # Keep running the websocket connection
    while True:
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            ws.close()
            break
        except Exception as e:
            logging.error(f"Websocket error: {e}")
            logging.info("Retrying in 5 seconds...")
            time.sleep(5)
