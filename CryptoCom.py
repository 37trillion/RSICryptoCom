import hmac
from urllib.parse import urljoin
import hashlib
import time

class CryptoComAPI:
    
    def __init__(self, api_key, api_secret, api_url='https://api.crypto.com/v2/'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url

    def _generate_signature(self, params):
        params_str = ''
        for key in sorted(params.keys()):
            params_str += str(key) + str(params[key])
        signature = hmac.new(bytes(self.api_secret, 'utf-8'), 
                             bytes(params_str, 'utf-8'), hashlib.sha256).hexdigest()
        logging.INFO(f"the {_generate_signature} status is {message}")
        logging._Level(f"{INFO}")
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
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def connect(self):
        # Test connection
        try:
            self._request('GET', 'public/get-instruments')
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
        logging.info("Connection successful.")
        return True

    def get_instruments(self):
        response = self._request('GET', 'public/get-instruments')
        return response['result']

    def get_open_orders(self, symbol):
        params = {'instrument_name': symbol}
        
        response = self._request('GET', 'private/get-open-orders', params=params)
        logging.INFO(f"The {get_open_orders} status is {message}")
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
        logging.INFO(f"the {place_order} status is {message}")
        return response['result']['order_id']
    
    def cancel_order(self, symbol, order_id):
        params = {
            'instrument_name': symbol,
            'order_id': order_id,
        }
        response = self._request('DELETE', 'private/cancel-order', json=params)
        return response['result']['order_id']
    def parse_ws_message(self, message):
        """
        Parses WebSocket message received from Crypto.com exchange.
        """
        message = json.loads(message)
        if 'e' in message:
            # This is a response to a subscription request.
            if message['e'] == 'subscribe':
                if message['success']:
                    logging.info(f"Subscription to {message['stream']} successful.")
                else:
                    logging.error(f"Subscription to {message['stream']} failed: {message['message']}")
            # This is a regular data update message.
            elif message['e'] == 'update':
                # Do something with the data.
                pass
        else:
            logging.warning(f"Unrecognized WebSocket message: {message}")
