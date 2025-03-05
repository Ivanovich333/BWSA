import json
import asyncio
import websockets
import logging
import time
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from binance_websocket.models import PriceUpdate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('binance_websocket_client')

class BinanceWebSocketClient:
    def __init__(self, symbol="btcusdt", channel="trade", batch_size=None):
        self.symbol = symbol.lower()
        self.channel = channel
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@{self.channel}"
        self.connection = None
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.running = False
        self.batch_size = batch_size
        self.message_buffer = []
        self.channel_layer = get_channel_layer()
    
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
                'trade_time': datetime.datetime.fromtimestamp(message_data['T'] / 1000.0, tz=datetime.timezone.utc),
                'event_time': datetime.datetime.fromtimestamp(message_data['E'] / 1000.0, tz=datetime.timezone.utc),
                'is_market_maker': message_data['m'],
                'raw_data': message_data,
            }
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None
    
    async def process_message(self, message):
        try:
            message_data = json.loads(message)
            parsed_data = self.parse_trade_message(message_data)
            
            if parsed_data:
                logger.info(f"Trade: {parsed_data['ticker_symbol']} @ {parsed_data['price']} ({parsed_data['volume']})")
                
                if not self.batch_size:
                    await self.save_to_database(parsed_data)
                else:
                    self.message_buffer.append(parsed_data)
                    
                    if len(self.message_buffer) >= self.batch_size:
                        await self.process_batch()
                
                await self.send_to_channel_layer(parsed_data)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def process_batch(self):
        if not self.message_buffer:
            return
            
        logger.info(f"Processing batch of {len(self.message_buffer)} messages")
        
        try:
            for data in self.message_buffer:
                await self.save_to_database(data)
                
            self.message_buffer = []
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
    
    async def save_to_database(self, data):
        try:
            price_update = PriceUpdate(
                ticker_symbol=data['ticker_symbol'],
                price=data['price'],
                volume=data['volume'],
            )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, price_update.save)
            
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
    
    async def send_to_channel_layer(self, data):
        try:
            await self.channel_layer.group_send(
                "binance_data",
                {
                    "type": "binance_message",
                    "message": {
                        "ticker_symbol": data['ticker_symbol'],
                        "price": str(data['price']),
                        "volume": str(data['volume']),
                        "trade_time": data['trade_time'].isoformat(),
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending to channel layer: {str(e)}")
    
    async def listen(self):
        self.running = True
        
        while self.running:
            connected = await self.connect()
            
            if not connected:
                connected = await self.reconnect()
                if not connected:
                    continue
            
            try:
                async for message in self.connection:
                    await self.process_message(message)
            
            except websockets.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {str(e)}")
            
            if self.running:
                await self.reconnect()
    
    async def stop(self):
        self.running = False
        
        if self.batch_size and self.message_buffer:
            await self.process_batch()
        
        if self.connection:
            await self.connection.close()
            logger.info("WebSocket connection closed")


class Command(BaseCommand):
    help = 'Run the Binance WebSocket client to collect trade data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            default='btcusdt',
            help='Symbol to track (e.g., btcusdt)'
        )
        parser.add_argument(
            '--channel',
            default='trade',
            help='Channel to subscribe to (e.g., trade, kline_1m)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=None,
            help='Number of messages to batch before saving to the database'
        )

    def handle(self, *args, **options):
        symbol = options['symbol']
        channel = options['channel']
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.SUCCESS(f'Starting Binance WebSocket client for {symbol}@{channel}'))
        
        if batch_size:
            self.stdout.write(f'Batching enabled with batch size: {batch_size}')
        else:
            self.stdout.write('Processing trades immediately (no batching)')
        
        client = BinanceWebSocketClient(
            symbol=symbol,
            channel=channel,
            batch_size=batch_size
        )
        
        try:
            asyncio.run(client.listen())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Interrupted by user, shutting down...'))
            asyncio.run(client.stop())
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Binance WebSocket client stopped')) 