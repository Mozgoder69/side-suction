# .side_suction/ui/content_editor.py

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Tuple

from config.icons import FLDF, FLDT
from config.settings import settings
from logic.progress_manager import progress
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QTextCharFormat, QTextOption
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from qasync import asyncSlot
from ui.syntax_parser import SyntaxParser

# Constants
BACK_COLOR = QColor("#234")
FORE_COLOR = QColor("#9cf")
FONT_SIZE = settings.defaultFontSize
PANEL_SIZE = FONT_SIZE << 1


# Utility functions
@contextmanager
def painterContext(widget):
    painter = QPainter(widget)
    try:
        yield painter
    finally:
        painter.end()


class Ribbon(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.contentEditor = editor
        self.backColor = BACK_COLOR
        self.foreColor = FORE_COLOR
        self.setFont(QFont(settings.defaultFontName, settings.defaultFontSize))

    def paintEvent(self, event: Any) -> None:
        with painterContext(self) as painter:
            painter.fillRect(event.rect(), self.backColor)
            painter.setPen(self.foreColor)
            self.drawContent(painter, event.rect())


# Area classes for UI components
class LineNumberArea(Ribbon):
    def sizeHint(self) -> QSize:
        return QSize(self.contentEditor.lineNumberWidth(), 0)

    def drawContent(self, painter: QPainter, rect: QRect) -> None:
        for block, block_number, top in self.contentEditor.iterate_visible_blocks(rect):
            number = str(block_number + 1)
            height = self.contentEditor.lineHeight
            painter.drawText(0, int(top), self.width(), height, Qt.AlignRight, number)


class FoldMarkerArea(Ribbon):
    def sizeHint(self) -> QSize:
        return QSize(PANEL_SIZE, 0)

    def visible_foldable_blocks(
        self, rect: QRect = None, pos: QPoint = None
    ) -> Iterator[Tuple[int, QRect, str]]:
        for block, block_number, top in self.contentEditor.iterate_visible_blocks(rect):
            filename = self.contentEditor.contentMap.get_current_file(block_number)
            if filename:
                first_line = self.contentEditor.contentMap.fileStartLines[filename]
                if block_number == first_line:
                    height = self.contentEditor.lineHeight
                    marker_rect = QRect(0, int(top), PANEL_SIZE, height)
                    if pos is None or marker_rect.contains(pos):
                        yield block_number, marker_rect, filename

    def drawContent(self, painter: QPainter, rect: QRect):
        for _, marker_rect, filename in self.visible_foldable_blocks(rect=rect):
            is_folded = self.contentEditor.contentMap.folded_blocks.get(filename, False)
            marker_symbol = f"{FLDF}" if is_folded else f"{FLDT}"
            painter.drawText(marker_rect, Qt.AlignCenter, marker_symbol)

    def mouseMoveEvent(self, event):
        """Обрабатывает движение мыши для изменения внешнего вида курсора."""
        positions = self.visible_foldable_blocks(pos=event.pos())
        self.setCursor(
            QCursor(Qt.PointingHandCursor if any(positions) else Qt.ArrowCursor)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for blockNumber, _, _ in self.visible_foldable_blocks(pos=event.pos()):
                filename = self.contentEditor.contentMap.get_current_file(blockNumber)
                self.contentEditor.toggleFold(filename)
                break  # Обрабатываем только первый подходящий блок
        super().mousePressEvent(event)


class TopInfoArea(Ribbon):
    def drawContent(self, painter: QPainter, rect: QRect) -> None:
        block = self.contentEditor.firstVisibleBlock()
        topLine = block.blockNumber()
        filename = self.contentEditor.contentMap.get_current_file(topLine)
        infoText = filename if filename else "Not a File"
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter, infoText)


class BotInfoArea(Ribbon):
    def drawContent(self, painter: QPainter, rect: QRect) -> None:
        cursorChar = self.contentEditor.textCursor().position()
        totalChars = len(self.contentEditor.toPlainText())
        cursorLine = self.contentEditor.textCursor().blockNumber() + 1
        totalLines = self.contentEditor.document().blockCount()
        totalSize = self.contentEditor.computedFileSize
        infoText = f"Line: {cursorLine} of {totalLines} | Pos: {cursorChar} of {totalChars} | {totalSize} bytes"
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter, infoText)


