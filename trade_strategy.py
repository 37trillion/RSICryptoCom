import logging
from CryptoCom import CryptoComAPI
from ta.momentum import RSIIndicator
import time
class TradeStrategy:
    def __init__(self, api, symbol, interval, params):
        self.api = api
        self.symbol = symbol
        self.interval = interval
        self.buy_threshold = params.get("buy_threshold", 0.5)
        self.sell_threshold = params.get("sell_threshold", -0.5)
        self.stop_loss = params.get("stop_loss", -5)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_upper = params.get("rsi_upper", 70)
        self.rsi_lower = params.get("rsi_lower", 30)
        self.last_price = None
        self.last_bid_price = None
        self.last_ask_price = None
        self.last_rsi = None
        self.order_id = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def handle_message(self, message):
        data = self.api.parse_ws_message(message)
        if data.get("method") == "kline.update":
            self.process_kline_update(data.get("params"))
        elif data.get("method") == "trade":
            self.process_trade(data.get("params"))

    def process_kline_update(self, params):
        if params.get("symbol") != self.symbol or params.get("interval") != self.interval:
            return
        candle = params.get("data")[0]
        close_price = float(candle.get("c"))
        bid_price = float(candle.get("b"))
        ask_price = float(candle.get("a"))
        if self.last_price is None:
            self.last_price = close_price
        if self.last_bid_price is None:
            self.last_bid_price = bid_price
        if self.last_ask_price is None:
            self.last_ask_price = ask_price
        rsi = self.calculate_rsi(close_price)
        self.logger.info("Close price: {:.8f}, Bid price: {:.8f}, Ask price: {:.8f}, RSI: {:.2f}".format(close_price, bid_price, ask_price, rsi))
        if rsi is not None and self.last_rsi is not None:
            if self.last_rsi < self.rsi_upper and rsi >= self.rsi_upper and close_price > self.last_price and ask_price <= self.last_bid_price:
                self.logger.info("RSI crossover upper threshold, executing sell order")
                self.sell(ask_price)
            elif self.last_rsi > self.rsi_lower and rsi <= self.rsi_lower and close_price < self.last_price and bid_price >= self.last_ask_price:
                self.logger.info("RSI crossover lower threshold, executing buy order")
                self.buy(bid_price)
        self.last_price = close_price
        self.last_bid_price = bid_price
        self.last_ask_price = ask_price
        self.last_rsi = rsi

    def process_trade(self, params):
        if params.get("symbol") != self.symbol:
            return
        price = float(params.get("p"))
        if params.get("s") == "buy":
            self.logger.info("Buy order executed at {:.8f}".format(price))
            self.order_id = None
        elif params.get("s") == "sell":
            self.logger.info("Sell order executed at {:.8f}".format(price))
            self.order_id = None

    def calculate_rsi(self, close_price):
        rsi = RSIIndicator(close_price, self.rsi_period)
        return rsi.rsi()

    def execute_strategy(self, candles):
        close_price = [float(candle["close"]) for candle in candles]
        rsi = self.calculate_rsi(close_price)
        last_rsi = rsi[-1]
        logging.info(f"RSI: {last_rsi:.2f}")

        if last_rsi > self.rsi_upper:
            # Sell signal
            if self.api.has_position(self.symbol):
                response = self.api.close_position(
                    self.symbol, type="limit", price=self.api.get_ticker_price(self.symbol)
                )
                logging.info(f"Closed position: {response}")
            else:
                logging.info("No position to close")

        elif last_rsi < self.buy_threshold:
            # Buy signal
            if not self.api.has_position(self.symbol):
                response = self.api.open_position(
                    self.symbol, "buy", type="limit", price=self.api.get_ticker_price(self.symbol)
                )
                logging.info(f"Opened position: {response}")
            else:
                logging.info("Already has position")
        else:
            logging.info("No signal")

    def run(self):
        while True:
            try:
                candles = self.api.get_candles(self.symbol, self.interval)
                if candles:
                    self.execute_strategy(candles)
            except Exception as e:
                logging.exception(f"Error occurred: {e}")
            time.sleep(60) # Wait for 1 minute before running again
