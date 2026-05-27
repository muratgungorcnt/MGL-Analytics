"""
BIST (Istanbul Stock Exchange) market analysis worker
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List
from src.config import ConfigManager
from src.database import DatabaseManager
from src.notifications import TelegramNotifier
from src.indicators import TechnicalIndicators
from src.http_client import AsyncHTTPClient
from src.decorators import async_safe_run

logger = logging.getLogger(__name__)


class BistWorker:
    """
    Analyzes BIST stocks and sends signals.
    """

    def __init__(
        self,
        config: ConfigManager,
        db: DatabaseManager,
        notifier: TelegramNotifier
    ):
        """
        Initialize BIST worker.

        Args:
            config: Configuration manager
            db: Database manager
            notifier: Telegram notifier
        """
        self.config = config
        self.db = db
        self.notifier = notifier
        self.base_url = "https://query1.finance.yahoo.com"
        self.last_signals = {}
        self.duplicate_interval = config.get(
            "signals.duplicate_check_interval", 300
        )

    def _can_send_signal(self, symbol: str) -> bool:
        """
        Check if enough time has passed since last signal.

        Args:
            symbol: Stock ticker

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
    async def analyze_symbol(self, ticker: str, name: str) -> dict:
        """
        Analyze a single BIST stock.

        Args:
            ticker: Stock ticker (e.g., THYAO.IS)
            name: Stock name

        Returns:
            Analysis result dictionary
        """
        try:
            async with AsyncHTTPClient(ssl_verify=False) as client:
                # Yahoo Finance API
                url = f"{self.base_url}/v8/finance/chart/{ticker}"
                params = {
                    "interval": "1h",
                    "range": "5d"
                }

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }

                data = await client.get(url, params=params, headers=headers)

                if not data or "chart" not in data or "result" not in data["chart"]:
                    return None

                result_data = data["chart"]["result"][0]
                meta = result_data.get("meta", {})
                current_price = float(meta.get("regularMarketPrice", 0))

                if not current_price:
                    return None

                # Extract OHLCV data
                indicators = result_data.get("indicators", {}).get("quote", [{}])[0]
                closes = [float(c) for c in indicators.get("close", []) if c]
                volumes = [float(v) for v in indicators.get("volume", []) if v]

                if not closes or not volumes:
                    return None

                # Calculate indicators
                rsi = TechnicalIndicators.calculate_rsi(closes)
                macd, signal, histogram = TechnicalIndicators.calculate_macd(closes)
                stoch = TechnicalIndicators.calculate_stochastic(closes)
                volume, volume_change = TechnicalIndicators.calculate_volume_analysis(
                    volumes
                )

                # Determine direction
                prev_price = self.db.get_price_history(ticker, limit=1)
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
                    "signals.alarm_threshold_bist", 1.0
                )
                should_alert = (
                    abs(price_change) >= alarm_threshold
                    or rsi >= 70
                    or rsi <= 30
                )

                result = {
                    "ticker": ticker,
                    "name": name,
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
                    "symbol": ticker,
                    "price": current_price,
                    "rsi": rsi,
                    "macd": macd,
                    "macd_signal": signal,
                    "stochastic": stoch,
                    "volume": volume,
                    "volume_change": volume_change,
                    "direction": direction,
                    "signal_type": "BIST",
                    "decision": decision
                })

                # Update symbol price
                self.db.update_symbol_price(ticker, current_price, name)

                # Send notification if threshold met
                if should_alert and self._can_send_signal(ticker):
                    await self.notifier.send_analysis(
                        symbol=name,
                        price=current_price,
                        rsi=rsi,
                        macd=macd,
                        macd_signal=signal,
                        stochastic=stoch,
                        volume_change=volume_change,
                        direction=direction,
                        decision=decision,
                        market_type="BIST"
                    )
                    logger.info(f"📢 Signal sent for {name} ({ticker})")

                return result

        except Exception as e:
            logger.error(f"Error analyzing {name} ({ticker}): {str(e)[:100]}")
            return None

    async def analyze_all(self, symbols: Dict[str, str]) -> dict:
        """
        Analyze multiple BIST stocks concurrently.

        Args:
            symbols: Dictionary of ticker -> name

        Returns:
            Dictionary of analysis results
        """
        logger.info(f"🇹🇷 Starting BIST analysis for {len(symbols)} stocks")

        tasks = [
            self.analyze_symbol(ticker, name)
            for ticker, name in symbols.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        valid_results = {}
        for (ticker, name), result in zip(symbols.items(), results):
            if result:
                valid_results[ticker] = result

        logger.info(f"✅ BIST analysis completed: {len(valid_results)}/{len(symbols)}")
        return valid_results
