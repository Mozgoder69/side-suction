# .side_suction/logic/status_manager.py

import asyncio
import time
from contextlib import asynccontextmanager
from enum import IntEnum
from typing import AsyncIterable

from config.colors import Colors
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QProgressBar


class Levels(IntEnum):
    FAIL = 0
    WARN = 1
    PASS = 2


# UI Configuration
class ReportConfig:
    parent = None
    callback = None


report_config = ReportConfig()


def report_result(message="", title="", level=Levels.PASS):
    parent = report_config.parent
    callback = report_config.callback
    color = Colors.PASS
    if message and level in (Levels.FAIL, Levels.WARN):
        print(message)
        QMessageBox.warning(parent, title or "Alert", message)
        color = Colors.FAIL if level == Levels.FAIL else Colors.WARN

    if callback:
        callback(color)

    return color == Colors.PASS


def handle_error(context):
    exc = context.get("exception")
    message = str(exc) if exc else "Unknown error occurred"
    title = str(exc.__class__.__name__) if exc else "Error"
    report_result(message, title, 0)


# Set up the global handler
loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_error)


class ProgressManager(QObject):
    updated = Signal(int, str)

    def __init__(self, min_interval=0.2, enum_mult=10):
        super().__init__()
        self.progress_bar = None
        self.min_interval = min_interval
        self.enum_mult = enum_mult
        self.reset()

    def set_progress_bar(self, progress_bar: QProgressBar):
        self.progress_bar = progress_bar
        self.updated.connect(self.update_progress_bar)

    def update_progress_bar(self, progress, status):
        if self.progress_bar:
            if progress is not None and progress != self.progress_bar.value():
                self.progress_bar.setValue(progress)
            if status is not None and status != self.progress_bar.format():
                self.progress_bar.setFormat(status)

    def reset(self):
        self.last_update = 0
        if self.progress_bar:
            self.progress_bar.reset()

    def update(self, progress, status):
        now = time.monotonic()
        current_progress = self.progress_bar.value() if self.progress_bar else 0
        current_status = self.progress_bar.format() if self.progress_bar else ""

        target_progress = progress if progress is not None else current_progress
        target_status = status if status is not None else current_status

        differs = target_progress != current_progress
        delay_ok = now - self.last_update >= self.min_interval

        if differs and (delay_ok or target_progress in (0, 100)):
            self.updated.emit(int(target_progress), target_status)
            self.last_update = now

    def _calculate_progress(self, current, total):
        if total and total > 0:
            return min(100, int((current / total) * 100))
        return min(99, current * self.enum_mult)

    def _format_status(self, current, total, label):
        if total:
            return f"{label}: {int((current / total) * 100)}% of {total}"
        return f"{label} step: {current}"

    def step(self, current, total, label):
        progress = self._calculate_progress(current, total)
        status = self._format_status(current, total, label)
        self.update(progress, status)

    def progress_callback(self, total, label):
        current = 0

        def callback(step=1):
            nonlocal current
            current = min(current + step, total)
            self.step(current, total, label)

        return callback

    @asynccontextmanager
    async def progress_context(self, total, label):
        self.update(0, label)
        callback = self.progress_callback(total, label)
        try:
            yield callback
            self.update(100, f"{label} - Complete")
        except Exception as e:
            self.update(0, f"{label} - Error: {str(e)}")
            raise

    async def track(self, iterable: AsyncIterable, label) -> AsyncIterable:
        try:
            total = len(iterable) if hasattr(iterable, "__len__") else None
        except TypeError:
            total = None

        is_async = isinstance(iterable, AsyncIterable)
        iterator = iterable.__aiter__() if is_async else iter(iterable)
        current = 0

        self.update(0, label)

        while True:
            try:
                item = await iterator.__anext__() if is_async else next(iterator)
                current += 1
                self.step(current, total, label)
                yield item
            except (StopIteration, StopAsyncIteration):
                self.update(100, f"{label} - Complete")
                break
            except Exception as e:
                self.update(0, f"{label} - Error: {str(e)}")
                raise

    def __call__(self, iterable: AsyncIterable, label) -> AsyncIterable:
        return self.track(iterable, label)


progress = ProgressManager()
