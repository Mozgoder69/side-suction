# .side_suction/tests/test_file_handler.py

from pathlib import Path

import pytest
from file_handler import FileHandler


# Простая реализация фиктивного progress_manager для тестов
class DummyProgressManager:
    def update(self, value, format_text=None):
        pass


def test_set_project_path_valid(tmp_path):
    fh = FileHandler()
    result = fh.setProjectPath(str(tmp_path))
    assert result is True
    assert fh.projectPath == tmp_path


def test_set_project_path_invalid(tmp_path):
    fh = FileHandler()
    # Создаем файл вместо директории
    file_path = tmp_path / "dummy.txt"
    file_path.write_text("dummy")
    result = fh.setProjectPath(str(file_path))
    assert result is False


def test_scan_project_without_project_path():
    fh = FileHandler()
    with pytest.raises(ValueError) as excinfo:
        # projectPath не установлен, должно возникнуть исключение
        import asyncio

        asyncio.run(fh.scanProject())
    assert "No project directory selected." in str(excinfo.value)


def test_is_relative_to_error():
    fh = FileHandler()
    # Передадим два пути, где второй не является родительским для первого.
    path = Path("/a/b/c")
    other = Path("/x/y")
    # Ожидаем, что метод вернёт False, так как c не относительный к /x/y
    assert fh.is_relative_to(path, other) is False


@pytest.mark.asyncio
async def test_scan_project(tmp_path):
    # Создаем структуру: один файл в корне и один в поддиректории
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file1 = tmp_path / "file1.txt"
    file2 = subdir / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    fh = FileHandler()
    fh.setProjectPath(str(tmp_path))
    progress = DummyProgressManager()
    result = await fh.scanProject(progress_manager=progress)
    # Проверяем, что найдено 2 файла
    assert len(result["fileInfoList"]) == 2
    # Проверяем, что расширения включают '.txt'
    assert ".txt" in result["availableExtensions"]
    # Директории должны быть обнаружены (хотя их точное число зависит от структуры)
    assert len(result["availableDirectories"]) >= 1


@pytest.mark.asyncio
async def test_refresh_file_list(tmp_path):
    # Создаем файлы с разными расширениями
    file_txt = tmp_path / "file1.txt"
    file_md = tmp_path / "file2.md"
    file_txt.write_text("text")
    file_md.write_text("markdown")

    fh = FileHandler()
    fh.setProjectPath(str(tmp_path))
    await fh.scanProject()
    # Фильтруем файлы по расширению .txt
    filtered = await fh.refreshFileList(
        selectedExtensions={".txt"}, selectedDirectories=set()
    )
    returned_files = [str(rel) for rel, full in filtered]
    # Проверяем, что возвращается только файл с расширением .txt
    assert any("file1.txt" in fname for fname in returned_files)
    assert all(fname.endswith(".txt") for fname in returned_files)


def test_refresh_directory_list():
    # Симулируем структуру директорий

    fh = FileHandler()
    subdir1 = Path("subdir1")
    subdir2 = Path("subdir1/subdir2")
    fh.availableDirectories = {subdir1, subdir2}
    # Если выбрана subdir1, то subdir2 (находящаяся внутри subdir1) не должна отображаться
    visible = fh.refreshDirectoryList({subdir1})
    assert subdir1 in visible
    assert subdir2 not in visible


def test_refresh_extension_list(tmp_path):
    # Подготавливаем fileInfoList с двумя файлами
    fh = FileHandler()
    dummy1 = tmp_path / "a.txt"
    dummy2 = tmp_path / "b.py"
    fh.fileInfoList = [
        (dummy1.relative_to(tmp_path), dummy1),
        (dummy2.relative_to(tmp_path), dummy2),
    ]
    extensions = fh.refreshExtensionList()
    assert ".txt" in extensions
    assert ".py" in extensions


def test_refresh_indexed_file_list():
    # Создаем фиктивные объекты, имитирующие QListWidgetItem с методом data(role)
    class DummyItem:
        def __init__(self, data_value):
            self._data = data_value

        def data(self, role):
            return self._data

    fh = FileHandler()
    item1 = DummyItem("file1")
    item2 = DummyItem("file2")
    selected = [item1, item2]
    indexes = fh.refreshIndexedFileList(selected)
    assert indexes["file1"] == 1
    assert indexes["file2"] == 2
