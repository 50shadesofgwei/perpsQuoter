from utils.logger import *
from utils.globalUtils import *
import os
import time
from dotenv import load_dotenv
from clients.binanceClient import GLOBAL_BINANCE_CLIENT
import concurrent.futures
import json
from callers.binanceCallerUtils import *


class BinanceQuoter:
    
    def __init__(self):
        self.client = GLOBAL_BINANCE_CLIENT
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.MAX_RETRIES = 5  
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

        logger.error(f"BinanceCaller - Failed after {self.MAX_RETRIES} retries.")
        return None

    def get_quotes_for_all_symbols(self) -> dict:
        try:
            all_quotes = []
            all_symbols = BINANCE_TOKEN_LIST

            def process_symbol(symbol):
                return self.get_all_quotes_for_symbol(symbol)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(process_symbol, all_symbols))

            for quotes in results:
                if quotes:
                    all_quotes.append(quotes)
            
            with open(f'quotes.json', 'w') as f:
                json.dump(all_quotes, f, indent=4)

            return all_quotes

        except Exception as e:
            logger.error(f"BinanceCaller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(
        self, 
        symbol: str
        ) -> dict:

        try:
            
            full_symbol = symbol + 'USDT'
            if symbol == 'ETHBTC':
                full_symbol = symbol
            

            orderbook_data = self.client.depth(
                symbol=full_symbol,
                limit='500',
            )
            
            
            index_price = float(self.client.mark_price(full_symbol)['indexPrice'])

            if orderbook_data:
                asks = orderbook_data['asks']
                bids = orderbook_data['bids']

            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size, asks, index_price)
                return long_quote

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size, bids, index_price)
                return short_quote

            with concurrent.futures.ThreadPoolExecutor() as executor:
                long_results = list(executor.map(get_long_quote, TARGET_TRADE_SIZES))
                short_results = list(executor.map(get_short_quote, TARGET_TRADE_SIZES))

            quotes = {
                'long': long_results,
                'short': short_results
            }

            return quotes


        except Exception as e:
            logger.error(f"BinanceCaller - An error occurred while fetching all quotes for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(
            self, 
            symbol: str, 
            is_long: bool, 
            trade_size_usd: float,
            orders: list,
            index_price: float,
            ) -> float:

        try:
            trade_size_in_asset = trade_size_usd / index_price
            average_price = calculate_average_entry_price(orders, is_long, trade_size_in_asset)
            fees: float = get_fees(trade_size_usd)

            response_data = self.build_response_object(
                symbol,
                average_price,
                index_price,
                trade_size_usd,
                is_long,
                fees
            )

            return response_data

        except Exception as e:
            logger.error(f"BinanceCaller - An error occurred while fetching a quote for symbol {symbol}, trade size {trade_size_usd}: {e}", exc_info=True)
            return None

    
    def build_response_object(
        self, 
        symbol: str, 
        execution_price: float, 
        index_price: float, 
        absolute_trade_size_usd: float, 
        is_long: bool, 
        fees: float
        ) -> dict:

        try:
            timestamp = get_timestamp()
            side = get_side_for_is_long(is_long)

            if symbol == '1000BONK':
                if execution_price == None:
                    execution_price = 1
                execution_price = execution_price / 1000
                index_price = index_price / 1000
                symbol = 'BONK'
                if execution_price == 1:
                    execution_price = 0
            
            if symbol == '1000PEPE':
                if execution_price == None:
                    execution_price = 1
                execution_price = execution_price / 1000
                index_price = index_price / 1000
                symbol = 'PEPE'
                if execution_price == 1:
                    execution_price = 0
            
            if symbol == '1000SHIB':
                if execution_price == None:
                    execution_price = 1
                execution_price = execution_price / 1000
                index_price = index_price / 1000
                symbol = 'SHIB'
                if execution_price == 1:
                    execution_price = 0


            api_response = {
                'exchange': 'Binance',
                'symbol': symbol,
                'timestamp': timestamp,
                'side': side,
                'trade_size': absolute_trade_size_usd,
                'index_price': index_price,
                'fill_price': execution_price,
                'fees': fees
            }

            return api_response
        
        except Exception as e:
            logger.error(f"BinanceCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None

x = BinanceQuoter()
y = x.get_quotes_for_all_symbols()
