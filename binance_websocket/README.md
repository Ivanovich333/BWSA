# Binance WebSocket Client

This module provides a robust WebSocket client for connecting to Binance's streaming API to collect real-time cryptocurrency trade data.

## Features

- Connects to Binance WebSocket API to receive real-time trade updates
- Parses and normalizes incoming trade messages
- Provides robust reconnection logic with exponential backoff
- Supports both immediate and batched database storage
- Integrates with Django Channels for real-time frontend updates
- Provides standalone testing capabilities

## Components

### Django Management Command

The main client is implemented as a Django management command, which can be run using:

```bash
python manage.py binance_websocket_client --symbol btcusdt --channel trade [--batch-size 100]
```

Options:
- `--symbol`: Trading pair to track (default: btcusdt)
- `--channel`: Channel to subscribe to (default: trade)
- `--batch-size`: Number of messages to batch before saving to database (optional)

### Standalone Client

A simplified standalone client is provided for testing the Binance WebSocket connection without Django dependencies:

```bash
python binance_websocket/scripts/standalone_client.py [symbol] [channel] [limit]
```

Arguments:
- `symbol`: Trading pair to monitor (default: btcusdt)
- `channel`: Channel to connect to (default: trade)
- `limit`: Number of messages to receive before exiting (default: 10)

## Data Collection Approach

The client supports two approaches to data collection:

1. **Immediate Processing**: Each trade message is immediately processed and saved to the database.
2. **Batch Processing**: Messages are accumulated in memory and saved in batches to reduce database load.

## Message Format

The Binance trade message format is parsed into the following fields:

- `ticker_symbol`: The trading pair (e.g., "BTCUSDT")
- `price`: The price at which the trade occurred
- `volume`: The quantity traded
- `trade_id`: Unique identifier for the trade
- `trade_time`: Time when the trade occurred
- `event_time`: Time when the event was processed by Binance
- `is_market_maker`: Whether the buyer was the market maker

## Error Handling

The client implements robust error handling and reconnection logic:

- WebSocket connection failures trigger reconnection with exponential backoff
- Connection drops are automatically detected and reconnection is attempted
- Parse errors for individual messages are logged but don't crash the client
- Database errors are logged and isolated to prevent crashing the entire process

## Usage in Django

The WebSocket client is integrated with Django's Channels framework to provide real-time updates to frontend clients. When new trade data is received:

1. It's processed and saved to the database (PriceUpdate model)
2. The data is sent to the "binance_data" channel group for real-time updates to connected clients

## Testing

The module includes a comprehensive suite of tests organized in the `tests/` directory:

```bash
# Run all tests
python manage.py test binance_websocket.tests

# Run specific test modules
python manage.py test binance_websocket.tests.test_models
python manage.py test binance_websocket.tests.test_websocket_client
python manage.py test binance_websocket.tests.test_standalone_client
```

### Manual Testing

For manual testing without database integration, use the provided manual test script:

```bash
# Test the Django WebSocket client
python binance_websocket/tests/manual_test.py --client=django --symbol=btcusdt --limit=5

# Test the standalone client
python binance_websocket/tests/manual_test.py --client=standalone --symbol=ethusdt --channel=trade --limit=10
```

### Test Structure

- `test_models.py`: Tests for the PriceUpdate model
- `test_websocket_client.py`: Tests for the Django management command client
- `test_standalone_client.py`: Tests for the standalone client
- `utils.py`: Common utilities and fixtures for testing
- `manual_test.py`: Script for manual testing with real Binance connections

## Dependencies

- Django 5.1+
- Channels 4.0+
- websockets 11.0+
- channels-redis 4.0+ 