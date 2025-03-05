import asyncio
import json
import logging
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from binance_websocket.management.commands.binance_websocket_client import BinanceWebSocketClient

def async_test(test_case):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_case(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

class TestBinanceWebSocketClient(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.client = BinanceWebSocketClient(symbol="btcusdt", channel="trade")

    @async_test
    async def test_connect(self):
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            
            result = await self.client.connect()
            
            self.assertTrue(result)
            mock_connect.assert_called_once_with(self.client.ws_url)
            self.assertEqual(self.client.connection, mock_ws)

    def test_parse_trade_message(self):
        sample_message = {
            "e": "trade",
            "E": 1598520003277,
            "s": "BTCUSDT",
            "t": 12345,
            "p": "11850.15",
            "q": "0.1",
            "b": 88,
            "a": 50,
            "T": 1598520003276,
            "m": True,
            "M": True
        }
        
        result = self.client.parse_trade_message(sample_message)
        
        self.assertEqual(result['ticker_symbol'], "BTCUSDT")
        self.assertEqual(result['price'], Decimal("11850.15"))
        self.assertEqual(result['volume'], Decimal("0.1"))
        self.assertEqual(result['trade_id'], 12345)
        self.assertTrue(result['is_market_maker'])

    def test_reconnect_delay_calculation(self):
        self.assertEqual(self.client.reconnect_delay, 1)
        
        self.client.reconnect_delay = min(self.client.reconnect_delay * 2, self.client.max_reconnect_delay)
        self.assertEqual(self.client.reconnect_delay, 2)
        
        self.client.reconnect_delay = min(self.client.reconnect_delay * 2, self.client.max_reconnect_delay)
        self.assertEqual(self.client.reconnect_delay, 4)
        
        for _ in range(10):
            self.client.reconnect_delay = min(self.client.reconnect_delay * 2, self.client.max_reconnect_delay)
        
        self.assertEqual(self.client.reconnect_delay, self.client.max_reconnect_delay)

    @async_test
    async def test_full_message_flow(self):
        sample_message = json.dumps({
            "e": "trade",
            "E": 1598520003277,
            "s": "BTCUSDT",
            "t": 12345,
            "p": "11850.15",
            "q": "0.1",
            "b": 88,
            "a": 50,
            "T": 1598520003276,
            "m": True,
            "M": True
        })
        
        with patch.object(self.client, 'save_to_database', new_callable=AsyncMock) as mock_save:
            with patch.object(self.client, 'send_to_channel_layer', new_callable=AsyncMock) as mock_channel:
                await self.client.process_message(sample_message)
                
                mock_save.assert_called_once()
                
                mock_channel.assert_called_once()


if __name__ == "__main__":
    async def manual_test():
        print("Starting manual test with real Binance connection...")
        client = BinanceWebSocketClient()
        
        original_process = client.process_message
        
        async def simple_process(message):
            data = json.loads(message)
            print(f"Received: {json.dumps(data, indent=2)}")
            client.message_count = getattr(client, 'message_count', 0) + 1
            if client.message_count >= 5:
                client.running = False
        
        client.process_message = simple_process
        
        try:
            await client.listen()
        except KeyboardInterrupt:
            print("Manual test interrupted")
        finally:
            client.process_message = original_process
            await client.stop()
        
        print("Manual test completed")

    
    unittest.main() 