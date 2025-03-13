# .side_suction/ui/ui_handler.py

from pathlib import Path

from config.colors import Colors
from config.icons import CHKF, CHKT
from config.settings import settings
from logic.progress_manager import progress
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QTextEdit
from qasync import asyncSlot
from utils.report import report_result


class UIHandler:
    def init_ui_handler(self):
        self.fontSize = settings.defaultFontSize
        self.fontName = settings.defaultFontName
        self.connectSignals()

    def connectSignals(self):
        self.dirListWidget.itemSelectionChanged.connect(self.onDirectorySelected)
        self.extListWidget.itemSelectionChanged.connect(self.onExtensionSelected)
        self.fileListWidget.selectionModel().selectionChanged.connect(
            self.onFileSelected
        )
        self.projectPathLineEdit.returnPressed.connect(self.onProjectPathEntered)
        self.projectSearchButton.clicked.connect(self.onProjectPathSelected)
        self.saveSelectionButton.clicked.connect(self.saveSelection)
        self.loadSelectionButton.clicked.connect(self.loadSelection)
        self.extractContentButton.clicked.connect(self.extractContent)
        self.toggleSelectionButton.clicked.connect(self.toggleSelection)
        self.toggleFoldingButton.toggled.connect(self.toggleFolding)
        self.copyContentButton.clicked.connect(self.copyContent)
        self.searchButton.clicked.connect(self.searchInCode)
        self.searchLineEdit.returnPressed.connect(self.searchInCode)
        self.fontNameComboBox.activated.connect(self.updateFontName)
        self.fontSizeComboBox.currentIndexChanged.connect(self.updateFontSize)

    def setProjectPathAndScan(self, project_path: str = None):
        if not project_path:
            project_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not project_path or not self.browser_manager.set_project_path(project_path):
            report_result("Select or enter a valid path.", "Path Error", 0)
            return
        self.projectPathLineEdit.setText(str(self.browser_manager.projectPath))
        self.resetSelections()
        self.scanProject()
        report_result()

    def onProjectPathEntered(self):
        project_path = self.projectPathLineEdit.text().strip()
        self.setProjectPathAndScan(project_path)

    def onProjectPathSelected(self):
        self.setProjectPathAndScan()

    @asyncSlot()
    async def onDirectorySelected(self, update_files=True):
        self.selectedDirs = {
            Path(item.text()) for item in self.dirListWidget.selectedItems()
        }
        self.filteredDirs = await self.browser_manager.get_filtered_dirs(
            self.selectedDirs
        )
        await self.refreshDirectoryList()
        if update_files:
            await self.refreshFileList()

    @asyncSlot()
    async def onExtensionSelected(self, update_files=True):
        self.selectedExts = {item.text() for item in self.extListWidget.selectedItems()}
        if update_files:
            await self.refreshFileList()

    def onFileSelected(self, selected, deselected):
        for index in selected.indexes():
            item = self.fileListWidget.itemFromIndex(index)
            file_path = item.data(Qt.UserRole + 1)
            if file_path not in self.selectedFilePaths:
                self.selectedFilePaths.append(file_path)
        for index in deselected.indexes():
            item = self.fileListWidget.itemFromIndex(index)
            file_path = item.data(Qt.UserRole + 1)
            if file_path in self.selectedFilePaths:
                self.selectedFilePaths.remove(file_path)
        self.refreshIndexedFileList()

    # Методы обновления UI
    @asyncSlot()
    async def scanProject(self):
        data = await self.browser_manager.scan_project()
        self.projectPathLineEdit.setText(str(self.browser_manager.projectPath))
        await self.updateUIWithData(data)
        report_result()

    async def updateUIWithData(self, data):
        self.filteredDirs = data["filteredDirs"]
        await self.refreshDirectoryList()
        self.filteredExts = data["filteredExts"]
        await self.refreshExtensionList()
        self.fileInfoList = data["filteredFiles"]
        await self.refreshFileList()

    def updateLabels(self):
        self.extLabel.setText(
            f"Included Exts: {', '.join(sorted(self.selectedExts))}"
            if self.selectedExts
            else "Included Exts: All"
        )
        self.dirLabel.setText(
            f"Excluded Dirs: {', '.join(sorted(map(str, self.selectedDirs)))}"
            if self.selectedDirs
            else "Excluded Dirs: None"
        )

    async def refreshDirectoryList(self):
        with QSignalBlocker(self.dirListWidget):
            self.dirListWidget.clear()
            dirList = sorted(self.filteredDirs)
            async for dir in progress(dirList, "Refreshing Directories"):
                item = QListWidgetItem(str(dir))
                self.dirListWidget.addItem(item)
                if dir in self.selectedDirs:
                    item.setSelected(True)
            self.selectedDirs = {
                Path(item.text()) for item in self.dirListWidget.selectedItems()
            }

    async def refreshExtensionList(self):
        with QSignalBlocker(self.extListWidget):
            self.extListWidget.clear()
            extList = sorted(self.filteredExts)
            async for ext in progress(extList, "Refreshing Extensions"):
                item = QListWidgetItem(ext)
                self.extListWidget.addItem(item)
                if ext in self.selectedExts:
                    item.setSelected(True)
            self.selectedExts = {
                item.text() for item in self.extListWidget.selectedItems()
            }

    @asyncSlot()
    async def refreshFileList(self):
        fileList = await self.browser_manager.get_filtered_files(
            self.selectedExts, self.selectedDirs
        )
        with QSignalBlocker(self.fileListWidget):
            self.fileListWidget.clear()
            async for relPath, fullPath in progress(fileList, "Refreshing Files"):
                item = QListWidgetItem(str(relPath))
                item.setData(Qt.UserRole + 1, str(relPath))
                item.setData(Qt.UserRole + 2, str(fullPath))
                self.fileListWidget.addItem(item)
                if item.data(Qt.UserRole + 1) in self.selectedFilePaths:
                    item.setSelected(True)
            self.updateLabels()
            self.refreshIndexedFileList()

    @asyncSlot()
    async def refreshIndexedFileList(self):
        self.selectedFileIndexes.clear()
        for index, file_path in enumerate(self.selectedFilePaths, start=1):
            self.selectedFileIndexes[file_path] = index
        async for i in progress(range(self.fileListWidget.count()), "Indexing Files"):
            item = self.fileListWidget.item(i)
            display_text = item.data(Qt.UserRole + 1)
            if display_text in self.selectedFileIndexes:
                display_text = (
                    f"[{self.selectedFileIndexes[display_text]}] {display_text}"
                )
            item.setData(Qt.DisplayRole, display_text)

    # Методы экспорта и импорта

    @asyncSlot()
    async def saveSelection(self):
        projectPath = str(self.browser_manager.projectPath)
        if not projectPath:
            report_result("No project path selected", "Project Error", 0)
            return
        selections = {
            "project_path": str(projectPath),
            "directories": list(map(str, self.selectedDirs)),
            "extensions": list(self.selectedExts),
            "files": self.selectedFilePaths,
        }
        async for key in progress(selections.keys(), "Saving Selection"):
            await self.selection_manager.saveSelection(
                projectPath, {key: selections[key]}
            )
        report_result()

    @asyncSlot()
    async def loadSelection(self):
        projectPath = str(self.browser_manager.projectPath)
        if not projectPath:
            report_result("Project path is not selected", "Input Error", 0)
            return
        savedData = await self.selection_manager.loadSelection(projectPath)
        if not savedData:
            report_result("No saved data for the project", "Data Error", 0)
            return
        self.resetSelections()
        self.selectedDirs = set(map(Path, savedData.get("directories", [])))
        await self.refreshDirectoryList()
        await self.onDirectorySelected(update_files=False)
        self.selectedExts = set(savedData.get("extensions", []))
        await self.refreshExtensionList()
        await self.onExtensionSelected(update_files=False)
        self.selectedFilePaths = savedData.get("files", [])
        await self.refreshFileList()
        report_result()

    # Извлечение и обработка кода
    @asyncSlot()
    async def extractContent(self):
        files = self.fileListWidget.selectedItems()
        if not files:
            report_result("Select a File", "File Error", 0)
            return
        self.isContentMinified = False
        content = await self.content_manager.extract_content(files)
        self.contentEditor.setContent(content)
        report_result()

    def copyContent(self):
        if not self.isContentMinified:
            self.isContentMinified = True
            content = self.content_manager.minify_content(
                self.contentEditor.toPlainText()
            )
            self.contentEditor.setContent(content)
            self.setHighlightColor(Colors.INFO)
        textToCopy = self.contentEditor.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.clear()
        clipboard.setText(textToCopy)

    def searchInCode(self):
        searchTerm = self.searchLineEdit.text()
        if not searchTerm:
            report_result("Enter a valid search term", "Input Error", 0)
            return
        self.contentEditor.setExtraSelections([])
        self.contentEditor.moveCursor(QTextCursor.Start)
        extraSelections = []
        matches = []
        while self.contentEditor.find(searchTerm):
            cursor = self.contentEditor.textCursor()
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#ffaa00"))
            selection.format.setForeground(QColor("#000000"))
            selection.cursor = cursor
            extraSelections.append(selection)
            matches.append(cursor.blockNumber())
        if matches:
            if not hasattr(self, "currentMatchIndex"):
                self.currentMatchIndex = 0
            else:
                self.currentMatchIndex = (self.currentMatchIndex + 1) % len(matches)
            match_block = self.contentEditor.document().findBlockByNumber(
                matches[self.currentMatchIndex]
            )
            cursor = QTextCursor(match_block)
            self.contentEditor.setTextCursor(cursor)
            self.contentEditor.ensureCursorVisible()
            self.setHighlightColor(Colors.INFO)
        else:
            report_result("Nothing found for this search term", "Empty Result", 1)
        self.contentEditor.setExtraSelections(extraSelections)

    # Управление выборкой файлов
    def toggleSelection(self, checked):
        if checked:
            self.fileListWidget.selectAll()
            self.toggleSelectionButton.setText(f"{CHKF} Deselect All")
        else:
            self.fileListWidget.clearSelection()
            self.toggleSelectionButton.setText(f"{CHKT} Select All")

    def toggleFolding(self, checked):
        if checked:
            self.contentEditor.foldAll()
            self.toggleFoldingButton.setText(f"{CHKF} Unfold All")
        else:
            self.contentEditor.unfoldAll()
            self.toggleFoldingButton.setText(f"{CHKT} Fold All")

    def resetSelections(self):
        with (
            QSignalBlocker(self.dirListWidget),
            QSignalBlocker(self.extListWidget),
            QSignalBlocker(self.fileListWidget.selectionModel()),
        ):
            self.dirListWidget.clearSelection()
            self.extListWidget.clearSelection()
            self.fileListWidget.clearSelection()
        self.selectedDirs.clear()
        self.selectedExts.clear()
        self.selectedFilePaths.clear()
        self.selectedFileIndexes.clear()
        self.updateLabels()
        self.refreshIndexedFileList()

    # Шрифты и цвета
    def applyFont(self):
        self.contentEditor.setCustomFont(self.fontName, self.fontSize)
        self.contentEditor.update()

    def updateFontName(self):
        self.fontName = self.fontNameComboBox.currentText()
        self.applyFont()

    def updateFontSize(self):
        self.fontSize = int(self.fontSizeComboBox.currentText())
        self.applyFont()
