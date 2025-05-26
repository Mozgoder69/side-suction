# .side_suction/main.py

import asyncio
import sys

from logic.selection_manager import SelectionManager
from logic.status_manager import progress, report_config, report_result
from PySide6.QtWidgets import QApplication, QWidget
from qasync import QEventLoop
from ui.ui_builder import UIBuilder
from ui.ui_handler import UIHandler


class SideSuction(QWidget, UIBuilder, UIHandler):
    """Main application window for extracting and displaying code."""

    def __init__(self):
        super().__init__()
        self.filteredDirs = set()
        self.filteredExts = set()
        self.filteredFiles = []
        self.selectedDirs = set()
        self.selectedExts = set()
        self.selectedFilePaths = []
        self.selectedFileIndexes = {}
        self.init_ui_builder()
        progress.set_progress_bar(self.progressBar)
        self.selection_manager = SelectionManager()

        self.init_ui_handler()
        self.setWindowProps()

    def setWindowProps(self):
        self.setWindowTitle("A little code base Extractor")
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        self.full_width = geometry.width()
        self.full_height = geometry.height()
        self.width = int(self.full_width * 5 / 6)
        self.height = int(self.full_height * 5 / 6)
        self.x = (self.full_width - self.width) >> 1
        self.y = (self.full_height - self.height) >> 1
        self.setGeometry(self.x, self.y, self.width, self.height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustPanelSizes()

    def adjustPanelSizes(self):
        minHeight = self.width >> 2
        maxHeight = self.width << 2
        minWidth = self.height >> 2
        maxWidth = self.height << 2
        self.browserPanel.setMinimumWidth(minHeight)
        self.contentPanel.setMinimumWidth(minHeight)
        self.setMinimumHeight(minHeight)
        self.setMaximumHeight(maxHeight)
        self.setMinimumWidth(minWidth)
        self.setMaximumWidth(maxWidth)

    def setHighlightColor(self, color):
        self.contentEditor.setStyleSheet(f"border-color: {color.value};")

    def closeEvent(self, event):
        # перед закрытием окна — закрываем GitHub-сессию
        if hasattr(self, "projectSrc") and hasattr(self.projectSrc, "close"):
            # schedule close, т.к. здесь нельзя await
            asyncio.get_event_loop().create_task(self.projectSrc.close())
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = SideSuction()
    report_config.parent = window
    report_config.callback = window.setHighlightColor
    window.show()
    try:
        with loop:
            loop.run_forever()
    except Exception as e:
        report_result(str(e), str(e.__class__.__name__), 0)
