# .side_suction/logic/selection_manager.py

import json
from pathlib import Path

import aiofiles
from config.settings import settings
from logic.status_manager import report_result


class SelectionManager:
    async def _load_db(self):
        try:
            async with aiofiles.open(settings.databasePath, "r", encoding="utf-8") as f:
                return json.loads(await f.read())
        except Exception as e:
            report_result(f"No selection loaded: {e}", "Load Error", 1)
            return {}

    async def _save_db(self, data):
        try:
            async with aiofiles.open(settings.databasePath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            report_result(f"No selection saved: {e}", "Save Error", 1)
            return False

    async def saveSelection(self, path, selections):
        data = await self._load_db()
        if path not in data:
            data[path] = {}
        data[path].update(selections)
        await self._save_db(data)

    async def loadSelection(self, path):
        data = await self._load_db()
        return data.get(path)
