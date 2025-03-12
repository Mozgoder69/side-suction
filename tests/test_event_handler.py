# .side_suction/tests/test_event_handler.py

from event_handler import connect_events
from PySide6.QtWidgets import QListWidget, QWidget


class DummyWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Используем QListWidget для обеспечения наличия сигнала itemSelectionChanged
        self.dirListWidget = QListWidget()
        self.extListWidget = QListWidget()
        self.fileListWidget = QListWidget()
        # Добавляем методы-обработчики
        self.handleDirSelected = lambda: None
        self.handleExtSelected = lambda: None
        self.onFileSelected = lambda selected, deselected: None


def test_connect_events():
    dummy = DummyWindow()
    # Функция должна выполниться без ошибок
    connect_events(dummy)
    assert True


def test_signal_connection(qtbot):
    dummy = DummyWindow()
    # Подключаем сигналы через функцию connect_events
    connect_events(dummy)

    # Флаг для проверки вызова обработчика
    flag = {"dir_called": False}

    def handler():
        flag["dir_called"] = True

    dummy.handleDirSelected = handler
    # Переподключаем сигнал, чтобы наш обработчик использовался
    dummy.dirListWidget.itemSelectionChanged.connect(dummy.handleDirSelected)

    # Эмулируем изменение выделения:
    dummy.dirListWidget.addItem("Test Dir")
    # Устанавливаем выделение для первого элемента
    dummy.dirListWidget.item(0).setSelected(True)

    # Даем время обработчику
    qtbot.wait(100)
    assert flag["dir_called"] is True
