from utils.logger import logger

def get_fees(trade_size_usd: float) -> float:
    try:
        fee: float = trade_size_usd * 0.0005
        return fee
    except Exception as e:
            logger.error(f"BinanceCallerUtils - Failed to calculate fees on order size: {trade_size_usd}. Error: {e}")
            return None

def calculate_average_entry_price_binance(orders: list, is_long: bool, trade_size_in_asset: float) -> float:
    total_cost = 0.0
    total_filled = 0.0
    if is_long:
        orders.sort(key=lambda x: float(x[0]))
    else:
        orders.sort(key=lambda x: float (x[0]), reverse=True)

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
        logger.error(f'GlobalUtils - Insufficient liquidity on the orderbook for trade size {trade_size_in_asset}: Returning None.')
        return None

    average_price = total_cost / total_filled
    return average_price