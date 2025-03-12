# .side_suction/logic/content_manager.py

import re
from pathlib import Path

import aiofiles
from config.settings import settings
from logic.progress_manager import progress
from PySide6.QtCore import Qt


class ContentManager:
    async def extract_content(self, selected_items):
        content = []
        async for item in progress(selected_items, "Extracting Content"):
            path = Path(item.data(Qt.UserRole + 2))
            if path.stat().st_size > settings.maxFileSize:
                print(f"Skipping {path}: too large")
                continue
            try:
                async with aiofiles.open(
                    path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    content.append(f"```{path.name}\n{await f.read()}\n```")
            except Exception as e:
                print(f"Error reading {path}: {e}")
        return "\n".join(content)

    def minify_web_tags(self, code: str) -> str:
        tag_pattern = re.compile(r"<(/?[A-Za-z][A-Za-z0-9\-]*)(.*?)(/?)>", re.DOTALL)

        def repl(m: re.Match) -> str:
            tag_name, inner, slash = m.groups()
            inner = re.sub(r"[\r\n]+", " ", inner)
            inner = re.sub(r"\s{2,}", " ", inner).strip()
            return f"<{tag_name} {inner}{slash}>" if inner else f"<{tag_name}{slash}>"

        minified_code = tag_pattern.sub(repl, code)
        leading_spaces_pattern = re.compile(r"^[ \t]+(?=<)", re.MULTILINE)
        return leading_spaces_pattern.sub("", minified_code)

    def minify_content(self, content: str) -> str:
        if not content:
            return content
        content = ", ".join([line.strip() for line in content.split(",\n")])
        content = content.replace("\n\n", "\n").replace(" ", " ")
        return self.minify_web_tags(content)
