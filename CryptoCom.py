import json
import logging
import hmac
from urllib.parse import urljoin
import hashlib
import time
import websocket
import requests

class CryptoComAPI:

    def __init__(self, api_key, api_secret, api_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url

    def _generate_signature(self, params):
        params_str = ''
        for key in sorted(params.keys()):
            params_str += str(key) + str(params[key])
        signature = hmac.new(bytes(self.api_secret, 'utf-8'),
                             bytes(params_str, 'utf-8'), hashlib.sha256).hexdigest()
        return signature

    def _request(self, method, path, **kwargs):
        url = urljoin(self.api_url, path)
        params = kwargs.get('params', {})
        params['api_key'] = self.api_key
        params['timestamp'] = int(time.time() * 1000)
        kwargs['params'] = params
        kwargs['headers'] = {
            'Content-Type': 'application/json',
            'X-MBX-APIKEY': self.api_key,
        }
        kwargs['params']['signature'] = self._generate_signature(params)
        response = requests.get(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def connect(self):
        # Test connection
        try:
            self._request('GET', 'public/auth')
        except Exception as e:
            logging.error(f'Connection failed: {e}')
            return False
        logging.info('Connection successful.')
        return True

    def get_instruments(self):
        response = self._request('GET', 'public/get-instruments')
        return response['result']

    def get_open_orders(self, symbol):
        params = {'instrument_name': symbol}

        response = self._request('GET', 'private/get-open-orders', params=params)
        return response['result']['orders']

    def place_order(self, symbol, side, price, quantity):
        params = {
            'instrument_name': symbol,
            'side': side,
            'price': price,
            'quantity': quantity,
            'type': 'LIMIT',
            'time_in_force': 'GOOD_TILL_CANCEL',
        }

        response = self._request('POST', 'private/create-order', json=params)
        return response['result']['order_id']

    def cancel_order(self, symbol, order_id):
        params = {
            'instrument_name': symbol,
            'order_id': order_id,
        }
        response = self._request('DELETE', 'private/cancel-order', json=params)
        return response['result']['order_id']

    def on_message(self, ws, message):
        """
        This function will be called each time a new message is received from the WebSocket connection.
        """
        logging.info(f'Received message: {message}')

        # Send heartbeat message back to the server
        message_data = json.loads(message)
        if message_data.get('ping'):
            ws.send(json.dumps({'pong': message_data['ping']}))

    
    def start_websocket(self, symbol):
        endpoint = f"wss://ws.crypto.com/v2/market"
        ws = websocket.WebSocketApp(endpoint,
                                    on_open=lambda ws: self._on_open(ws, symbol),
                                    on_message=lambda ws, message: self._on_message(ws, message),
                                    on_error=lambda ws, error: self._on_error(ws, error),
                                    on_close=lambda ws: self._on_close(ws))
        ws.run_forever()

    def _on_open(self, ws, symbol):
        logging.info(f"WebSocket connection opened to {ws.url}")
        self._subscribe(ws, symbol)

    def _on_message(self, ws, message):
        logging.info(f"Received message: {message}")
        self.parse_ws_message(message)

    def _on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")

    def _on_close(self, ws):
        logging.info(f"WebSocket connection closed")

    def _subscribe(self, ws, symbol):
        params = {
            "method": "subscribe",
            "id": "1",
            "params": {
                "channels": [f"trades.{symbol}"]
            }
        }
        message = json.dumps(params)
        ws.send(message)
        logging.info(f"Subscribing to trades for {symbol}")