# Main editor class
class ContentEditor(QPlainTextEdit):
    """Элементы UI (ленты нумерации строк и маркеров, верхняя и нижняя инфопанели) и взаимодействие с пользователем"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Initialize metrics
        self.lineHeight = self.fontMetrics().height()
        # Initialize ribbons (UI areas)
        self.topInfoArea = TopInfoArea(self)
        self.botInfoArea = BotInfoArea(self)
        self.lineNumberArea = LineNumberArea(self)
        self.foldMarkerArea = FoldMarkerArea(self)
        self.foldMarkerArea.setMouseTracking(True)
        # Connect signals
        self.updateRequest.connect(self.updateAreas)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        # Initialize properties
        self.topMarginHeight = PANEL_SIZE
        self.botMarginHeight = PANEL_SIZE
        self.computedFileSize = 0
        # Setup highlighter
        self.contentMap = ContentMap(self.document())
        self.highlighter = SyntaxParser(self.document())
        # Initial setup
        self.setCustomFont(settings.defaultFontName, settings.defaultFontSize)
        self.setTabSize(2)

    # Setup and configuration methods
    def setCustomFont(self, fontName, fontSize):
        """Устанавливает шрифты для редактора и его компонентов."""
        font = QFont(fontName, fontSize)
        self.setFont(font)  # For the editor content

    def setTabSize(self, spaces=4):
        """Устанавливает размер табуляции в пробелах."""
        option = QTextOption()
        option.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * spaces)
        self.document().setDefaultTextOption(option)

    def lineNumberWidth(self) -> int:
        """Вычисляет ширину области номеров строк."""
        digits = len(str(max(1, self.blockCount()))) + 1.5
        # Use the font's metrics for accurate width calculation
        width = self.fontMetrics().horizontalAdvance("8")
        return width * digits

    # Geometry and area management methods
    def updateEditorMargins(self) -> None:
        """Обновляет отступы редактора."""
        self.setViewportMargins(
            self.lineNumberWidth() + PANEL_SIZE, PANEL_SIZE, 0, PANEL_SIZE
        )

    @asyncSlot(QRect, int)
    async def updateAreas(self, rect: QRect, dy: int) -> None:
        """Обновляет области UI при прокрутке или изменении размеров."""
        if dy:
            self.lineNumberArea.scroll(0, dy)
            self.foldMarkerArea.scroll(0, dy)
        elif rect.contains(self.viewport().rect()):
            self.updateEditorMargins()
        self.update()

    def resizeEvent(self, event: Any) -> None:
        """Обрабатывает изменение размеров редактора."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        ribbonHeight = cr.height() - (PANEL_SIZE << 1)
        ribbonTop = cr.top() + PANEL_SIZE
        ribbonWidth = self.lineNumberWidth()
        # Line number area
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), ribbonTop, ribbonWidth, ribbonHeight)
        )
        # Fold marker area
        self.foldMarkerArea.setGeometry(
            QRect(cr.left() + ribbonWidth, ribbonTop, PANEL_SIZE, ribbonHeight)
        )
        # Top info area
        self.topInfoArea.setGeometry(QRect(cr.left(), cr.top(), cr.width(), PANEL_SIZE))
        # Bottom info area
        self.botInfoArea.setGeometry(
            QRect(cr.left(), cr.bottom() - PANEL_SIZE + 1, cr.width(), PANEL_SIZE)
        )

    def setComputedFileSize(self, size: int) -> None:
        """Устанавливает вычисленный размер файла."""
        self.computedFileSize = size
        self.update()

    def setContent(self, content: str) -> None:
        """Асинхронно устанавливает содержимое редактора и обновляет структуру."""
        self.setPlainText(content)
        self.contentMap.update_structure(content)
        self.setComputedFileSize(len(content.encode("utf-8")))
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def toggleFold(self, filename: str):
        """Асинхронно сворачивает/разворачивает блок, начинающийся с start_line."""
        self.contentMap.toggle_fold(filename)
        self.updateBlockVisibility(filename)

    def foldAll(self):
        """Сворачивает все блоки."""
        self.contentMap.fold_all()
        self.updateBlockVisibility()

    def unfoldAll(self):
        """Разворачивает все блоки."""
        self.contentMap.unfold_all()
        self.updateBlockVisibility()

    @asyncSlot()
    async def updateBlockVisibility(self, filename: str = None):
        """Асинхронно обновляет видимость блоков по данным файла, если указан, иначе обновляет видимость всех блоков"""
        changes = {}
        files = [filename] if filename else self.contentMap.fileStartLines.keys()

        async for filename in progress(files, "Computing Changes"):
            changes.update(self.computeChanges(filename))
        await self.applyChanges(changes.items())

    def computeChanges(self, filename: str = None):
        doc = self.document()
        changes = {}
        start_line, end_line = self.contentMap.get_file_boundaries(filename)
        if not (start_line or end_line):
            return {}
        is_folded = self.contentMap.is_folded(filename)
        current_visibility = doc.findBlockByNumber(start_line).next().isVisible()
        if current_visibility != (not is_folded):
            changes[(start_line, end_line)] = not is_folded
        return changes

    async def applyChanges(self, changes):
        doc = self.document()
        async for (start, end), state in progress(changes, "Applying Changes"):
            start_block = doc.findBlockByNumber(start)
            end_block = doc.findBlockByNumber(end)
            block = start_block.next()
            while block != end_block:
                block.setVisible(state)
                block = block.next()
        self.update()
        doc.markContentsDirty(0, doc.characterCount())

    def iterate_visible_blocks(self, rect: QRect = None):
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()
        while block.isValid() and (rect is None or top <= rect.bottom()):
            if block.isVisible():
                yield block, block_number, top
            block = block.next()
            block_number += 1
            top = self.blockBoundingGeometry(block).translated(offset).top()

    # UI update and rendering methods
    def highlightCurrentLine(self) -> None:
        """Подсвечивает текущую строку."""
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(BACK_COLOR)
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])


