from web3 import *
from dotenv import load_dotenv
from utils.logger import logger
import json
from clients.synthetixClient import *
from callers.Synthetix.synthetixCallerUtils import *
from utils.globalUtils import *

load_dotenv()

class SynthetixV2MarketDirectory:
    contract_interfaces = {}
    _markets = {}
    _file_path = 'synthetix_v2_markets.json'
    _is_initialized = False
    _all_symbols = []

    @classmethod
    def initialize(cls):
        try:
            if not cls._is_initialized:
                cls.update_all_market_parameters()
                cls._is_initialized = True
                cls._all_symbols = cls.get_all_valid_symbols()
                logger.info('SynthetixV2MarketDirectory - Markets Initialized')
        except FileNotFoundError:
            logger.error("SynthetixV2MarketDirectory - No existing market file found. Starting fresh.")
        except json.JSONDecodeError:
            logger.error("SynthetixV2MarketDirectory - Error decoding JSON. Starting with an empty dictionary.")

    @classmethod
    def save_market_to_file(cls):
        try:
            with open(cls._file_path, 'w') as file:
                json.dump(cls._markets, file)
        except Exception as e:
            logger.error(f"SynthetixV2MarketDirectory - Failed to save markets to file: {e}")

    @classmethod
    def load_markets_from_file(cls):
        try:
            with open('markets.json', 'r') as f:
                cls._markets = json.load(f)
        except FileNotFoundError:
            logger.error("SynthetixV2MarketDirectory - Market file not found. Starting with an empty dictionary.")
            cls._markets = {}
    
    @classmethod
    def update_all_market_parameters(cls):
        try:
            market_data = SNXV2MarketProxy.functions.allProxiedMarketSummaries().call()
            processed_data = process_market_data(market_data)
            cls.contract_interfaces = cls.create_contract_interfaces(processed_data, web3)
        except Exception as e:
            logger.error(f"SynthetixV2MarketDirectory - Failed to build market directory. Error: {e}", exc_info=True)
        
    @classmethod
    def create_contract_interfaces(cls, contract_data: list, w3: Web3):
        contract_interfaces = {}
        with open('utils/ABIs/SNXV2PerpsMarket.json', 'r') as a:
            abi = json.load(a)
        
        with open('utils/ABIs/SNXV2PerpsMarketViews.json', 'r') as b:
            views_abi = json.load(b)

        with open('utils/ABIs/SNXV2MarketData.json', 'r') as c:
            data_abi = json.load(c)
        
        for data in contract_data:
            if data['token_symbol'] == 'sBTC':
                data['token_symbol'] = 'BTC'
            if data['token_symbol'] == 'sETH':
                data['token_symbol'] = 'ETH'
            
            contract = w3.eth.contract(address=Web3.to_checksum_address(data['market_address']), abi=abi)
            views_contract = w3.eth.contract(address=Web3.to_checksum_address(data['market_address']), abi=views_abi)
            data_contract = w3.eth.contract(address='0x340B5d664834113735730Ad4aFb3760219Ad9112', abi=data_abi)

            contract_interface = {
                'views_contract': views_contract,
                'perps_market_contract': contract,
                'market_data_contract': data_contract,
                'address': data['market_address'],
                'symbol': data['token_symbol']
            }
            contract_interfaces[data['token_symbol']] = contract_interface
        
        return contract_interfaces

    @classmethod
    def get_all_valid_symbols(cls) -> list:
        try:
            symbols = list(set(info['symbol'] for info in cls.contract_interfaces.values()))
            return symbols
        except Exception as e:
            logger.error(f"SynthetixV2MarketDirectory - Failed to parse valid symbols from market object: Error: {e}", exc_info=True)
            return []
    
    @classmethod
    def get_contract_object_for_symbol(cls, symbol: str) -> dict:
        try:
            contract_interface = cls.contract_interfaces[symbol]
            return contract_interface

        except Exception as e:
            logger.error(f"SynthetixV2MarketDirectory - Failed to find corresponding contract for symbol {symbol}: Error: {e}", exc_info=True)
            return []