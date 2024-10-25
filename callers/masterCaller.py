from callers.Binance.binanceCaller import BinanceQuoter
from callers.ByBit.bybitCaller import ByBitQuoter
from callers.GMX.gmxCaller import GMXQuoter
from callers.Hyperliquid.hyperliquidCaller import HyperLiquidQuoter
from callers.Synthetix.synthetixV2Caller import SynthetixV2Quoter
from callers.Synthetix.synthetixV3Caller import SynthetixV3Quoter

class MasterQuoter:
    def __init__(self):
        self.binance = BinanceQuoter()
        self.bybit = ByBitQuoter()
        self.GMX = GMXQuoter()
        self.hyperliquid = HyperLiquidQuoter()
        self.synthetixV2 = SynthetixV2Quoter()
        self.synthetixv3 = SynthetixV3Quoter()

    def get_all_quotes()
