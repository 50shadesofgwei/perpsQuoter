from clients.bybit import *
from pubsub import pub
import os
import time
from dotenv import load_dotenv
from utils.globalUtils import *
from utils.logger import logger
import concurrent.futures
from callers.bybitCallerUtils import *
import json

class ByBitQuoter:
    
    def __init__(self):
        self.client = GLOBAL_BYBIT_CLIENT
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
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

        logger.error(f"GMXCaller - Failed after {self.MAX_RETRIES} retries.")
        return None

    def get_quotes_for_all_symbols(self) -> dict:
        try:
            all_quotes = []
            all_symbols = []



            def process_symbol(symbol):
                return self.get_all_quotes_for_symbol(symbol)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(process_symbol, all_symbols))

            for quotes in results:
                if quotes:
                    all_quotes.append(quotes)

            return all_quotes

        except Exception as e:
            logger.error(f"SynthetixCaller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(
        self, 
        symbol: str
        ) -> dict:

        try:
            full_symbol = symbol + 'USDT'
            ticker_data = self.client.get_tickers(
                category='linear',
                symbol=full_symbol,
                limit='1',
                fundingInterval='1'
            )
            index_price = float(ticker_data['indexPrice'])
            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size, index_price)
                return long_quote

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size, index_price)
                return short_quote

            with concurrent.futures.ThreadPoolExecutor() as executor:
                long_results = list(executor.map(get_long_quote, TARGET_TRADE_SIZES))
                short_results = list(executor.map(get_short_quote, TARGET_TRADE_SIZES))

            quotes = {
                'long': long_results,
                'short': short_results
            }

            with open(f'{symbol}_quotes.json', 'w') as f:
                json.dump(quotes, f, indent=4)

            return quotes

        except Exception as e:
            logger.error(f"SynthetixCaller - An error occurred while executing a trade for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(
        self, 
        symbol: str, 
        is_long: bool, 
        trade_size_usd: float,
        index_price: float = None
        ) -> float:

        try:
            full_symbol = symbol + 'USDT'
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, trade_size_usd)
            qty_step_raw = self.get_qty_step(full_symbol)
            qty_step = normalize_qty_step(qty_step_raw)
            truncated_value = str(f"{trade_size_in_asset:.{qty_step}f}")

            orderbook_data = self.client.get_orderbook(
                category='linear',
                symbol=full_symbol,
                limit='10',
            )

            with open(f'prices.json', 'w') as f:
                json.dump(orderbook_data, f, indent=4)

            if orderbook_data and 'result' in orderbook_data and 'list' in orderbook_data['result']:
                ticker_data = orderbook_data['result']['list'][0] 


                fees: float = get_fees(trade_size_usd)

                # response_data = self.build_response_object(
                #     symbol,
                #     execution_price,
                #     index_price,
                #     trade_size_usd,
                #     is_long,
                #     fees
                # )

                return orderbook_data

            else:
                logger.error(f"GMXCaller - No valid ticker data found for {symbol}")
                return None

        except Exception as e:
            logger.error(f"GMXCaller - An error occurred while fetching a quote for symbol {symbol}, trade size {trade_size_usd}: {e}", exc_info=True)
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

            api_response = {
                'exchange': 'ByBit',
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
            logger.error(f"SynthetixCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None

    def get_qty_step(self, symbol: str) -> float:
        try:
            response = self.client.get_instruments_info(
                category='linear',
                symbol=symbol
            )

            instruments = response.get('result', {}).get('list', [])
            if not instruments:
                return None
            
            qty_step_str = instruments[0].get('lotSizeFilter', {}).get('qtyStep', None)

            if qty_step_str is not None:
                return float(qty_step_str)
            else:
                return None
        except Exception as e:
            logger.error(f'ByBitPositionController - Error while retrieving qtyStep for symbol {symbol}. Error: {e}')
            return None

x = ByBitQuoter()
y = x.get_quote_for_trade(
    'BTC',
    True,
    500000
)
print(y)