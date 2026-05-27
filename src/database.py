"""
SQLite3 database manager for storing market analysis data
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading
from contextlib import contextmanager
from src.decorators import safe_run
from src.errors import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite3 database manager with thread-safe operations.
    Stores technical analysis signals and market data.
    """

    def __init__(self, db_path: str = "data/analytics.db", max_records: int = 500):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
            max_records: Maximum records to keep per symbol
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_records = max_records
        self.lock = threading.Lock()
        self._init_database()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            SQLite3 connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """
        Initialize database schema.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    price REAL,
                    rsi REAL,
                    macd REAL,
                    macd_signal REAL,
                    stochastic REAL,
                    volume REAL,
                    volume_change REAL,
                    direction TEXT,
                    signal_type TEXT,
                    decision TEXT,
                    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
                )
            """)

            # Symbols table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    market_type TEXT,
                    last_price REAL,
                    last_checked DATETIME,
                    signal_count INTEGER DEFAULT 0
                )
            """)

            # Price history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    price REAL,
                    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
                )
            """)

            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp
                ON signals(symbol, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_history_symbol_timestamp
                ON price_history(symbol, timestamp DESC)
            """)

            logger.info(f"Database initialized at {self.db_path}")

    @safe_run(default_return=None, log_level="ERROR")
    def add_signal(self, signal_data: Dict[str, Any]) -> int:
        """
        Add a new signal to the database.

        Args:
            signal_data: Dictionary containing signal information
                Required keys: symbol, price, rsi, macd, macd_signal,
                              stochastic, volume, volume_change, direction

        Returns:
            Signal ID or None on error
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Ensure symbol exists
                symbol = signal_data.get("symbol")
                cursor.execute(
                    "INSERT OR IGNORE INTO symbols (symbol) VALUES (?)",
                    (symbol,)
                )

                # Insert signal
                cursor.execute("""
                    INSERT INTO signals
                    (symbol, price, rsi, macd, macd_signal, stochastic,
                     volume, volume_change, direction, signal_type, decision)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data.get("symbol"),
                    signal_data.get("price"),
                    signal_data.get("rsi"),
                    signal_data.get("macd"),
                    signal_data.get("macd_signal"),
                    signal_data.get("stochastic"),
                    signal_data.get("volume"),
                    signal_data.get("volume_change"),
                    signal_data.get("direction"),
                    signal_data.get("signal_type", "ANALYSIS"),
                    signal_data.get("decision")
                ))

                signal_id = cursor.lastrowid
                self._cleanup_old_records(symbol)
                logger.debug(f"Signal added: {symbol} (ID: {signal_id})")
                return signal_id

    @safe_run(default_return=[], log_level="WARNING")
    def get_signals(
        self,
        symbol: str,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve signals for a symbol.

        Args:
            symbol: Market symbol
            limit: Maximum number of records to return
            days: Number of days to look back

        Returns:
            List of signal records
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM signals
                    WHERE symbol = ?
                    AND timestamp >= datetime('now', ?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (symbol, f"-{days} days", limit))

                return [dict(row) for row in cursor.fetchall()]

    @safe_run(default_return={}, log_level="WARNING")
    def get_all_signals(self, limit: int = 100) -> Dict[str, List[Dict]]:
        """
        Retrieve all recent signals grouped by symbol.

        Args:
            limit: Maximum records per symbol

        Returns:
            Dictionary of signals by symbol
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM signals
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

                signals = {}
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    symbol = row_dict['symbol']
                    if symbol not in signals:
                        signals[symbol] = []
                    signals[symbol].append(row_dict)

                return signals

    @safe_run(log_level="WARNING")
    def update_symbol_price(self, symbol: str, price: float, name: str = None) -> bool:
        """
        Update symbol's last price.

        Args:
            symbol: Market symbol
            price: Current price
            name: Symbol name (optional)

        Returns:
            True on success, False on error
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO symbols (symbol, name, last_price, last_checked)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (symbol, name or symbol, price))

                return True

    @safe_run(default_return=[], log_level="WARNING")
    def get_price_history(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get price history for a symbol.

        Args:
            symbol: Market symbol
            limit: Maximum records to return

        Returns:
            List of price history records
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT timestamp, symbol, price FROM price_history
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (symbol, limit))

                return [dict(row) for row in cursor.fetchall()]

    def _cleanup_old_records(self, symbol: str) -> None:
        """
        Remove old records for a symbol to maintain max_records limit.

        Args:
            symbol: Market symbol
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM signals
                WHERE symbol = ?
                AND id NOT IN (
                    SELECT id FROM signals
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """, (symbol, symbol, self.max_records))

    @safe_run(log_level="WARNING")
    def cleanup_database(self) -> bool:
        """
        Perform database cleanup and optimization.

        Returns:
            True on success, False on error
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Remove signals older than 30 days
                cursor.execute("""
                    DELETE FROM signals
                    WHERE timestamp < datetime('now', '-30 days')
                """)

                # Remove price history older than 7 days
                cursor.execute("""
                    DELETE FROM price_history
                    WHERE timestamp < datetime('now', '-7 days')
                """)

                # Optimize database
                cursor.execute("VACUUM")

                logger.info("Database cleanup completed")
                return True

    def __repr__(self) -> str:
        return f"DatabaseManager(path={self.db_path}, max_records={self.max_records})"
