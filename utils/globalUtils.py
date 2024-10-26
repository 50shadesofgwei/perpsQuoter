from clients.synthetixClient import GLOBAL_SYNTHETIX_V3_CLIENT
from utils.logger import logger
from datetime import datetime

TARGET_TRADE_SIZES =  [100, 10000, 100000, 500000, 1000000, 5000000, 10000000, 25000000, 50000000]
NULL_ADDRESS = '0x0000000000000000000000000000000000000000'

DECIMALS = {
    "BTC": 8,
    "ETH": 18,
    "SNX": 18,
    "SOL": 9,
    "W": 18,
    "WIF": 6,
    "ARB": 18,
    "BNB": 18,
    "ENA": 18,
    "DOGE": 8,
    "AVAX": 18,
    "PENDLE": 18,
    "NEAR": 24,
    "AAVE": 18,
    "ATOM": 6,
    "XRP": 6,
    "LINK": 18,
    "UNI": 18,
    "LTC": 8,
    "OP": 18,
    "GMX": 18,
    "PEPE": 18,
}

def get_decimals_for_symbol(symbol):
    return DECIMALS.get(symbol, None)

def get_timestamp() -> str:
    timestamp = datetime.now()
    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

def get_side_for_is_long(is_long: bool) -> str:
    try:
        if is_long:
            side = 'Long' 
        else:
            side = 'Short' 
        return side

    except Exception as e:
        logger.error(f"globalUtils - Failed to determine side for is_long {is_long}: {e}")
        return None

def adjust_size_for_is_long(trade_size_usd: float, is_long: bool) -> float:
    try:
        if is_long:
            trade_size_usd = abs(trade_size_usd) 
        else:
            trade_size_usd = -abs(trade_size_usd) 
        return trade_size_usd
    except Exception as e:
        logger.error(f"globalUtils - An error occurred: {e}")
        return None

def get_price_from_pyth(symbol: str):
    try:
        response = GLOBAL_SYNTHETIX_V3_CLIENT.pyth.get_price_from_symbols([symbol])
        
        feed_id = next(iter(response['meta']))
        meta_data = response['meta'].get(feed_id, {})
        price: float = meta_data.get('price')

        if price is not None:
            return price

    except KeyError as ke:
        logger.error(f"GlobalUtils - KeyError accessing Pyth response data for {symbol}: {ke}")
        return None
    except Exception as e:
        logger.error(f"GlobalUtils - Unexpected error fetching asset price for {symbol} from Pyth: {e}")
        return None


def get_asset_amount_for_given_dollar_amount(asset: str, dollar_amount: float) -> float:
    try:
        asset_price = get_price_from_pyth(asset)
        asset_amount = dollar_amount / asset_price
        return asset_amount
    except ZeroDivisionError:
        logger.error(f"GlobalUtils - Error calculating asset amount for {asset}: Price is zero")
    return 0.0

def get_dollar_amount_for_given_asset_amount(asset: str, asset_amount: float) -> float:
    try:
        asset_price = get_price_from_pyth(asset)
        dollar_amount = asset_amount * asset_price
        return dollar_amount
    except Exception as e:
        logger.error(f"GlobalUtils - Error converting asset amount to dollar amount for {asset}: {e}")
        return 0.0

def calculate_average_entry_price(orders: list, is_long: bool, trade_size_in_asset: float) -> float:
    total_cost = 0.0
    total_filled = 0.0
    if is_long:
        orders.sort(key=lambda x: float(x[0]))

    for price_str, size_str in orders:
        price = float(price_str)
        size = float(size_str)

        if total_filled + size >= trade_size_in_asset:
            remaining_size = trade_size_in_asset - total_filled
            total_cost += remaining_size * price
            total_filled += remaining_size
            break
        else:
            total_cost += size * price
            total_filled += size

    if total_filled < trade_size_in_asset:
        return 0

    average_price = total_cost / total_filled
    return average_price

def string_to_bytes32(input_string: str) -> bytes:
    return bytes(input_string.ljust(32), 'utf-8')


BYBIT_TOKEN_LIST = [
    'BTC','ETH','SNX','SOL','W','WIF','ARB','AVAX','BNB','1000BONK','DOGE','ENA','FTM','POL','OP','ORDI','1000PEPE','RUNE','ARKM','AXL','BOME','ETHFI','GALA','GMX','INJ','LINK','PENDLE','STX','SUI','TAO','TIA','TON','AAVE','ADA','ALGO','APT','ATOM','AXS','BAL','BCH','BLUR','COMP','CRV','DOT','DYDX','EOS','ETC','ETHBTC','FIL','FLOW','FXS','GRT','ICP','IMX','JTO','JUP','LDO','LTC','MEME','NEAR','PYTH','SEI','SHIB1000','STRK','SUSHI','TRX','UNI','XLM','XRP','YFI','EIGEN','IO','MEW','MKR','NOT','PEOPLE','POL','POPCAT','RENDER','WLD','ZRO'
]

BINANCE_TOKEN_LIST = [
     'BTC','ETH','SNX','SOL','W','WIF','ARB','AVAX','BNB','1000BONK','DOGE','ENA','FTM','POL','OP','ORDI','1000PEPE','RUNE','ARKM','AXL','BOME','ETHFI','GALA','GMX','INJ','LINK','PENDLE','STX','SUI','TAO','TIA','TON','AAVE','ADA','ALGO','APT','ATOM','AXS','BAL','BCH','BLUR','COMP','CRV','DOT','DYDX','EOS','ETC','ETHBTC','FIL','FLOW','FXS','GRT','ICP','IMX','JTO','JUP','LDO','LTC','MEME','NEAR','PYTH','SEI','1000SHIB','STRK','SUSHI','TRX','UNI','XLM','XRP','YFI','EIGEN','IO','MEW','MKR','NOT','PEOPLE','POL','POPCAT','RENDER','1000SATS','WLD','ZRO'
]

HYPERLIQUID_TOKEN_LIST = [
    "BTC", "ETH", "SNX", "SOL", "W", "WIF", "ARB", "AVAX", "BNB", "DOGE", "ENA", "FTM", "OP", "ORDI", "RUNE", "GMX", "INJ", "LINK", "PENDLE", "STX", "SUI", "TAO", "TIA", "TON", "AAVE", "ADA", "APT", "ATOM", "BCH", "CRV", "DOT", "DYDX", "ETC", "FIL", "FXS", "LDO", "LTC", "NEAR", "SEI", "STRK", "SUSHI", "TRX", "UNI", "XRP"
]