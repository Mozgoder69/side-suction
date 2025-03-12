# .side_suction/main.py
import asyncio
import sys

from logic.browser_manager import BrowserManager
from logic.content_manager import ContentManager
from logic.progress_manager import progress
from logic.selection_manager import SelectionManager
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
        self.browser_manager = BrowserManager()
        self.content_manager = ContentManager()
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
        self.contentEditor.setStyleSheet(
            f"border: 1px solid {color.value}; border-radius: 4px"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = SideSuction()
    window.show()
    with loop:
        loop.run_forever()
