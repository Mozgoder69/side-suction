# .side_suction/logic/project_manager.py

from pathlib import Path

from logic.progress_manager import progress
from PySide6.QtCore import Qt
import re
from pathlib import Path

import aiofiles
from config.settings import settings
from logic.progress_manager import progress
from utils.report import report_result


class ProjectManager:
    def __init__(self):
        self.projectPath = None
        self.filteredDirs = set()
        self.filteredExts = set()
        self.filteredFiles = []

    def set_project_path(self, path):
        self.projectPath = Path(path)
        return self.projectPath.is_dir()

    async def scan_project(self):
        self.filteredFiles.clear()
        self.filteredExts.clear()
        self.filteredDirs.clear()
        files = list(self.projectPath.rglob("*"))
        result = []
        async for file in progress(files, "Scanning Project"):
            if file.is_file():
                rel_path = file.relative_to(self.projectPath)
                result.append((rel_path, file))
                self.filteredExts.add(file.suffix)
                self.filteredDirs.update(rel_path.parents)
        self.filteredFiles = result
        self.filteredDirs.discard(Path("."))
        return {
            "filteredFiles": self.filteredFiles,
            "filteredExts": self.filteredExts,
            "filteredDirs": self.filteredDirs,
        }

    async def get_filtered_files(self, selectedExts, selectedDirs):
        excluded = {self.projectPath / d for d in selectedDirs}
        filtered = []
        async for rel, full in progress(self.filteredFiles, "Filtering Files"):
            if not any(p in excluded for p in full.parents) and (
                not selectedExts or full.suffix in selectedExts
            ):
                filtered.append((rel, full))
        return filtered

    async def get_filtered_dirs(self, selectedDirs):
        filtered_dirs = set()
        async for d in progress(self.filteredDirs, "Filtering Directories"):
            if not any(d.is_relative_to(s) for s in selectedDirs if d != s):
                filtered_dirs.add(d)
        return filtered_dirs

    def get_filtered_exts(self):
        return {f.suffix for _, f in self.filteredFiles}

    def get_files_indexes(self, selectedFiles):
        return {
            item.data(Qt.UserRole + 1): i + 1 for i, item in enumerate(selectedFiles)
        }

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
