import asyncio
import json
from decimal import Decimal
from unittest.mock import patch, AsyncMock

def async_test(test_case):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_case(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

SAMPLE_TRADE_MESSAGE = {
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

def create_sample_trade(
    symbol="BTCUSDT", 
    price="11850.15", 
    quantity="0.1", 
    trade_id=12345,
    is_market_maker=True
):
    message = SAMPLE_TRADE_MESSAGE.copy()
    message["s"] = symbol
    message["p"] = price
    message["q"] = quantity
    message["t"] = trade_id
    message["m"] = is_market_maker
    return message

async def test_live_connection(client, message_limit=5):
    received_messages = []
    
    original_process = client.process_message
    
    async def collect_messages(message):
        data = json.loads(message)
        received_messages.append(data)
        if len(received_messages) >= message_limit:
            client.running = False
    
    client.process_message = collect_messages
    
    try:
        await client.listen()
    finally:
        client.process_message = original_process
        await client.stop()
    
    return received_messages 