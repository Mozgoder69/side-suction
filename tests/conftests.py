# .side_suction/tests/conftest.py
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app():
    """Фикстура для создания экземпляра QApplication, используемая pytest-qt."""
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
