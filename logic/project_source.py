# logic/project_source.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import aiofiles
import aiohttp


class IProjectSource(ABC):
    """Интерфейс источника проекта: список файлов и чтение их содержимого."""

    @abstractmethod
    def __str__(self) -> str:
        """Человекочитаемое представление (например, путь или owner/repo#branch)."""
        pass

    @abstractmethod
    async def list_files(self) -> List[Path]:
        """
        Вернуть список путей всех файлов (относительно корня источника).
        """
        pass

    @abstractmethod
    async def read_file(self, rel_path: Path) -> str:
        """
        Прочитать содержимое файла по относительному пути.
        """
        pass

    async def close(self):
        """
        Опциональная очистка ресурсов (например, закрытие HTTP-сессии).
        """
        pass


class LocalSource(IProjectSource):
    """Источник из локальной папки."""

    def __init__(self, root: str):
        self.root = Path(root)

    def __str__(self) -> str:
        return str(self.root)

    async def list_files(self) -> List[Path]:
        return [p.relative_to(self.root) for p in self.root.rglob("*") if p.is_file()]

    async def read_file(self, rel_path: Path) -> str:
        p = self.root / rel_path
        async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
            return await f.read()


class GitHubSource(IProjectSource):
    """Источник из публичного GitHub-репозитория."""

    def __init__(self, owner: str, repo: str, branch: str = "main"):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.session = aiohttp.ClientSession()
        # URL для получения дерева файлов
        self.api_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/git/trees/{branch}?recursive=1"
        )
        # Базовый URL для «сырых» файлов
        self.raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"

    def __str__(self) -> str:
        return f"{self.owner}/{self.repo}#{self.branch}"

    @classmethod
    def from_tree_url(cls, url: str) -> "GitHubSource":
        """
        Альтернативный конструктор из полного GitHub API URL вида
        https://api.github.com/repos/owner/repo/git/trees/branch?recursive=1
        """
        import re

        m = re.match(
            r"https://api.github.com/repos/([^/]+)/([^/]+)/git/trees/([^?]+)", url
        )
        if not m:
            raise ValueError(f"Invalid GitHub tree URL: {url}")
        owner, repo, branch = m.groups()
        return cls(owner, repo, branch)

    async def list_files(self) -> List[Path]:
        async with self.session.get(self.api_url) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return [
            Path(item["path"])
            for item in data.get("tree", [])
            if item.get("type") == "blob"
        ]

    async def read_file(self, rel_path: Path) -> str:
        # GitHub raw URLs всегда используют прямые слэши
        rel = rel_path.as_posix() if isinstance(rel_path, Path) else str(rel_path)
        url = f"{self.raw_base}{rel}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def close(self):
        await self.session.close()
