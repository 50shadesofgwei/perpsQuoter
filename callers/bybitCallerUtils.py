from utils.logger import logger

def normalize_qty_step(qty_step: float) -> int:
    decimal_str = str(qty_step)
    if '.' in decimal_str:
        return len(decimal_str.split('.')[1])
    else:
        return 0

def get_side(is_long: bool) -> str:
        if is_long:
            side = 'Buy'
            return side
        else:
            side = 'Sell'
            return side

def get_opposite_side(side: str) -> str:
    try:
        if side == 'Buy' or side == 'Sell':
            if side == 'Buy':
                opposite_side = 'Sell'
            elif side == 'Sell':
                opposite_side = 'Buy'
            return opposite_side
        else:
            logger.error(f"ByBitCallerUtils - get_opposite_side called with an argument that is neither 'Buy' nor 'Sell', arg = {side}.")
            return None
    except Exception as e:
            logger.error(f"ByBitCallerUtils - Failed to get opposite side for input: {side}. Error: {e}")
            return None

def get_fees(trade_size_usd: float) -> float:
    try:
        fee: float = trade_size_usd * 0.00055
        return fee
    except Exception as e:
            logger.error(f"ByBitCallerUtils - Failed to calculate fees on order size: {trade_size_usd}. Error: {e}")
            return None