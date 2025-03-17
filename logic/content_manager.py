# .side_suction/logic/content_manager.py

import re
from pathlib import Path

import aiofiles
from config.settings import settings
from logic.progress_manager import progress
from utils.report import report_result


class ContentManager:
    async def extract_content(self, project_path, selected_items):
        content = []
        project_path = Path(project_path)
        async for item in progress(selected_items, "Extracting Content"):
            rel_path = Path(item)
            abs_path = project_path / rel_path
            if abs_path.stat().st_size > settings.maxFileSize:
                report_result(f"File {rel_path} is too large", "File Size Limit", 1)
                continue

            async with aiofiles.open(abs_path, encoding="utf-8", errors="replace") as f:
                content.append(f"```{rel_path}\n{await f.read()}\n```")
        return "\n".join(content)

    def minify_web_tags(self, content: str) -> str:
        tag_pattern = re.compile(r"<(/?[A-Za-z][A-Za-z0-9\-]*)(.*?)(/?)>", re.DOTALL)

        def repl(m: re.Match) -> str:
            tag_name, inner, slash = m.groups()
            inner = re.sub(r"[\r\n]+", " ", inner)
            inner = re.sub(r"\s{2,}", " ", inner).strip()
            return f"<{tag_name} {inner}{slash}>" if inner else f"<{tag_name}{slash}>"

        minified_content = tag_pattern.sub(repl, content)
        leading_spaces_pattern = re.compile(r"^[ \t]+(?=<)", re.MULTILINE)
        return leading_spaces_pattern.sub("", minified_content)

    def minify_content(self, content: str) -> str:
        if not content:
            return content
        content = ", ".join([line.strip() for line in content.split(",\n")])
        content = content.replace("\n\n", "\n").replace(" ", " ")
        return self.minify_web_tags(content)
