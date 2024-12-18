from synthetix import *
from utils.logger import logger
from utils.marketDirectories.synthetixMarketDirectory import SynthetixMarketDirectory
from utils.globalUtils import *
from clients.synthetixClient import GLOBAL_SYNTHETIX_V3_CLIENT
import time
import json
import concurrent.futures

class SynthetixV3Quoter:
    def __init__(self):
        self.client = GLOBAL_SYNTHETIX_V3_CLIENT
        self.MAX_RETRIES = 1  
        self.BACKOFF_FACTOR = 0.5
    
    def retry_with_backoff(self, func, *args):
        retries = 0
        delay = 0.5

        while retries < self.MAX_RETRIES:
            try:
                return func(*args)
            except Exception as e:
                if "rate limit" or '429' in str(e).lower():
                    logger.warning(f"Rate limit hit, retrying in {delay} seconds... (Attempt {retries + 1}/{self.MAX_RETRIES})")
                    time.sleep(delay)
                    delay *= self.BACKOFF_FACTOR 
                    retries += 1
                else:
                    logger.error(f"Error occurred: {e}")
                    raise  

        logger.error(f"SynthetixCaller - Failed after {self.MAX_RETRIES} retries.")
        return None

    def get_quotes_for_all_symbols(self) -> dict:
        try:
            all_quotes = []

            def process_symbol(symbol):
                return self.get_all_quotes_for_symbol(symbol)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(process_symbol, SynthetixMarketDirectory._all_symbols))

            for quotes in results:
                if quotes:
                    all_quotes.append(quotes)

            return all_quotes

        except Exception as e:
            logger.error(f"SynthetixCaller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(self, symbol: str) -> dict:
        try:
            index_price = get_price_from_pyth(symbol)
            market_depth = self.get_market_depth(symbol, index_price)

            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size)
                return self.build_response_object(symbol, long_quote, size, True, index_price)

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size)
                return self.build_response_object(symbol, short_quote, size, False, index_price)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                long_results = list(executor.map(get_long_quote, TARGET_TRADE_SIZES))
                short_results = list(executor.map(get_short_quote, TARGET_TRADE_SIZES))

            quotes = {
                'long': long_results,
                'short': short_results,
                'depth': market_depth
            }

            return quotes

        except Exception as e:
            logger.error(f"SynthetixCaller - An error occurred while fetching all quotes for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(self, symbol: str, is_long: bool, trade_size_usd: float):
        try:
            adjusted_trade_size: float = adjust_size_for_is_long(trade_size_usd, is_long)
            adjusted_trade_size_in_asset: float = get_asset_amount_for_given_dollar_amount(symbol, adjusted_trade_size)
            market_id = SynthetixMarketDirectory.get_market_id(symbol)
            quote_dict = self.client.perps.get_quote(size=adjusted_trade_size_in_asset, market_id=market_id)

            return quote_dict

        except Exception as e:
            logger.error(f"SynthetixCaller - An error occurred while fetching a quote for {symbol}: {e}", exc_info=True)
            return None

    def get_market_depth(self, symbol: str, price: float) -> dict:
        try:
            market_id = SynthetixMarketDirectory.get_market_id(symbol)
            market_summary = self.client.perps.get_market_summary(market_id=market_id)
            max_open_interest = float(market_summary['max_open_interest'])
            open_interest = float(market_summary['size'])
            open_interest_usd = open_interest * price
            max_open_interest_usd = max_open_interest * price
            market_depth = max_open_interest_usd - open_interest_usd
           
            return market_depth

        except Exception as e:
            logger.error(f"SynthetixV2Caller - An error occurred while fetching market depth for asset : {e}", exc_info=True)
            return None
    
    def build_response_object(self, symbol: str, quote: dict, absolute_trade_size_usd: float, is_long: bool, index_price: float) -> dict:
        try:
            timestamp = get_timestamp()
            side = get_side_for_is_long(is_long)
            fill_price = float(quote['fill_price'])
            fees = float(quote['order_fees'])

            api_response = {
                'exchange': 'SynthetixV3Base',
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
            logger.error(f"SynthetixCaller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None