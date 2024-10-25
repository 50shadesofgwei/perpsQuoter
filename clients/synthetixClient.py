from synthetix import *
from kwenta import *
from hexbytes import *
import os
from dotenv import load_dotenv
from enum import Enum
from utils.logger import logger
from web3 import *
import json

load_dotenv()

class SynthetixEnvVars(Enum):
    BASE_PROVIDER_RPC = 'BASE_PROVIDER_RPC'
    CHAIN_ID_BASE = 'CHAIN_ID_BASE'
    ADDRESS = 'ADDRESS'
    PRIVATE_KEY = 'PRIVATE_KEY'

    
    def get_value(self):
        value = os.getenv(self.value)
        if value is None:
            raise ValueError(f"Environment variable for {self.name} not found.")
        return value


def get_synthetix_v3_client() -> Synthetix:
    tracking_code: str = '0x46756e64696e67426f7400000000000000000000000000000000000000000000'
    synthetix_client = Synthetix(
                provider_rpc=SynthetixEnvVars.BASE_PROVIDER_RPC.get_value(),
                private_key=SynthetixEnvVars.PRIVATE_KEY.get_value(),
                tracking_code=tracking_code
    )
    return synthetix_client

def get_synthetix_v2_client() -> Kwenta:
    try:
        kwenta = Kwenta(
            network_id=10,
            provider_rpc=os.getenv('OPTIMISM_PROVIDER_RPC'),
            wallet_address=os.getenv('ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY')
        )

        return kwenta

    except Exception as e:
            logger.error(f"SynthetixClient - Failed to build v2 client - Error: {e}", exc_info=True)
            return None

web3 = Web3(Web3.HTTPProvider(os.getenv('OPTIMISM_PROVIDER_RPC')))

with open('utils/ABIs/SNXV2MarketProxy.json') as abi_file:
    contract_abi = json.load(abi_file)

contract_address = '0x340B5d664834113735730Ad4aFb3760219Ad9112'
SNXV2MarketProxy = web3.eth.contract(address=contract_address, abi=contract_abi)


GLOBAL_SYNTHETIX_V3_CLIENT = get_synthetix_v3_client()
GLOBAL_SYNTHETIX_V2_CLIENT = get_synthetix_v2_client()