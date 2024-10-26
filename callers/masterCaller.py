from callers.Binance.binanceCaller import BinanceQuoter
from callers.ByBit.bybitCaller import ByBitQuoter
from callers.GMX.gmxCaller import GMXQuoter
from callers.Hyperliquid.hyperliquidCaller import HyperLiquidQuoter
from callers.Synthetix.synthetixV2Caller import SynthetixV2Quoter
from callers.Synthetix.synthetixV3Caller import SynthetixV3Quoter
from utils.logger import logger
import json
from utils.marketDirectories.gmxMarketDirectory import GMXMarketDirectory
from utils.marketDirectories.synthetixMarketDirectory import SynthetixMarketDirectory
from utils.marketDirectories.synthetixV2MarketDirectory import SynthetixV2MarketDirectory
import schedule
import time

class MasterQuoter:
    def __init__(self):
        self.binance = BinanceQuoter()
        self.bybit = ByBitQuoter()
        self.GMX = GMXQuoter()
        self.hyperliquid = HyperLiquidQuoter()
        self.synthetixV2 = SynthetixV2Quoter()
        self.synthetixv3 = SynthetixV3Quoter()
        GMXMarketDirectory.initialize()
        SynthetixMarketDirectory.initialize()
        SynthetixV2MarketDirectory.initialize()
        self.most_recent_quotes = {}

    def hourly_runner(func):
        try:
            schedule.every(1).hours.do(func)

            while True:
                schedule.run_pending()
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"MasterCaller - An error occurred with the hourly runner: {e}", exc_info=True)
            return None

    def get_all_quotes(self):
        try:
            binance_quotes = self.binance.get_quotes_for_all_symbols()
            bybit_quotes = self.bybit.get_quotes_for_all_symbols()
            gmx_quotes = self.GMX.get_quotes_for_all_symbols()
            hyperliquid_quotes = self.hyperliquid.get_quotes_for_all_symbols()
            snxv2_quotes = self.synthetixV2.get_quotes_for_all_symbols()
            snxv3_quotes = self.synthetixv3.get_quotes_for_all_symbols()

            all_quotes = {
                'binance': binance_quotes,
                'bybit': bybit_quotes,
                'gmx': gmx_quotes,
                'hyperliquid': hyperliquid_quotes,
                'snxv2': snxv2_quotes,
                'snxv3': snxv3_quotes
            }

            with open('TESTRUN.json', 'w') as f:
                json.dump(all_quotes, f, indent=4)
        
        except Exception as e:
            logger.error(f"MasterCaller - An error occurred collecting quotes: {e}", exc_info=True)
            return None

x = MasterQuoter()
x.get_all_quotes()