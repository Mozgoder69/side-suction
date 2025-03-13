# .side_suction/utils/report.py

import asyncio
from enum import IntEnum

from config.colors import Colors
from PySide6.QtWidgets import QMessageBox


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
