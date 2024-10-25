from clients.synthetixClient import *
from utils.logger import logger
import time
import concurrent.futures
from utils.globalUtils import *
import json
from web3 import *
from callers.Synthetix.synthetixCallerUtils import *
from utils.marketDirectories.synthetixV2MarketDirectory import SynthetixV2MarketDirectory

class SynthetixV2Quoter:
    def __init__(self):
        self.client = GLOBAL_SYNTHETIX_V2_CLIENT
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

        logger.error(f"Synthetixv2Caller - Failed after {self.MAX_RETRIES} retries.")
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
            logger.error(f"SynthetixV2Caller - An error occurred while processing symbols: {e}", exc_info=True)
            return None

    def get_all_quotes_for_symbol(self, symbol: str) -> dict:
        try:
            contract = SynthetixV2MarketDirectory.get_contract_object_for_symbol(symbol)
            raw_return_object = contract.functions.assetPrice().call()
            mark_price: float = raw_return_object[0] / 10**18
            index_price: float = get_price_from_pyth(symbol)

            def get_long_quote(size):
                long_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, True, size, index_price, mark_price)
                return long_quote

            def get_short_quote(size):
                short_quote = self.retry_with_backoff(self.get_quote_for_trade, symbol, False, size, index_price, mark_price)
                return short_quote

            with concurrent.futures.ThreadPoolExecutor() as executor:
                long_results = list(executor.map(get_long_quote, TARGET_TRADE_SIZES))
                short_results = list(executor.map(get_short_quote, TARGET_TRADE_SIZES))

            quotes = {
                'long': long_results,
                'short': short_results
            }

            with open(f'SNXV2BTC.json', 'w') as f:
                json.dump(quotes, f, indent=4)

            return quotes

        except Exception as e:
            logger.error(f"SynthetixV2Caller - An error occurred while executing a trade for {symbol}: {e}", exc_info=True)
            return None

    def get_quote_for_trade(
        self, 
        symbol: str, 
        is_long: bool, 
        trade_size_usd: float,
        index_price: float,
        mark_price: float
        ) -> float:
        try:
            decimals = get_decimals_for_symbol(symbol)
            size_in_asset: float = trade_size_usd / mark_price
            size_by_decimals: int = size_in_asset * 10 ** decimals
            size_delta: int = int(adjust_size_for_is_long(size_by_decimals, is_long))
            contract = SynthetixV2MarketDirectory.get_contract_object_for_symbol(symbol)
            raw_return_object = contract.functions.fillPrice(size_delta).call()
            quote_price = raw_return_object[0] / 10**18

            quote = self.build_response_object(
                symbol,
                quote_price,
                index_price,
                trade_size_usd,
                is_long
            )

            return quote

        except Exception as e:
            logger.error(f"SynthetixV2Caller - An error occurred while fetching a quote for {symbol}: {e}", exc_info=True)
            return None

    def get_max_market_value(self, symbol: str) -> dict:
        try:
            contract = SynthetixV2MarketDirectory.get_contract_object_for_symbol(symbol)
            
        
            # return all_quotes

        except Exception as e:
            logger.error(f"SynthetixV2Caller - An error occurred while fetching market depth for asset {symbol}: {e}", exc_info=True)
            return None

    def get_market_depth(self, symbol: str) -> dict:
        try:
            market_depth = self.client
        
            # return all_quotes

        except Exception as e:
            logger.error(f"SynthetixV2Caller - An error occurred while fetching market depth for asset {symbol}: {e}", exc_info=True)
            return None
    
    def build_response_object(
        self, 
        symbol: str, 
        fill_price: float, 
        index_price: float,
        absolute_trade_size_usd: float, 
        is_long: bool
        ) -> dict:
        try:
            timestamp = get_timestamp()
            side = get_side_for_is_long(is_long)
            fees = 0.69

            api_response = {
                'exchange': 'SynthetixV2OP',
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
            logger.error(f"SynthetixV2Caller - An error occurred while fetching quote data for {symbol}: {e}", exc_info=True)
            return None

SynthetixV2MarketDirectory.initialize()
x = SynthetixV2Quoter()
y = x.get_all_quotes_for_symbol(
    'BTC'
)

contract = x.client.get_market_contract('sBTC')
print(contract)