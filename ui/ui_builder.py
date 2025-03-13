# .side_suction/ui/ui_builder.py

import json

from config.icons import CHKT, COPY, FIND, LOAD, READ, SAVE
from config.settings import settings
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from ui.content_editor import ContentEditor

LABEL_HEIGHT = 26


class BrowserPanel:
    def init_browser_panel(self):
        self.browserPanel = QWidget()
        self.browserPanelLayout = QVBoxLayout(self.browserPanel)
        self.addProjectEntryLayout()
        self.addProjectStructureLayout()
        self.addProjectControlsLayout()

    def addProjectEntryLayout(self):
        """Создает секцию выбора директории"""
        project_layout = QHBoxLayout()
        self.projectPathLineEdit = QLineEdit()
        self.projectSearchButton = QPushButton(f"{FIND} Select Project ")
        project_layout.addWidget(self.projectPathLineEdit, 1)
        project_layout.addWidget(self.projectSearchButton)
        self.browserPanelLayout.addLayout(project_layout)

    def addProjectStructureLayout(self):
        """Создаёт секции списков и добавляет их в сплиттер"""
        self.projectListsSplitter = QSplitter(Qt.Vertical)  # instead of layout
        widgets_config = [
            ("Excluded Dirs: None", "dirLabel", "dirListWidget"),
            ("Included Exts: All", "extLabel", "extListWidget"),
            ("Filtered Files", "fileLabel", "fileListWidget"),
        ]
        for label_text, label_name, widget_name in widgets_config:
            label = QLabel(label_text)
            widget = QListWidget()

            setattr(self, label_name, label)
            setattr(self, widget_name, widget)

            label.setMinimumHeight(LABEL_HEIGHT)
            widget.setSelectionMode(QListWidget.MultiSelection)

            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            self.projectListsSplitter.addWidget(label)
            self.projectListsSplitter.addWidget(widget)
        for i in range(6):
            self.projectListsSplitter.setStretchFactor(i, i % 2)
        self.browserPanelLayout.addWidget(self.projectListsSplitter)

    def addProjectControlsLayout(self):
        """Adds control buttons with Unicode icons instead of text."""
        controls_config = [
            (f"{CHKT} Select All", "toggleSelectionButton"),
            (f"{SAVE} Save Selection", "saveSelectionButton"),
            (f"{LOAD} Load Selection", "loadSelectionButton"),
            (f"{READ} Extract Content", "extractContentButton"),
        ]
        controls_layout = QHBoxLayout()
        for ctrl_text, ctrl_name in controls_config:
            control = QPushButton(ctrl_text)
            setattr(self, ctrl_name, control)
            controls_layout.addWidget(control, stretch=1)
        self.toggleSelectionButton.setCheckable(True)
        self.browserPanelLayout.addLayout(controls_layout)


class ContentPanel:
    def init_content_panel(self):
        self.contentPanel = QWidget()
        self.contentPanelLayout = QVBoxLayout(self.contentPanel)
        self.addContentSearchLayout()
        self.addContentEditorLayout()
        self.addContentControlsLayout()

    def addContentSearchLayout(self):
        """Создает секцию поиска"""
        search_layout = QHBoxLayout()
        self.searchLineEdit = QLineEdit()
        self.searchButton = QPushButton(f"{FIND} Search Text ")
        search_layout.addWidget(self.searchLineEdit, 1)
        search_layout.addWidget(self.searchButton)
        self.contentPanelLayout.addLayout(search_layout)

    def addContentEditorLayout(self):
        self.contentEditor = ContentEditor()
        self.contentPanelLayout.addWidget(self.contentEditor)

    def addContentControlsLayout(self):
        """Создает секцию контролов редактора"""
        controls_config = [
            (f"{CHKT} Fold All", None, "toggleFoldingButton", QPushButton),
            (None, settings.allFontNames, "fontNameComboBox", QComboBox),
            (None, settings.allFontSizes, "fontSizeComboBox", QComboBox),
            (f"{COPY} Copy Content", None, "copyContentButton", QPushButton),
        ]
        controls_layout = QHBoxLayout()
        for ctrl_text, ctrl_items, ctrl_name, ctrl_type in controls_config:
            control = ctrl_type(ctrl_text)
            setattr(self, ctrl_name, control)
            if ctrl_items:
                control.addItems(ctrl_items)
            controls_layout.addWidget(control)
        self.toggleFoldingButton.setCheckable(True)
        self.fontSizeComboBox.setCurrentText(str(settings.defaultFontSize))
        self.contentPanelLayout.addLayout(controls_layout)


class UIBuilder(BrowserPanel, ContentPanel):
    def init_ui_builder(self):
        self.saved_projects = []
        self.mainLayout = QVBoxLayout(self)
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.panelsSplitter = QSplitter(Qt.Horizontal)
        self.init_browser_panel()
        self.setProjectsAutoComplete()
        self.init_content_panel()
        self.panelsSplitter.addWidget(self.browserPanel)
        self.panelsSplitter.addWidget(self.contentPanel)
        self.mainLayout.addWidget(self.progressBar)
        self.mainLayout.addWidget(self.panelsSplitter)
        self.applyStylesheet()

    def setProjectsAutoComplete(self):
        projectCompleter = QCompleter([], self)
        if settings.databasePath.exists():
            with open(settings.databasePath, "r", encoding="utf-8") as f:
                content = f.read()
                all_selections = json.loads(content) if content else {}
            projects = list(all_selections.keys())
            projectCompleter = QCompleter(projects, self)
            projectCompleter.setCaseSensitivity(Qt.CaseInsensitive)
            projectCompleter.setFilterMode(Qt.MatchContains)
            projectCompleter.setCompletionMode(QCompleter.PopupCompletion)
            model = projectCompleter.popup().model()
            if model.rowCount() > 0:
                index = model.index(0, 0)
                projectCompleter.popup().setCurrentIndex(index)
        self.projectPathLineEdit.setCompleter(projectCompleter)
        self.projectCompleter = projectCompleter

    def applyStylesheet(self):
        path_to_stylesheet = settings.stylesheetPath
        with open(path_to_stylesheet, "r") as file:
            styles = file.read()
            self.setStyleSheet(styles)
            self.projectPathLineEdit.completer().popup().setStyleSheet(styles)
            self.contentEditor.verticalScrollBar().setStyleSheet(styles)
