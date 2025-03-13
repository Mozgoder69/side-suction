# .side_suction/ui/syntax_parser.py
from enum import IntEnum

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class State(IntEnum):
    DEFAULT = 0
    COMMENT = 1
    STRING = 2


class SyntaxParser(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.definePatterns()
        self.precompileRegex()
        self.constructRules()
        self.createFormats()
        self.addParserRules()

    def constructRules(self):
        self.stringRanges = []
        self.commentRanges = []
        self.blockCommentRegexes = [
            (QRegularExpression(start), QRegularExpression(end))
            for start, end in self.blockCommentPatterns
        ]
        self.inlineCommentRegexes = [
            QRegularExpression(p) for p in self.inlineCommentPatterns
        ]
        self.blockStringRegexes = [
            (QRegularExpression(start), QRegularExpression(end))
            for start, end in self.blockStringPatterns
        ]
        self.inlineStringRegexes = [
            QRegularExpression(p) for p in self.inlineStringPatterns
        ]

    def protectedRanges(self):
        return self.stringRanges + self.commentRanges

    def definePatterns(self):
        self.separatorPatterns = [r"[,;(){}\[\]:]"]
        self.operatorPatterns = [
            r"(?i)[+\-*/%<>&^|~!]=?|<<|>>|==|!=|===|!==|[+\-*/%&|^]=?|<<=?|>>=?|&&|\|\||\?\??|:|\.{1,3}|"
        ]
        self.sectionPatterns = [
            r"<[a-zA-Z][a-zA-Z0-9]*\b[^>]*>|<\/[a-zA-Z][a-zA-Z0-9]*>|\[[^\]]+\]|![a-zA-Z0-9\-]+|(?i)(?:@|#\s*(pragma|define|include|if|endif|else)|#\[.*?\]|\.\w+|\b[a-zA-Z0-9_]+:)|(?:\{\%|\{\{|--\[)"
        ]
        self.attributePatterns = [
            r"\b[A-Za-z0-9_-]+\s*=\s*[^\n]*|\b[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\b|\b(href|src|id|style|alt|title|name|value|type)\b"
        ]
        self.callablePatterns = [
            r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()|\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\()"
        ]
        self.keywordPatterns = [
            r"(?i)\b(not|and|or|if|else|elif|switch|case|default|for|foreach|while|do|break|continue|return|pass|"
            r"let|var|const|function|def|lambda|class|interface|struct|enum|implements|extends|final|"
            r"static|abstract|public|protected|private|package|namespace|module|template|import|export|using|new|"
            r"try|catch|finally|throw|throws|exception|raise|with|include|require|typename|typedef|await|async|yield|"
            r"in|is|as|self|this|super|unsigned|long|short|extern|volatile|signed|sizeof|goto|inline|constexpr|"
            r"friend|override|virtual|operator|typeof|instanceof|native|synchronized|transient|strictfp|nonlocal|global|"
            r"assert|del|symbol|infinity|nan|of|nullptr|get|set|decltype|noexcept|explicit|implicit|mutable|"
            r"register|restrict|co_await|co_yield|co_return|concept|requires|event|delegate|property|"
            r"from|where|select|delete|update|insert|union|join|group|order|by)\b"
        ]
        self.datatypePatterns = [
            r"(?i)\b(bool|boolean|int|float|double|char|string|void)\b"
        ]
        self.constantPatterns = [r"(?i)\b(true|false|null|none|undefined|nan)\b"]
        self.numberPatterns = [r"\b(?:\d*\.?\d+(?:[eE][+-]?\d+)?|\d+)\b"]
        self.inlineStringPatterns = [
            r'"(?:\\.|[^"\\])*"',
            r"'(?:\\.|[^'\\])*'",
            r"`(?:\\.|[^`\\])*`",
        ]
        self.blockStringPatterns = [(r"'''", r"'''"), (r'"""', r'"""')]
        self.inlineCommentPatterns = [r"(//|#|--)[^\n]*"]
        self.blockCommentPatterns = [(r"/\*", r"\*/"), (r"<!--", r"-->")]

    def precompileRegex(self):
        self.compiledPatterns = {
            "separator": [QRegularExpression(p) for p in self.separatorPatterns],
            "operator": [QRegularExpression(p) for p in self.operatorPatterns],
            "section": {QRegularExpression(p) for p in self.sectionPatterns},
            "attribute": {QRegularExpression(p) for p in self.attributePatterns},
            "callable": {QRegularExpression(p) for p in self.callablePatterns},
            "keyword": [QRegularExpression(p) for p in self.keywordPatterns],
            "datatype": [QRegularExpression(p) for p in self.datatypePatterns],
            "constant": [QRegularExpression(p) for p in self.constantPatterns],
            "number": [QRegularExpression(p) for p in self.numberPatterns],
        }

    def createFormats(self):
        """Predefined tokens which exists independently of user input can be bold"""
        format_configs = {
            "default": ("#ccc", False),  # Plain text, variables - user data
            "separator": ("#ccc", True),  # Separators - structural element
            "operator": ("#f6c", True),  # Operators - structural element
            "section": ("#6cf", True),  # Tags, annotations - structural element
            "attribute": ("#8c0", False),  # Keys, properties - user data
            "callable": ("#f0a", False),  # Functions, methods - user data
            "keyword": ("#08c", True),  # Keywords - structural element
            "datatype": ("#80c", True),  # Datatypes - structural element
            "literal": ("#fc6", False),  # Strings, numbers, constants - user data
            "comment": ("#096", False),  # Documentation - user data
        }
        self.formats = {}
        for key, args in format_configs.items():
            color, bold = args
            textFormat = QTextCharFormat()
            textFormat.setForeground(QColor(color))
            if bold:
                textFormat.setFontWeight(QFont.Bold)
            self.formats[key] = textFormat

    def addParserRules(self):
        self.parserRules = []
        priority_config = [
            ("separator", "separator"),
            ("operator", "operator"),
            ("section", "section"),
            ("attribute", "attribute"),
            ("callable", "callable"),
            ("keyword", "keyword"),
            ("datatype", "datatype"),
            ("constant", "literal"),
            ("number", "literal"),
        ]

        for item in priority_config:
            patterns, formats = item
            for pattern in self.compiledPatterns[patterns]:
                format = self.formats[formats]
                self.parserRules.append((pattern, format))

        self.commentFormat = self.formats["comment"]
        self.stringFormat = self.formats["literal"]

    def is_inside_range(self, start, ranges):
        return any(s <= start and e > start for s, e in ranges)

    def is_protected(self, start, end, exclude_ranges=None):
        ranges = self.protectedRanges()
        if exclude_ranges:
            ranges = [r for r in ranges if r not in exclude_ranges]
        return any(s < end and e > start for s, e in ranges)

    def _is_protected_match(self, match, state):
        """Проверка находится ли совпадение в защищенной области"""
        start = match.capturedStart()
        used_ranges = self.commentRanges if state == State.STRING else self.stringRanges
        return self.is_inside_range(start, used_ranges)

    def _apply_format(self, start, length, format, target_ranges):
        """Применение форматирования и добавление в список диапазонов"""
        self.setFormat(start, length, format)
        end = start + length
        target_ranges.append((start, end))

    def handleInlineConstruct(self, text, patterns, format, is_comment):
        if is_comment:
            target_ranges, used_ranges = self.commentRanges, self.stringRanges
        else:
            target_ranges, used_ranges = self.stringRanges, self.commentRanges
        for pattern in patterns:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start, length = match.capturedStart(), match.capturedLength()
                if not self.is_inside_range(start, used_ranges):
                    self.setFormat(start, length, format)
                    target_ranges.append((start, start + length))

    def handleInlineStrings(self, text):
        self.handleInlineConstruct(
            text, self.inlineStringRegexes, self.stringFormat, False
        )

    def handleInlineComments(self, text):
        self.handleInlineConstruct(
            text, self.inlineCommentRegexes, self.commentFormat, True
        )

    def handleBlockConstruct(self, text, patterns, cur_state, format, ranges):
        txt_len = len(text)
        prev_state = self.previousBlockState()

        # Обработка продолжения конструкции
        if prev_state == cur_state:
            # Форматируем весь блок
            self._apply_format(0, txt_len, format, ranges)
            for start_regex, end_regex in patterns:
                end_match = end_regex.match(text)
                if not end_match.hasMatch():
                    continue
                end_ix = end_match.capturedEnd()
                # Проверяем, защищено ли закрытие
                if not self._is_protected_match(end_match, cur_state):
                    # Форматируем до закрытия
                    self._apply_format(0, end_ix, format, ranges)
                    # Сбрасываем форматирование остатка в "default"
                    if end_ix < txt_len:
                        match_len = txt_len - end_ix
                        self._apply_format(
                            end_ix, match_len, self.formats["default"], ranges
                        )
                    self.setCurrentBlockState(State.DEFAULT)
                    return
            self.setCurrentBlockState(cur_state)
            return

        # Поиск новой конструкции
        pos = 0
        while pos < txt_len:
            for start_regex, end_regex in patterns:
                start_match = start_regex.match(text, pos)
                if not start_match.hasMatch():
                    continue
                start_ix = start_match.capturedStart()
                # Проверяем, защищено ли начало
                if self._is_protected_match(start_match, cur_state):
                    continue
                match_length = len(start_match.captured())
                end_match = end_regex.match(text, start_ix + match_length)
                if end_match.hasMatch():
                    end_ix = end_match.capturedEnd()
                    # Проверяем закрытие
                    if not self._is_protected_match(end_match, cur_state):
                        self._apply_format(start_ix, end_ix - start_ix, format, ranges)
                        # Сбрасываем форматирование остатка в "default"
                        if end_ix < txt_len:
                            match_len = txt_len - end_ix
                            self._apply_format(
                                end_ix, match_len, self.formats["default"], ranges
                            )
                        self.setCurrentBlockState(State.DEFAULT)
                        return
                # Обработка многострочной конструкции
                other_ranges = (
                    self.commentRanges
                    if cur_state == State.STRING
                    else self.stringRanges
                )
                last_end = max([e for s, e in other_ranges if e <= start_ix] or [-1])
                format_start = max(start_ix, last_end + 1)
                format_len = txt_len - format_start
                self._apply_format(format_start, format_len, format, ranges)
                self.setCurrentBlockState(cur_state)
                return
            pos += 1

        self.setCurrentBlockState(State.DEFAULT)

    # Обновлённые методы
    def handleBlockStrings(self, text):
        self.handleBlockConstruct(
            text,
            self.blockStringRegexes,
            State.STRING,
            self.stringFormat,
            self.stringRanges,
        )

    def handleBlockComments(self, text):
        self.handleBlockConstruct(
            text,
            self.blockCommentRegexes,
            State.COMMENT,
            self.commentFormat,
            self.commentRanges,
        )

    # Обновляем highlightBlock для использования новых методов
    def highlightBlock(self, text):
        self.setFormat(0, len(text), self.formats["default"])
        self.stringRanges.clear()
        self.commentRanges.clear()

        # Обрабатываем строки, если не внутри комментария
        if self.currentBlockState() != State.COMMENT:
            self.handleBlockStrings(text)

        # Обрабатываем комментарии, если не внутри строки
        if self.currentBlockState() != State.STRING:
            self.handleBlockComments(text)

        self.handleInlineStrings(text)
        self.handleInlineComments(text)

        for pattern, format in self.parserRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start, length = match.capturedStart(), match.capturedLength()
                end = start + length
                if not self.is_protected(start, end):
                    self.setFormat(start, length, format)
