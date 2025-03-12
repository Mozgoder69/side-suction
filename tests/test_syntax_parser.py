# .side_suction/tests/test_syntax_parser.py

from PySide6.QtGui import QTextDocument
from syntax_parser import SyntaxParser


def test_syntax_parser_rules(qtbot):
    doc = QTextDocument()
    highlighter = SyntaxParser(doc)
    # Проверяем, что ключевые категории присутствуют и не пусты
    expected_keys = ["keywords", "additional", "comments_single", "strings", "other"]
    for key in expected_keys:
        assert key in highlighter.compiledPatterns
        # Например, для ключевых слов должно быть не пусто
        if key == "keywords":
            assert len(highlighter.compiledPatterns[key]) > 0

    # Тестируем перерасчёт подсветки с примером многострочного комментария
    test_text = "/* This is a\nmultiline comment */\ncode"
    doc.setPlainText(test_text)
    highlighter.rehighlight()
    # Основная цель – отсутствие исключений при обработке
    assert True
