from utils.logger import logger

def decode_bytes(byte_value: bytes) -> str:
    return byte_value.decode('utf-8').rstrip('\x00')

def scale_value(value: int, decimals: int) -> float:
    return value / (10 ** decimals)

def process_market_data(raw_data):
    try:
        processed_data = []
        for item in raw_data:

            market_address = item[0]  
            token_symbol = decode_bytes(item[1])  
            market_symbol = decode_bytes(item[2]) 
            leverage = scale_value(item[3], 18)
            open_interest = scale_value(item[4], 18)



            processed_data.append({
                'market_address': market_address,
                'token_symbol': token_symbol,
                'market_symbol': market_symbol,
                'leverage': leverage,
                'open_interest': open_interest,
            })

        return processed_data
    
    except Exception as e:
        logger.error(f"SynthetixCallerUtils - An error occurred while formatting market data from the contract: {e}", exc_info=True)
        return None