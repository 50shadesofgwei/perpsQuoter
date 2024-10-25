from utils.logger import logger
from utils.marketDirectories.gmxMarketDirectory import GMXMarketDirectory
from gmx_python_sdk.scripts.v2.get.get import OraclePrices
from utils.marketDirectories.gmxContractUtils import *
from utils.globalUtils import *

def build_params_object(symbol: str, is_long: bool, trade_size_usd: float, prices: OraclePrices) -> dict:
    try:
        market_key: str = GMXMarketDirectory.get_market_key_for_symbol(symbol)
        index_token_address: str = get_index_token_address_for_symbol(symbol)
        size_delta = int(trade_size_usd * 10**30)
        if not is_long:
            size_delta = size_delta * -1
        
        params = {
            'data_store_address': '0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8',
            'market_key': market_key,
            'index_token_price': [
                int(prices[index_token_address]['maxPriceFull']),
                int(prices[index_token_address]['minPriceFull'])
            ],
            'position_size_in_usd': 0,
            'position_size_in_tokens': 0,
            'size_delta': size_delta,
            'is_long': is_long
        }

        return params
        

    except Exception as e:
            logger.error(f"GMXCallerUtils - An error occurred while building params object for {symbol}, size {trade_size_usd}: {e}", exc_info=True)
            return None

def get_midpoint_price(data: dict, symbol: str) -> float:
    try:
        if symbol == 'BTC':
            symbol = 'wBTC.b'
        for price_data in data.get('signedPrices', []):
            if price_data.get('tokenSymbol') == symbol:
                min_price = float(price_data['minPriceFull'])
                max_price = float(price_data['maxPriceFull'])
                midpoint = (min_price + max_price) / 2
                return midpoint

        raise ValueError(f"Symbol '{symbol}' not found in the provided data.")
    except Exception as e:
        logger.error(f"GMXCallerUtils - Failed to calculate midpoint price from API response: {e}")
        return None

def get_depth_from_dict(depth_dict: dict, symbol: str) -> dict:
    try:

        long_depth = depth_dict['long'].get(symbol, 0)
        short_depth = depth_dict['short'].get(symbol, 0)
        
        return {
            'long': long_depth,
            'short': short_depth
        }

    except Exception as e:
        logger.error(f"GMXCallerUtils - Failed to get depth from dictionary. Error: {e}", exc_info=True)
        return None