# .side_suction/tests/test_progress_manager.py

from progress_manager import ProgressManager


# Фиктивный класс для имитации progress_bar
class DummyProgressBar:
    def __init__(self):
        self.value = 0
        self.format_text = ""

    def setValue(self, val):
        self.value = val

    def setFormat(self, fmt):
        self.format_text = fmt

    def reset(self):
        self.value = 0
        self.format_text = ""


def test_progress_manager_extreme_values():
    class DummyProgressBar:
        def __init__(self):
            self.value = 0

        def setValue(self, val):
            self.value = val

    bar = DummyProgressBar()
    pm = ProgressManager(bar, min_interval=0)
    pm.update(100)
    assert bar.value == 100
    pm.update(0)
    assert bar.value == 0


def test_progress_manager_update_and_reset():
    bar = DummyProgressBar()
    # Устанавливаем минимальный интервал равным 0 для тестирования
    pm = ProgressManager(bar, min_interval=0)
    pm.update(50, "Halfway")
    assert bar.value == 50
    assert bar.format_text == "Halfway"
    pm.reset()
    assert bar.value == 0
    assert bar.format_text == ""


def test_update_with_format():
    bar = DummyProgressBar()
    pm = ProgressManager(bar, min_interval=0)
    pm.update(50, "Halfway")
    assert bar.value == 50
    assert bar.format_text == "Halfway"


def test_reset():
    bar = DummyProgressBar()
    pm = ProgressManager(bar, min_interval=0)
    pm.update(50, "Halfway")
    pm.reset()
    assert bar.value == 0
    assert bar.format_text == ""
