# .side_suction/logic/browser_manager.py

from pathlib import Path

from logic.progress_manager import progress
from PySide6.QtCore import Qt


class BrowserManager:
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

    # async def get_filtered_dirs(self, selectedDirs):
    #     if not hasattr(self, '_dir_tree'):
    #         self._dir_tree = {d: set(d.parents) for d in self.filteredDirs}
    #     return {
    #         d for d in self.filteredDirs
    #         if not any(d in self._dir_tree[s] for s in selectedDirs if d != s)
    #     }

    # def get_filtered_dirs(self, selectedDirs):
    #     return {
    #         d
    #         for d in self.filteredDirs
    #         if not any(d.is_relative_to(s) for s in selectedDirs if d != s)
    #     }

    def get_filtered_exts(self):
        return {f.suffix for _, f in self.filteredFiles}

    def get_files_indexes(self, selectedFiles):
        return {
            item.data(Qt.UserRole + 1): i + 1 for i, item in enumerate(selectedFiles)
        }
