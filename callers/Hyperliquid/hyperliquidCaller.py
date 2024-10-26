from hyperliquid.info import *
import json
from utils.logger import logger
import time
import concurrent.futures
from utils.globalUtils import *
from callers.Hyperliquid.hyperliquidCallerUtils import *

class HyperLiquidQuoter:

    def __init__(self):
        self.client = Info()
        self.MAX_RETRIES = 1 
        self.BACKOFF_FACTOR = 0.5

    def retry_with_backoff(self, func, *args):
        retries = 0
        delay = 0.5

        while retries < self.MAX_RETRIES:
            try:
                return func(*args)
            except Exception as e:
                if "rate limit" in str(e).lower():
                    logger.warning(f"Rate limit hit, retrying in {delay} seconds... (Attempt {retries + 1}/{self.MAX_RETRIES})")
                    time.sleep(delay)
                    delay *= self.BACKOFF_FACTOR 
                    retries += 1
                else:
                    logger.error(f"Error occurred: {e}")
                    raise  

        logger.error(f"HyperiquidCaller - Failed after {self.MAX_RETRIES} retries.")
        return None

    def get_quotes_for_all_symbols(self) -> dict:
        try:
            all_quotes = []

            def process_symbol(symbol):
                index_price = self.client.all_mids()[symbol]
                return self.get_all_quotes_for_symbol(symbol, index_price)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(process_symbol, HYPERLIQUID_TOKEN_LIST))

            for quotes in results:
                if quotes:
                    all_quotes.append(quotes)

            return all_quotes

        except Exception as e:
            logger.error(f"HyperiquidCaller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(
        self, 
        symbol: str,
        index_price: float
        ) -> dict:

        try:
            index_price = get_price_from_pyth(symbol)
            orderbook_data = self.get_orderbook_for_symbol(symbol)
            depth = tally_orderbook(orderbook_data, index_price)
        
            
            if orderbook_data:
                asks = orderbook_data['levels'][0]
                bids = orderbook_data['levels'][1]
                with open(f'hyperliquidBTCasks.json', 'w') as f:
                    json.dump(asks, f, indent=4)


            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size, asks, index_price)
                return long_quote

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size, bids, index_price)
                return short_quote

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                long_results = list(executor.map(get_long_quote, TARGET_TRADE_SIZES))
                short_results = list(executor.map(get_short_quote, TARGET_TRADE_SIZES))

            quotes = {
                'long': long_results,
                'short': short_results,
                'depth': depth
            }

            return quotes


        except Exception as e:
            logger.error(f"HyperiquidCaller - An error occurred while fetching all quotes for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(
        self, 
        symbol: str, 
        is_long: bool, 
        trade_size_usd: float,
        orders: list,
        index_price: float
        ):

        try:
            trade_size_in_asset: float = get_asset_amount_for_given_dollar_amount(symbol, trade_size_usd)
            average_price = calculate_average_entry_price_hyperliquid(orders, is_long, trade_size_in_asset)
            fees = get_fees(trade_size_usd)

            response_data = self.build_response_object(
                symbol,
                trade_size_usd,
                is_long,
                index_price,
                average_price,
                fees
            )


            return response_data

        except Exception as e:
            logger.error(f"HyperiquidCaller - An error occurred while executing a trade for {symbol}: {e}", exc_info=True)
            return None
    
    def build_response_object(
        self, 
        symbol: str, 
        absolute_trade_size_usd: float, 
        is_long: bool, 
        index_price: float, 
        fill_price: float, 
        fees: float
        ) -> dict:

        try:
            timestamp = get_timestamp()
            side = get_side_for_is_long(is_long)

            api_response = {
                'exchange': 'Hyperliquid',
                'symbol': symbol,
                'timestamp': timestamp,
                'side': side,
                'trade_size': absolute_trade_size_usd,
                'index_price': index_price,
                'fill_price': fill_price,
                'fees': fees
            }

            return api_response
        
        except Exception as e:
            logger.error(f"HyperiquidCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None

    def get_orderbook_for_symbol(self, symbol: str):
        try:
            orderbook = self.client.l2_snapshot(symbol)
            return orderbook
        
        except Exception as e:
            logger.error(f"HyperiquidCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None
        