# .side_suction/tests/test_ui_setup.py

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget
from ui_setup import UISetup


# Класс-«заглушка», объединяющий QWidget и UISetup
class DummyWidget(QWidget, UISetup):
    def __init__(self):
        super().__init__()
        self.fontSize = 11  # Нужен для установки шрифта
        # Заглушки для методов, к которым привязывается UISetup
        self.onProjectPathEntered_called = False
        self.onProjectPathEntered = self.stub_onProjectPathEntered
        self.onProjectPathSelected = lambda: None
        self.toggleSelection = lambda checked: None
        self.saveSelection = lambda: None
        self.loadSelection = lambda: None
        self.extractCode = lambda: None
        self.searchInCode = lambda: None
        self.applyFont = lambda: None
        self.updateFontSize = lambda: None
        self.copyOutput = lambda: None
        self.initializeUI()

    def stub_onProjectPathEntered(self):
        self.onProjectPathEntered_called = True


def test_initialize_ui(qtbot):
    widget = DummyWidget()
    qtbot.addWidget(widget)
    assert widget.progressBar is not None
    assert widget.splitter is not None


def test_ui_setup_initialization(qtbot):
    widget = DummyWidget()
    qtbot.addWidget(widget)
    # Проверяем, что после инициализации появились основные виджеты
    assert hasattr(widget, "progressBar")
    assert hasattr(widget, "splitter")
    # Проверяем, что progressBar имеет значение 0
    assert widget.progressBar.value() == 0


def test_on_project_path_entered(qtbot):
    widget = DummyWidget()
    qtbot.addWidget(widget)
    # Симулируем нажатие Enter в поле ввода пути проекта
    QTest.keyClick(widget.projectPathLineEdit, Qt.Key_Return)
    # Проверяем, что заглушка вызвалась
    assert widget.onProjectPathEntered_called is True


def test_create_labeled_list_section():
    # Используем DummyWidget, который является QWidget и содержит UISetup
    widget = DummyWidget()
    # Используем простой QWidget для списка
    list_widget = QWidget()
    label, _ = widget.createLabeledListSection("Test Label", list_widget, "testLabel")
    assert label.text() == "Test Label"
    # Атрибут должен быть установлен в widget (а не в каком‑то отдельном объекте)
    assert hasattr(widget, "testLabel")


def test_create_button_group():
    widget = DummyWidget()
    buttons_config = [
        ("Test1", lambda: None, False, "btn1"),
        ("Test2", lambda: None, True, "btn2"),
    ]
    # Вызываем метод, который должен установить атрибуты на widget
    widget.createButtonGroup(buttons_config)
    # Проверяем, что кнопки добавлены как атрибуты в widget
    assert hasattr(widget, "btn1")
    assert hasattr(widget, "btn2")
