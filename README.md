# MGL Analytics - Production Ready Market Analysis System

## Overview

MGL Analytics is a professional-grade cryptocurrency and stock market analysis system with:

- **Asynchronous Processing**: Using `aiohttp` for concurrent API requests
- **SQLite Database**: Persistent storage of market data and signals
- **Centralized Error Handling**: `@safe_run` decorator for robust error management
- **Configuration Management**: YAML-based config with environment variable overrides
- **Technical Analysis**: RSI, MACD, Stochastic, and Volume indicators
- **Telegram Notifications**: Real-time market alerts
- **Production Ready**: PEP 8 compliant, modular architecture

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/muratgungorcnt/MGL-Analytics.git
   cd MGL-Analytics
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram credentials
   nano .env
   ```

5. **Or set environment variables directly**
   ```bash
   export TELEGRAM_TOKEN="your_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

## Configuration

### config.yaml Structure

The system is configured via `config.yaml`:

```yaml
telegram:
  token: "${TELEGRAM_TOKEN}"  # Environment variable
  chat_id: "${TELEGRAM_CHAT_ID}"
  timeout: 15

api:
  binance:
    base_url: "https://api.binance.com/api/v3"
    timeout: 15
    rate_limit: 50

database:
  path: "data/analytics.db"
  max_records_per_symbol: 500
```

**Environment variables override config.yaml values.**

## Module Structure

```
src/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── decorators.py        # Error handling decorators (@safe_run)
├── database.py          # SQLite database manager
├── http_client.py       # Async HTTP client (aiohttp)
├── indicators.py        # Technical indicators
├── notifications.py     # Telegram notifier
└── errors.py            # Custom exceptions
```

## Key Features

### 1. Centralized Error Handling

Use `@safe_run` decorator for automatic error handling:

```python
from src.decorators import safe_run

@safe_run(default_return=[], log_level="ERROR", retries=2)
def fetch_data():
    # Function code
    pass
```

### 2. Async HTTP Requests

Asynchronous API calls with aiohttp:

```python
from src.http_client import AsyncHTTPClient

async with AsyncHTTPClient() as client:
    data = await client.get("https://api.example.com/data")
```

### 3. SQLite Database

Persistent data storage:

```python
from src.database import DatabaseManager

db = DatabaseManager()
signal_id = db.add_signal({
    "symbol": "BTCUSDT",
    "price": 45000.0,
    "rsi": 65.5,
    # ... other fields
})
```

### 4. Technical Indicators

Calculate market indicators:

```python
from src.indicators import TechnicalIndicators

rsi = TechnicalIndicators.calculate_rsi(closes, period=14)
macd, signal, histogram = TechnicalIndicators.calculate_macd(closes)
decision = TechnicalIndicators.generate_decision(rsi, macd, signal, stoch)
```

### 5. Telegram Notifications

Send market alerts:

```python
from src.notifications import TelegramNotifier

notifier = TelegramNotifier(
    token=config.get_telegram_token(),
    chat_id=config.get_telegram_chat_id()
)

await notifier.send_analysis(
    symbol="BTC",
    price=45000,
    rsi=65.5,
    # ... other parameters
)
```

## Usage Examples

### Basic Setup

```python
from src.config import ConfigManager
from src.database import DatabaseManager
from src.notifications import TelegramNotifier

# Load configuration
config = ConfigManager("config.yaml")

# Initialize database
db = DatabaseManager(config.get_database_path())

# Initialize notifier
notifier = TelegramNotifier(
    token=config.get_telegram_token(),
    chat_id=config.get_telegram_chat_id(),
    test_mode=config.is_test_mode()
)
```

### Fetch and Analyze Cryptocurrency

```python
import asyncio
from src.http_client import AsyncHTTPClient
from src.indicators import TechnicalIndicators

async def analyze_crypto(symbol: str):
    async with AsyncHTTPClient() as client:
        # Fetch price data
        url = f"https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1h", "limit": 50}
        data = await client.get(url, params=params)
        
        # Extract closes
        closes = [float(candle[4]) for candle in data]
        
        # Calculate indicators
        rsi = TechnicalIndicators.calculate_rsi(closes)
        macd, signal, hist = TechnicalIndicators.calculate_macd(closes)
        stoch = TechnicalIndicators.calculate_stochastic(closes)
        
        # Generate decision
        decision = TechnicalIndicators.generate_decision(rsi, macd, signal, stoch)
        
        return {
            "symbol": symbol,
            "rsi": rsi,
            "macd": macd,
            "decision": decision
        }

# Run analysis
result = asyncio.run(analyze_crypto("BTCUSDT"))
print(result)
```

## Error Handling

The `@safe_run` decorator provides:

- **Automatic exception catching** - No uncaught exceptions
- **Logging** - Errors are logged at specified level
- **Default returns** - Function returns default value on error
- **Retries** - Automatic retry logic for transient errors
- **Type flexibility** - Works with sync and async functions

```python
@safe_run(
    default_return=[],          # Return empty list on error
    log_level="WARNING",        # Log level
    raise_on_error=False,       # Don't re-raise
    retries=2                   # Retry 2 times
)
def risky_operation():
    # Code that might fail
    pass
```

## Database Schema

### signals table
```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    price REAL,
    rsi REAL,
    macd REAL,
    macd_signal REAL,
    stochastic REAL,
    volume REAL,
    volume_change REAL,
    direction TEXT,
    decision TEXT
);
```

### symbols table
```sql
CREATE TABLE symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    last_price REAL,
    last_checked DATETIME
);
```

## Best Practices

1. **Always use context managers** for HTTP clients and database connections
2. **Leverage @safe_run decorator** instead of try-catch blocks
3. **Configure via config.yaml**, not hardcoded values
4. **Use environment variables** for sensitive data
5. **Enable logging** for debugging and monitoring
6. **Run database cleanup** periodically
7. **Use async/await** for concurrent operations

## Logging

Configure logging in `config.yaml`:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file:
    enabled: true
    directory: "logs"
    retention_days: 30
```

## Performance Tips

1. **Use async operations** for concurrent API calls
2. **Implement rate limiting** to avoid API throttling
3. **Clean up old database records** regularly
4. **Use connection pooling** for database
5. **Cache indicators** when possible

## Security

⚠️ **NEVER commit credentials to version control**

- Use `.env` file for local development
- Use environment variables in production
- Rotate API tokens regularly
- Use HTTPS for all API calls
- Validate all external inputs

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### Database Locked
```python
# Database manager handles locking, but if issues persist:
db.cleanup_database()
```

### Telegram Errors
- Verify `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`
- Check Telegram Bot API status
- Enable test mode to debug: `TEST_MODE=true`

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Create GitHub issue
- Check existing documentation
- Review log files in `logs/` directory

## Version History

### v2.0.0 (Current)
- Async/await support with aiohttp
- SQLite database backend
- Centralized error handling with @safe_run
- YAML configuration management
- Modular architecture
- PEP 8 compliance

### v1.0.0 (Legacy)
- Initial release with synchronous requests
- Excel-based storage
- Inline error handling

---

**Made with ❤️ by Murat Gungor**
