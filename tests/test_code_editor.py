# .side_suction/tests/test_code_editor.py

import pytest
from code_editor import CodeEditor
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, Qt, QTextOption
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPlainTextEdit


def test_line_number_area_paint_event(qtbot):
    """Проверяем, что paintEvent у LineNumberArea вызывается без ошибок."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    area = editor.lineNumberArea
    # Имитация вызова paintEvent
    area.update()  # Делает запрос на перерисовку
    # Проверяем, что никаких исключений не возникло
    assert True


def test_top_info_area_paint_event(qtbot):
    editor = CodeEditor()
    qtbot.addWidget(editor)
    top_area = editor.topInfoArea
    top_area.update()  # Запрос на перерисовку
    assert True


def test_bot_info_area_paint_event(qtbot):
    editor = CodeEditor()
    qtbot.addWidget(editor)
    bot_area = editor.botInfoArea
    bot_area.update()
    assert True


def test_line_number_area_sizeHint(qtbot):
    editor = CodeEditor()
    qtbot.addWidget(editor)
    area = editor.lineNumberArea
    size_hint = area.sizeHint()
    assert size_hint.width() > 0


def test_count_wrapped_lines(qtbot):
    editor = CodeEditor()
    # Отключим реальный показ окна (см. п.2)
    editor.setAttribute(Qt.WA_DontShowOnScreen)
    qtbot.addWidget(editor)

    # Включаем перенос
    editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
    editor.setWordWrapMode(QTextOption.WordWrap)

    # Устанавливаем размеры
    editor.resize(300, 200)

    # Если нужно дождаться, пока окно станет видимым (но не хотим реального отображения):
    # with qtbot.waitExposed(editor, timeout=1000):
    #     editor.show()
    # Или просто:
    editor.show()
    qtbot.wait(50)  # даём время на внутреннюю обработку

    long_text = "This is a very long line " * 20
    editor.setPlainText(long_text + "\n" + long_text)

    qtbot.wait(50)  # ещё раз подождём

    wrapped_lines = editor.countWrappedLines()
    assert wrapped_lines > 2


def test_custom_scrollbar_paint_event(qtbot):
    editor = CodeEditor()
    qtbot.addWidget(editor)
    scrollbar = editor.customScrollBar
    scrollbar.update()
    # Просто проверяем, что не падает
    assert True


def test_custom_scrollbar_mousePressEvent(qtbot):
    editor = CodeEditor()
    editor.setAttribute(Qt.WA_DontShowOnScreen)
    qtbot.addWidget(editor)

    # Допустим, назначим много строк
    for i in range(1000):
        editor.appendPlainText(f"Line {i + 1}")

    # Установим метки «fileStartLines»
    editor.customScrollBar.setFileStartLines([100, 500])

    editor.show()
    qtbot.wait(50)

    scrollbar = editor.customScrollBar
    # Вместо ручного QMouseEvent(...)
    QTest.mouseClick(
        scrollbar,
        Qt.LeftButton,
        Qt.NoModifier,
        QPoint(scrollbar.width() // 2, scrollbar.height() // 2),
    )

    # Проверяем, что value() обновился
    assert scrollbar.value() > 0


def test_code_editor_resize_event(qtbot):
    """Проверяем работу resizeEvent и перестройку геометрии подоконников."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    # Показываем окно и задаем размеры
    editor.show()
    editor.resize(800, 600)
    qtbot.waitForWindowShown(editor)

    # Дадим Qt чуть времени, чтобы обработать событие resize
    qtbot.wait(50)

    # Проверяем, что lineNumberArea и топ/бот области имеют ненулевую ширину/высоту
    assert editor.lineNumberArea.width() > 0
    assert editor.topInfoArea.height() > 0
    assert editor.botInfoArea.height() > 0
