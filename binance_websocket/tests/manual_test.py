import asyncio
import argparse
import json
import logging
import os
import sys
import signal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from binance_websocket.management.commands.binance_websocket_client import BinanceWebSocketClient
from binance_websocket.scripts.standalone_client import StandaloneBinanceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('manual_test')

def parse_args():
    parser = argparse.ArgumentParser(description='Manual test for Binance WebSocket clients')
    parser.add_argument('--client', choices=['django', 'standalone'], default='django',
                        help='Client type to test (django or standalone)')
    parser.add_argument('--symbol', default='btcusdt',
                        help='Trading symbol (e.g., btcusdt)')
    parser.add_argument('--channel', default='trade',
                        help='Channel to subscribe to (e.g., trade, kline_1m)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of messages to receive before stopping')
    return parser.parse_args()

async def main():
    args = parse_args()
    
    logger.info(f"Starting manual test with Binance {args.client} client")
    logger.info(f"Symbol: {args.symbol}, Channel: {args.channel}, Limit: {args.limit}")
    
    message_queue = asyncio.Queue()
    
    message_count = 0
    
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received interrupt signal, shutting down...")
        loop.stop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    if args.client == 'django':
        client = BinanceWebSocketClient(
            symbol=args.symbol,
            channel=args.channel
        )
        
        original_process = client.process_message
        
        async def queue_message(message):
            await message_queue.put(message)
        
        client.process_message = queue_message
        
        try:
            connected = await client.connect()
            
            if not connected:
                logger.error("Failed to connect to Binance WebSocket")
                return
            
            listen_task = asyncio.create_task(client.listen())
            
            while True:
                try:
                    message = await asyncio.wait_for(message_queue.get(), timeout=5.0)
                    
                    message_count += 1
                    
                    print(f"Message {message_count}:")
                    print(json.dumps(json.loads(message), indent=2))
                    
                    message_queue.task_done()
                    
                    if args.limit and message_count >= args.limit:
                        logger.info(f"Received {message_count} messages, stopping as requested")
                        client.running = False
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("No message received for 5 seconds")
                    if message_count > 0:
                        logger.info("Connection may be stale, stopping")
                        client.running = False
                        break
                
                except asyncio.CancelledError:
                    logger.info("Task was cancelled")
                    client.running = False
                    break
            
            await asyncio.wait_for(listen_task, timeout=5.0)
            
        except Exception as e:
            logger.error(f"Error during Django client test: {str(e)}")
        finally:
            client.process_message = original_process
            logger.info("WebSocket connection closed, manual test completed")
    
    elif args.client == 'standalone':
        client = StandaloneBinanceClient(symbol=args.symbol)
        
        try:
            await client.listen(limit=args.limit)
        except Exception as e:
            logger.error(f"Error during standalone client test: {str(e)}")
        finally:
            await client.stop()
            logger.info("Standalone client closed, manual test completed")

if __name__ == "__main__":
    asyncio.run(main()) 