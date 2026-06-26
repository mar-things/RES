"""
RES - ui/settings_view.py
=========================
Administrative settings and production readiness checks.
"""

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig
from services.security_service import run_security_audit
from ui.kiosk_view import KioskView


class SettingsView(QWidget):
    """Admin settings surface for language, security, and kiosk mode."""

    def __init__(self, parent=None) -> None:
        """Build the settings view."""
        super().__init__(parent)
        self._kiosk = None
        self._build_ui()
        self._run_audit()

    def _build_ui(self) -> None:
        """Create controls."""
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel(self.tr("System Settings"))
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        language_row = QHBoxLayout()
        language_row.addWidget(QLabel(self.tr("Language")))
        self._language = QComboBox()
        self._language.addItem(self.tr("English"), "en")
        self._language.addItem(self.tr("Spanish"), "es")
        current_index = self._language.findData(AppConfig.LANGUAGE)
        self._language.setCurrentIndex(max(0, current_index))
        language_row.addWidget(self._language)
        language_row.addWidget(QLabel(self.tr("Restart-free switching is applied to new views.")))
        language_row.addStretch()
        root.addLayout(language_row)

        kiosk_btn = QPushButton(self.tr("Open Kiosk Display"))
        kiosk_btn.clicked.connect(self._open_kiosk)
        root.addWidget(kiosk_btn)

        audit_btn = QPushButton(self.tr("Run Security Audit"))
        audit_btn.setObjectName("secondaryButton")
        audit_btn.clicked.connect(self._run_audit)
        root.addWidget(audit_btn)

        self._audit_output = QTextEdit()
        self._audit_output.setReadOnly(True)
        root.addWidget(self._audit_output)

        package = QLabel(
            self.tr(
                "Windows packaging: run `uv run pyinstaller --onefile --windowed main.py`."
            )
        )
        package.setObjectName("subtitle")
        root.addWidget(package)

    def _open_kiosk(self) -> None:
        """Open the fullscreen kiosk board."""
        self._kiosk = KioskView()
        self._kiosk.showFullScreen()

    def _run_audit(self) -> None:
        """Render security audit findings."""
        findings = run_security_audit()
        if not findings:
            self._audit_output.setPlainText(self.tr("No checked security issues found."))
            return
        self._audit_output.setPlainText(
            "\n".join(
                f"[{finding.severity.upper()}] {finding.code}: {finding.message}"
                for finding in findings
            )
        )
