"""
RES — Repair Execution System
==============================
Application entry point.

Initialises the Qt application, loads the appropriate translation,
applies the dark theme, and launches the main window.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo
from PySide6.QtGui import QFontDatabase

from config import AppConfig
from ui.main_window import MainWindow


def load_translation(app: QApplication, language: str) -> QTranslator:
    """
    Load a .qm translation file for the given language code.

    Args:
        app:      The QApplication instance.
        language: ISO 639-1 language code, e.g. 'en' or 'es'.

    Returns:
        The installed QTranslator (keep a reference to prevent GC).
    """
    translator = QTranslator(app)
    qm_path = Path(__file__).parent / "assets" / "translations" / f"res_{language}.qm"
    if qm_path.exists():
        translator.load(str(qm_path))
        app.installTranslator(translator)
    return translator


def load_stylesheet(app: QApplication) -> None:
    """
    Load and apply the Qt dark theme stylesheet.

    Args:
        app: The QApplication instance.
    """
    qss_path = Path(__file__).parent / "assets" / "styles" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def main() -> None:
    """
    Bootstrap and run the RES application.

    Sets up the Qt application, translation, theme, and main window,
    then enters the Qt event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setOrganizationName("RES")

    # Load translation (default: English; change to 'es' for Spanish)
    _translator = load_translation(app, AppConfig.LANGUAGE)

    # Apply dark theme
    load_stylesheet(app)

    # Initialise database tables and seed default data
    from core.database import init_db
    from core.seeds import seed_all
    init_db()
    seed_all()

    # Launch main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()