import asyncio
import json
import logging
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal

from binance_websocket.tests.utils import async_test, create_sample_trade, SAMPLE_TRADE_MESSAGE

from binance_websocket.management.commands.binance_websocket_client import BinanceWebSocketClient

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
        sample_message = SAMPLE_TRADE_MESSAGE
        
        result = self.client.parse_trade_message(sample_message)
        
        self.assertEqual(result['ticker_symbol'], "BTCUSDT")
        self.assertEqual(result['price'], Decimal("11850.15"))
        self.assertEqual(result['volume'], Decimal("0.1"))
        self.assertEqual(result['trade_id'], 12345)
        self.assertTrue(result['is_market_maker'])
        
        custom_sample = create_sample_trade(
            symbol="ETHUSDT", 
            price="3200.50", 
            quantity="2.5", 
            trade_id=67890,
            is_market_maker=False
        )
        
        result = self.client.parse_trade_message(custom_sample)
        self.assertEqual(result['ticker_symbol'], "ETHUSDT")
        self.assertEqual(result['price'], Decimal("3200.50"))
        self.assertEqual(result['volume'], Decimal("2.5"))
        self.assertEqual(result['trade_id'], 67890)
        self.assertFalse(result['is_market_maker'])

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
        sample_message = json.dumps(SAMPLE_TRADE_MESSAGE)
        
        with patch.object(self.client, 'save_to_database', new_callable=AsyncMock) as mock_save:
            with patch.object(self.client, 'send_to_channel_layer', new_callable=AsyncMock) as mock_channel:
                await self.client.process_message(sample_message)
                
                mock_save.assert_called_once()
                
                mock_channel.assert_called_once()

    @async_test
    async def test_batch_processing(self):
        batch_client = BinanceWebSocketClient(symbol="btcusdt", channel="trade", batch_size=3)
        
        with patch.object(batch_client, 'save_to_database', new_callable=AsyncMock) as mock_save:
            with patch.object(batch_client, 'send_to_channel_layer', new_callable=AsyncMock) as mock_channel:
                
                for i in range(2):
                    message = create_sample_trade(trade_id=i+1)
                    await batch_client.process_message(json.dumps(message))
                
                mock_save.assert_not_called()
                
                self.assertEqual(mock_channel.call_count, 2)
                
                message = create_sample_trade(trade_id=3)
                await batch_client.process_message(json.dumps(message))
                
                self.assertEqual(mock_save.call_count, 3)
                
                self.assertEqual(mock_channel.call_count, 3)


if __name__ == "__main__":
    unittest.main() 