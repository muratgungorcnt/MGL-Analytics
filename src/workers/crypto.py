"""
Cryptocurrency market analysis worker
"""

import logging
import asyncio
from datetime import datetime
from typing import List
import aiohttp
from src.config import ConfigManager
from src.database import DatabaseManager
from src.notifications import TelegramNotifier
from src.indicators import TechnicalIndicators
from src.http_client import AsyncHTTPClient
from src.decorators import async_safe_run

logger = logging.getLogger(__name__)


class CryptoWorker:
    """
    Analyzes cryptocurrency markets and sends signals.
    """

    def __init__(
        self,
        config: ConfigManager,
        db: DatabaseManager,
        notifier: TelegramNotifier
    ):
        """
        Initialize crypto worker.

        Args:
            config: Configuration manager
            db: Database manager
            notifier: Telegram notifier
        """
        self.config = config
        self.db = db
        self.notifier = notifier
        self.base_url = config.get("api.binance.base_url")
        self.last_signals = {}
        self.duplicate_interval = config.get(
            "signals.duplicate_check_interval", 300
        )

    def _can_send_signal(self, symbol: str) -> bool:
        """
        Check if enough time has passed since last signal.

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            True if signal can be sent
        """
        now = datetime.now().timestamp()
        last_signal = self.last_signals.get(symbol, 0)

        if now - last_signal >= self.duplicate_interval:
            self.last_signals[symbol] = now
            return True

        return False

    @async_safe_run(default_return=None, log_level="WARNING")
    async def analyze_symbol(self, symbol: str) -> dict:
        """
        Analyze a single cryptocurrency symbol.

        Args:
            symbol: Cryptocurrency symbol (e.g., BTCUSDT)

        Returns:
            Analysis result dictionary
        """
        try:
            async with AsyncHTTPClient() as client:
                # Fetch 24h ticker data
                ticker_url = f"{self.base_url}/ticker/24hr"
                ticker_data = await client.get(
                    ticker_url,
                    params={"symbol": symbol}
                )

                if not ticker_data:
                    return None

                current_price = float(ticker_data.get("lastPrice", 0))

                # Fetch 1h candlestick data
                klines_url = f"{self.base_url}/klines"
                klines_data = await client.get(
                    klines_url,
                    params={
                        "symbol": symbol,
                        "interval": "1h",
                        "limit": 50
                    }
                )

                if not klines_data:
                    return None

                # Extract OHLCV data
                closes = [float(candle[4]) for candle in klines_data]
                volumes = [float(candle[7]) for candle in klines_data]

                # Calculate indicators
                rsi = TechnicalIndicators.calculate_rsi(closes)
                macd, signal, histogram = TechnicalIndicators.calculate_macd(closes)
                stoch = TechnicalIndicators.calculate_stochastic(closes)
                volume, volume_change = TechnicalIndicators.calculate_volume_analysis(
                    volumes
                )

                # Determine direction
                prev_price = self.db.get_price_history(symbol, limit=1)
                if prev_price:
                    old_price = float(prev_price[0]["price"])
                    direction = "UP" if current_price > old_price else "DOWN"
                    price_change = ((current_price - old_price) / old_price) * 100
                else:
                    direction = "NEUTRAL"
                    price_change = 0

                # Generate decision
                decision = TechnicalIndicators.generate_decision(
                    rsi, macd, signal, stoch
                )

                # Check alarm thresholds
                alarm_threshold = self.config.get(
                    "signals.alarm_threshold_crypto", 2.0
                )
                should_alert = (
                    abs(price_change) >= alarm_threshold
                    or rsi >= 70
                    or rsi <= 30
                    or volume_change > 50
                )

                result = {
                    "symbol": symbol,
                    "price": current_price,
                    "rsi": rsi,
                    "macd": macd,
                    "macd_signal": signal,
                    "stochastic": stoch,
                    "volume": volume,
                    "volume_change": volume_change,
                    "direction": direction,
                    "price_change": price_change,
                    "decision": decision,
                    "should_alert": should_alert
                }

                # Store in database
                self.db.add_signal({
                    "symbol": symbol,
                    "price": current_price,
                    "rsi": rsi,
                    "macd": macd,
                    "macd_signal": signal,
                    "stochastic": stoch,
                    "volume": volume,
                    "volume_change": volume_change,
                    "direction": direction,
                    "signal_type": "CRYPTO",
                    "decision": decision
                })

                # Update symbol price
                self.db.update_symbol_price(symbol, current_price)

                # Send notification if threshold met
                if should_alert and self._can_send_signal(symbol):
                    await self.notifier.send_analysis(
                        symbol=symbol.replace("USDT", ""),
                        price=current_price,
                        rsi=rsi,
                        macd=macd,
                        macd_signal=signal,
                        stochastic=stoch,
                        volume_change=volume_change,
                        direction=direction,
                        decision=decision,
                        market_type="CRYPTO"
                    )
                    logger.info(f"📢 Signal sent for {symbol}")

                return result

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)[:100]}")
            return None

    async def analyze_all(self, symbols: List[str]) -> dict:
        """
        Analyze multiple symbols concurrently.

        Args:
            symbols: List of symbols to analyze

        Returns:
            Dictionary of analysis results
        """
        logger.info(f"🪙 Starting crypto analysis for {len(symbols)} symbols")

        tasks = [self.analyze_symbol(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        valid_results = {}
        for symbol, result in zip(symbols, results):
            if result:
                valid_results[symbol] = result

        logger.info(f"✅ Crypto analysis completed: {len(valid_results)}/{len(symbols)}")
        return valid_results
