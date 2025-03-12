# .side_suction/test_main.py
import asyncio
import json
from pathlib import Path

import pytest
from main import SideSuction
from PySide6.QtCore import QItemSelection, QItemSelectionModel, Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMessageBox


# Уже существующий тест создания окна
def test_main_window_instantiation(qtbot):
    # Создаем окно приложения без запуска цикла событий
    window = SideSuction()
    qtbot.addWidget(window)
    # Проверяем, что основные атрибуты созданы
    assert hasattr(window, "progressBar")
    assert hasattr(window, "splitter")
    # Можно проверить, что некоторые виджеты внутри не равны None
    assert window.progressBar is not None


# Фикстура для SideSuction с временной директорией проекта
@pytest.fixture
def side_suction(qtbot, tmp_path):
    window = SideSuction()
    qtbot.addWidget(window)
    # Устанавливаем временную директорию в качестве projectPath
    window.file_handler.projectPath = tmp_path
    window.projectPathLineEdit.setText(str(tmp_path))
    return window


# Тест, где onProjectPathEntered вызывается с корректным путём.
@pytest.mark.asyncio
async def test_onProjectPathEntered_valid(side_suction, tmp_path):
    valid_path = tmp_path
    side_suction.projectPathLineEdit.setText(str(valid_path))

    async def dummy_scan():
        return {
            "fileInfoList": [],
            "availableExtensions": set(),
            "availableDirectories": set(),
        }

    side_suction.file_handler.scanProject = dummy_scan

    # Теперь вызов происходит в асинхронном контексте – event loop уже запущен
    side_suction.onProjectPathEntered()
    # Ждем немного, чтобы запустилась запланированная задача
    await asyncio.sleep(0.1)
    assert side_suction.file_handler.projectPath == valid_path


# Тест для неверного ввода пути – также делаем асинхронным
@pytest.mark.asyncio
async def test_onProjectPathEntered_invalid(side_suction, monkeypatch):
    invalid_path = "/non/existent/path"
    side_suction.projectPathLineEdit.setText(invalid_path)

    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    side_suction.onProjectPathEntered()
    await asyncio.sleep(0.1)
    assert warned is True


def test_toggleSelection(side_suction):
    # Добавляем несколько элементов в список файлов
    for i in range(3):
        item = QListWidgetItem(f"file{i}.txt")
        side_suction.fileListWidget.addItem(item)

    side_suction.toggleSelection(True)
    for i in range(side_suction.fileListWidget.count()):
        item = side_suction.fileListWidget.item(i)
        assert item.isSelected()

    side_suction.toggleSelection(False)
    for i in range(side_suction.fileListWidget.count()):
        item = side_suction.fileListWidget.item(i)
        assert not item.isSelected()


def test_updateLabels(side_suction):
    side_suction.selectedExtensions = {".py", ".txt"}
    side_suction.selectedDirectories = {Path("dir1"), Path("dir2")}
    side_suction.updateLabels()
    ext_text = side_suction.extLabel.text()
    assert ".py" in ext_text and ".txt" in ext_text
    dir_text = side_suction.dirLabel.text()
    assert "dir1" in dir_text and "dir2" in dir_text


@pytest.mark.asyncio
async def test_asyncExtractCode(side_suction):
    dummy_content = "```test.txt\ncontent\n```\n"

    async def dummy_extract(items, progress_manager=None):
        return dummy_content

    side_suction.code_extractor.extract_code = dummy_extract

    item = QListWidgetItem("test.txt")
    item.setData(Qt.UserRole + 1, "test.txt")
    item.setData(
        Qt.UserRole + 2, str(side_suction.file_handler.projectPath / "test.txt")
    )
    side_suction.fileListWidget.addItem(item)
    # Отмечаем элемент как выбранный, чтобы он попадал в selectedItems()
    item.setSelected(True)

    await side_suction.asyncExtractCode()
    assert side_suction.codeEditor.toPlainText() == dummy_content


def test_minifyOutputCode(side_suction, monkeypatch):
    original_text = "line1,\nline2,\nline3"
    side_suction.codeEditor.setPlainText(original_text)

    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    side_suction.minifyOutputCode()
    minified = side_suction.codeEditor.toPlainText()
    assert "\n" not in minified
    assert side_suction.isCodeMinified is True


