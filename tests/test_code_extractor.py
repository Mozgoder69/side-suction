# .side_suction/tests/test_code_extractor.py

from pathlib import Path

import pytest
from code_extractor import CodeExtractor
from file_handler import FileHandler
from PySide6.QtCore import Qt


# Фиктивный элемент для имитации объекта QListWidgetItem
class DummyItem:
    def __init__(self, path):
        self._path = str(path)

    def data(self, role):
        # Для роли Qt.UserRole+2 возвращаем абсолютный путь
        if role == Qt.UserRole + 2:
            return self._path
        # Для роли Qt.UserRole+1 возвращаем имя файла
        elif role == Qt.UserRole + 1:
            return Path(self._path).name


@pytest.mark.asyncio
async def test_extract_code(tmp_path):
    # Создаем временный файл с содержимым
    file = tmp_path / "test.txt"
    content = "Hello, world!"
    file.write_text(content, encoding="utf-8")

    # Создаем фиктивный элемент для CodeExtractor
    item = DummyItem(file)
    # Инициализируем FileHandler и устанавливаем projectPath
    fh = FileHandler()
    fh.projectPath = tmp_path
    ce = CodeExtractor(fh)

    # Фиктивный progress_manager
    class DummyProgress:
        def update(self, value, format_text=None):
            pass

    progress = DummyProgress()

    extracted = await ce.extract_code([item], progress_manager=progress)
    # Проверяем, что извлеченный контент содержит имя файла и его содержимое
    assert "test.txt" in extracted
    assert "Hello, world!" in extracted


@pytest.mark.asyncio
async def test_extract_code_nonexistent_file(tmp_path):
    # Файл не существует – ожидаем, что его не включат в вывод
    dummy = DummyItem(tmp_path / "nonexistent.txt")
    fh = FileHandler()
    fh.projectPath = tmp_path
    ce = CodeExtractor(fh)
    result = await ce.extract_code([dummy])
    # В результате не должно быть имени несуществующего файла
    assert "nonexistent.txt" not in result


@pytest.mark.asyncio
async def test_extract_code_exceeds_max_size(tmp_path, monkeypatch):
    # Создаём файл, размер которого превышает ограничение
    dummy_file = tmp_path / "big.txt"
    dummy_file.write_text("a" * (2 << 20 + 1), encoding="utf-8")
    dummy = DummyItem(dummy_file)
    fh = FileHandler()
    fh.projectPath = tmp_path
    ce = CodeExtractor(fh)
    # Перехватываем вызов QMessageBox.warning (чтобы не возникало GUI)
    warned = False
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: nonlocal_set_warning()
    )

    def nonlocal_set_warning():
        nonlocal warned
        warned = True

    result = await ce.extract_code([dummy])
    # Файл не должен быть включён в результат
    assert "big.txt" not in result
    assert warned is True
