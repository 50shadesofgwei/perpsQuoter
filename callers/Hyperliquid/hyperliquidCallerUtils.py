from utils.logger import logger

def get_fees(trade_size_usd: float) -> float:
    try:
        fee: float = trade_size_usd * 0.00035
        return fee
    except Exception as e:
            logger.error(f"Hyperliquid - Failed to calculate fees on order size: {trade_size_usd}. Error: {e}")
            return None

def calculate_average_entry_price_hyperliquid(orders: list, is_long: bool, trade_size_in_asset: float) -> float:
    total_cost = 0.0
    total_filled = 0.0

    orders.sort(key=lambda x: float(x["px"]), reverse=not is_long)

    for order in orders:
        price = float(order["px"])
        size = float(order["sz"])

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

def tally_orderbook(orderbook: dict, index_price: float) -> dict:
    bids = orderbook['levels'][0]
    asks = orderbook['levels'][1]
    
    total_bids = sum(float(order['sz']) for order in bids) * index_price
    total_asks = sum(float(order['sz']) for order in asks) * index_price
    
    return {
        'total_bids': total_bids,
        'total_asks': total_asks
    }