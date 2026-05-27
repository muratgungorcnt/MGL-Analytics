"""
Telegram notification service
"""

import logging
from typing import Optional
from src.http_client import AsyncHTTPClient
from src.decorators import async_safe_run
from src.errors import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Sends notifications via Telegram Bot API.
    """

    API_URL = "https://api.telegram.org"

    def __init__(
        self,
        token: str,
        chat_id: str,
        test_mode: bool = False
    ):
        """
        Initialize Telegram notifier.

        Args:
            token: Telegram bot token
            chat_id: Chat ID to send messages to
            test_mode: If True, log messages instead of sending
        """
        self.token = token
        self.chat_id = chat_id
        self.test_mode = test_mode
        self.http_client = AsyncHTTPClient(timeout=15, ssl_verify=False)

    @async_safe_run(default_return=False, log_level="ERROR", retries=2)
    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send message via Telegram.

        Args:
            text: Message text
            parse_mode: Message format (HTML, Markdown, etc.)
            disable_web_page_preview: Disable preview of URLs

        Returns:
            True if successful, False otherwise

        Raises:
            TelegramError: If token or chat_id is invalid
        """
        if not self.token or not self.chat_id:
            raise TelegramError("Telegram token or chat_id not configured")

        if self.test_mode:
            logger.info(f"[TEST MODE] Telegram message would be sent:\n{text}")
            return True

        url = f"{self.API_URL}/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }

        async with self.http_client as client:
            result = await client.post(url, json=payload)

            if result and result.get("ok"):
                logger.debug(f"Telegram message sent successfully")
                return True
            else:
                logger.warning(f"Telegram send failed: {result}")
                return False

    async def send_analysis(
        self,
        symbol: str,
        price: float,
        rsi: float,
        macd: float,
        macd_signal: float,
        stochastic: float,
        volume_change: float,
        direction: str,
        decision: str,
        market_type: str = "CRYPTO"
    ) -> bool:
        """
        Send technical analysis report.

        Args:
            symbol: Market symbol
            price: Current price
            rsi: RSI value
            macd: MACD value
            macd_signal: MACD signal line
            stochastic: Stochastic value
            volume_change: Volume change percentage
            direction: Price direction (UP/DOWN)
            decision: Trading decision
            market_type: Market type (CRYPTO/BIST)

        Returns:
            True if successful
        """
        # Determine RSI status
        if rsi >= 70:
            rsi_status = "🔴 OVERBOUGHT"
        elif rsi <= 30:
            rsi_status = "🟢 OVERSOLD"
        else:
            rsi_status = "⚪ NORMAL"

        # Determine MACD status
        macd_status = "🟢 BULLISH" if macd > macd_signal else "🔴 BEARISH"

        # Determine Stochastic status
        if stochastic >= 80:
            stoch_status = "🔴 SELL READY"
        elif stochastic <= 20:
            stoch_status = "🟢 BUY READY"
        else:
            stoch_status = "⚪ NEUTRAL"

        message = f"""
<b>[{market_type}] {symbol} - TECHNICAL ANALYSIS</b>

<b>PRICE:</b> ${price:.2f}
<b>DIRECTION:</b> {direction}

<b>INDICATORS:</b>
• RSI({rsi:.1f}): {rsi_status}
• MACD: {macd_status}
• Stochastic({stochastic:.1f}): {stoch_status}
• Volume Change: {volume_change:+.1f}%

<b>DECISION:</b> {decision}

🔗 Join VIP channel → @Muratgungorr
        """

        return await self.send_message(message)

    def __repr__(self) -> str:
        return f"TelegramNotifier(chat_id={self.chat_id})"
