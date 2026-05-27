"""
Scheduler for periodic tasks
"""

import logging
import asyncio
from datetime import datetime
from typing import Callable, Optional
import pytz
from src.config import ConfigManager

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Schedules periodic tasks to run at specific times or intervals.
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize scheduler.

        Args:
            config: Configuration manager
        """
        self.config = config
        self.timezone = pytz.timezone(config.get_timezone())
        self.tasks = []
        self.running = False

    def add_interval_task(
        self,
        task: Callable,
        interval_seconds: int,
        name: str = None
    ) -> None:
        """
        Add a task to run at regular intervals.

        Args:
            task: Async function to run
            interval_seconds: Interval in seconds
            name: Task name (optional)
        """
        task_name = name or getattr(task, "__name__", "unnamed")
        self.tasks.append({
            "type": "interval",
            "task": task,
            "interval": interval_seconds,
            "name": task_name,
            "last_run": None
        })
        logger.info(f"Added interval task: {task_name} (every {interval_seconds}s)")

    def add_time_task(
        self,
        task: Callable,
        run_times: list,
        name: str = None
    ) -> None:
        """
        Add a task to run at specific times.

        Args:
            task: Async function to run
            run_times: List of times in HH:MM format (e.g., ["09:00", "13:00"])
            name: Task name (optional)
        """
        task_name = name or getattr(task, "__name__", "unnamed")
        self.tasks.append({
            "type": "time",
            "task": task,
            "run_times": run_times,
            "name": task_name,
            "last_run": None
        })
        logger.info(f"Added time task: {task_name} at {run_times}")

    def add_market_hours_task(
        self,
        task: Callable,
        market_type: str = "bist",
        name: str = None
    ) -> None:
        """
        Add a task to run during market hours.

        Args:
            task: Async function to run
            market_type: Market type (bist, usa)
            name: Task name (optional)
        """
        task_name = name or getattr(task, "__name__", "unnamed")
        self.tasks.append({
            "type": "market_hours",
            "task": task,
            "market_type": market_type,
            "name": task_name,
            "last_run": None
        })
        logger.info(f"Added market hours task: {task_name} ({market_type})")

    def _is_market_open(self, market_type: str) -> bool:
        """
        Check if market is currently open.

        Args:
            market_type: Market type (bist, usa)

        Returns:
            True if market is open
        """
        now = datetime.now(self.timezone)
        hour = now.hour
        weekday = now.weekday()  # 0-4 are weekdays, 5-6 are weekend

        # Skip weekends
        if weekday >= 5:
            return False

        if market_type == "bist":
            open_hour = self.config.get("market_hours.bist.open", 9)
            close_hour = self.config.get("market_hours.bist.close", 18)
        elif market_type == "usa":
            open_hour = self.config.get("market_hours.usa.open", 16)
            close_hour = self.config.get("market_hours.usa.close", 23)
        else:
            return True

        return open_hour <= hour < close_hour

    def _should_run_task(self, task: dict) -> bool:
        """
        Determine if a task should run now.

        Args:
            task: Task dictionary

        Returns:
            True if task should run
        """
        now = datetime.now(self.timezone)

        if task["type"] == "interval":
            if task["last_run"] is None:
                return True
            elapsed = (now - task["last_run"]).total_seconds()
            return elapsed >= task["interval"]

        elif task["type"] == "time":
            current_time = now.strftime("%H:%M")
            last_run_date = (
                task["last_run"].date() if task["last_run"] else None
            )
            today = now.date()

            if current_time in task["run_times"] and last_run_date != today:
                return True

        elif task["type"] == "market_hours":
            if self._is_market_open(task["market_type"]):
                if task["last_run"] is None:
                    return True
                elapsed = (now - task["last_run"]).total_seconds()
                return elapsed >= 300  # Run every 5 minutes during market hours

        return False

    async def _run_task(self, task: dict) -> None:
        """
        Execute a single task.

        Args:
            task: Task dictionary
        """
        try:
            logger.debug(f"Running task: {task['name']}")
            await task["task"]()
            task["last_run"] = datetime.now(self.timezone)
            logger.debug(f"Task completed: {task['name']}")
        except Exception as e:
            logger.error(f"Task error ({task['name']}): {str(e)[:100]}")

    async def start(self) -> None:
        """
        Start the scheduler.
        Runs indefinitely, checking tasks at regular intervals.
        """
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        logger.info(f"Scheduler started with {len(self.tasks)} tasks")

        try:
            while self.running:
                now = datetime.now(self.timezone)

                for task in self.tasks:
                    if self._should_run_task(task):
                        await self._run_task(task)

                # Check every 30 seconds
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            self.running = False
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            self.running = False

    def stop(self) -> None:
        """
        Stop the scheduler.
        """
        self.running = False
        logger.info("Scheduler stopped")

    def __repr__(self) -> str:
        return f"TaskScheduler(tasks={len(self.tasks)}, timezone={self.timezone})"
