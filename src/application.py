"""
Main application orchestrator
"""

import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import pytz
from src.config import ConfigManager
from src.database import DatabaseManager
from src.notifications import TelegramNotifier
from src.workers.crypto import CryptoWorker
from src.workers.bist import BistWorker
from src.scheduler import TaskScheduler
from src.reporting import ExcelReporter
from src.decorators import async_safe_run

logger = logging.getLogger(__name__)


class AnalyticsApplication:
    """
    Main application orchestrator for market analysis system.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize application.

        Args:
            config_path: Path to config.yaml
        """
        self.config = ConfigManager(config_path)
        self.db = DatabaseManager(
            self.config.get_database_path(),
            max_records=self.config.get(
                "database.max_records_per_symbol", 500
            )
        )

        try:
            self.notifier = TelegramNotifier(
                token=self.config.get_telegram_token(),
                chat_id=self.config.get_telegram_chat_id(),
                test_mode=self.config.is_test_mode()
            )
        except ValueError as e:
            logger.warning(f"Telegram not configured: {e}")
            self.notifier = None

        self.crypto_worker = CryptoWorker(self.config, self.db, self.notifier)
        self.bist_worker = BistWorker(self.config, self.db, self.notifier)
        self.scheduler = TaskScheduler(self.config)
        self.reporter = ExcelReporter(self.config, self.db)
        self.running = False
        self.timezone = pytz.timezone(self.config.get_timezone())

        logger.info(f"Application initialized: {self}")

    async def analyze_crypto(self) -> None:
        """
        Run cryptocurrency analysis.
        """
        symbols = self.config.get_crypto_symbols()
        if symbols:
            await self.crypto_worker.analyze_all(symbols)
        else:
            logger.warning("No cryptocurrency symbols configured")

    async def analyze_bist(self) -> None:
        """
        Run BIST stock analysis.
        """
        symbols = self.config.get_bist_symbols()
        if symbols:
            await self.bist_worker.analyze_all(symbols)
        else:
            logger.warning("No BIST symbols configured")

    async def generate_report(self) -> None:
        """
        Generate daily report.
        """
        now = datetime.now(self.timezone)
        logger.info(f"📊 Generating daily report ({now.strftime('%H:%M:%S')})")

        # Generate Excel report
        self.reporter.generate_daily_summary()

        # Send summary via Telegram
        if self.notifier:
            all_signals = self.db.get_all_signals(limit=50)
            summary = self._create_summary(all_signals)
            await self.notifier.send_message(summary)

    def _create_summary(self, signals: dict) -> str:
        """
        Create text summary of signals.

        Args:
            signals: Dictionary of signals

        Returns:
            Formatted summary text
        """
        now = datetime.now(self.timezone)

        crypto_count = sum(
            1 for symbol, sigs in signals.items()
            if sigs and sigs[0].get("signal_type") == "CRYPTO"
        )
        bist_count = sum(
            1 for symbol, sigs in signals.items()
            if sigs and sigs[0].get("signal_type") == "BIST"
        )

        summary = f"""
<b>📊 MGL ANALYTICS - DAILY SUMMARY</b>

<b>Date:</b> {now.strftime('%d.%m.%Y %H:%M:%S')}

<b>Analysis Results:</b>
🪙 Crypto Signals: {crypto_count}
🇹🇷 BIST Signals: {bist_count}
📈 Total: {crypto_count + bist_count}

<b>System Status:</b>
✅ Database: Active
✅ Notifications: {'Enabled' if self.notifier else 'Disabled'}
✅ Test Mode: {'Yes' if self.config.is_test_mode() else 'No'}

📊 Report generated automatically
🔗 Join VIP → @Muratgungorr
        """
        return summary

    async def start(self) -> None:
        """
        Start the application.
        """
        if self.running:
            logger.warning("Application already running")
            return

        self.running = True
        logger.info("="*60)
        logger.info("🚀 MGL ANALYTICS v2.0.0 - STARTING")
        logger.info(f"Timezone: {self.timezone}")
        logger.info(f"Test Mode: {self.config.is_test_mode()}")
        logger.info(f"Debug Mode: {self.config.is_debug_mode()}")
        logger.info("="*60)

        # Schedule crypto analysis
        crypto_interval = self.config.get(
            "cryptocurrencies.check_interval", 3600
        )
        self.scheduler.add_interval_task(
            self.analyze_crypto,
            crypto_interval,
            "Crypto Analysis"
        )

        # Schedule BIST analysis during market hours
        self.scheduler.add_market_hours_task(
            self.analyze_bist,
            market_type="bist",
            name="BIST Analysis"
        )

        # Schedule daily reports
        report_times = self.config.get("reports.schedule", ["09:00", "13:00", "19:00"])
        self.scheduler.add_time_task(
            self.generate_report,
            report_times,
            "Daily Report"
        )

        # Schedule database cleanup
        cleanup_interval = self.config.get(
            "database.cleanup_interval", 3600
        )
        self.scheduler.add_interval_task(
            self.cleanup_database,
            cleanup_interval,
            "Database Cleanup"
        )

        # Start scheduler
        try:
            await self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            await self.shutdown()

    async def cleanup_database(self) -> None:
        """
        Clean up old database records.
        """
        self.db.cleanup_database()
        logger.info("🧹 Database cleanup completed")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the application.
        """
        self.running = False
        self.scheduler.stop()

        # Generate final report
        logger.info("💾 Generating final report...")
        self.reporter.generate_daily_summary()

        logger.info("="*60)
        logger.info("✅ APPLICATION SHUTDOWN COMPLETE")
        logger.info("="*60)

    def __repr__(self) -> str:
        return (
            f"AnalyticsApplication(timezone={self.timezone}, "
            f"test_mode={self.config.is_test_mode()})"
        )
