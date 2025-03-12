# .side_suction/ui/syntax_parser.py

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class SyntaxParser(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.definePatterns()
        self.precompileRegex()
        self.constructRules()
        self.createFormats()
        self.addHighlightingRules()

    def constructRules(self):
        self.STATE_NONE = 0
        self.STATE_COMMENT = 1
        self.STATE_STRING = 2
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
        self.miscPatterns = {
            "section": r"<[a-zA-Z][a-zA-Z0-9]*\b[^>]*>|<\/[a-zA-Z][a-zA-Z0-9]*>|\[[^\]]+\]|![a-zA-Z0-9\-]+|(?i)(?:@|#\s*(pragma|define|include|if|endif|else)|#\[.*?\]|\.\w+|\b[a-zA-Z0-9_]+:)|(?:\{\%|\{\{|--\[)",
            "attribute": r"\b[A-Za-z0-9_-]+\s*=\s*[^\n]*|\b[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\b|\b(href|src|id|style|alt|title|name|value|type)\b",
            "callable": r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()|\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\()",
        }
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
            "separators": [QRegularExpression(p) for p in self.separatorPatterns],
            "operators": [QRegularExpression(p) for p in self.operatorPatterns],
            "misc": {k: QRegularExpression(v) for k, v in self.miscPatterns.items()},
            "keywords": [QRegularExpression(p) for p in self.keywordPatterns],
            "datatypes": [QRegularExpression(p) for p in self.datatypePatterns],
            "constants": [QRegularExpression(p) for p in self.constantPatterns],
            "numbers": [QRegularExpression(p) for p in self.numberPatterns],
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
        self.syntaxFormats = {}
        for key, args in format_configs.items():
            color, bold = args
            textFormat = QTextCharFormat()
            textFormat.setForeground(QColor(color))
            if bold:
                textFormat.setFontWeight(QFont.Bold)
            self.syntaxFormats[key] = textFormat

    def addHighlightingRules(self):
        self.highlightingRules = []
        priority_order = [
            ("separators", "separator"),
            ("operators", "operator"),
            ("misc", "section", "section"),
            ("misc", "attribute", "attribute"),
            ("misc", "callable", "callable"),
            ("keywords", "keyword"),
            ("datatypes", "datatype"),
            ("constants", "literal"),
            ("numbers", "literal"),
        ]

        for item in priority_order:
            if len(item) == 3:
                category, key, format_name = item
                pattern = self.compiledPatterns[category].get(key)
                if pattern:
                    fmt = self.syntaxFormats[format_name]
                    self.highlightingRules.append((pattern, fmt))
            else:
                category, format_name = item
                for pattern in self.compiledPatterns[category]:
                    fmt = self.syntaxFormats[format_name]
                    self.highlightingRules.append((pattern, fmt))

        self.blockCommentFormat = self.syntaxFormats["comment"]
        self.blockStringFormat = self.syntaxFormats["literal"]

    def is_inside_range(self, start, ranges):
        return any(s <= start < e for s, e in ranges)

    def is_protected(self, start, end, exclude_ranges=None):
        ranges = self.protectedRanges()
        if exclude_ranges:
            ranges = [r for r in ranges if r not in exclude_ranges]
        return any(s < end and e > start for s, e in ranges)

    def _is_protected_match(self, match, state_flag):
        """Проверка находится ли совпадение в защищенной области"""
        start = match.capturedStart()
        other_ranges = (
            self.commentRanges if state_flag == self.STATE_STRING else self.stringRanges
        )
        return self.is_inside_range(start, other_ranges)

    def _apply_format(self, start, length, format_type, range_list):
        """Применение форматирования и добавление в список диапазонов"""
        self.setFormat(start, length, format_type)
        range_list.append((start, start + length))

    def handleInlineConstruct(
        self, text, patterns, format_type, range_list, protected_ranges
    ):
        for pattern in patterns:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start, length = match.capturedStart(), match.capturedLength()
                if not self.is_inside_range(start, protected_ranges):
                    self.setFormat(start, length, format_type)
                    range_list.append((start, start + length))

    def handleInlineStrings(self, text):
        self.handleInlineConstruct(
            text,
            self.inlineStringRegexes,
            self.blockStringFormat,
            self.stringRanges,
            self.commentRanges,
        )

    def handleInlineComments(self, text):
        self.handleInlineConstruct(
            text,
            self.inlineCommentRegexes,
            self.blockCommentFormat,
            self.commentRanges,
            self.stringRanges,
        )

    def handleBlockConstruct(self, text, patterns, state_flag, format_type, range_list):
        text_length = len(text)
        prev_state = self.previousBlockState()

        # Обработка продолжения конструкции
        if prev_state == state_flag:
            # Форматируем весь блок
            self._apply_format(0, text_length, format_type, range_list)
            for start_regex, end_regex in patterns:
                end_match = end_regex.match(text)
                if not end_match.hasMatch():
                    continue
                end_index = end_match.capturedEnd()
                # Проверяем, защищено ли закрытие
                if not self._is_protected_match(end_match, state_flag):
                    # Форматируем до закрытия
                    self._apply_format(0, end_index, format_type, range_list)
                    # Сбрасываем форматирование остатка в "default"
                    if end_index < text_length:
                        self._apply_format(
                            end_index,
                            text_length - end_index,
                            self.syntaxFormats["default"],
                            range_list,
                        )
                    self.setCurrentBlockState(self.STATE_NONE)
                    return
            self.setCurrentBlockState(state_flag)
            return

        # Поиск новой конструкции
        pos = 0
        while pos < text_length:
            for start_regex, end_regex in patterns:
                start_match = start_regex.match(text, pos)
                if not start_match.hasMatch():
                    continue
                start_index = start_match.capturedStart()
                # Проверяем, защищено ли начало
                if self._is_protected_match(start_match, state_flag):
                    continue
                match_length = len(start_match.captured())
                end_match = end_regex.match(text, start_index + match_length)
                if end_match.hasMatch():
                    end_index = end_match.capturedEnd()
                    # Проверяем закрытие
                    if not self._is_protected_match(end_match, state_flag):
                        self._apply_format(
                            start_index,
                            end_index - start_index,
                            format_type,
                            range_list,
                        )
                        # Сбрасываем форматирование остатка в "default"
                        if end_index < text_length:
                            self._apply_format(
                                end_index,
                                text_length - end_index,
                                self.syntaxFormats["default"],
                                range_list,
                            )
                        self.setCurrentBlockState(self.STATE_NONE)
                        return
                # Обработка многострочной конструкции
                other_ranges = (
                    self.commentRanges
                    if state_flag == self.STATE_STRING
                    else self.stringRanges
                )
                last_end = max([e for s, e in other_ranges if e <= start_index] or [-1])
                format_start = max(start_index, last_end + 1)
                self._apply_format(
                    format_start, text_length - format_start, format_type, range_list
                )
                self.setCurrentBlockState(state_flag)
                return
            pos += 1

        self.setCurrentBlockState(self.STATE_NONE)

    # Обновлённые методы
    def handleBlockStrings(self, text):
        self.handleBlockConstruct(
            text,
            self.blockStringRegexes,
            self.STATE_STRING,
            self.blockStringFormat,
            self.stringRanges,
        )

    def handleBlockComments(self, text):
        self.handleBlockConstruct(
            text,
            self.blockCommentRegexes,
            self.STATE_COMMENT,
            self.blockCommentFormat,
            self.commentRanges,
        )

    # Обновляем highlightBlock для использования новых методов
    def highlightBlock(self, text):
        self.setFormat(0, len(text), self.syntaxFormats["default"])
        self.stringRanges.clear()
        self.commentRanges.clear()

        # Обрабатываем строки, если не внутри комментария
        if self.currentBlockState() != self.STATE_COMMENT:
            self.handleBlockStrings(text)

        # Обрабатываем комментарии, если не внутри строки
        if self.currentBlockState() != self.STATE_STRING:
            self.handleBlockComments(text)

        self.handleInlineStrings(text)
        self.handleInlineComments(text)

        for pattern, fmt in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start, length = match.capturedStart(), match.capturedLength()
                end = start + length
                if not self.is_protected(start, end):
                    self.setFormat(start, length, fmt)