class ContentMap:
    """Управление структурой документа: маппинг строк на файлы, границы файлов в номерах строк"""

    def __init__(self, document):
        self.document = document
        self.fileLineMap: Dict[int, str] = {}
        self.fileStartLines: Dict[str, int] = {}
        self.fileEndLines: Dict[str, int] = {}
        self.folded_blocks: Dict[str, bool] = {}

    @asyncSlot()
    async def update_structure(self, content: str) -> None:
        lines = content.splitlines()
        current_file = None
        line_number = 0
        async for line in progress(lines, "Updating Structure"):
            if line.startswith("```") and not line.endswith("```") and not current_file:
                current_file = line.strip("`").strip()
                self.fileStartLines[current_file] = line_number
                self.fileLineMap[line_number] = current_file
            elif line.startswith("```") and current_file:
                self.fileLineMap[line_number] = current_file
                self.fileEndLines[current_file] = line_number
                current_file = None
            elif current_file:
                self.fileLineMap[line_number] = current_file
            line_number += 1
        await self.apply_folded_blocks()

    async def apply_folded_blocks(self):
        unique_files = set(self.fileLineMap.values())
        async for filename in progress(unique_files, "Applying Folded Blocks"):
            if filename not in self.folded_blocks:
                self.folded_blocks[filename] = False

    def set_file_line_map(self, mapping: Dict[int, str]) -> None:
        """Устанавливает маппинг строк на файлы и обновляет список начальных строк."""
        self.fileLineMap = mapping

    def get_current_file(self, lineNumber: int) -> Optional[str]:
        """Возвращает имя файла для указанной строки."""
        return self.fileLineMap.get(lineNumber)

    def get_file_boundaries(self, filename: str):
        return (self.fileStartLines[filename], self.fileEndLines[filename])

    def is_folded(self, filename: str) -> bool:
        """Возвращает, свёрнут ли файл."""
        return self.folded_blocks[filename]

    def toggle_fold(self, filename: str) -> None:
        """Переключает состояние сворачивания файла."""
        if filename in self.folded_blocks:
            self.folded_blocks[filename] = not self.folded_blocks[filename]

    def fold_all(self) -> None:
        """Сворачивает все файлы."""
        for filename in self.folded_blocks:
            self.folded_blocks[filename] = True

    def unfold_all(self) -> None:
        """Разворачивает все файлы."""
        for filename in self.folded_blocks:
            self.folded_blocks[filename] = False
