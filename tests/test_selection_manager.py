# .side_suction/tests/test_selection_manager.py

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox
from selection_manager import SelectionManager


@pytest.mark.asyncio
async def test_save_selection_exception(tmp_path, monkeypatch):
    # Симулируем ошибку при чтении файла
    db_path = tmp_path / "db.json"
    sm = SelectionManager(db_path)
    monkeypatch.setattr(sm, "PROJ_DB", db_path)
    # Подавляем QMessageBox.critical, чтобы не появлялось окно
    monkeypatch.setattr(
        "selection_manager.QMessageBox.critical", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "aiofiles.open",
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Test error")),
    )
    result = await sm.saveSelection(Path("/dummy"), {"data": 123})
    assert result is False


@pytest.mark.asyncio
async def test_load_selection_no_file(tmp_path):
    db_path = tmp_path / "nonexistent.json"
    sm = SelectionManager(db_path)
    selection = await sm.loadSelection(Path("/dummy"))
    assert selection is None


@pytest.mark.asyncio
async def test_load_selection_invalid_json(tmp_path, monkeypatch):
    db_path = tmp_path / "db.json"
    db_path.write_text("invalid_json", encoding="utf-8")
    sm = SelectionManager(db_path)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    selection = await sm.loadSelection(Path("/dummy"))
    assert selection is None


@pytest.mark.asyncio
async def test_save_and_load_selection(tmp_path, monkeypatch):
    # Используем временный файл для базы данных
    db_path = tmp_path / "side_db.json"
    sm = SelectionManager(db_path)
    project_path = tmp_path / "project"
    project_path.mkdir()
    selections = {
        "directories": ["dir1", "dir2"],
        "extensions": [".py"],
        "files": ["file1.py"],
    }
    # Подменяем QMessageBox, чтобы не выскакивали окна
    monkeypatch.setattr(
        "selection_manager.QMessageBox.critical", lambda *args, **kwargs: None
    )

    result = await sm.saveSelection(project_path, selections)
    assert result is True

    loaded = await sm.loadSelection(project_path)
    assert loaded == selections


@pytest.mark.asyncio
async def test_save_and_load_selection_valid(tmp_path, monkeypatch):
    # Создаем временный файл для БД
    db_path = tmp_path / "db.json"
    sm = SelectionManager(db_path)
    project_path = tmp_path / "project"
    project_path.mkdir()
    selections = {"directories": ["dirA"], "extensions": [".py"], "files": ["a.py"]}
    monkeypatch.setattr(
        "selection_manager.QMessageBox.critical", lambda *args, **kwargs: None
    )
    result = await sm.saveSelection(project_path, selections)
    assert result is True
    # Перечитываем файл вручную и проверяем содержимое
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert str(project_path) in data
    loaded = await sm.loadSelection(project_path)
    assert loaded == selections


@pytest.mark.asyncio
async def test_load_no_db(tmp_path):
    db_path = tmp_path / "non_existent.json"
    sm = SelectionManager(db_path)
    project_path = tmp_path / "project"
    project_path.mkdir()
    loaded = await sm.loadSelection(project_path)
    assert loaded is None
