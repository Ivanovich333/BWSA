import unittest
import logging

from binance_websocket.scripts.standalone_client import StandaloneBinanceClient

class TestStandaloneBinanceClient(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.client = StandaloneBinanceClient(symbol="btcusdt", channel="trade")

    def test_url_formation(self):
        self.assertEqual(
            self.client.ws_url,
            "wss://stream.binance.com:9443/ws/btcusdt@trade"
        )
        
        client = StandaloneBinanceClient(symbol="ethusdt", channel="kline_1m")
        self.assertEqual(
            client.ws_url,
            "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
        )

if __name__ == "__main__":
    unittest.main() 