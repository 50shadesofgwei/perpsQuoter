from utils.logger import logger
from utils.marketDirectories.gmxMarketDirectory import GMXMarketDirectory
from utils.globalUtils import *
import time
import json
import concurrent.futures
from gmx_python_sdk.scripts.v2.gmx_utils import get_execution_price_and_price_impact
from gmx_python_sdk.scripts.v2.get.get import OraclePrices
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from clients.gmxClient import ARBITRUM_CONFIG_OBJECT
from callers.GMX.gmxCallerUtils import *

class GMXQuoter:
    def __init__(self):
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
            prices = OraclePrices(ARBITRUM_CONFIG_OBJECT.chain).get_recent_prices()
            open_interest = OpenInterest(ARBITRUM_CONFIG_OBJECT)._get_data_processing(prices)


            def process_symbol(symbol):
                return self.get_all_quotes_for_symbol(symbol, open_interest)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(process_symbol, GMXMarketDirectory._all_symbols))

            for quotes in results:
                if quotes:
                    all_quotes.append(quotes)

            return all_quotes

        except Exception as e:
            logger.error(f"GMXCaller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(
        self, 
        symbol: str, 
        prices: OraclePrices, 
        open_interest: OpenInterest
        ) -> dict:

        try:
            print('made it to here')
            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size, prices, open_interest)
                return long_quote

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size, prices, open_interest)
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
            logger.error(f"GMXCaller - An error occurred while executing a trade for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(
        self, 
        symbol: str, 
        is_long: bool, 
        trade_size_usd: float, 
        prices: OraclePrices, 
        open_interest: OpenInterest
        ) -> dict:

        try:
            decimals = get_decimals_for_symbol(symbol)
            params = build_params_object(
                symbol,
                is_long,
                trade_size_usd,
                prices
            )

            execution_price_dict: dict = get_execution_price_and_price_impact(
                ARBITRUM_CONFIG_OBJECT,
                params,
                decimals
            )

            fees: float = GMXMarketDirectory.get_total_opening_fee(
                symbol,
                is_long,
                trade_size_usd,
                open_interest
            )

            quote: dict = self.build_response_object(
                symbol,
                execution_price_dict,
                trade_size_usd,
                is_long,
                prices,
                fees
            )
            
            return quote

        except Exception as e:
            logger.error(f"GMXCaller - An error occurred while fetching a quote for symbol {symbol}, trade size {trade_size_usd}: {e}", exc_info=True)
            return None
    
    def build_response_object(
        self, 
        symbol: str, 
        execution_price_dict: dict, 
        absolute_trade_size_usd: float, 
        is_long: bool, 
        prices: OraclePrices,
        fees: float
        ) -> dict:

        try:
            decimals = get_decimals_for_symbol(symbol)
            timestamp = get_timestamp()
            side = get_side_for_is_long(is_long)
            index_price = get_midpoint_price(
                prices,
                symbol
            ) / 10**decimals
            fill_price = float(execution_price_dict['execution_price'])

            api_response = {
                'exchange': 'GMXv2',
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
            logger.error(f"GMXCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None

GMXMarketDirectory.initialize()
prices = OraclePrices(ARBITRUM_CONFIG_OBJECT.chain).get_recent_prices()
open_interest = OpenInterest(ARBITRUM_CONFIG_OBJECT)._get_data_processing(prices)

x = GMXQuoter()
y = x.get_all_quotes_for_symbol(
    'BTC',
    prices,
    open_interest
)
print(y)
with open(f'prices.json', 'w') as f:
    json.dump(prices, f, indent=4)