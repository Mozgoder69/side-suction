# .side_suction/logic/project_manager.py

import re
from pathlib import Path

import aiofiles
from config.settings import settings
from logic.project_source import LocalSource
from logic.status_manager import progress, report_result
from PySide6.QtCore import Qt


class ProjectManager:
    def __init__(self, source):
        self.source = source
        self.projectPath = (
            Path(str(source)) if isinstance(source, LocalSource) else None
        )
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

        rel_paths = await self.source.list_files()
        async for rel in progress(rel_paths, "Scanning Project"):
            # для локального source.read_file понадобится full_path, но фильтровать будем по rel
            full = None
            if hasattr(self.source, "root"):
                full = Path(self.source.root) / rel

            self.filteredFiles.append((rel, full))
            self.filteredExts.add(rel.suffix)
            self.filteredDirs.update(rel.parents)

        self.filteredDirs.discard(Path("."))
        return {
            "filteredFiles": self.filteredFiles,
            "filteredExts": self.filteredExts,
            "filteredDirs": self.filteredDirs,
        }

    async def get_filtered_files(self, selectedExts, selectedDirs):
        filtered = []
        async for rel, full in progress(self.filteredFiles, "Filtering Files"):
            # 1) исключаем по директориям
            if selectedDirs and any(parent in selectedDirs for parent in rel.parents):
                continue
            # 2) фильтруем по расширениям
            if selectedExts and rel.suffix not in selectedExts:
                continue

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

    async def extract_content(self, selected_items):
        content_pieces = []
        async for rel_path, _ in progress(selected_items, "Extracting Content"):
            try:
                text = await self.source.read_file(rel_path)
            except Exception as e:
                report_result(f"Cannot read {rel_path}: {e}", "Read Error", 1)
                continue

            # пусть размер считается уже по строке
            if len(text.encode("utf-8")) > settings.maxFileSize:
                report_result(f"File {rel_path} is too large", "File Size Limit", 1)
                continue

            content_pieces.append(f"```{rel_path}\n{text}\n```")

        return "\n".join(content_pieces)

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
