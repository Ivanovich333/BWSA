import asyncio
import json
import logging
import sys
import argparse
import datetime
from decimal import Decimal

import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('binance_standalone_client')


class StandaloneBinanceClient:
    
    def __init__(self, symbol="btcusdt", channel="trade"):
        self.symbol = symbol.lower()
        self.channel = channel
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@{self.channel}"
        self.connection = None
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.running = False
    
    async def connect(self):
        try:
            self.connection = await websockets.connect(self.ws_url)
            self.reconnect_delay = 1
            logger.info(f"Connected to Binance WebSocket: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {str(e)}")
            return False
    
    async def reconnect(self):
        logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        return await self.connect()
    
    def parse_trade_message(self, message_data):
        try:
            return {
                'ticker_symbol': message_data['s'],
                'price': Decimal(message_data['p']),
                'volume': Decimal(message_data['q']),
                'trade_id': message_data['t'],
                'trade_time': datetime.datetime.fromtimestamp(
                    message_data['T'] / 1000.0, 
                    tz=datetime.timezone.utc
                ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'is_market_maker': message_data['m'],
            }
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None
    
    async def listen(self, limit=None):
        self.running = True
        message_count = 0
        
        while self.running:
            connected = await self.connect()
            
            if not connected:
                connected = await self.reconnect()
                if not connected:
                    continue
            
            try:
                async for message in self.connection:
                    try:
                        message_data = json.loads(message)
                        parsed_data = self.parse_trade_message(message_data)
                        
                        if parsed_data:
                            message_count += 1
                            print(f"[{message_count}] Trade: {parsed_data['ticker_symbol']} @ "
                                  f"{parsed_data['price']} | Volume: {parsed_data['volume']} | "
                                  f"Time: {parsed_data['trade_time']} | "
                                  f"Market Maker: {'Yes' if parsed_data['is_market_maker'] else 'No'}")
                            
                            if limit and message_count >= limit:
                                logger.info(f"Received {message_count} messages, stopping as requested")
                                self.running = False
                                break
                                
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON: {message}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                
                if not self.running:
                    break
                    
            except websockets.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {str(e)}")
            
            if self.running:
                await self.reconnect()
    
    async def stop(self):
        self.running = False
        
        if self.connection:
            await self.connection.close()
            logger.info("WebSocket connection closed")


async def main():
    parser = argparse.ArgumentParser(description='Standalone Binance WebSocket Client')
    parser.add_argument('symbol', nargs='?', default='btcusdt', help='Symbol to track (e.g., btcusdt)')
    parser.add_argument('channel', nargs='?', default='trade', help='Channel to subscribe to (e.g., trade, kline_1m)')
    parser.add_argument('limit', nargs='?', type=int, default=10, help='Number of messages to receive before exiting')
    
    args = parser.parse_args()
    
    print(f"Starting Standalone Binance WebSocket Client")
    print(f"Symbol: {args.symbol}")
    print(f"Channel: {args.channel}")
    print(f"Message Limit: {args.limit}")
    print("-" * 80)
    
    client = StandaloneBinanceClient(
        symbol=args.symbol,
        channel=args.channel
    )
    
    try:
        await client.listen(limit=args.limit)
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down...")
    finally:
        await client.stop()
    
    print("Binance WebSocket client stopped")


if __name__ == "__main__":
    asyncio.run(main()) 