def test_searchInCode(side_suction):
    content = "test search\nanother test search\nend"
    side_suction.codeEditor.setPlainText(content)
    side_suction.searchLineEdit.setText("search")
    side_suction.searchInCode()
    extra = side_suction.codeEditor.extraSelections()
    assert len(extra) > 0


def test_copyOutput(side_suction, monkeypatch):
    sample_text = "sample output"
    side_suction.codeEditor.setPlainText(sample_text)
    side_suction.isCodeMinified = False
    monkeypatch.setattr(side_suction, "minifyOutputCode", lambda: None)
    side_suction.copyOutput()
    clipboard = QApplication.clipboard()
    assert clipboard.text() == sample_text


def test_resetSelections(side_suction):
    item_dir = QListWidgetItem("dir1")
    side_suction.dirListWidget.addItem(item_dir)
    item_dir.setSelected(True)

    item_ext = QListWidgetItem("ext1")
    side_suction.extListWidget.addItem(item_ext)
    item_ext.setSelected(True)

    item_file = QListWidgetItem("file1.txt")
    side_suction.fileListWidget.addItem(item_file)
    item_file.setSelected(True)

    side_suction.selectedDirectories.add(Path("dir1"))
    side_suction.selectedExtensions.add("ext1")
    side_suction.selectedFilePaths.append("file1.txt")
    side_suction.selectedFileIndexes["file1.txt"] = 1

    side_suction.resetSelections()
    assert not side_suction.dirListWidget.selectedItems()
    assert not side_suction.extListWidget.selectedItems()
    assert not side_suction.fileListWidget.selectedItems()
    assert side_suction.selectedDirectories == set()
    assert side_suction.selectedExtensions == set()
    assert side_suction.selectedFilePaths == []
    assert side_suction.selectedFileIndexes == {}


