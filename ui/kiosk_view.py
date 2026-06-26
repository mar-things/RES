"""
RES - ui/kiosk_view.py
======================
Fullscreen workshop floor display without customer PII.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.process_engine import get_all_active_vehicle_logs
from core.time_tracker import format_duration


class KioskView(QWidget):
    """No-PII active vehicle board for workshop floor displays."""

    def __init__(self, parent=None) -> None:
        """Create and start the kiosk auto-refresh."""
        super().__init__(parent)
        self._build_ui()
        self.refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(15_000)

    def _build_ui(self) -> None:
        """Build the kiosk board layout."""
        root = QVBoxLayout(self)
        title = QLabel(self.tr("Workshop Floor Board"))
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        scroll.setWidget(self._container)
        root.addWidget(scroll)

    def refresh(self) -> None:
        """Refresh active vehicle cards."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, log in enumerate(get_all_active_vehicle_logs()):
            label = QLabel(
                self.tr("{plate}\n{process}\nElapsed: {elapsed}").format(
                    plate=log["plate"],
                    process=log["process_name"],
                    elapsed=format_duration(log["elapsed_minutes"]),
                )
            )
            label.setObjectName("vehicleCard")
            label.setProperty("color", log["color"])
            label.setMinimumSize(220, 100)
            self._grid.addWidget(label, index // 4, index % 4)
