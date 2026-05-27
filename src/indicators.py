"""
Technical indicators calculation module
"""

import logging
from typing import List, Tuple, Optional
from src.decorators import safe_run

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calculate technical indicators for market analysis.
    """

    @staticmethod
    @safe_run(default_return=50, log_level="WARNING")
    def calculate_rsi(
        closes: List[float],
        period: int = 14
    ) -> float:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            closes: List of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        if len(closes) <= period:
            return 50

        # Calculate price changes
        changes = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]

        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes[-period:]]
        losses = [abs(change) if change < 0 else 0 for change in changes[-period:]]

        # Calculate averages
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Calculate RS and RSI
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @staticmethod
    @safe_run(default_return=0, log_level="WARNING")
    def calculate_ema(
        values: List[float],
        period: int
    ) -> float:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            values: List of values
            period: EMA period

        Returns:
            EMA value
        """
        if len(values) < period:
            return sum(values) / len(values) if values else 0

        k = 2.0 / (period + 1)
        ema = sum(values[:period]) / period

        for i in range(period, len(values)):
            ema = values[i] * k + ema * (1 - k)

        return round(ema, 4)

    @staticmethod
    @safe_run(default_return=(0, 0, 0), log_level="WARNING")
    def calculate_macd(
        closes: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            closes: List of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)

        Returns:
            Tuple of (MACD, Signal, Histogram)
        """
        if len(closes) < slow_period:
            return 0, 0, 0

        # Calculate EMAs
        ema_fast = TechnicalIndicators.calculate_ema(closes, fast_period)
        ema_slow = TechnicalIndicators.calculate_ema(closes, slow_period)

        # Calculate MACD
        macd = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        # Simplified: use exponential smoothing
        signal = macd * 0.67

        # Calculate histogram
        histogram = macd - signal

        return (
            round(macd, 4),
            round(signal, 4),
            round(histogram, 4)
        )

    @staticmethod
    @safe_run(default_return=(0, 0), log_level="WARNING")
    def calculate_volume_analysis(
        volumes: List[float],
        period: int = 20
    ) -> Tuple[float, float]:
        """
        Analyze volume changes.

        Args:
            volumes: List of volume values
            period: Analysis period (default 20)

        Returns:
            Tuple of (last_volume, volume_change_percent)
        """
        if not volumes:
            return 0, 0

        recent_volumes = volumes[-period:]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        last_volume = volumes[-1]

        if avg_volume == 0:
            return round(last_volume, 2), 0

        change_percent = ((last_volume - avg_volume) / avg_volume) * 100

        return round(last_volume, 2), round(change_percent, 2)

    @staticmethod
    @safe_run(default_return=50, log_level="WARNING")
    def calculate_stochastic(
        closes: List[float],
        period: int = 14
    ) -> float:
        """
        Calculate Stochastic Oscillator.

        Args:
            closes: List of closing prices
            period: Stochastic period (default 14)

        Returns:
            Stochastic value (0-100)
        """
        if len(closes) < period:
            return 50

        recent_closes = closes[-period:]
        highest = max(recent_closes)
        lowest = min(recent_closes)

        if highest == lowest:
            return 50

        k = ((closes[-1] - lowest) / (highest - lowest)) * 100

        return round(k, 2)

    @staticmethod
    @safe_run(default_return="NEUTRAL", log_level="WARNING")
    def generate_decision(
        rsi: float,
        macd: float,
        macd_signal: float,
        stochastic: float
    ) -> str:
        """
        Generate trading decision based on indicators.

        Args:
            rsi: RSI value
            macd: MACD value
            macd_signal: MACD signal line
            stochastic: Stochastic value

        Returns:
            Trading decision string
        """
        score = 0

        # RSI interpretation
        if rsi < 30:
            score += 2  # Strong buy
        elif rsi > 70:
            score -= 2  # Strong sell

        # MACD interpretation
        if macd > macd_signal:
            score += 1  # Bullish
        else:
            score -= 1  # Bearish

        # Stochastic interpretation
        if stochastic < 20:
            score += 1  # Buy signal
        elif stochastic > 80:
            score -= 1  # Sell signal

        # Convert score to decision
        if score >= 3:
            return "🟢 STRONG BUY"
        elif score >= 1:
            return "🟡 BUY OPPORTUNITY"
        elif score <= -3:
            return "🔴 STRONG SELL"
        elif score <= -1:
            return "🟠 SELL PRESSURE"
        else:
            return "⚪ NEUTRAL / WAIT"

    def __repr__(self) -> str:
        return "TechnicalIndicators()"