@pytest.mark.asyncio
async def test_asyncLoadSelection(side_suction, tmp_path, monkeypatch):
    db_path = tmp_path / "side_db.json"
    selections = {
        str(side_suction.file_handler.projectPath): {
            "directories": ["dir1"],
            "extensions": [".py"],
            "files": ["file1.py"],
        }
    }
    db_path.write_text(
        json.dumps(selections, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    # Обновляем базу данных для selection_manager
    side_suction.selection_manager.PROJ_DB = db_path

    # Чтобы refreshDirectoryList добавил нужный элемент, задаем availableDirectories
    side_suction.file_handler.availableDirectories = {Path("dir1")}

    # Заполняем fileInfoList, чтобы refreshFileList добавил файл "file1.py"
    side_suction.file_handler.fileInfoList = [
        (Path("file1.py"), side_suction.file_handler.projectPath / "file1.py")
    ]

    # Добавляем фиктивный элемент для расширения (чтобы его можно было выбрать)
    item_ext = QListWidgetItem(".py")
    side_suction.extListWidget.addItem(item_ext)

    # Добавляем элемент для директории (хотя asyncLoadSelection его пересоздаёт)
    item_dir = QListWidgetItem("dir1")
    side_suction.dirListWidget.addItem(item_dir)

    # Убираем элемент для файла, т.к. refreshFileList его создаст заново
    # monkeypatch подменяет QMessageBox, чтобы окна не появлялись
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    # Вызываем asyncLoadSelection
    await side_suction.asyncLoadSelection()

    # Даем время на обработку событий
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()
    await asyncio.sleep(0.1)

    # Проверяем, что в списке директорий появился элемент "dir1" и он выбран
    found = False
    for i in range(side_suction.dirListWidget.count()):
        item = side_suction.dirListWidget.item(i)
        if item.text() == "dir1":
            found = item.isSelected()
            break
    assert found, "Элемент 'dir1' не выбран после asyncLoadSelection"

    # Проверяем, что элемент для расширения выбран
    assert item_ext.isSelected()

    # Проверяем, что в fileListWidget появился файл "file1.py" и выбран
    selected_files = [
        i.data(Qt.UserRole + 1) for i in side_suction.fileListWidget.selectedItems()
    ]
    assert "file1.py" in selected_files


def test_onFileSelected(side_suction):
    # Создаем два элемента
    item1 = QListWidgetItem("file1.txt")
    item1.setData(Qt.UserRole + 1, "file1.txt")
    item2 = QListWidgetItem("file2.txt")
    item2.setData(Qt.UserRole + 1, "file2.txt")
    side_suction.fileListWidget.addItem(item1)
    side_suction.fileListWidget.addItem(item2)

    # Получаем модель выбора
    selection_model = side_suction.fileListWidget.selectionModel()
    # Получаем индексы элементов
    index1 = side_suction.fileListWidget.indexFromItem(item1)
    index2 = side_suction.fileListWidget.indexFromItem(item2)
    # Выбираем оба элемента через модель
    selection_model.select(index1, QItemSelectionModel.Select)
    selection_model.select(index2, QItemSelectionModel.Select)

    # Получаем текущую выборку как QItemSelection
    selected = selection_model.selection()
    deselected = QItemSelection()  # пустая выборка

    # Вызываем onFileSelected с корректными аргументами
    side_suction.onFileSelected(selected, deselected)
    side_suction.refreshIndexedFileList()

    assert side_suction.selectedFileIndexes.get("file1.txt") == 1
    assert side_suction.selectedFileIndexes.get("file2.txt") == 2


def test_updateScrollbarAfterContentChange(side_suction):
    side_suction.codeEditor.verticalScrollBar().setValue(50)
    side_suction.updateScrollbarAfterContentChange()
    assert side_suction.codeEditor.verticalScrollBar().value() == 0


def test_update_progress(side_suction):
    side_suction.progressBar.setValue(0)
    side_suction.update_progress(75, "75%")
    assert side_suction.progressBar.value() == 75


@pytest.mark.asyncio
async def test_on_project_path_selected_cancel(qtbot, monkeypatch):
    """Проверяем ветку, когда пользователь нажимает 'Отмена' в диалоге."""
    window = SideSuction()
    qtbot.addWidget(window)

    # Мокаем диалог так, чтобы он возвращал пустую строку
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: "")
    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    window.onProjectPathSelected()
    await asyncio.sleep(0.05)
    assert warned is False, (
        "Не должно быть предупреждения, т.к. мы просто выходим, не выбран путь"
    )


@pytest.mark.asyncio
async def test_extract_code_no_selection(qtbot, monkeypatch):
    """Проверяем ветку, где не выделено ни одного файла."""
    window = SideSuction()
    qtbot.addWidget(window)
    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    # Не добавляем никаких файлов в fileListWidget
    # Вызываем extractCode()
    window.extractCode()
    await asyncio.sleep(0.05)
    assert warned is True
    # Проверяем, что HighlightColor = WARN (Color.WARN)
    # Можно, если нужно, проверить само окно.


@pytest.mark.asyncio
async def test_minify_output_no_comma(qtbot, monkeypatch):
    """Проверка ветки в minifyOutputCode, когда нет запятых."""
    window = SideSuction()
    qtbot.addWidget(window)

    # Устанавливаем текст, в котором нет запятых
    window.codeEditor.setPlainText("some text without comma")
    window.isCodeMinified = False

    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    window.minifyOutputCode()
    await asyncio.sleep(0.05)
    assert warned is True
    assert window.isCodeMinified is False, "Не должно переключиться в minified"


@pytest.mark.asyncio
async def test_search_in_code_no_matches(qtbot):
    """Ищем текст, который не встречается в документе."""
    window = SideSuction()
    qtbot.addWidget(window)
    window.codeEditor.setPlainText("some text here")
    window.searchLineEdit.setText("notfound")
    window.searchInCode()
    # Проверяем, что нет extraSelections (нет совпадений)
    assert not window.codeEditor.extraSelections()


@pytest.mark.asyncio
async def test_save_selection_no_project(qtbot, monkeypatch):
    """Проверяем вызов saveSelection, когда проект не задан."""
    window = SideSuction()
    qtbot.addWidget(window)
    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    # Обнулим projectPath
    window.file_handler.projectPath = None
    await window.asyncSaveSelection()
    assert warned is True


@pytest.mark.asyncio
async def test_load_selection_no_project(qtbot, monkeypatch):
    window = SideSuction()
    qtbot.addWidget(window)
    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    window.file_handler.projectPath = None
    await window.asyncLoadSelection()
    assert warned is True


@pytest.mark.asyncio
async def test_scan_project_no_path(qtbot, monkeypatch):
    """Вызываем scanProject, когда путь не задан."""
    window = SideSuction()
    qtbot.addWidget(window)

    window.file_handler.projectPath = None
    # Перехватываем QMessageBox.warning
    warned = False

    def fake_warning(*args, **kwargs):
        nonlocal warned
        warned = True

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)

    await window.scanProject()
    assert warned is True
