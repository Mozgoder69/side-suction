# .side_suction/config/settings.py

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    allFontSizes: list = [str(size) for size in range(9, 28)]
    defaultFontSize: int = 11
    allFontNames: list = [
        "FantasqueSansM Nerd Font Mono",
        "Cascadia Code",
        "Consolas",
        "Courier",
    ]
    defaultFontName: str = "FantasqueSansM Nerd Font Mono"
    databasePath: Path = Path(__file__).parent.parent / "database\\selections.json"
    stylesheetPath: Path = Path(__file__).parent / "styles.qss"
    maxFileSize: int = 33554433  # (2 << (3 << 3)) + 1 | (1 << 25) + 1 | 2**25 + 1 |


# Initialize settings
settings = Settings()
