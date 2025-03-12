# .side_suction/logic/selection_manager.py

import json

import aiofiles
from config.settings import settings


class SelectionManager:
    async def _load_db(self):
        try:
            async with aiofiles.open(settings.databasePath, "r", encoding="utf-8") as f:
                return json.loads(await f.read())
        except Exception as e:
            print(f"No selection loaded: {e}")
            return {}

    async def _save_db(self, data):
        try:
            async with aiofiles.open(settings.databasePath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            print(f"No selection saved: {e}")
            return False

    async def saveSelection(self, project_path, selections):
        all_data = await self._load_db()
        if project_path not in all_data:
            all_data[project_path] = {}
        all_data[project_path].update(selections)
        await self._save_db(all_data)

    async def loadSelection(self, project_path):
        all_data = await self._load_db()
        project_data = all_data.get(project_path)
        return project_data
